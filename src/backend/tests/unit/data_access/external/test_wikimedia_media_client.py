"""REQ-029-A — SSRF-hardening tests for the Wikimedia media client download path.

The file URL comes from a third-party (Wikimedia) response and is dialed
server-side, so ``download`` must refuse internal/non-https targets before any
request. These tests also implicitly assert the two-argument
``ExternalSourceError(source, message)`` signature is used on the reject path.
"""

import pytest

from app.common.exceptions import ExternalSourceError
from app.data_access.external.wikimedia_media_client import WikimediaCommonsMediaClient


def test_download_rejects_metadata_endpoint_ssrf():
    client = WikimediaCommonsMediaClient()
    try:
        with pytest.raises(ExternalSourceError):
            client.download("https://169.254.169.254/latest/meta-data/")
    finally:
        client.close()


def test_download_rejects_non_https_url():
    client = WikimediaCommonsMediaClient()
    try:
        with pytest.raises(ExternalSourceError):
            client.download("http://upload.wikimedia.org/img.jpg")
    finally:
        client.close()
