"""nginx never caches the service worker or the manifest, and the CSP names the worker (REQ-053 WP 9.1, #2741).

Guardrail G-W9 (d): the Workbox service worker stays at ``/sw.js`` and nginx serves
it and ``/manifest.json`` with ``Cache-Control: no-store``. Without an exact
``location = /sw.js`` the file falls into the static-asset regex location
(``~* \\.(js|css|...)$`` → ``expires 1y`` + ``public, immutable``) — the trap the
wave-9 plan names at ``nginx.conf:104-106`` — and no worker update would ever
reach a browser: the old worker, its precache and its cache rules would stay on
every device for a year.

Both places that configure the frontend's nginx are scanned by ONE detector,
:func:`_findings`: the image's ``src/frontend/nginx.conf`` and the
``frontend-nginx`` ConfigMap in ``helm/kamerplanter/values*.yaml``, which
*replaces* the image's ``conf.d`` in a Helm install. In the image a location with
its own ``add_header`` drops the server-level headers, so it must re-include the
security-header snippet; the snippet's CSP must name ``worker-src 'self'`` and
nothing broader.

**Not seen**: an Ingress or CDN in front of nginx that adds its own caching —
that is the P-7 header probe at the prod ingress (WP 9.17).
"""

from __future__ import annotations

import pathlib
import re

import pytest
import yaml

REPO_ROOT = pathlib.Path(__file__).resolve().parents[5]
IMAGE_CONF = REPO_ROOT / "src/frontend/nginx.conf"
SECURITY_HEADERS = REPO_ROOT / "src/frontend/nginx-security-headers.inc"
HELM_DIR = REPO_ROOT / "helm/kamerplanter"

_NO_STORE_PATHS = ("/sw.js", "/manifest.json")
_CACHE_CONTROL = re.compile(r'add_header\s+Cache-Control\s+"([^"]*)"')
_CSP = re.compile(r'add_header\s+Content-Security-Policy\s+"([^"]*)"')


def _strip_comments(conf: str) -> str:
    return "\n".join(line.split("#", 1)[0] for line in conf.splitlines())


def _exact_location(conf: str, path: str) -> str | None:
    """The body of ``location = <path> { ... }`` (no nested blocks), or ``None``."""
    match = re.search(r"location\s*=\s*" + re.escape(path) + r"\s*\{([^{}]*)\}", _strip_comments(conf))
    return match.group(1) if match else None


def _findings(conf: str, where: str, *, needs_header_include: bool) -> list[str]:
    """THE detector: every way *conf* could let a browser or proxy keep the worker or the manifest."""
    conf = _strip_comments(conf)
    findings: list[str] = []
    for path in _NO_STORE_PATHS:
        body = _exact_location(conf, path)
        if body is None:
            findings.append(f"{where}: no `location = {path}` — it falls into the 1y immutable asset regex")
            continue
        values = _CACHE_CONTROL.findall(body)
        if not any("no-store" in [d.strip().lower() for d in value.split(",")] for value in values):
            findings.append(f"{where}: `location = {path}` does not send Cache-Control no-store")
        if any("immutable" in value or "max-age" in value for value in values):
            findings.append(f"{where}: `location = {path}` still allows caching")
        if re.search(r"^\s*expires\s+(?!off|epoch|-1)", body, re.MULTILINE):
            findings.append(f"{where}: `location = {path}` sets an expiry")
        if needs_header_include and "nginx-security-headers.inc" not in body:
            findings.append(f"{where}: `location = {path}` drops the security headers (own add_header)")
    return findings


def _csp_findings(snippet: str, where: str) -> list[str]:
    findings: list[str] = []
    policies = _CSP.findall(_strip_comments(snippet))
    if len(policies) != 1:
        return [f"{where}: expected exactly one Content-Security-Policy, found {len(policies)}"]
    directives = {d.strip().split()[0]: d.strip().split()[1:] for d in policies[0].split(";") if d.strip()}
    if directives.get("worker-src") != ["'self'"]:
        findings.append(f"{where}: worker-src is {directives.get('worker-src')!r}, expected only 'self'")
    return findings


