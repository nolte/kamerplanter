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
*replaces* the image's ``conf.d`` in a Helm install. A location with its own
``add_header`` drops the server-level headers: in the image it re-includes the
security-header snippet, in the chart it repeats ``X-Content-Type-Options``,
``X-Frame-Options`` and ``Referrer-Policy`` and carries the image snippet's CSP
verbatim (#2786 review). The snippet's CSP must name ``worker-src 'self'`` and
nothing broader. ``/manifest.json`` is served as ``application/manifest+json``
through a ``types`` block — ``default_type`` is ineffective there, because the
global ``mime.types`` already maps ``.json``.

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


_MANIFEST_TYPES = re.compile(r"\btypes\s*\{\s*application/manifest\+json\s+json\s*;\s*\}")
_REPEATED_HEADERS = ("X-Content-Type-Options", "X-Frame-Options", "Referrer-Policy")


def _exact_location(conf: str, path: str) -> str | None:
    """The body of ``location = <path> { ... }`` (one level of nested blocks, e.g. ``types``), or ``None``."""
    pattern = r"location\s*=\s*" + re.escape(path) + r"\s*\{((?:[^{}]|\{[^{}]*\})*)\}"
    match = re.search(pattern, _strip_comments(conf))
    return match.group(1) if match else None


def _image_csp() -> str:
    policies = _CSP.findall(_strip_comments(SECURITY_HEADERS.read_text(encoding="utf-8")))
    return policies[0] if policies else ""


def _header_findings(body: str, where: str, path: str, *, needs_header_include: bool) -> list[str]:
    """The location must not lose the server-level security headers to its own ``add_header``."""
    body = _strip_comments(body)
    if needs_header_include:
        if "nginx-security-headers.inc" not in body:
            return [f"{where}: `location = {path}` drops the security headers (own add_header)"]
        return []
    findings = [
        f"{where}: `location = {path}` drops {header} (own add_header)"
        for header in _REPEATED_HEADERS
        if not re.search(r"add_header\s+" + re.escape(header) + r"\s", body)
    ]
    if _CSP.findall(body) != [_image_csp()]:
        findings.append(f"{where}: `location = {path}` does not carry the image's CSP verbatim")
    return findings


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
        findings += _header_findings(body, where, path, needs_header_include=needs_header_include)
        if path == "/manifest.json":
            if not _MANIFEST_TYPES.search(body):
                findings.append(f"{where}: `location = {path}` is not typed application/manifest+json")
            if re.search(r"^\s*default_type\s", body, re.MULTILINE):
                findings.append(f"{where}: `location = {path}` relies on the ineffective default_type")
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


_MANIFEST_TYPES_LINE = "types { application/manifest+json json; }"

_MANIFEST_MUTATIONS = [
    ("manifest-untyped", _MANIFEST_TYPES_LINE, ""),
    ("manifest-default-type", _MANIFEST_TYPES_LINE, "default_type application/manifest+json;"),
]


@pytest.mark.parametrize(("mutation", "old", "new"), _MANIFEST_MUTATIONS, ids=[m[0] for m in _MANIFEST_MUTATIONS])
def test_the_detector_sees_an_untyped_manifest(mutation: str, old: str, new: str) -> None:
    conf = IMAGE_CONF.read_text(encoding="utf-8")
    # prose-permeable: mutation precondition: the literal it replaces must be present verbatim
    assert old in conf, f"mutation {mutation} no longer applies — update it"
    assert _findings(conf.replace(old, new, 1), "mutated", needs_header_include=True) != []


_HELM_MUTATIONS = [
    ("helm-no-nosniff", 'add_header X-Content-Type-Options "nosniff" always;'),
    ("helm-no-frame-options", 'add_header X-Frame-Options "SAMEORIGIN" always;'),
    ("helm-no-referrer-policy", 'add_header Referrer-Policy "strict-origin-when-cross-origin" always;'),
    ("helm-no-csp", "add_header Content-Security-Policy "),
]


@pytest.mark.parametrize(("mutation", "dropped"), _HELM_MUTATIONS, ids=[m[0] for m in _HELM_MUTATIONS])
def test_the_detector_sees_a_dropped_chart_header(mutation: str, dropped: str) -> None:
    """Drop the header inside the chart's `location = /sw.js` only — the server-level copy stays."""
    conf = _helm_configs()["values.yaml"]
    body = _exact_location(conf, "/sw.js")
    assert body is not None
    assert dropped in body, f"mutation {mutation} no longer applies — update it"
    lines = [line for line in body.splitlines() if dropped not in line]
    mutated = conf.replace(body, "\n".join(lines), 1)
    assert _findings(mutated, "mutated", needs_header_include=False) != []


def test_the_chart_csp_drift_is_seen() -> None:
    conf = _helm_configs()["values.yaml"]
    assert "worker-src 'self';" in conf
    drifted = conf.replace("worker-src 'self';", "worker-src 'self' blob:;", 1)
    assert _findings(drifted, "mutated", needs_header_include=False) != []


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
