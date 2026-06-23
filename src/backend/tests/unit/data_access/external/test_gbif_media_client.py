"""REQ-029-A — SSRF-hardening tests for the GBIF media client download path.

The occurrence-media URL comes from a third-party (GBIF) response and is dialed
server-side, so ``download`` must refuse internal/non-https targets before any
request. These tests also implicitly assert the two-argument
``ExternalSourceError(source, message)`` signature is used on the reject path.
"""

import pytest

from app.common.exceptions import ExternalSourceError
from app.data_access.external.gbif_media_client import GBIFMediaClient


def test_download_rejects_loopback_url_ssrf():
    client = GBIFMediaClient()
    try:
        with pytest.raises(ExternalSourceError):
            client.download("https://127.0.0.1/media/img.jpg")
    finally:
        client.close()


def test_download_rejects_non_https_url():
    client = GBIFMediaClient()
    try:
        with pytest.raises(ExternalSourceError):
            client.download("http://api.gbif.org/media/img.jpg")
    finally:
        client.close()
