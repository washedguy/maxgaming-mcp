import os
from unittest.mock import AsyncMock, patch

import pytest

from maxgaming_mcp.client import Client, RetailerError

FIXTURES = os.path.join(os.path.dirname(__file__), "fixtures")


def _read(name):
    return open(os.path.join(FIXTURES, name)).read()


@pytest.mark.asyncio
async def test_search_page_parses_fixture():
    text = _read("search_us.html")
    with patch("maxgaming_mcp.shop.search.get", new_callable=AsyncMock) as mock_get:
        mock_resp = AsyncMock()
        mock_resp.status_code = 200
        mock_resp.text = text
        mock_resp.url = "https://us.maxgaming.com/search?q=mouse"
        mock_get.return_value = mock_resp
        client = Client("us")
        result = await client.search("mouse")
        assert result["count"] > 0
        assert result["products"][0]["id"] == "30041"


@pytest.mark.asyncio
async def test_product_page_parses_fixture():
    text = _read("product_us.html")
    with patch("maxgaming_mcp.shop.products.get", new_callable=AsyncMock) as mock_get:
        mock_resp = AsyncMock()
        mock_resp.status_code = 200
        mock_resp.text = text
        mock_resp.url = "https://us.maxgaming.com/us/wireless-mouses/razer-viper-v3-pro-black"
        mock_get.return_value = mock_resp
        client = Client("us")
        result = await client.product("https://us.maxgaming.com/us/wireless-mouses/razer-viper-v3-pro-black")
        assert result["found"] is True
        assert result["product"]["title"] == "Viper V3 Pro Wireless Gaming Mouse - Black"


@pytest.mark.asyncio
async def test_invalid_country():
    with pytest.raises(ValueError):
        Client("xx")


@pytest.mark.asyncio
async def test_invalid_url():
    client = Client("us")
    with pytest.raises(RetailerError):
        await client.product("https://evil.com/product/123")


@pytest.mark.asyncio
async def test_not_found_product():
    with patch("maxgaming_mcp.shop.products.get", new_callable=AsyncMock) as mock_get:
        mock_resp = AsyncMock()
        mock_resp.status_code = 404
        mock_get.return_value = mock_resp
        client = Client("us")
        result = await client.product("https://us.maxgaming.com/us/wireless-mouses/nonexistent")
        assert result["found"] is False
        assert result["reason"] == "product_url_not_found"