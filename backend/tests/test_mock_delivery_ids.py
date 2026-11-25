"""Repeated synthetic deliveries must not violate the message ID uniqueness constraint."""
import asyncio
import pytest

from app.services.instagram.client import instagram_client


@pytest.mark.parametrize("method,payload", [
    ("send_text_message", "Same reply"),
    ("send_image_message", "https://example.com/ring.jpg"),
    ("send_product_cards", [{"title": "Ring"}]),
])
def test_mock_delivery_ids_are_unique(method, payload):
    async def send_twice():
        send = getattr(instagram_client, method)
        first = await send("test_recipient", payload, "test_token")
        second = await send("test_recipient", payload, "test_token")
        assert first["message_id"] != second["message_id"]
    asyncio.run(send_twice())
