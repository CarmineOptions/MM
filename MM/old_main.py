from typing import Any, Tuple
import argparse
import asyncio
import logging
import requests
import sys
from remus import RemusManager

from starknet_py.net.full_node_client import FullNodeClient
# from starknet_py.hash.selector import get_selector_from_name
# from starknet_py.net.client_models import Call
from starknet_py.contract import Contract
from starknet_py.net.account.account import Account
from starknet_py.net.signer.stark_curve_signer import KeyPair
from starknet_py.net.models.chains import StarknetChainId
from starknet_py.net.client_errors import ClientError
from starknet_py.transaction_errors import TransactionNotReceivedError
# from starknet_py.utils.typed_data import EnumParameter
# from starknet_py.net.client_models import ResourceBounds

from config import token_config, env_config, market_config, MAX_FEE, SOURCE_DATA, SLEEPER_SECONDS_BETWEEN_REQUOTING



async def async_main():
    """Main async execution function."""
    args = parse_arguments()
    setup_logging(args.log_level)

    logging.info("Starting Simple Stupid Market Maker")

    account = get_account()

    # FIXME: This was half done, yet merged to master. Keeping it for now for the sake of making
    # the code run (without having enough time to fix things).
    # TODO: the remus_manager is f*** up, not sure whether to remove and redo completely.
    remus_contract = await Contract.from_address(address = env_config.remus_address, provider = account)

    all_remus_cfgs = await remus_contract.functions['get_all_market_configs'].call()

    # remus_manager = RemusManager(account, env_config, remus_contract, all_remus_cfgs)

    # Unlimited approvals
    nonce = await account.get_nonce()
    for i, market_id in enumerate([x[0] for x in all_remus_cfgs[0] if x[0] in market_config.market_maker_cfg]):
        market_cfg, market_maker_cfg = get_market_cfg(all_remus_cfgs, market_id)
        base_token_contract = await Contract.from_address(address = market_cfg[1]['base_token'], provider = account)
        quote_token_contract = await Contract.from_address(address = market_cfg[1]['quote_token'], provider = account)
        await setup_unlimited_approvals(account, remus_contract, market_cfg, base_token_contract, quote_token_contract, nonce+2*i)
    await asyncio.sleep(15)
    
    while True:
        await asyncio.sleep(SLEEPER_SECONDS_BETWEEN_REQUOTING)
        for market_id in [x[0] for x in all_remus_cfgs[0] if x[0] in market_config.market_maker_cfg]:
            try:
                market_cfg, market_maker_cfg = get_market_cfg(all_remus_cfgs, market_id)

                # 1) Claim tokens
                # TODO ideally the claim would happen after the order deletion.
                await claim_tokens(market_cfg, remus_contract)

                # 2) Get prices
                r = requests.get(SOURCE_DATA[market_id])
                fair_price = float(sorted(r.json(), key = lambda x: x['T'])[-1]['p'])
                logging.info('Fair price queried: %s.', fair_price)

                # 3) Get orders
                my_orders = await remus_contract.functions['get_all_user_orders'].call(user=env_config.wallet_address)

                bids = [x for x in my_orders[0] if x['market_id'] == market_id and x['order_side'].variant == 'Bid']
                asks = [x for x in my_orders[0] if x['market_id'] == market_id and x['order_side'].variant == 'Ask']
                bids = sorted(bids, key = lambda x: -x['price'])
                asks = sorted(asks, key = lambda x: -x['price'])
                logging.debug(f'My remaining orders queried: {bids}, {asks}.')
                pretty_print_orders(asks, bids)

                # 4) Get position (balance of + open orders)
                # TODO: the remus_manager is messed up, it has to be debugged and fixed
                # base_token_contract = await remus_manager.get_base_contract()
                # quote_token_contract = await remus_manager.get_quote_contract()

                base_token_contract = await Contract.from_address(address = market_cfg[1]['base_token'], provider = account)
                quote_token_contract = await Contract.from_address(address = market_cfg[1]['quote_token'], provider = account)

                total_possible_position_base, total_possible_position_quote = await get_position(
                    market_cfg, account, asks, bids, base_token_contract, quote_token_contract
                )

                # 5) Calculate optimal quotes
                to_be_canceled, to_be_created = get_optimal_quotes(asks, bids, market_maker_cfg, market_cfg, fair_price)

                # 6) update quotes
                nonce = await update_delete_quotes(account, market_cfg, remus_contract, to_be_canceled, to_be_created, base_token_contract, quote_token_contract)
                assert nonce is not None
                assert nonce != 0
                await update_best_quotes(account, market_id, market_cfg, remus_contract, to_be_canceled, to_be_created, base_token_contract, quote_token_contract, nonce)

                logging.info("Application running successfully.")
                # assert False
            except ClientError as e:
                # ClientError can be
                # starknet_py.net.client_errors.ClientError: Client failed with code 63. Message: An unexpected error occurred. Data: HTTP status server error (502 Bad Gateway) for url (https://alpha-mainnet.starknet.io/gateway/add_transaction)
                # Client failed with code 55. Message: Account validation failed. Data: Invalid transaction nonce of contract at address 0x0463de332da5b88a1676bfb4671dcbe4cc1a9147c46300a1658ed43a22d830c3. Account nonce: 0x0000000000000000000000000000000000000000000000000000000000022046; got: 0x0000000000000000000000000000000000000000000000000000000000022043
                logging.error("A ClientError error occurred: %s", str(e), exc_info=True)
                logging.error("Restarting in 5 seconds!")

                await asyncio.sleep(5)

                # Often the main fails because of the Account not having a proper nonce. So let's re-initialize it.
                account = get_account()
                remus_contract = await Contract.from_address(address = env_config.remus_address, provider = account)

            except TransactionNotReceivedError as e:
                # starknet_py.transaction_errors.TransactionNotReceivedError: Transaction was not received on Starknet.

                logging.error("A ClientError error occurred: %s", str(e), exc_info=True)
                logging.error("Restarting in 5 seconds!")

                account = get_account()
                remus_contract = await Contract.from_address(address = env_config.remus_address, provider = account)

            except Exception as e:
                logging.error("An error occurred: %s", str(e), exc_info=True)
                logging.error("Starting to cancel all - wait.")

                await asyncio.sleep(5)

                # Often the main fails because of the Account not having a proper nonce. So let's re-initialize it.
                account = get_account()
                remus_contract = await Contract.from_address(address = env_config.remus_address, provider = account)

                # Get all existing orders
                logging.error("Starting to cancel all - get_all_user_orders.")
                my_orders = await remus_contract.functions['get_all_user_orders'].call(user=env_config.wallet_address)
                logging.error("Starting to cancel all - my_orders:{%s}.", my_orders)

                # Cancel all existing orders
                nonce = await account.get_nonce()
                for i, order in enumerate(my_orders[0]):
                    await (await remus_contract.functions['delete_maker_order'].invoke_v1(
                        maker_order_id=order['maker_order_id'],
                        max_fee=int(MAX_FEE/10),
                        nonce = nonce + i
                    )).wait_for_acceptance()

                # Waiting a little and checking existing orders
                logging.error("Ending cancel all - wait before exit.")
                await asyncio.sleep(15)
                my_orders = await remus_contract.functions['get_all_user_orders'].call(user=env_config.wallet_address)
                logging.error("Ending cancel all - remaining my_orders:{%s}.", my_orders)

                #Claiming unclaimed
                logging.error("Ending cancel all - claiming unclaimed.")
                for market_id in market_config.market_maker_cfg.keys():
                    try:
                        market_cfg, market_maker_cfg = get_market_cfg(all_remus_cfgs, market_id)
                        await claim_tokens(market_cfg, remus_contract)
                    except:
                        logging.error("An error while closing session occured: %s", str(e), exc_info=True)

                logging.error("Ending cancel all - FINISHED.")

                # sys.exit(1)


if __name__ == "__main__":
    asyncio.run(async_main())