def _helm_configs() -> dict[str, str]:
    """Every values file's enabled ``frontend-nginx`` ``default.conf``."""
    configs: dict[str, str] = {}
    for values in sorted(HELM_DIR.glob("values*.yaml")):
        data = yaml.safe_load(values.read_text(encoding="utf-8")) or {}
        entry = (data.get("configMaps") or {}).get("frontend-nginx") or {}
        conf = (entry.get("data") or {}).get("default.conf")
        if entry.get("enabled", True) and conf:
            configs[values.name] = conf
    return configs


def test_the_selector_finds_both_copies() -> None:
    assert IMAGE_CONF.is_file()
    assert SECURITY_HEADERS.is_file()
    assert "values.yaml" in _helm_configs(), "the base chart's frontend-nginx ConfigMap left the scan"


def test_the_image_never_caches_the_worker_or_the_manifest() -> None:
    conf = IMAGE_CONF.read_text(encoding="utf-8")
    assert _findings(conf, "src/frontend/nginx.conf", needs_header_include=True) == []


@pytest.mark.parametrize("name", sorted(_helm_configs()))
def test_the_chart_never_caches_the_worker_or_the_manifest(name: str) -> None:
    assert _findings(_helm_configs()[name], f"helm:{name}", needs_header_include=False) == []


def test_the_csp_names_the_worker_source() -> None:
    assert _csp_findings(SECURITY_HEADERS.read_text(encoding="utf-8"), "nginx-security-headers.inc") == []


_SW = "location = /sw.js {\n        "
_SW_NO_STORE = 'add_header Cache-Control "no-store, no-cache, must-revalidate";'
_SW_INCLUDE = "\n        include /etc/nginx/conf.d/nginx-security-headers.inc;"

_MUTATIONS = [
    ("no-sw-location", "location = /sw.js {", "location = /sw-old.js {"),
    ("no-manifest-location", "location = /manifest.json {", "location = /manifest-old.json {"),
    ("cacheable-sw", _SW + _SW_NO_STORE, _SW + 'add_header Cache-Control "public";'),
    ("immutable-sw", _SW + _SW_NO_STORE, _SW + 'add_header Cache-Control "no-store, immutable";'),
    ("expires-sw", _SW + _SW_NO_STORE, _SW + "expires 1y;\n        " + _SW_NO_STORE),
    ("headers-dropped", _SW + _SW_NO_STORE + _SW_INCLUDE, _SW + _SW_NO_STORE),
]


@pytest.mark.parametrize(("mutation", "old", "new"), _MUTATIONS, ids=[m[0] for m in _MUTATIONS])
def test_the_detector_sees_each_regression(mutation: str, old: str, new: str) -> None:
    """Red first, through the same detector: a mutated copy of the real config is refused."""
    conf = IMAGE_CONF.read_text(encoding="utf-8")
    # prose-permeable: mutation precondition: the literal it replaces must be present verbatim, else the mutation
    # is a no-op and the red case proves nothing
    assert old in conf, f"mutation {mutation} no longer applies — update it"
    assert _findings(conf.replace(old, new, 1), "mutated", needs_header_include=True) != []


@pytest.mark.parametrize(
    ("mutation", "old", "new"),
    [
        ("missing", "worker-src 'self'; ", ""),
        ("blob-worker", "worker-src 'self';", "worker-src 'self' blob:;"),
        ("wildcard-worker", "worker-src 'self';", "worker-src *;"),
    ],
)
def test_the_csp_detector_sees_each_regression(mutation: str, old: str, new: str) -> None:
    snippet = SECURITY_HEADERS.read_text(encoding="utf-8")
    # prose-permeable: the mutation rewrites these exact bytes of the file; the check proves it still applies.
    assert old in snippet, f"mutation {mutation} no longer applies — update it"
    assert _csp_findings(snippet.replace(old, new, 1), "mutated") != []
