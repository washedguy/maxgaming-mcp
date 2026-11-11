import os
from unittest.mock import AsyncMock, patch

from mcp import Client as MCPClient
from maxgaming_mcp.server import mcp

FIXTURES = os.path.join(os.path.dirname(__file__), "fixtures")


def _read(name):
    return open(os.path.join(FIXTURES, name)).read()


class TestMCP:
    async def test_tool_discovery(self):
        async with MCPClient(mcp) as client:
            tools = await client.list_tools()
            names = {t.name for t in tools.tools}
            assert names == {"list_storefronts", "search_products", "browse_page", "get_product"}
            assert all(t.output_schema for t in tools.tools)

    async def test_list_storefronts(self):
        async with MCPClient(mcp) as client:
            r = await client.call_tool("list_storefronts")
            assert not r.is_error
            assert len(r.structured_content["storefronts"]) == 9

    async def test_bad_price_range(self):
        async with MCPClient(mcp) as client:
            r = await client.call_tool("search_products", {"query": "test", "min_price": 100, "max_price": 10})
            assert r.is_error

    async def test_search_with_mock(self):
        result = {"retailer": "maxgaming", "country": "us", "language": "en", "query": "test",
                  "products": [], "count": 0, "total_products": 0, "page": 1, "next_page": None,
                  "paging": {"current_page": 1, "page_count": 0, "max_page": 1},
                  "source": "search_page", "coverage": "search_page"}
        with patch("maxgaming_mcp.server.Client") as factory:
            factory.return_value.search = AsyncMock(return_value=result)
            async with MCPClient(mcp) as client:
                r = await client.call_tool("search_products", {"query": "test"})
                assert not r.is_error
                assert r.structured_content["count"] == 0

    async def test_get_product_with_mock(self):
        result = {"retailer": "maxgaming", "country": "us", "language": "en", "reference": "30041",
                  "found": True, "product": {"id": "30041", "title": "Test", "brand": "Razer",
                  "price": 129.99, "currency": "USD", "url": "https://example.com", "resolved_url": "https://example.com",
                  "delivery": {"status": "available", "retailer_status": "In stock", "retailer_code": None, "earliest": None},
                  "variants": [], "marketplace_offers": [], "offers_coverage": "none",
                  "description": None, "description_marketing": None, "images": [], "rating": {},
                  "categories": [], "features": [], "ean": None}, "reason": None,
                  "observed_at": None, "cache": None}
        with patch("maxgaming_mcp.server.Client") as factory:
            factory.return_value.product = AsyncMock(return_value=result)
            async with MCPClient(mcp) as client:
                r = await client.call_tool("get_product", {"reference": "30041"})
                assert not r.is_error
                assert r.structured_content["found"] is True