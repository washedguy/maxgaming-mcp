"""Parse MaxGaming search and product pages."""
import html
import re
from urllib.parse import urljoin



def _strip_tags(text):
    return re.sub(r"<[^>]+>", "", text)


def _html_to_text(html_text):
    text = re.sub(r"<br\s*/?>", "\n", html_text)
    text = re.sub(r"<[^>]+>", " ", text)
    text = html.unescape(text)
    lines = [line.strip() for line in text.splitlines()]
    return "\n".join(line for line in lines if line) or None


def _parse_price(text):
    if not text:
        return None
    text = html.unescape(text)
    cleaned = re.sub(r"[^\d.,]", "", text)
    if not cleaned:
        return None
    if "," in cleaned and "." in cleaned:
        if cleaned.rfind(",") > cleaned.rfind("."):
            cleaned = cleaned.replace(".", "").replace(",", ".")
        else:
            cleaned = cleaned.replace(",", "")
    elif "," in cleaned:
        parts = cleaned.split(",")
        if len(parts) == 2 and len(parts[1]) <= 2:
            cleaned = cleaned.replace(",", ".")
        else:
            cleaned = cleaned.replace(",", "")
    try:
        return float(cleaned)
    except ValueError:
        return None


def _detect_currency(price_text, url):
    if "$" in price_text or "&#36;" in price_text:
        return "USD"
    if "kr" in price_text:
        if "maxgaming.dk" in url:
            return "DKK"
        if "maxgaming.no" in url:
            return "NOK"
        return "SEK"
    if "€" in price_text or "&euro;" in price_text or "&#8364;" in price_text:
        return "EUR"
    return None


def _currency_for_url(url):
    if "us.maxgaming.com" in url:
        return "USD"
    if "maxgaming.se" in url:
        return "SEK"
    if "maxgaming.no" in url:
        return "NOK"
    if "maxgaming.dk" in url:
        return "DKK"
    return "EUR"


def parse_search_page(text, base, url):
    """Parse a search result page into a structured dict."""
    products = []

    # Split by PT_Wrapper markers
    parts = text.split('<div class="PT_Wrapper">')
    for part in parts[1:]:
        # Find the end: next PT_Wrapper or end of relevant container
        # The card ends at the next PT_Wrapper or </div></div></div>
        card = part
        # Truncate at next PT_Wrapper
        idx = card.find('<div class="PT_Wrapper">')
        if idx != -1:
            card = card[:idx]
        _parse_card(card, base, products)

    # Remove duplicates by URL
    seen = set()
    unique = []
    for p in products:
        if p["url"] in seen:
            continue
        seen.add(p["url"])
        unique.append(p)
    products = unique

    # Extract total product count
    total = None
    m = re.search(r"(\d+)\s*products", text, re.IGNORECASE)
    if m:
        total = int(m.group(1))
    m = re.search(r"Visar\s+\d+\s+av\s+(\d+)", text, re.IGNORECASE)
    if m:
        total = int(m.group(1))
    # Swedish: "Visar 60 av 110 träffar"
    m = re.search(r"av\s+(\d+)\s*träffar", text, re.IGNORECASE)
    if m:
        total = int(m.group(1))

    # Current page
    page = 1
    m = re.search(r"[?&]page=(\d+)", url)
    if m:
        page = int(m.group(1))

    per_page = 60
    page_count = None
    max_page = None
    if total:
        page_count = (total + per_page - 1) // per_page
        max_page = min(page_count, 30)

    next_page = page + 1 if max_page and page < max_page else None

    return {
        "products": products,
        "total_products": total,
        "page": page,
        "next_page": next_page,
        "paging": {"current_page": page, "page_count": page_count, "max_page": max_page},
    }


