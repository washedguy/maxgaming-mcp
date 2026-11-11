import os
from unittest.mock import patch

import pytest

from maxgaming_mcp.shop import http


def test_validate_proxy_environment_rejects_obsolete():
    with patch.dict(os.environ, {"MAXGAMING_PROXY": "http://proxy"}):
        with pytest.raises(Exception):
            http.validate_proxy_environment()


def test_request_error_proxy():
    exc = Exception("proxy authentication failed")
    err = http.request_error("ctx", exc)
    assert err.code == "proxy_error"


def test_request_error_network():
    exc = Exception("connection reset")
    err = http.request_error("ctx", exc)
    assert err.code == "network_error"