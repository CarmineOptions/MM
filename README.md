
## ⚠️ Disclaimer

This project is for **educational and research purposes only**. It does **not constitute financial advice** or a recommendation to trade. Use it at your own risk.

We make **no guarantees** about performance, profitability, or safety. You are solely responsible for any outcomes, and must ensure compliance with applicable laws and regulations.


# MM bot

This MM bot is heavily inspired by https://github.com/blockworks-foundation/mango-explorer/
its goal and purpose is to be an educational material to whoever wants to learn about market making
and about Starknet.

The MM bot integrates Remus DEX and Ekubo DEX. In case of Ekubo it integrates pools that allow 
for usage of limit orders.

## Logic

The MM bot follows this logic:
1) Query all required data - oracle prices, orderbook, own orders,...
2) Calculate fair price.
3) Calculate optimal market orders around the fair price. Adjusted for current inventory.
4) Reconcile between optimal and existing market orders.
5) Push transactions (create/cancel) to Starknet.

## Remus DEX integration

Remus DEX integration is implemented in `RemusDexClient` and in `RemusDexView` available in 
`/MM/venues/remus/remus.py`

## Ekubo DEX integration

Ekubo DEX integration is implemented in `EkuboClient` and in `EkuboView` available in 
`/MM/venues/ekubo/ekubo.py`

## Quick Start

The purpose of this bot is **educational and research purposes only**. It is meant to show how 
a market making bot can be implemented and to show how integration to Remus and Ekubo on Starknet 
can be implemented.

### Configuration

To be able to run the MM bot you have to set up a configuration file.
```
[account]
# Configuration of account and connection

rpc_url_env = "RPC_URL"
wallet_address_env = "WALLET_ADDRESS"
password_path_env = "KEYSTORE_PWD_PATH"
keystore_path_env = "KEYSTORE_PATH"

[market]
venue = 'remus'
market_id = 2  # market_id has to be queried from Remus DEX smart contract.

[price_source]
base_asset = "STRK"
quote_asset = "USDC"
price_source = 'binance'

[reconciler]
name = 'bounded_reconciler'
max_relative_distance_from_fp = "0.075" # Threshold for an order to be considered too far from FP to be best order (it is considered deep order).
min_relative_distance_from_fp = "0.0005" # Threshold for an order to be considered too close to FP to exist -> if closer kill the order.
minimal_remaining_size = "0"  # in Base asset
max_orders_per_side = 1  # Number of orders allowed on bid and on ask sides.

[tx_builder]
name = 'bundling_tx_builder'  # Transaction builder. For example "bundling_tx_builder" bundles transactions into a multicall.

[[orderchain]]
name = 'skew_fair_price_on_position'
bias = '0.005'
max_skew = '0.002'

[[orderchain]]
name = 'fixed_params'
target_relative_distance_from_fp = "0.005"  # Where best order is created 
order_size_quote = "10"  # In Quote asset (human-readable)
```

### Run

After config is set up you can run the MM bot with docker

```
sudo docker compose up -d
```

or in a local environment
```
KEYSTORE_PWD_PATH=$KEYSTORE_PWD_PATH KEYSTORE_PATH=$KEYSTORE_PATH WALLET_ADDRESS=$WALLET_ADDRESS RPC_URL=$RPC_URL PYTHONPATH=. python3 ./MM/main.py --cfg ./cfg/example_cfg.toml
```
