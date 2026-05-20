import httpx

BASE_URL = "https://localhost:44389/"


async def cancel_order(order_id: str):

    async with httpx.AsyncClient() as client:

        response = await client.post(
            f"{BASE_URL}/orders/{order_id}/cancel"
        )

        response.raise_for_status()

        return response.json()


async def refund_order(order_id: str):

    async with httpx.AsyncClient() as client:

        response = await client.post(
            f"{BASE_URL}/orders/{order_id}/refund"
        )

        response.raise_for_status()

        return response.json()