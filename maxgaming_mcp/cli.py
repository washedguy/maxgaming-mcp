"""Command-line entry point and live diagnostics."""
import argparse
import asyncio
import json
import shutil
from pathlib import Path
import sys
from .client import Client, RetailerError
from .shop.config import STOREFRONTS


async def _check(country: str = "us", language: str | None = None) -> int:
    stage = "search_products"
    try:
        client = Client(country, language)
        search = await client.search("mouse")
        print(f"{country}: {stage} OK ({len(search['products'])} products)", flush=True)
        if not search["products"] or not search["products"][0].get("id"):
            raise RetailerError("Search returned no usable product ID; cannot test product details.")
        product_ref = search["products"][0].get("url") or search["products"][0]["id"]
        stage = "get_product"
        product = await client.product(product_ref)
        if not product.get("found"):
            raise RetailerError(f"Could not resolve product {product_ref}: {product.get('reason')}")
        print(f"{country}: {stage} OK (product {product['product'].get('id')})", flush=True)
        return 0
    except (RetailerError, ValueError) as exc:
        print(f"{country}: {stage} failed: {exc}", file=sys.stderr)
        return 1


def main():
    parser = argparse.ArgumentParser(description="MaxGaming MCP server. Run without arguments to serve over stdio.")
    parser.add_argument("--config", action="store_true", help="Print MCP client configuration for this Python environment and exit.")
    parser.add_argument("--check", action="store_true", help="Run a live connectivity check and exit.")
    parser.add_argument("--country", choices=list(STOREFRONTS), default="us", help="Country for --check (default: us).")
    parser.add_argument("--language", help="Storefront language for --check.")
    parser.add_argument("--env-file", metavar="PATH", help="With --config, generate a launcher that loads this dotenv file using uv.")
    args = parser.parse_args()
    env_file = str(Path(args.env_file).expanduser().resolve()) if args.env_file else None
    if env_file and not args.config:
        parser.error("--env-file requires --config; for diagnostics use uv run --env-file PATH")
    if args.config and args.check:
        parser.error("--config and --check cannot be combined")
    if args.config:
        config = {"command": sys.executable, "args": ["-m", "maxgaming_mcp.server"]}
        if env_file:
            if not Path(env_file).is_file():
                parser.error("--env-file must point to an existing file")
            uv = shutil.which("uv")
            if not uv:
                parser.error("uv must be available on PATH to generate an --env-file configuration")
            config = {"command": str(Path(uv).resolve()), "args": ["run", "--no-project", "--env-file", env_file,
                     "--", sys.executable, "-m", "maxgaming_mcp.server"]}
        print(json.dumps({"mcpServers": {"maxgaming": config}}, indent=2))
    elif args.check:
        raise SystemExit(asyncio.run(_check(args.country, args.language)))
    else:
        from .server import mcp
        mcp.run(transport="stdio")