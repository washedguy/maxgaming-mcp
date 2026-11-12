# maxgaming-mcp

MCP server for MaxGaming products, prices, and availability.

## Quick start

Install [uv](https://docs.astral.sh/uv/getting-started/installation/) and add this to your MCP client configuration:

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

## Notes

- Set `HTTPS_PROXY` (or `ALL_PROXY` and `NO_PROXY`) to configure a proxy.
- Brand, price, and availability filters apply locally per page. Prices and availability can change.
- This is an unofficial integration and storefront behavior may change.

## Development

```bash
git clone https://github.com/washedguy/maxgaming-mcp.git
cd maxgaming-mcp
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

[MIT](LICENSE)
