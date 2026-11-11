from unittest.mock import AsyncMock

import pytest

from maxgaming_mcp.shop import cache


@pytest.mark.asyncio
async def test_cache_hit():
    cache._entries.clear()
    result = {"retailer": "maxgaming", "count": 5, "products": []}
    fetch = AsyncMock(return_value=result)
    first = await cache.cached_call("search", ("us", "en", "mouse"), False, fetch)
    assert first["cache"]["hit"] is False
    second = await cache.cached_call("search", ("us", "en", "mouse"), False, fetch)
    assert second["cache"]["hit"] is True
    assert fetch.call_count == 1


@pytest.mark.asyncio
async def test_fresh_bypasses_cache():
    cache._entries.clear()
    result = {"retailer": "maxgaming", "count": 5, "products": []}
    fetch = AsyncMock(return_value=result)
    await cache.cached_call("search", ("us", "en", "mouse"), False, fetch)
    await cache.cached_call("search", ("us", "en", "mouse"), True, fetch)
    assert fetch.call_count == 2


@pytest.mark.asyncio
async def test_missing_product_not_cached():
    cache._entries.clear()
    result = {"retailer": "maxgaming", "found": False, "product": None}
    fetch = AsyncMock(return_value=result)
    await cache.cached_call("product", ("us", "en", "999"), False, fetch)
    await cache.cached_call("product", ("us", "en", "999"), False, fetch)
    assert fetch.call_count == 2