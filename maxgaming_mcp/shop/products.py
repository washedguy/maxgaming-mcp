"""Retrieve product pages."""
import re
from urllib.parse import urljoin

from .errors import RetailerError
from .http import get, post, validate_url
from .parsing import parse_product_page


async def product(self, reference):
    """Resolve an ID or URL and read product details."""
    reference = reference.strip()
    if not reference:
        raise RetailerError("Reference must not be blank.", code="invalid_input")

    # If it looks like a URL, validate and use it
    if reference.startswith("http://") or reference.startswith("https://"):
        parts = validate_url(self, reference)
        url = f"{parts.scheme}://{parts.netloc}{parts.path}"
    elif reference.isdigit():
        # Use the search API to find the product URL by article number
        url = await _find_product_url(self, reference)
        if not url:
            return {"retailer": "maxgaming", "country": self.country, "language": self.language,
                    "reference": reference, "found": False, "product": None,
                    "reason": "product_not_found"}
    else:
        # Treat as a relative path or slug
        raise RetailerError("Use an HTTPS product URL or a numeric article number.", code="invalid_input")

    response = await get(self, url)
    if response.status_code == 404:
        return {"retailer": "maxgaming", "country": self.country, "language": self.language,
                "reference": reference, "found": False, "product": None,
                "reason": "product_url_not_found"}
    if response.status_code != 200:
        raise RetailerError(f"Product page returned HTTP {response.status_code}.")

    details = parse_product_page(response.text, self.base, str(response.url))
    if not details.get("id"):
        return {"retailer": "maxgaming", "country": self.country, "language": self.language,
                "reference": reference, "found": False, "product": None,
                "reason": "product_data_not_found"}
    if reference.isdigit() and details.get("id") != reference:
        return {"retailer": "maxgaming", "country": self.country, "language": self.language,
                "reference": reference, "found": False, "product": None,
                "reason": "requested_product_not_on_page"}

    details["retailer"] = "maxgaming"
    return {"retailer": "maxgaming", "country": self.country, "language": self.language,
            "reference": reference, "found": True, "product": details, "reason": None}


async def _find_product_url(self, article_number):
    """Use the search API to find a product URL by article number."""
    try:
        response = await post(self, f"{self.base}/cgi-bin/ibutik/API.fcgi",
                             json_body={"action": "rlws_search_ajax", "q": article_number,
                                        "take": 5, "skip": 0})
        if response.status_code != 200:
            return None
        data = response.json()
        html_text = data.get("data", {}).get("html", "")
        m = re.search(r'href="([^"]+)"', html_text)
        if m:
            return urljoin(self.base, m.group(1))
    except Exception:
        pass
    return None