def _parse_card(card, base, products):
    # URL
    url = None
    m = re.search(r'class="PT_Lank"\s+href="([^"]+)"', card)
    if m:
        url = urljoin(base, m.group(1))
    if not url:
        m = re.search(r'href="([^"]+)"[^>]*>\s*<img', card)
        if m:
            url = urljoin(base, m.group(1))
    if not url:
        return

    # Product ID (article number)
    pid = None
    m = re.search(r'data-artnr="(\d+)"', card)
    if m:
        pid = m.group(1)
    if not pid:
        m = re.search(r"/bilder/artiklar/(?:liten|zoom)/(\d+)_", card)
        if m:
            pid = m.group(1)

    # Brand
    brand = None
    m = re.search(r'class="PT_Varum[^"]*">(.*?)</div>', card, re.DOTALL)
    if m:
        brand = _strip_tags(m.group(1)).strip()

    # Title: text inside PT_Beskr after the PT_Varum div
    title = None
    m = re.search(r'class="PT_Beskr[^"]*">(.*?)</div>\s*</div>', card, re.DOTALL)
    if m:
        beskr = m.group(1)
        # Remove the PT_Varum div
        beskr_clean = re.sub(r'<div class="PT_Varum[^"]*">.*?</div>', "", beskr, flags=re.DOTALL)
        title = _strip_tags(beskr_clean).strip()
        # Remove brand prefix if present
        if brand and title.startswith(brand):
            title = title[len(brand):].strip()

    # Price
    price = None
    currency = None
    m = re.search(r'class="PT_PrisNormal">(.*?)</span>', card, re.DOTALL)
    if m:
        price_text = _strip_tags(m.group(1)).strip()
        price = _parse_price(price_text)
        currency = _detect_currency(price_text, url)

    # Availability
    availability = None
    m = re.search(r'class="PT_text_Lagerstatus[^"]*">(.*?)</div>', card, re.DOTALL)
    if m:
        availability = _strip_tags(m.group(1)).strip()

    # Currency fallback
    if not currency:
        currency = _currency_for_url(url)

    products.append({
        "id": pid,
        "title": title,
        "brand": brand,
        "price": price,
        "currency": currency,
        "url": url,
        "availability_text": availability,
        "delivery": _availability_to_delivery(availability),
    })


_AVAILABLE_KEYWORDS = ("in stock", "auf lager", "i lager", "på lager", "varastossa",
                       "op voorraad", "en stock", "pronta consegna", "raktáron",
                       "in voorraad", "op lager", "disponible")
_UNAVAILABLE_KEYWORDS = ("out of stock", "nicht auf lager", "tillfälligt slut", "utsolgt",
                         "udsolgt", "loppu", "uitverkocht", "épuisé", "nicht verfügbar",
                         "tijdelijk uitverkocht", "slut i lager")
_PREORDER_KEYWORDS = ("pre-order", "preorder", "vorbestell", "förhandsboka",
                      "forhåndsbestill", "forudbestil", "ennakkotilaus", "voorbestellen")


def _availability_to_delivery(avail):
    status = "unknown"
    if avail:
        low = avail.lower()
        if any(k in low for k in _UNAVAILABLE_KEYWORDS):
            status = "unavailable"
        elif any(k in low for k in _PREORDER_KEYWORDS):
            status = "preorder"
        elif any(k in low for k in _AVAILABLE_KEYWORDS):
            status = "available"
    return {"status": status, "retailer_status": avail, "retailer_code": None, "earliest": None}


