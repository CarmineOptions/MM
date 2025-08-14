# type: ignore

import logging
from decimal import Decimal

import httpx
from paradex_py.paradex import Paradex
from paradex_py.common.order import (
    Order as ParadexOrder,
    OrderType as ParadexOrderType,
    OrderSide as ParadexOrderSide
)

from marketmaking.order import BasicOrder, FutureOrder

class ParadexClient:
    def __init__(self, l1_address: str, l2_private_key: str):
        self.px = Paradex(
            env = 'prod',
            l1_address=l1_address,
            l2_private_key=l2_private_key
        )

    async def get_all_open_orders(self) -> list[BasicOrder]:
        res =  await self._get_authorized('orders', params = None)
        res.raise_for_status()
        raw_orders: list[dict] = res.json()['results']
        return [
            _paradex_response_order_to_basic_order(i)
            for i in raw_orders
        ]

    async def get_all_open_orders_for_market(self, market: str):
        res = await self._get_authorized('orders', {'market': market})
        res.raise_for_status()
        raw_orders: list[dict] = res.json()['results']
        return [
            _paradex_response_order_to_basic_order(i)
            for i in raw_orders
        ]

    async def cancel_order(self, order: BasicOrder):
        await self._delete_authorized(path = f'orders/{order.order_id}', params = None, payload = None)       

    async def cancel_all_orders(self):
        await self._delete_authorized(path = 'orders', params = None, payload = None)

    async def cancel_orders_batch(self, orders: list[BasicOrder]):
        await self._delete_authorized(
            path = 'orders/batch',
            params = None,
            payload = {
                'order_ids': [i.order_id for i in orders]
            }
        )

    async def _submit_single_order(self, order: FutureOrder):

        px_order = _future_order_to_paradex_order(order)
        
        if self.px.account is None:
            raise ValueError("No account to sign order with")

        px_order.signature = self.px.account.sign_order(px_order)
        order_payload = px_order.dump_to_dict()

        return await self._post_authorized(path="orders", payload=order_payload)
    
    async def _submit_orders_batch(self, orders: list[FutureOrder]):
        if self.px.account is None:
            raise ValueError("No account to sign order with")

        px_orders = [
            _future_order_to_paradex_order(i)
            for i in orders
        ]

        order_payloads = []
        for px_order in px_orders:
            px_order.signature = self.px.account.sign_order(px_order)
            order_payload = px_order.dump_to_dict()
            order_payloads.append(order_payload)

        return await self._post_authorized(path="orders/batch", payload=order_payloads)

    # PRIVATE FUNCTIONS

    async def _get_authorized(self, path: str, params: dict | None):
        self.px.api_client._validate_auth()
        return await self._get(path = path, params = params)

    async def _get(self, path: str, params: dict | None):
        url = f"{self.px.api_client.api_url}/{path}"

        async with httpx.AsyncClient() as client:
            res = await client.get(
                url=url,
                params = params,
                headers = self.px.api_client.client.headers
            )
        
        return res
    
    async def _delete_authorized(self, path: str, params: dict | None, payload: dict|None):
        self.px.api_client._validate_auth()
        await self._delete(path=path, params=params, payload=payload)

    async def _delete(self, path: str, params: dict | None, payload: dict | None):
        url = f"{self.px.api_client.api_url}/{path}"

        async with httpx.AsyncClient() as client:
            await client.request(
                method = 'DELETE',
                url = url,
                params = params,
                headers = self.px.api_client.client.headers,
                json = payload
            )

    async def _post_authorized(self, path: str, payload: dict | list):
        self.px.api_client._validate_auth()
        return await self._post(path, payload)

    async def _post(self, path: str, payload: dict | list):
        url = f"{self.px.api_client.api_url}/{path}"
        async with httpx.AsyncClient() as client:
            return await client.request(
                method="POST",
                url=url,
                json=payload,
                headers=self.px.api_client.client.headers,
            )
        

def _paradex_response_order_to_basic_order(o: dict[str, str]) -> BasicOrder:
    logging.error("No market id!!!!")

    side = 'Bid' if o['side'].lower() == 'buy' else 'Ask'

    return BasicOrder(
        price = Decimal(o['price']),
        amount = Decimal(o['size']),
        amount_remaining = Decimal(o['size_remaining']),
        order_id = int(o['id']),
        market_id = 0,
        order_side = side,
        entry_time = int(o['published_at']),
        venue = 'Paradex'
    )

def _future_order_to_paradex_order(o: FutureOrder) -> ParadexOrder:
    if 1 == 1:
        raise NotImplementedError("Missing market-id <> paradex market mapping")
    side = ParadexOrderSide.Buy if o.order_side.lower() == 'bid' else ParadexOrderSide.Sell
    
    return ParadexOrder(
        market='...',
        order_type= ParadexOrderType.Limit,
        order_side=side,
        size = o.amount
    )