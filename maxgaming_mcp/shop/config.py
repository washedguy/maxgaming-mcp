"""Storefront configuration for MaxGaming."""

STOREFRONTS = {
    "us": ("us.maxgaming.com", "USD", "us", "en"),
    "se": ("maxgaming.se", "SEK", "sv", "sv"),
    "de": ("maxgaming.gg", "EUR", "de", "de"),
    "no": ("maxgaming.no", "NOK", "no", "no"),
    "dk": ("maxgaming.dk", "DKK", "dk", "da"),
    "fi": ("maxgaming.fi", "EUR", "fi", "fi"),
    "nl": ("maxgaming.com", "EUR", "en", "en"),
    "be": ("maxgaming.com", "EUR", "en", "en"),
    "eu": ("maxgaming.com", "EUR", "en", "en"),
}

# Map country code to a human-readable shop/region name.
REGION_NAMES = {
    "us": "International",
    "se": "Sweden",
    "de": "Germany",
    "no": "Norway",
    "dk": "Denmark",
    "fi": "Finland",
    "nl": "Netherlands",
    "be": "Belgium",
    "eu": "EU",
}