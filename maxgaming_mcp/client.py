"""Public storefront client, composed from focused request modules."""

from .shop import products, search as search_api
from .shop.config import STOREFRONTS, REGION_NAMES
from .shop.errors import RetailerError as RetailerError


class Client:
    def __init__(self, country: str = "us", language: str | None = None):
        if country not in STOREFRONTS:
            raise ValueError(f"Unsupported country: {country}. Choose: {', '.join(STOREFRONTS)}.")
        host, currency, lang_path, default_lang = STOREFRONTS[country]
        language = language or default_lang
        # MaxGaming uses one language per storefront domain.
        if language != default_lang:
            raise ValueError(f"Unsupported language for {country}; only '{default_lang}' is available.")
        self.country = country
        self.language = language
        self.currency = currency
        self.host = host
        self.lang_path = lang_path
        self.region = REGION_NAMES.get(country, country)
        self.base = f"https://{host}"
        self.hosts = {host, host.removeprefix("www.")}

    async def search_page(self, query, page=1, filters=None, order_by=None):
        return await search_api.search_page(self, query, page, filters, order_by=order_by)

    async def browse_page(self, url, page=1):
        return await search_api.browse_page(self, url, page)

    async def search(self, query, page=1, brand=None, min_price=None, max_price=None, availability=None, order_by=None):
        return await search_api.search(self, query, page, brand, min_price, max_price, availability, order_by=order_by)

    async def product(self, reference):
        return await products.product(self, reference)