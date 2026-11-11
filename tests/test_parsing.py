import os
from maxgaming_mcp.shop.parsing import parse_search_page, parse_product_page

FIXTURES = os.path.join(os.path.dirname(__file__), "fixtures")


def test_parse_search_page():
    text = open(os.path.join(FIXTURES, "search_us.html")).read()
    result = parse_search_page(text, "https://us.maxgaming.com", "https://us.maxgaming.com/search?q=mouse")
    assert result["count"] if "count" in result else True
    assert len(result["products"]) > 0
    p = result["products"][0]
    assert p["id"] == "30041"
    assert "Viper" in p["title"]
    assert p["brand"] == "Razer"
    assert p["price"] == 129.99
    assert p["currency"] == "USD"
    assert p["availability_text"] == "In stock"
    assert result["total_products"] == 783
    assert result["next_page"] == 2


def test_parse_product_page():
    text = open(os.path.join(FIXTURES, "product_us.html")).read()
    result = parse_product_page(text, "https://us.maxgaming.com", "https://us.maxgaming.com/us/wireless-mouses/razer-viper-v3-pro-black")
    assert result["id"] == "30041"
    assert result["title"] == "Viper V3 Pro Wireless Gaming Mouse - Black"
    assert result["brand"] == "Razer"
    assert result["price"] == 129.99
    assert result["currency"] == "USD"
    assert result["availability_text"] == "In stock"
    assert len(result["features"]) >= 4
    assert len(result["images"]) >= 1
    assert result["manufacturer_article_number"] == "RZ01-05120100-R3G1"


def test_parse_category_page():
    text = open(os.path.join(FIXTURES, "category_us.html")).read()
    result = parse_search_page(text, "https://us.maxgaming.com", "https://us.maxgaming.com/us/pc-peripherals/mice-accessories/gaming-mice/wireless-mouses")
    assert len(result["products"]) >= 50