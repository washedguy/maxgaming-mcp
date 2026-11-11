"""Search MaxGaming pages."""
import re
from urllib.parse import quote, unquote, urlencode, urljoin, urlsplit

from .errors import RetailerError
from .http import get
from .parsing import parse_search_page


async def search_page(self, query, page=1, filters=None, order_by=None):
    """Read the public search page."""
    params = [("q", query), ("page", str(page))]
    if order_by:
        params.append(("orderBy", order_by))
    url = f"{self.base}/search?{urlencode(params, quote_via=quote)}"
    response = await get(self, url)
    if response.status_code == 404:
        raise RetailerError("Search page not found.", code="not_found")
    if response.status_code != 200:
        raise RetailerError(f"Search page returned HTTP {response.status_code}.")
    result = parse_search_page(response.text, self.base, str(response.url))
    result["retailer"] = "maxgaming"
    result["country"] = self.country
    result["language"] = self.language
    result["query"] = query
    result["source"] = "search_page"
    result["coverage"] = "search_page"
    result["redirected_url"] = None
    result["related_pages"] = None
    result["local_filters"] = []
    result["note"] = "The retailer may return products unrelated to the query. Prices and availability are snapshots."

    # Apply local filters
    products = result["products"]
    local_filters = []
    if filters:
        for item in filters:
            field, value = item.split(":", 1) if ":" in item else (item, "")
            if field == "brand":
                products = [p for p in products if p.get("brand") and p["brand"].casefold() == value.casefold()]
                local_filters.append(f"brand:{value}")
            elif field == "min_price":
                try:
                    mn = float(value)
                    products = [p for p in products if isinstance(p.get("price"), (int, float)) and p["price"] >= mn]
                    local_filters.append(f"min_price:{value}")
                except ValueError:
                    pass
            elif field == "max_price":
                try:
                    mx = float(value)
                    products = [p for p in products if isinstance(p.get("price"), (int, float)) and p["price"] <= mx]
                    local_filters.append(f"max_price:{value}")
                except ValueError:
                    pass
            elif field == "availability":
                products = [p for p in products if (p.get("availability_text") or "").casefold() == value.casefold()]
                local_filters.append(f"availability:{value}")
    result["products"] = products
    result["count"] = len(products)
    result["local_filters"] = local_filters
    return result


async def search(self, query, page=1, brand=None, min_price=None, max_price=None, availability=None, order_by=None):
    filters = []
    if brand:
        filters.append(f"brand:{brand}")
    if min_price is not None:
        filters.append(f"min_price:{min_price}")
    if max_price is not None:
        filters.append(f"max_price:{max_price}")
    if availability:
        filters.append(f"availability:{availability}")
    return await self.search_page(query, page, filters, order_by=order_by)


async def browse_page(self, url, page=1):
    """Browse a category or brand page."""
    parts = urlsplit(url)
    if not (parts.scheme == "https" and parts.hostname in self.hosts):
        raise RetailerError("Use an HTTPS URL from the selected storefront.", code="invalid_input")
    decoded_path = unquote(parts.path)
    if ".." in decoded_path.split("/") or "\\" in decoded_path:
        raise RetailerError("Invalid URL path.", code="invalid_input")
    target = url
    if page > 1:
        sep = "&" if "?" in target else "?"
        target = f"{target}{sep}page={page}"
    response = await get(self, target)
    if response.status_code != 200:
        raise RetailerError(f"Page returned HTTP {response.status_code}.")
    final = urlsplit(str(response.url))
    if final.path != parts.path:
        raise RetailerError("The page redirected to an unsupported location.", code="retailer_changed")
    result = parse_search_page(response.text, self.base, str(response.url))
    result["retailer"] = "maxgaming"
    result["country"] = self.country
    result["language"] = self.language
    result["query"] = url
    result["source"] = "browse_page"
    result["coverage"] = "browse_page"
    result["redirected_url"] = str(response.url) if str(response.url) != url else None

    # Extract related sub-pages
    prefix = parts.path.rstrip("/") + "/"
    related = []
    seen = set()
    for link in re.findall(r'href="(/[^"]+)"', response.text):
        if link.startswith(prefix) and link != parts.path and link not in seen:
            if not re.search(r"-\d+\.html$", link):
                seen.add(link)
                related.append(urljoin(self.base, link))
    result["related_pages"] = related[:30] if related else None

    result["count"] = len(result["products"])
    if result["count"] >= 50:
        result["next_page"] = page + 1
        result["paging"]["max_page"] = None
    result["local_filters"] = []
    result["note"] = "Products from a category or brand page. Prices and availability are snapshots."
    return result