def parse_product_page(text, base, url):
    """Parse a product detail page."""
    product_id = None
    m = re.search(r"Our article number:\s*(\d+)", text)
    if m:
        product_id = m.group(1)
    if not product_id:
        m = re.search(r'data-artnr="(\d+)"', text)
        if m:
            product_id = m.group(1)
    if not product_id:
        m = re.search(r"/bilder/artiklar/(?:liten|zoom)/(\d+)_", text)
        if m:
            product_id = m.group(1)

    title = None
    brand = None
    m = re.search(r'<h1[^>]*>(.*?)</h1>', text, re.DOTALL)
    if m:
        h1_content = m.group(1)
        # Brand is in VarumarkeFalt span
        bm = re.search(r'id="VarumarkeFalt"[^>]*>.*?<a[^>]*>(.*?)</a>', h1_content, re.DOTALL)
        if bm:
            brand = _strip_tags(bm.group(1)).strip()
        # Title is the remaining text
        title_text = re.sub(r'<span id="VarumarkeFalt".*?</span>', "", h1_content, flags=re.DOTALL)
        title = _strip_tags(title_text).strip()
        title = " ".join(title.split())

    price = None
    currency = None
    # Use itemprop price meta
    m = re.search(r'<meta[^>]*itemprop="price"[^>]*content="([^"]+)"', text)
    if m:
        price = _parse_price(m.group(1))
    m = re.search(r'<meta[^>]*itemprop="priceCurrency"[^>]*content="([^"]+)"', text)
    if m:
        currency = m.group(1)
    if price is None:
        m = re.search(r'class="PrisBOLD">(.*?)<', text, re.DOTALL)
        if m:
            price_text = html.unescape(m.group(1)).strip()
            price = _parse_price(price_text)
            currency = _detect_currency(price_text, url)

    availability = None
    m = re.search(r"class='Text_Lagerstatus[^']*'>(.*?)</div>", text, re.DOTALL)
    if m:
        availability = _strip_tags(m.group(1)).strip()
    if not availability:
        m = re.search(r'name="availability"\s+content="([^"]+)"', text)
        if m:
            availability = m.group(1).strip()

    # Stock count (only on some storefronts, e.g. US: "20+ left in stock")
    stock_text = None
    m = re.search(r"class=\"saldo\">.*?Availability:\s*(.+?)</div>", text, re.DOTALL)
    if m:
        stock_text = " ".join(_strip_tags(m.group(1)).split())
    if not stock_text:
        m = re.search(r"(\d+\+?\s*left in stock)", text, re.IGNORECASE)
        if m:
            stock_text = " ".join(m.group(1).split())

    manuf_artnr = None
    m = re.search(r"Manuf\.\s*article number:\s*(.+?)(?:<|$)", text, re.IGNORECASE | re.DOTALL)
    if not m:
        m = re.search(r"Hersteller-Nr\.\s*(.+?)(?:<|$)", text, re.IGNORECASE | re.DOTALL)
    if m:
        manuf_artnr = _strip_tags(m.group(1)).strip()

    description = None
    m = re.search(r"Product description(.*?)(?:Article number:|Products in bundle|Brand|$)", text, re.DOTALL | re.IGNORECASE)
    if m:
        description = _html_to_text(m.group(1))

    # Specifications
    features = []
    for m in re.finditer(r"<h3[^>]*>([^<]{1,80})</h3>\s*<table[^>]*>(.*?)</table>", text, re.DOTALL):
        group_name = m.group(1).strip()
        table_html = m.group(2)
        items = []
        for row in re.finditer(r"<tr[^>]*>\s*<td[^>]*>(.*?)</td>\s*<td[^>]*>(.*?)</td>\s*</tr>", table_html, re.DOTALL):
            name = _strip_tags(row.group(1)).strip()
            value = _strip_tags(row.group(2)).strip()
            if name and "<script" not in row.group(0) and len(name) < 100:
                items.append({"name": name, "value": value, "unit": None})
        if items and len(group_name) < 80:
            features.append({"group": group_name, "items": items})

    # Images
    images = []
    # Main product image
    m = re.search(r'src="(/img/bilder/artiklar/(\d+)\.jpg[^"]*)"', text)
    if m:
        images.append({"url": urljoin(base, m.group(1)), "alt": title})
    # Zoom images
    for m in re.finditer(r'href="(/bilder/artiklar/zoom/(\d+)_\d+\.jpg[^"]*)"', text):
        img_url = urljoin(base, m.group(1))
        if img_url not in [i["url"] for i in images]:
            images.append({"url": img_url, "alt": title})

    # Color variants (deduplicated)
    variants = []
    seen_urls = set()
    for m in re.finditer(r'<a[^>]*href="([^"]+)"[^>]*>\s*<img[^>]*src="[^"]*specialegenskaper[^"]*"', text):
        variant_url = urljoin(base, m.group(1))
        if variant_url in seen_urls:
            continue
        seen_urls.add(variant_url)
        variants.append({"product_id": None, "title": None, "variant_name": "Color",
                        "variant_value": None, "url": variant_url})

    categories = []

    rating = {"average": None, "count": None, "scale": None}

    delivery = _availability_to_delivery(availability)
    delivery_status = delivery["status"]

    if not currency:
        currency = _currency_for_url(url)

    details = {
        "id": product_id,
        "title": title,
        "brand": brand,
        "price": price,
        "currency": currency,
        "url": url,
        "resolved_url": url,
        "delivery": {"status": delivery_status, "retailer_status": availability,
                     "retailer_code": None, "earliest": None},
        "ean": None,
        "variants": variants,
        "marketplace_offers": [],
        "offers_coverage": "none",
        "description": description,
        "description_marketing": None,
        "images": images,
        "rating": rating,
        "categories": categories,
        "features": features,
        "manufacturer_article_number": manuf_artnr,
        "availability_text": availability,
        "stock_text": stock_text,
    }
    return details