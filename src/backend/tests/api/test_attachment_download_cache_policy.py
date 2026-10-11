"""#2254 — attachment download cache policy against token expiry and revocation.

* The token route (``/attachments/token/{token}``) answers ``no-store``: the
  token is a short-lived bearer credential, a stored copy would outlive both
  its expiry and a deletion of the attachment.
* The session routes (original + thumbnails) answer ``private, no-cache`` with
  an ETag: the browser revalidates every reuse; a matching ``If-None-Match``
  gets ``304`` only after the permission check, so a deleted attachment or a
  lost permission is never answered from cache.
"""

from __future__ import annotations

import ast
import asyncio
import re
import time
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.api.v1.attachments.response_headers import if_none_match_hits
from app.common.auth import get_current_tenant
from app.common.exceptions import ForbiddenError
from app.domain.engines.storage.thumbnail_generator import thumbnail_key
from tests.api.test_attachments_router import _base, _build, _make_jpeg

#: The policy the issue found on all three routes: cached for a day without asking.
_DAY_LONG = "max-age=86400"


def _upload(client: TestClient) -> str:
    resp = client.post(_base(), files={"file": ("p.jpg", _make_jpeg(), "image/jpeg")}, data={"category": "diary"})
    assert resp.status_code == 201, resp.text
    return str(resp.json()["attachment_id"])


def _token_path(client: TestClient, attachment_id: str) -> str:
    url = client.get(_base(f"/{attachment_id}/presign-download")).json()["download_url"]
    return url.split("testserver", 1)[-1]


class TestTokenDownload:
    def test_a_token_download_is_never_stored(self, tmp_path):
        app, _service, _adapter = _build(tmp_path)
        client = TestClient(app)
        resp = client.get(_token_path(client, _upload(client)))
        assert resp.status_code == 200
        assert resp.headers["cache-control"] == "no-store"
        assert _DAY_LONG not in resp.headers["cache-control"]

    def test_an_expired_token_is_refused(self, tmp_path):
        app, service, adapter = _build(tmp_path)
        client = TestClient(app)
        attachment_id = _upload(client)
        record = service._repo.get(attachment_id, "tenant_anna")
        token = adapter._make_token(
            {
                "op": "download",
                "key": record.storage_key,
                "tenant_key": "tenant_anna",
                "exp": int(time.time()) - 1,
                "disposition": None,
            }
        )
        resp = client.get(f"/api/v1/attachments/token/{token}")
        assert resp.status_code == 401

    def test_a_token_of_a_deleted_attachment_is_refused(self, tmp_path):
        app, _service, _adapter = _build(tmp_path)
        client = TestClient(app)
        attachment_id = _upload(client)
        path = _token_path(client, attachment_id)
        assert client.delete(_base(f"/{attachment_id}")).status_code == 204
        assert client.get(path).status_code == 401


class TestSessionDownload:
    def test_the_original_is_revalidated_on_every_reuse(self, tmp_path):
        app, _service, _adapter = _build(tmp_path)
        client = TestClient(app)
        resp = client.get(_base(f"/{_upload(client)}"))
        assert resp.status_code == 200
        assert resp.headers["cache-control"] == "private, no-cache"
        assert resp.headers["etag"].startswith('"')

    def test_a_matching_etag_answers_304_without_a_body(self, tmp_path):
        app, _service, _adapter = _build(tmp_path)
        client = TestClient(app)
        attachment_id = _upload(client)
        etag = client.get(_base(f"/{attachment_id}")).headers["etag"]
        resp = client.get(_base(f"/{attachment_id}"), headers={"If-None-Match": etag})
        assert resp.status_code == 304
        assert resp.content == b""
        assert resp.headers["etag"] == etag
        assert resp.headers["cache-control"] == "private, no-cache"

    def test_a_stale_etag_gets_the_full_object(self, tmp_path):
        app, _service, _adapter = _build(tmp_path)
        client = TestClient(app)
        resp = client.get(_base(f"/{_upload(client)}"), headers={"If-None-Match": '"other"'})
        assert resp.status_code == 200
        assert len(resp.content) > 0

    def test_a_deleted_attachment_is_not_revalidated_from_cache(self, tmp_path):
        # Revocation: the cached copy's ETag no longer buys a 304 once the object is gone.
        app, _service, _adapter = _build(tmp_path)
        client = TestClient(app)
        attachment_id = _upload(client)
        etag = client.get(_base(f"/{attachment_id}")).headers["etag"]
        assert client.delete(_base(f"/{attachment_id}")).status_code == 204
        resp = client.get(_base(f"/{attachment_id}"), headers={"If-None-Match": etag})
        assert resp.status_code == 404

    def test_a_caller_without_read_permission_gets_no_304(self, tmp_path):

        app, _service, _adapter = _build(tmp_path)
        client = TestClient(app)
        attachment_id = _upload(client)
        etag = client.get(_base(f"/{attachment_id}")).headers["etag"]

        def revoked():
            raise ForbiddenError("membership revoked")

        app.dependency_overrides[get_current_tenant] = revoked
        resp = client.get(_base(f"/{attachment_id}"), headers={"If-None-Match": etag})
        assert resp.status_code == 403


