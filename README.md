# MaxGaming MCP Server

Request-based MCP server for the MaxGaming gaming and esports store.

## Supported storefronts

| Country | Domain | Currency | Language |
|---------|--------|----------|----------|
| International | us.maxgaming.com | USD | English |
| Sweden | maxgaming.se | SEK | Swedish |
| Germany | maxgaming.gg | EUR | German |
| Norway | maxgaming.no | NOK | Norwegian |
| Denmark | maxgaming.dk | DKK | Danish |
| Finland | maxgaming.fi | EUR | Finnish |
| Netherlands | maxgaming.com | EUR | English |
| Belgium | maxgaming.com | EUR | English |
| EU | maxgaming.com | EUR | English |

MaxGaming is an online-only retailer; there are no physical stores or pickup locations.

## Quick start

### Local install

```bash
git clone <repository-url>
cd maxgaming-mcp
uv sync
uv run maxgaming-mcp
```

### MCP client configuration

```json
{
  "mcpServers": {
    "maxgaming": {
      "command": "uv",
      "args": ["run", "--directory", "/path/to/maxgaming-mcp", "maxgaming-mcp"]
    }
  }
}
```

Or using the Python module directly:

```bash
uv run python -m maxgaming_mcp.server
```

Generate a config snippet:

```bash
uv run maxgaming-mcp --config
```

### uvx

```json
{
  "mcpServers": {
    "maxgaming": {
      "command": "uvx",
      "args": ["--from", "git+https://github.com/washedguy/maxgaming-mcp", "maxgaming-mcp"]
    }
  }
}
```

## Tools

- `list_storefronts` - List supported countries, languages, currencies and regions.
- `search_products` - Search by keyword, model number or search term. Supports brand, price and availability filters (applied locally per page), sort order, optional detail loading and pagination.
- `browse_page` - Browse a category, brand or campaign page URL. Returns visible products and related sub-pages.
- `get_product` - Read product details by URL or numeric article number.

## Typical queries

- "Search for gaming mice on MaxGaming US"
- "Find Razer mice under $150"
- "Get details for article number 30041"
- "Browse the wireless mouse category on the German storefront"

## Proxy configuration

MaxGaming MCP supports standard proxy environment variables:

```bash
export HTTPS_PROXY=http://user:pass@proxy.example.com:8080
export ALL_PROXY=http://proxy.example.com:8080
export NO_PROXY=localhost,127.0.0.1
```

Special characters in proxy credentials must be URL-encoded (e.g., `@` → `%40`).

Proxy credentials are never logged or exposed in responses.

## Known limitations

- MaxGaming is online-only; no store finder or pickup availability.
- No EAN/barcode data is exposed on product pages.
- Brand, price and availability filters are applied locally per page (not by the shop).
- Marketplace offers and multiple sellers are not supported (MaxGaming sells directly).
- Product variants are color filter links, not separate product entries.
- Total product count is not available for category/brand pages (browse_page).
- Prices and availability are snapshots and can change.

## Development

```bash
uv sync
uv run pytest
uv run ruff check .
uv build
```

Live connectivity check:

```bash
uv run maxgaming-mcp --check --country us
```

## License

MIT