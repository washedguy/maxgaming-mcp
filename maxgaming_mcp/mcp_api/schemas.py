"""Typed MCP response schemas."""
from typing import Literal
from pydantic import BaseModel


class CacheInfo(BaseModel):
    hit: bool
    age_seconds: float
    ttl_seconds: int


class Observation(BaseModel):
    observed_at: str | None = None
    cache: CacheInfo | None = None


class Delivery(BaseModel):
    status: Literal["available", "unavailable", "preorder", "partial", "unknown"]
    retailer_status: str | None
    retailer_code: str | None
    earliest: str | None


class Product(BaseModel):
    id: str | None
    title: str | None
    brand: str | None
    price: float | None
    currency: str
    url: str | None
    delivery: Delivery
    availability_text: str | None = None
    variants: list["Variant"] | None = None
    features: list["FeatureGroup"] | None = None
    images: list["Image"] | None = None
    description: str | None = None
    manufacturer_article_number: str | None = None
    enrichment_error: str | None = None
    enrichment_error_code: str | None = None
    details_observed_at: str | None = None
    details_cache: CacheInfo | None = None


class Paging(BaseModel):
    current_page: int
    page_count: int | None
    max_page: int | None


class SearchResult(Observation):
    retailer: str
    country: str = "us"
    language: str = "en"
    query: str
    products: list[Product]
    count: int
    total_products: int | None
    page: int
    next_page: int | None
    paging: Paging
    source: str
    coverage: str
    redirected_url: str | None = None
    related_pages: list[str] | None = None
    local_filters: list[str] | None = None
    note: str | None = None


class Variant(BaseModel):
    product_id: str | None = None
    title: str | None = None
    variant_name: str | None = None
    variant_value: str | None = None
    url: str | None = None


class Image(BaseModel):
    url: str
    alt: str | None = None


class Rating(BaseModel):
    average: float | None = None
    count: int | None = None
    scale: int | float | None = None


class Feature(BaseModel):
    name: str
    value: str | int | float | bool | None = None
    unit: str | None = None


class FeatureGroup(BaseModel):
    group: str | None = None
    items: list[Feature]


class ProductDetails(Product):
    ean: str | None = None
    resolved_url: str
    variants: list[Variant] = []
    marketplace_offers: list = []
    offers_coverage: str = "none"
    description: str | None = None
    description_marketing: str | None = None
    images: list[Image] = []
    rating: Rating = Rating()
    categories: list[str] = []
    features: list[FeatureGroup] = []
    manufacturer_article_number: str | None = None


class ProductResult(Observation):
    retailer: str
    country: str = "us"
    language: str = "en"
    reference: str
    found: bool
    product: ProductDetails | None = None
    reason: str | None = None


class Storefront(BaseModel):
    country: str
    retailer: str
    languages: list[str]
    default_language: str
    currency: str
    url: str
    region: str


class StorefrontList(BaseModel):
    storefronts: list[Storefront]