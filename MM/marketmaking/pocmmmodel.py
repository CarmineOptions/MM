from decimal import Decimal
import logging

from venues.remus.remus_market_configs import RemusMarketConfig
from cfg.cfg_classes import MarketMakerConfig
from marketmaking.waccount import WAccount
from marketmaking.order import BasicOrder, FutureOrder
from marketmaking.statemarket import StateMarket


class POCMMModel:
    # POCMMModel contains the logic from the POC market maker. The goal is to test the SW and build the model later.
    # The POCMMModel also contains reconciliation.
    def __init__(
        self,
        market_cfg: RemusMarketConfig,
        market_maker_cfg: MarketMakerConfig,
    ) -> None:
        self._logger: logging.Logger = logging.getLogger(self.__class__.__name__)
        self._logger.info("Initializing POCMMModel")

        self.market_cfg = market_cfg
        self.market_maker_cfg: MarketMakerConfig = market_maker_cfg

    def get_optimal_orders(
        self, account: WAccount, state_market: StateMarket
    ) -> tuple[list[BasicOrder], list[FutureOrder]]:
        if not isinstance(state_market.oracle, Decimal):
            self._logger.error("State market oracle not initialized")
            return [], []

        fair_price = state_market.oracle

        return self._get_optimal_quotes(
            asks=state_market.my_orders["asks"],
            bids=state_market.my_orders["bids"],
            market_maker_cfg=self.market_maker_cfg,
            fair_price=fair_price,
        )

    def _get_optimal_quotes(
        self,
        asks: list[BasicOrder],
        bids: list[BasicOrder],
        market_maker_cfg: MarketMakerConfig,
        fair_price: Decimal,
    ) -> tuple[list[BasicOrder], list[FutureOrder]]:
        """
        If an existing quote has lower than market_maker_cfg['minimal_remaining_quote_size'] quantity, it is requoted.

        Optimal quote is in market_maker_cfg['target_relative_distance_from_FP'] distance from the FP, where FP is binance price.
        The order is never perfect and market_maker_cfg['max_distance_from_FP'] from optimal quote price level is allowed, meaning
        that an old best quote is considered deep quote and new best is created if the distance is outside of what is ok.

        If the Best quote gets too close to FP, less than market_maker_cfg['min_distance_from_FP'] distance, it is canceled.
        """
        to_be_canceled: list[BasicOrder] = []
        to_be_created: list[FutureOrder] = []

        # FIXME: This is weird, is it really the case that the quote decimals are not needed here
        # quote_decimals = token_config.decimals[market_cfg[1]['quote_token']]  # for example USDC

        for side, side_name in [(asks, "ask"), (bids, "bid")]:
            to_be_canceled_side: list[BasicOrder] = []

            for order in side:
                # If the remaining order size is too small requote (cancel order)
                if (
                    order.amount_remaining * order.price
                    < market_maker_cfg.minimal_remaining_size
                ):
                    self._logger.info(
                        f"Canceling order because of insufficient amount. amount remaining: {order.amount_remaining}, minimal remaining: {market_maker_cfg.minimal_remaining_size}"
                    )
                    self._logger.debug(
                        f"Canceling order because of insufficient amount. order: {order}"
                    )
                    to_be_canceled_side.append(order)
                    continue
                if (
                    (side_name == "bid")
                    and (
                        (1 - market_maker_cfg.min_relative_distance_from_FP)
                        * fair_price
                        < order.price
                    )
                ) or (
                    (side_name == "ask")
                    and (
                        order.price
                        < (1 + market_maker_cfg.min_relative_distance_from_FP)
                        * fair_price
                    )
                ):
                    self._logger.info(
                        f"Canceling order because too close to FP. "
                        f"fair_price: {fair_price}, order price: {order.price}"
                    )
                    self._logger.debug(
                        f"Canceling order because too close to FP. order: {order}"
                    )
                    to_be_canceled_side.append(order)
            # If there is too many orders in the market that are not being canceled, cancel those with the most distant price from FP
            # to a point that only the "allowed" number of orders is being kept.
            if (
                len(side) - len(to_be_canceled_side)
                > market_maker_cfg.max_orders_per_side
            ):
                # assumes "side" (e.g. asks and bids) are ordered from the best to the deepest
                to_be_canceled_side.extend(
                    [order for order in side if order not in to_be_canceled_side][
                        market_maker_cfg.max_orders_per_side :
                    ]
                )
            to_be_canceled.extend(to_be_canceled_side)

            # Create best order if there is no best order
            remaining = [order for order in side if order not in to_be_canceled]
            ordered_remaining = sorted(
                remaining, key=lambda x: x.price if side_name == "ask" else -x.price
            )
            if (
                (not ordered_remaining)
                or (
                    (side_name == "bid")
                    and
                    # ordered_remaining will not be empty here (`or` performs short-circuit eval)
                    (
                        ordered_remaining[0].price
                        < (1 - market_maker_cfg.max_relative_distance_from_FP)
                        * fair_price
                    )
                )
                or (
                    (side_name == "ask")
                    and
                    # ordered_remaining will not be empty here (`or` performs short-circuit eval)
                    (
                        (1 + market_maker_cfg.max_relative_distance_from_FP)
                        * fair_price
                        < ordered_remaining[0].price
                    )
                )
            ):
                if side_name.lower() == "ask":
                    optimal_price = fair_price * (
                        1 + market_maker_cfg.target_relative_distance_from_FP
                    )
                else:
                    optimal_price = fair_price * (
                        1 - market_maker_cfg.target_relative_distance_from_FP
                    )
                optimal_amount = market_maker_cfg.order_size / (optimal_price)

                new_order = FutureOrder(
                    order_side=side_name,
                    amount=optimal_amount,
                    price=optimal_price,
                    platform="Starknet",  # Not used rn, just a placeholder
                    venue="Remus",  # Not used rn, just a placeholder
                )
                to_be_created.append(new_order)

        self._logger.info(
            f"Optimal quotes calculated: to_be_canceled: {len(to_be_canceled)}, to_be_created: {len(to_be_created)}"
        )
        self._logger.debug(
            f"Optimal quotes calculated: to_be_canceled: {to_be_canceled}, to_be_created: {to_be_created}"
        )
        return to_be_canceled, to_be_created
