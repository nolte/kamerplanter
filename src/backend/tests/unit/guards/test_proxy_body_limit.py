"""#2144 (audit gap G-10) — the edge body limit admits every legitimate upload and stops the rest.

**The defect this is written against, measured 2026-10-09 on develop 6f93331f2.**
Neither nginx configuration set ``client_max_body_size`` — not the image's
``src/frontend/nginx.conf`` and not the ``default.conf`` the chart mounts over it
(``configMaps.frontend-nginx``, which REPLACES ``/etc/nginx/conf.d`` in every
Kubernetes release). nginx's default is 1 MiB. Both configurations, run in the
``nginx-unprivileged:1.31-alpine`` image and sent a POST to ``/api/v1/…``,
answered a 1 MiB body with 502 (forwarded; no backend behind the probe) and a
2 MiB, 25 MiB and 30 MiB body with **413** — so on the reference path
(ingress -> frontend nginx -> backend, the only path the backend's NetworkPolicy
admits, #1159) every attachment, plant photo, task photo, pest image and CSV
import above 1 MiB was refused at nginx, long before the backend's 25 MiB bound.

**The limit and its derivation.** The largest legitimate request body is an
attachment upload: ``storage_max_file_size_mb`` (25, a MiB bound — the backend
multiplies by ``1024 * 1024``) plus the multipart framing (boundaries, the
``category`` and ``capture_device`` fields, a few hundred bytes). Every other
upload bound is smaller (identification and CV images 5 MiB, pest images 8 MiB,
CSV import 10 MiB, an MCP image 4 MiB raw / about 5.4 MiB as base64 JSON). The
proxy limit is therefore ``storage_max_file_size_mb + 1`` MiB = ``26m`` (nginx's
``m`` is MiB): it never cuts a request the backend would accept, and a request
between 25 and 26 MiB still reaches the backend, which answers it with its own
typed 413 (``FileTooLargeError``). Everything above 26 MiB — including a JSON
body Starlette would otherwise read completely — stops at the edge.

**What is asserted.** The image's nginx.conf carries the limit once, at server
level (a ``location``-level directive would leave the other locations at 1 MiB),
equal to the Settings default + 1 MiB. The chart's ``default.conf`` and the
chart's ingress annotation (``nginx.ingress.kubernetes.io/proxy-body-size``, the
only per-Ingress body limit among the controllers the docs name — ingress-nginx
defaults to 1 MiB too) carry the SAME expression, derived from
``storage.maxFileSizeMb``, whose default equals the Settings default. What that
expression renders to — and that it follows ``storage.maxFileSizeMb`` — is held
by ``scripts/ci/assert_chart_contracts.sh`` (#2144 block); that nginx really
answers 413 above and forwards below is held by
``scripts/ci/probe_proxy_body_limit.sh``, which runs both configurations in the
production nginx image.

Traces to #2144 G-10 (no TC-ID: deployment configuration, no user-facing case).
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import yaml

from app.api.v1.imports.router import MAX_UPLOAD_SIZE_BYTES
from app.config.settings import Settings

_REPO = Path(__file__).resolve().parents[5]
_IMAGE_CONF = _REPO / "src" / "frontend" / "nginx.conf"
_CHART_VALUES = _REPO / "helm" / "kamerplanter" / "values.yaml"
_INGRESS_ANNOTATION = "nginx.ingress.kubernetes.io/proxy-body-size"
_MIB = 1024 * 1024
_HEADROOM_MIB = 1
_SIZE = re.compile(r"^(?P<n>\d+)(?P<unit>[kKmMgG]?)$")
_UNIT = {"": 1, "k": 1024, "m": _MIB, "g": 1024 * _MIB}


def _default(field: str) -> int:
    value = Settings.model_fields[field].default
    assert isinstance(value, int), f"Settings.{field} has no int default"
    return value


def _strip_comments(conf: str) -> str:
    return "\n".join(line.split("#", 1)[0] for line in conf.splitlines())


def _server_level_directives(conf: str, name: str) -> list[tuple[int, str]]:
    """Return ``(depth, value)`` of every ``name`` directive; depth 1 is inside ``server {}``.

    Braces inside quoted strings (the ``map`` regexes) are skipped, so a
    ``{1,3}`` quantifier does not count as a block, and a Helm expression
    (``{{ … }}`` in the chart's copy) is one opaque token, returned verbatim.
    """
    found: list[tuple[int, str]] = []
    depth = 0
    templates: list[str] = []

    def _hide(match: re.Match[str]) -> str:
        templates.append(match.group(0))
        return f"\x00{len(templates) - 1}\x00"

    def _restore(value: str) -> str:
        return re.sub(r"\x00(\d+)\x00", lambda m: templates[int(m.group(1))], value)

    text = re.sub(r"\{\{.*?\}\}", _hide, _strip_comments(conf))
    for statement in re.finditer(r'"[^"]*"|\'[^\']*\'|[{};]|[^\s{};"\']+(?:\s+[^{};]*)?', text):
        token = statement.group(0)
        if token == "{":
            depth += 1
        elif token == "}":
            depth -= 1
        elif not token.startswith(("'", '"')):
            parts = token.split(None, 1)
            if parts and parts[0] == name:
                found.append((depth, _restore(parts[1].strip()) if len(parts) > 1 else ""))
    assert depth == 0, "unbalanced braces in the nginx configuration"
    return found


def _bytes(size: str) -> int:
    match = _SIZE.match(size)
    assert match, f"client_max_body_size {size!r} is not a plain nginx size"
    return int(match["n"]) * _UNIT[match["unit"].lower()]


def _chart_values() -> dict[str, Any]:
    return yaml.safe_load(_CHART_VALUES.read_text(encoding="utf-8")) or {}


def _chart_default_conf() -> str:
    conf = _chart_values()["configMaps"]["frontend-nginx"]["data"]["default.conf"]
    assert isinstance(conf, str)
    return conf


def _expected_limit_bytes() -> int:
    return (_default("storage_max_file_size_mb") + _HEADROOM_MIB) * _MIB


def test_largest_legitimate_upload_is_the_attachment_bound() -> None:
    """The derivation's premise: no other upload bound exceeds the attachment bound."""
    largest = _default("storage_max_file_size_mb") * _MIB
    others = {
        "identification_max_image_size_mb": _default("identification_max_image_size_mb") * _MIB,
        "pest_detection_max_image_size_mb": _default("pest_detection_max_image_size_mb") * _MIB,
        "cv_diagnosis_max_image_size_mb": _default("cv_diagnosis_max_image_size_mb") * _MIB,
        # base64 inside a JSON-RPC body: 4/3 of the raw bytes.
        "mcp_max_image_payload_mb (base64)": _default("mcp_max_image_payload_mb") * _MIB * 4 // 3,
        "imports MAX_UPLOAD_SIZE_BYTES": MAX_UPLOAD_SIZE_BYTES,
    }
    too_big = {name: size for name, size in others.items() if size >= largest}
    assert not too_big, f"an upload bound reaches the attachment bound, re-derive the proxy limit: {too_big}"


def test_image_nginx_sets_the_limit_once_at_server_level() -> None:
    directives = _server_level_directives(_IMAGE_CONF.read_text(encoding="utf-8"), "client_max_body_size")
    assert [depth for depth, _ in directives] == [1], (
        f"{_IMAGE_CONF}: expected exactly one client_max_body_size inside server {{}} "
        f"(nginx's default is 1 MiB), found {directives}"
    )
    assert _bytes(directives[0][1]) == _expected_limit_bytes(), (
        f"{_IMAGE_CONF}: client_max_body_size {directives[0][1]} is not "
        f"storage_max_file_size_mb + {_HEADROOM_MIB} MiB = {_expected_limit_bytes()} bytes"
    )


def test_chart_storage_default_matches_the_backend_default() -> None:
    assert _chart_values()["storage"]["maxFileSizeMb"] == _default("storage_max_file_size_mb")


def test_chart_nginx_sets_the_limit_once_at_server_level_from_storage() -> None:
    directives = _server_level_directives(_chart_default_conf(), "client_max_body_size")
    assert [depth for depth, _ in directives] == [1], (
        "configMaps.frontend-nginx default.conf: expected exactly one client_max_body_size "
        f"inside server {{}}, found {directives}"
    )
    assert ".Values.storage.maxFileSizeMb" in directives[0][1], (
        f"the chart's nginx limit must follow storage.maxFileSizeMb, not a copied number: {directives[0][1]!r}"
    )


def test_chart_ingress_annotation_equals_the_nginx_limit() -> None:
    """The ingress and nginx limit are one expression, so they cannot drift apart."""
    nginx_value = _server_level_directives(_chart_default_conf(), "client_max_body_size")
    assert nginx_value, "configMaps.frontend-nginx default.conf sets no client_max_body_size"
    annotations = ((_chart_values().get("ingress") or {}).get("main") or {}).get("annotations") or {}
    assert annotations.get(_INGRESS_ANNOTATION) == nginx_value[0][1].rstrip(";").strip(), (
        f"ingress.main.annotations[{_INGRESS_ANNOTATION!r}] = "
        f"{annotations.get(_INGRESS_ANNOTATION)!r} differs from the nginx limit "
        f"{nginx_value[0][1]!r}"
    )
