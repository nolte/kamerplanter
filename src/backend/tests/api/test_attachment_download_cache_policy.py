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
import time
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.api.v1.attachments.response_headers import if_none_match_hits, object_etag, rendition_etag
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
        attachment_id = _upload(client)
        resp = client.get(_base(f"/{attachment_id}"))
        assert resp.status_code == 200
        assert resp.headers["cache-control"] == "private, no-cache"
        assert resp.headers["etag"].startswith('"')
        # Not the hash of the uploaded (pre-EXIF-strip) bytes: a holder of the
        # original file must not be able to confirm it was this upload.
        record = _service._repo.get(attachment_id, "tenant_anna")
        assert record.sha256 not in resp.headers["etag"]
        assert resp.headers["etag"] == object_etag(record.storage_key, record.sha256)

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
        assert resp.headers["etag"] == rendition_etag(record.storage_key, record.sha256, 128)
        assert record.sha256 not in resp.headers["etag"]

    def test_a_matching_thumbnail_etag_answers_304(self, tmp_path):
        client, attachment_id, _record = self._with_rendition(tmp_path)
        etag = client.get(_base(f"/{attachment_id}/thumbnails/128")).headers["etag"]
        resp = client.get(_base(f"/{attachment_id}/thumbnails/128"), headers={"If-None-Match": etag})
        assert resp.status_code == 304
        assert resp.content == b""

    def test_another_size_does_not_match(self, tmp_path):
        client, attachment_id, record = self._with_rendition(tmp_path, size=512)
        etag_128 = rendition_etag(record.storage_key, record.sha256, 128)
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


_APP_ROOT = Path(__file__).resolve().parents[2] / "app"
_API_ROOT = _APP_ROOT / "api"


def _docstring_ids(tree: ast.AST) -> set[int]:
    return {
        id(owner.body[0].value)
        for owner in ast.walk(tree)
        if isinstance(owner, ast.Module | ast.ClassDef | ast.FunctionDef | ast.AsyncFunctionDef)
        and owner.body
        and isinstance(owner.body[0], ast.Expr)
        and isinstance(owner.body[0].value, ast.Constant)
    }


def _module_string_constants() -> dict[str, str]:
    """Every module-level ``NAME = "literal"`` under ``app/`` — the values a header can name."""
    constants: dict[str, str] = {}
    for path in _APP_ROOT.rglob("*.py"):
        for node in ast.parse(path.read_text()).body:
            if isinstance(node, ast.Assign | ast.AnnAssign) and isinstance(node.value, ast.Constant):
                targets = node.targets if isinstance(node, ast.Assign) else [node.target]
                for target in targets:
                    if isinstance(target, ast.Name) and isinstance(node.value.value, str):
                        constants[target.id] = node.value.value
    return constants


def _cache_control_values(tree: ast.AST) -> list[ast.expr]:
    """The expressions a module sets as ``Cache-Control``: dict entries and header assignments."""
    found: list[ast.expr] = []

    def is_key(node: ast.AST | None) -> bool:
        return isinstance(node, ast.Constant) and isinstance(node.value, str) and node.value.lower() == "cache-control"

    for node in ast.walk(tree):
        if isinstance(node, ast.Dict):
            found.extend(value for key, value in zip(node.keys, node.values, strict=True) if is_key(key))
        elif isinstance(node, ast.Assign):
            found.extend(
                node.value for target in node.targets if isinstance(target, ast.Subscript) and is_key(target.slice)
            )
    return found


def _stores_without_asking(directive: str) -> bool:
    """``max-age``/``s-maxage`` > 0 without ``no-cache``/``no-store``: reused without asking the server."""
    parts = [part.strip().lower() for part in directive.split(",")]
    if "no-store" in parts or "no-cache" in parts:
        return False
    for part in parts:
        name, _, value = part.partition("=")
        if name.strip() in {"max-age", "s-maxage"} and value.strip().isdecimal() and int(value) > 0:
            return True
    return False


@pytest.mark.parametrize(
    ("directive", "stored"),
    [
        ("private, max-age=86400", True),
        ("public, max-age=86400", True),
        ("PRIVATE,MAX-AGE=60", True),
        ("s-maxage=10", True),
        ("private, no-cache", False),
        ("no-store", False),
        ("max-age=0", False),
        ("no-cache", False),
        ("max-age=86400, no-cache", False),
    ],
)
def test_the_directive_parser(directive, stored):
    assert _stores_without_asking(directive) is stored


