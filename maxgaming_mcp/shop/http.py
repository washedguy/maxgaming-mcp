"""Proxy configuration, request pacing, and HTTP helpers."""
import asyncio
import os
import re
import time
from contextlib import asynccontextmanager
from urllib.parse import urlsplit

from curl_cffi.requests import AsyncSession
from .errors import RetailerError

_lock = asyncio.Lock()
_last_request = 0.0


@asynccontextmanager
async def paced():
    global _last_request
    async with _lock:
        await asyncio.sleep(max(0, 1.0 - (time.monotonic() - _last_request)))
        _last_request = time.monotonic()
        yield


def request_error(context, exc):
    """Report proxy failures without exposing proxy URLs or credentials."""
    detail = str(exc).lower()
    if "connect tunnel failed" in detail or "proxy authentication" in detail or re.search(r"curl: \(\s*(5|97)\)", detail):
        return RetailerError(f"{context}: proxy connection or authentication failed; check proxy settings.", code="proxy_error")
    return RetailerError(f"{context} ({type(exc).__name__}); check network and proxy settings.", code="network_error")


def validate_proxy_environment():
    """Fail closed when an obsolete proxy setting would otherwise be ignored."""
    if os.environ.get("MAXGAMING_PROXY") or os.environ.get("MAXGAMING_PROXY_FILE"):
        raise RetailerError(
            "MAXGAMING_PROXY and MAXGAMING_PROXY_FILE are no longer supported; remove them and configure HTTPS_PROXY.",
            code="invalid_input",
        )


def _session(*, timeout):
    """Use libcurl's standard proxy environment variables and NO_PROXY rules."""
    validate_proxy_environment()
    return AsyncSession(impersonate="chrome", timeout=timeout)


async def get(self, url, *, timeout=20, allow_redirects=True):
    async with _session(timeout=timeout) as session:
        for attempt in range(3):
            async with paced():
                try:
                    response = await session.get(url, allow_redirects=allow_redirects)
                except Exception as exc:
                    raise request_error("Request failed", exc) from exc
            if (response.status_code == 429 or response.status_code >= 500) and attempt < 2:
                await asyncio.sleep(2 * (attempt + 1))
                continue
            if response.status_code == 403:
                raise RetailerError("Blocked by the retailer (HTTP 403).", code="blocked")
            return response
    raise RetailerError("Request failed after retries.")


async def post(self, url, *, json_body=None, timeout=20):
    async with _session(timeout=timeout) as session:
        for attempt in range(3):
            async with paced():
                try:
                    response = await session.post(url, json=json_body)
                except Exception as exc:
                    raise request_error("Request failed", exc) from exc
            if (response.status_code == 429 or response.status_code >= 500) and attempt < 2:
                await asyncio.sleep(2 * (attempt + 1))
                continue
            if response.status_code == 403:
                raise RetailerError("Blocked by the retailer (HTTP 403).", code="blocked")
            return response
    raise RetailerError("Request failed after retries.")


def validate_url(self, url):
    """Validate that a URL belongs to a supported storefront domain."""
    try:
        parts = urlsplit(url)
    except ValueError as exc:
        raise RetailerError("Invalid URL.", code="invalid_input") from exc
    valid_host = parts.hostname in self.hosts and parts.username is None and parts.port is None
    if parts.scheme != "https" or not valid_host:
        raise RetailerError("Use an HTTPS URL for the selected storefront.", code="invalid_input")
    return parts