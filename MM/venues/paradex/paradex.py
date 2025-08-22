
from typing import TypedDict

import httpx

from paradex_py.paradex import Paradex
from paradex_py.common.order import (
    Order as ParadexOrder,
)

class ParadexResponseOrder(TypedDict):
    id: str
    account: str
    market: str
    side: str
    type: str
    size: str
    remaining_size: str
    price: str
    status: str
    created_at: int
    last_updated_at: int
    timestamp: int
    cancel_reason: str
    client_id: str
    seq_no: int
    instruction: str
    avg_fill_price: str
    stp: str
    received_at: str
    published_at: str
    flags: list[str]
    trigger_price: str


class ParadexClient:
    def __init__(self, l1_address: str, l2_private_key: str):
        self.px = Paradex(
            env = 'prod',
            l1_address=l1_address,
            l2_private_key=l2_private_key
        )

        self._client = httpx.AsyncClient()

    async def get_all_open_orders(self) -> list[ParadexResponseOrder]:
        request =  self._get_authorized_request('orders', params = None)

        res = await self._client.send(request)
        res.raise_for_status()
        
        raw_orders: list[ParadexResponseOrder] = res.json()['results']
        return raw_orders

    async def get_all_open_orders_for_market(self, market: str) -> list[ParadexResponseOrder]:
        request = self._get_authorized_request('orders', {'market': market})

        res = await self._client.send(request)
        res.raise_for_status()

        raw_orders: list[ParadexResponseOrder] = res.json()['results']
        return raw_orders

    # Direct methods for sending/canceling orders

    async def cancel_order(self, id: str) -> httpx.Response:
        request = self.get_cancel_order_request(id)
        return await self._client.send(request)

    async def cancel_all_orders(self) -> httpx.Response:
        request = self.get_cancel_all_orders_request()
        return await self._client.send(request)

    async def cancel_orders_batch(self, ids: list[str]) -> httpx.Response:
        request = self.get_cancel_orders_batch_request(ids)
        return await self._client.send(request)   

    async def submit_single_order(self, order: ParadexOrder) -> httpx.Response:
        request = self.get_submit_single_order_request(order)
        return await self._client.send(request)
    
    async def submit_orders_batch(self, orders: list[ParadexOrder]) -> httpx.Response:
        request = self.get_submit_orders_batch_request(orders)
        return await self._client.send(request)

    # Methods that return a Request for sending/canceling orders
    def get_cancel_order_request(self, id: str) -> httpx.Request:
        return self._delete_authorized_request(path = f'orders/{id}', params = None, payload = None)       
    
    def get_cancel_all_orders_request(self) -> httpx.Request:
        return self._delete_authorized_request(path = 'orders', params = None, payload = None)

    def get_cancel_orders_batch_request(self, ids: list[str]) -> httpx.Request:
        return self._delete_authorized_request(
            path = 'orders/batch',
            params = None,
            payload = {
                'order_ids': ids
            }
        )

    def get_submit_single_order_request(self, order: ParadexOrder) -> httpx.Request:

        if self.px.account is None:
            raise ValueError("No account to sign order with")

        order.signature = self.px.account.sign_order(order)
        order_payload = order.dump_to_dict()

        request = self._post_authorized_request(path="orders", payload=order_payload)
        return request

    def get_submit_orders_batch_request(self, orders: list[ParadexOrder]) -> httpx.Request:
        if self.px.account is None:
            raise ValueError("No account to sign order with")

        order_payloads: list[dict[str, str]] = []
        for px_order in orders:
            px_order.signature = self.px.account.sign_order(px_order)
            order_payload = px_order.dump_to_dict()
            order_payloads.append(order_payload)

        request = self._post_authorized_request(path="orders/batch", payload=order_payloads)

        return request

    # PRIVATE FUNCTIONS

    def _get_authorized_request(self, path: str, params: dict[str, str] | None) -> httpx.Request:
        self.px.api_client._validate_auth() # type: ignore[no-untyped-call]
        return self._get_request(path = path, params = params)

    def _get_request(self, path: str, params: dict[str, str] | None) -> httpx.Request:
        url = f"{self.px.api_client.api_url}/{path}"
        request = self._client.build_request(
            url = url,
            method = "GET",
            params = params,
            headers = self.px.api_client.client.headers
        )
        return request
    
    def _delete_authorized_request(self, path: str, params: dict[str, str] | None, payload: dict[str, str | list[str]] | None) -> httpx.Request:
        self.px.api_client._validate_auth() # type: ignore[no-untyped-call]
        return self._delete_request(path=path, params=params, payload=payload)

    def _delete_request(self, path: str, params: dict[str, str] | None, payload: dict[str, str | list[str]] | None) -> httpx.Request:
        url = f"{self.px.api_client.api_url}/{path}"
        request = self._client.build_request(
            url = url,
            method = 'DELETE',
            params = params,
            headers = self.px.api_client.client.headers,
            json = payload
        )
        return request

    def _post_authorized_request(self, path: str, payload: dict[str, str] | list[str] | list[dict[str, str]]) -> httpx.Request:
        self.px.api_client._validate_auth() # type: ignore[no-untyped-call]
        return self._post_request(path, payload)

    def _post_request(self, path: str, payload: dict[str, str] | list[str] | list[dict[str, str]]) -> httpx.Request:
        url = f"{self.px.api_client.api_url}/{path}"

        request = self._client.build_request(
            method = 'POST',
            url = url,
            json = payload,
            headers = self.px.api_client.client.headers
        )
        
        return request