class TestThumbnailDownload:
    def _with_rendition(self, tmp_path, size: int = 128):
        app, service, adapter = _build(tmp_path)
        client = TestClient(app)
        attachment_id = _upload(client)
        record = service._repo.get(attachment_id, "tenant_anna")

        async def one_chunk():
            yield b"RIFF0000WEBP"

        asyncio.run(adapter.put_object(thumbnail_key(record.storage_key, size), one_chunk(), "image/webp"))
        return client, attachment_id, record

    def test_a_thumbnail_is_revalidated_under_a_weak_etag(self, tmp_path):
        client, attachment_id, record = self._with_rendition(tmp_path)
        resp = client.get(_base(f"/{attachment_id}/thumbnails/128"))
        assert resp.status_code == 200
        assert resp.headers["cache-control"] == "private, no-cache"
        assert resp.headers["etag"] == f'W/"{record.sha256}-128"'

    def test_a_matching_thumbnail_etag_answers_304(self, tmp_path):
        client, attachment_id, _record = self._with_rendition(tmp_path)
        etag = client.get(_base(f"/{attachment_id}/thumbnails/128")).headers["etag"]
        resp = client.get(_base(f"/{attachment_id}/thumbnails/128"), headers={"If-None-Match": etag})
        assert resp.status_code == 304
        assert resp.content == b""

    def test_another_size_does_not_match(self, tmp_path):
        client, attachment_id, record = self._with_rendition(tmp_path, size=512)
        etag_128 = f'W/"{record.sha256}-128"'
        resp = client.get(_base(f"/{attachment_id}/thumbnails/512"), headers={"If-None-Match": etag_128})
        assert resp.status_code == 200


class TestIfNoneMatch:
    @pytest.mark.parametrize(
        ("header", "hit"),
        [
            (None, False),
            ("", False),
            ('"abc"', True),
            ('W/"abc"', True),
            ('"x", "abc"', True),
            ('"x" , W/"abc"', True),
            ("*", True),
            ('"abcd"', False),
            ("abc", False),
        ],
    )
    def test_weak_comparison(self, header, hit):
        assert if_none_match_hits(header, '"abc"') is hit


_API_ROOT = Path(__file__).resolve().parents[2] / "app" / "api"


def test_no_private_download_is_cached_without_asking():
    """Class guard (#2254): no API route answers ``private, max-age=…`` again.

    A private answer is either session-authorized (revocable at any time) or
    token-authorized (expires in minutes); a fixed ``max-age`` outlives both.
    Use ``private, no-cache`` with an ETag, or ``no-store``.
    """
    pattern = re.compile(r"private,\s*max-age", re.IGNORECASE)
    offenders = []
    for path in sorted(_API_ROOT.rglob("*.py")):
        tree = ast.parse(path.read_text())
        docstrings = {
            id(owner.body[0].value)
            for owner in ast.walk(tree)
            if isinstance(owner, ast.Module | ast.ClassDef | ast.FunctionDef | ast.AsyncFunctionDef)
            and owner.body
            and isinstance(owner.body[0], ast.Expr)
            and isinstance(owner.body[0].value, ast.Constant)
        }
        offenders.extend(
            f"{path.relative_to(_API_ROOT)}:{node.lineno}"
            for node in ast.walk(tree)
            if isinstance(node, ast.Constant)
            and isinstance(node.value, str)
            and id(node) not in docstrings
            and pattern.search(node.value)
        )
    assert offenders == []


def test_no_upload_route_reads_a_file_without_a_bound():
    """Class guard (#2254): ``await <upload>.read()`` without a size reads whatever the body holds.

    Pass the route's limit + 1 (``await file.read(max_bytes + 1)``) or stream in
    bounded chunks; the ASGI ceiling is the backstop, not the per-route limit.
    """
    offenders = []
    for path in sorted(_API_ROOT.rglob("*.py")):
        for node in ast.walk(ast.parse(path.read_text())):
            call = node.value if isinstance(node, ast.Await) else None
            if (
                isinstance(call, ast.Call)
                and isinstance(call.func, ast.Attribute)
                and call.func.attr == "read"
                and not call.args
                and not call.keywords
            ):
                offenders.append(f"{path.relative_to(_API_ROOT)}:{node.lineno} {ast.unparse(call)}")
    assert offenders == []
