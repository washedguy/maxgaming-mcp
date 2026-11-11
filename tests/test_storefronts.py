from maxgaming_mcp.shop.config import STOREFRONTS, REGION_NAMES


def test_all_countries_present():
    expected = {"us", "se", "de", "no", "dk", "fi", "nl", "be", "eu"}
    assert set(STOREFRONTS.keys()) == expected


def test_storefront_tuple_shape():
    for country, (host, currency, lang_path, lang) in STOREFRONTS.items():
        assert host
        assert currency
        assert lang_path
        assert lang
        assert country in REGION_NAMES


def test_currency_values():
    assert STOREFRONTS["us"][1] == "USD"
    assert STOREFRONTS["se"][1] == "SEK"
    assert STOREFRONTS["de"][1] == "EUR"
    assert STOREFRONTS["no"][1] == "NOK"
    assert STOREFRONTS["dk"][1] == "DKK"