def test_no_route_answer_is_reused_without_asking():
    """Class guard (#2254): no ``Cache-Control`` the app sets lets a cache reuse an answer unasked.

    Every API answer needs a signed-in caller, a revocable session, or a token
    that expires in minutes; a ``max-age`` outlives all of them. Use
    ``private, no-cache`` with an ETag, or ``no-store``. A value the guard cannot
    resolve to a literal (or a module constant) is an offender too.
    """
    constants = _module_string_constants()
    offenders = []
    for path in sorted(_APP_ROOT.rglob("*.py")):
        for value in _cache_control_values(ast.parse(path.read_text())):
            if isinstance(value, ast.Constant) and isinstance(value.value, str):
                directive = value.value
            elif isinstance(value, ast.Name) and value.id in constants:
                directive = constants[value.id]
            else:
                offenders.append(f"{path.relative_to(_APP_ROOT)}:{value.lineno} unresolvable {ast.unparse(value)}")
                continue
            if _stores_without_asking(directive):
                offenders.append(f"{path.relative_to(_APP_ROOT)}:{value.lineno} {directive}")
    assert offenders == []


def test_the_cache_control_guard_sees_every_site_it_claims():
    # Positive control: the guard must find the sites that exist, or it proves nothing.
    sites = {
        path.relative_to(_APP_ROOT).as_posix()
        for path in _APP_ROOT.rglob("*.py")
        if _cache_control_values(ast.parse(path.read_text()))
    }
    assert {
        "api/v1/attachments/tenant_router.py",
        "api/v1/attachments/token_router.py",
        "api/v1/ipm/pest_images_router.py",
        "api/v1/calendar/feed_router.py",
        "main.py",
    } <= sites


def _is_minus_one(node: ast.expr) -> bool:
    return (
        isinstance(node, ast.UnaryOp)
        and isinstance(node.op, ast.USub)
        and isinstance(node.operand, ast.Constant)
        and node.operand.value == 1
    ) or (isinstance(node, ast.Constant) and node.value == -1)


def _unbounded_reads(source: str) -> list[ast.Call]:
    """Reads of a request body or upload that take whatever the body holds."""
    hits: list[ast.Call] = []
    for node in ast.walk(ast.parse(source)):
        if not (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)):
            continue
        attr = node.func.attr
        receiver = ast.unparse(node.func.value)
        whole = not node.args and not node.keywords or (len(node.args) == 1 and _is_minus_one(node.args[0]))
        if attr == "read" and whole:
            hits.append(node)  # ``await upload.read()``, ``upload.file.read()``, ``read(-1)``
        elif receiver.split(".")[-1] == "request" and attr in {"body", "form", "stream"}:
            hits.append(node)  # whole-body reads behind the route's back
    return hits


@pytest.mark.parametrize(
    ("source", "hits"),
    [
        ("async def f(file):\n    await file.read()", 1),
        ("async def f(file):\n    await file.read(-1)", 1),
        ("def f(file):\n    file.file.read()", 1),
        ("async def f(request):\n    await request.body()", 1),
        ("async def f(request):\n    await request.form()", 1),
        ("async def f(request):\n    request.stream()", 1),
        ("async def f(file):\n    await file.read(1024)", 0),
        ("async def f(file, n):\n    await file.read(n + 1)", 0),
    ],
)
def test_the_read_predicate(source, hits):
    assert len(_unbounded_reads(source)) == hits


def test_no_upload_route_reads_a_body_without_a_bound():
    """Class guard (#2254): no route reads a body or an upload without a size.

    Pass the route's limit + 1 (``await file.read(max_bytes + 1)``) or stream in
    bounded chunks; the ASGI ceiling is the backstop, not the per-route limit.
    """
    offenders = [
        f"{path.relative_to(_API_ROOT)}:{call.lineno} {ast.unparse(call)}"
        for path in sorted(_API_ROOT.rglob("*.py"))
        for call in _unbounded_reads(path.read_text())
    ]
    assert offenders == []
