"""English-language MCP tools for MaxGaming."""
from typing import Annotated, Literal

from .mcp_api.server import StructuredMCPServer
from mcp.server.mcpserver.exceptions import ToolError
from pydantic import Field
from .mcp_api.schemas import ProductResult, SearchResult, StorefrontList

from .client import Client, RetailerError, STOREFRONTS
from .shop.cache import cached_call

mcp = StructuredMCPServer("maxgaming", instructions=(
    "Search MaxGaming storefronts. Use list_storefronts to discover supported countries and shop languages. "
    "Use search_products to find products by name, model or keyword and get_product to resolve exact product URLs or article numbers. "
    "MaxGaming is an online-only retailer; no physical stores or pickup. "
    "Prices and availability can change."
))

Country = Annotated[Literal["us", "se", "de", "no", "dk", "fi", "nl", "be", "eu"],
                    Field(description="Storefront country code. Defaults to us (International).")]
Language = Annotated[str | None, Field(description="Shop language; defaults to the country's language. MaxGaming uses one language per storefront.")]

def _client(country, language):
    try:
        return Client(country, language)
    except ValueError as exc:
        raise ToolError(f"[invalid_input] {exc}") from exc

Query = Annotated[str, Field(min_length=1, max_length=200, description="Product keywords, model number, or search term.")]


@mcp.tool(structured_output=True)
async def list_storefronts() -> StorefrontList:
    """List supported countries, languages, currencies and regions for MaxGaming."""
    shops = []
    for country, (host, currency, lang_path, lang) in STOREFRONTS.items():
        shops.append({
            "country": country,
            "retailer": "maxgaming",
            "languages": [lang],
            "default_language": lang,
            "currency": currency,
            "url": f"https://{host}",
            "region": country.upper(),
        })
    return StorefrontList.model_validate({"storefronts": shops})


@mcp.tool(structured_output=True)
async def search_products(
    query: Query,
    country: Country = "us",
    language: Language = None,
    page: Annotated[int, Field(ge=1, le=30, description="Results page, starting at 1. Use next_page to continue.")] = 1,
    brand: Annotated[str | None, Field(min_length=1, max_length=100, description="Filter by brand name (applied locally per page).")] = None,
    min_price: Annotated[float | None, Field(ge=0, description="Minimum price in the local currency (applied locally per page).")] = None,
    max_price: Annotated[float | None, Field(ge=0, description="Maximum price in the local currency (applied locally per page).")] = None,
    availability: Annotated[str | None, Field(description="Filter by availability text, e.g. 'In stock', 'Pre-order', 'Out of stock' (applied locally per page).")] = None,
    order_by: Annotated[str | None, Field(description="Sort order: '' (recommended), 'DisplayName-Asc', 'DisplayName-Desc', 'SalesPrice-Asc', 'SalesPrice-Desc'.")] = None,
    include_details: Annotated[bool, Field(description="Fetch each product page to include full details, variants and specifications. Slower.")] = False,
    fresh: Annotated[bool, Field(description="Bypass the process cache and request current shop data.")] = False,
) -> SearchResult:
    """Search the selected MaxGaming storefront. Results and total_products may include products unrelated to the query. Brand, price and availability filters are applied locally per page. Sort order and include_details are optional. Use get_product for exact URLs or article numbers."""
    if not query.strip():
        raise ToolError("[invalid_input] query must not be blank")
    if min_price is not None and max_price is not None and min_price > max_price:
        raise ToolError("[invalid_input] min_price must not exceed max_price")
    if brand is not None and not brand.strip():
        raise ToolError("[invalid_input] brand must not be blank")
    if order_by is not None and order_by not in ("", "DisplayName-Asc", "DisplayName-Desc", "SalesPrice-Asc", "SalesPrice-Desc"):
        raise ToolError("[invalid_input] invalid order_by value")
    try:
        client = _client(country, language)
        search_args = (query.strip(), page, brand.strip() if brand else None, min_price, max_price,
                       availability.strip() if availability else None, order_by)
        result = await cached_call("search", (country, language, *search_args), fresh,
                                   lambda: client.search(*search_args))
        if include_details:
            for item in result["products"]:
                if not item.get("id") or not item.get("url"):
                    item["enrichment_error"] = "Product URL missing; page details unavailable."
                    item["enrichment_error_code"] = "retailer_changed"
                    continue
                try:
                    detail = await cached_call("product", (country, language, item["url"]), fresh,
                                               lambda url=item["url"]: client.product(url))
                    if not detail.get("found"):
                        item["enrichment_error"] = f"Product page unavailable: {detail.get('reason')}"
                        item["enrichment_error_code"] = "not_found"
                        continue
                    data = detail["product"]
                    for key in ("variants", "features", "images", "description", "manufacturer_article_number"):
                        if key in data:
                            item[key] = data[key]
                    item["details_observed_at"] = detail["observed_at"]
                    item["details_cache"] = detail["cache"]
                except RetailerError as exc:
                    item["enrichment_error"] = str(exc)
                    item["enrichment_error_code"] = exc.code
        return SearchResult.model_validate(result)
    except RetailerError as exc:
        raise ToolError(f"[{exc.code}] {exc}") from exc


@mcp.tool(structured_output=True)
async def browse_page(
    url: Annotated[str, Field(min_length=1, max_length=1000, description="Shop category, brand or campaign URL from MaxGaming.")],
    country: Country = "us",
    language: Language = None,
    page: Annotated[int, Field(ge=1, le=30, description="Listing page, starting at 1; use next_page to continue.")] = 1,
    fresh: Annotated[bool, Field(description="Bypass the process cache and request current shop data.")] = False,
) -> SearchResult:
    """Browse a MaxGaming category, brand or campaign page. Returns visible products with embedded data."""
    try:
        client = _client(country, language)
        result = await cached_call("search", ("browse_page", country, language, url, page), fresh,
                                   lambda: client.browse_page(url, page))
        return SearchResult.model_validate(result)
    except RetailerError as exc:
        raise ToolError(f"[{exc.code}] {exc}") from exc


@mcp.tool(structured_output=True)
async def get_product(
    reference: Annotated[str, Field(min_length=1, max_length=500, description="Exact product URL or numeric article number from MaxGaming.")],
    country: Country = "us",
    language: Language = None,
    fresh: Annotated[bool, Field(description="Bypass the process cache and request current shop data.")] = False,
) -> ProductResult:
    """Read product details from a MaxGaming product page by URL or article number, including description, images, specifications, variants and availability. Returns found=false for a 404 or missing product."""
    if not reference.strip():
        raise ToolError("[invalid_input] reference must not be blank")
    try:
        client = _client(country, language)
        result = await cached_call("product", (country, language, reference.strip()), fresh,
                                   lambda: client.product(reference.strip()))
        return ProductResult.model_validate(result)
    except RetailerError as exc:
        raise ToolError(f"[{exc.code}] {exc}") from exc


def main():
    from .cli import main as cli_main
    cli_main()


if __name__ == "__main__":
    main()