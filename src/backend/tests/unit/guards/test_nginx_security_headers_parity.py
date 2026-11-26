"""The Helm chart's frontend nginx sends the image's security headers on every path, minus HSTS (#2816).

The image serves ``src/frontend/nginx.conf`` and includes ``nginx-security-headers.inc`` from
every location. A Helm install mounts the ``frontend-nginx`` ConfigMap over ``/etc/nginx/conf.d``,
which *replaces* both files, so the chart carries its own copy of the snippet as a second
ConfigMap key. A Helm value cannot read a file outside the chart, so one physical source is not
possible; this guard holds the two copies equal instead. Before #2816 the chart sent no CSP on
``index.html`` at all: the document's CSP is what decides whether a service worker may register
(``worker-src``), and an XSS on the document faced no policy.

The class, not the reported sites:

* **Drift** — the chart snippet's header set equals the image snippet's, header for header
  (name, value, ``always``), except ``Strict-Transport-Security``.
* **Inheritance loss** — nginx scopes ``add_header`` per location: a location with its own
  ``add_header`` drops every server-level one. So EVERY location, in the image and in every
  enabled chart config, includes the snippet, and the chart has no server-level ``add_header``
  that would only look like coverage.
* **HSTS ownership** — TLS terminates at the Ingress, which owns HSTS (operator decision D4); the
  pod sends none, so it can never contradict the Ingress.
* **Plain-HTTP access** — ``kubectl port-forward`` serves over ``http://localhost``; the CSP must
  not carry ``upgrade-insecure-requests``/``block-all-mixed-content`` or an ``https:``-only source.

**Not seen**: what an Ingress or CDN in front adds or strips — the curl through a port-forward and
through the Ingress host is the runtime check (docs/de/deployment/helm.md).
"""

from __future__ import annotations

import pathlib
import re

import pytest
import yaml

REPO_ROOT = pathlib.Path(__file__).resolve().parents[5]
IMAGE_CONF = REPO_ROOT / "src/frontend/nginx.conf"
IMAGE_SNIPPET = REPO_ROOT / "src/frontend/nginx-security-headers.inc"
HELM_DIR = REPO_ROOT / "helm/kamerplanter"

SNIPPET_NAME = "nginx-security-headers.inc"
HSTS = "strict-transport-security"

_ADD_HEADER = re.compile(r'\badd_header\s+([A-Za-z0-9-]+)\s+"([^"]*)"\s*(always)?\s*;')
_LOCATION = re.compile(r"\blocation\b([^{;]*)\{((?:[^{}]|\{[^{}]*\})*)\}")
_LOCATION_KEYWORD = re.compile(r"\blocation\b")
_INCLUDE = re.compile(r"\binclude\s+(\S+)\s*;")
_HELM_EXPR = re.compile(r"\{\{.*?\}\}")


def _strip_comments(conf: str) -> str:
    return "\n".join(line.split("#", 1)[0] for line in conf.splitlines())


def _headers(snippet: str) -> dict[str, tuple[str, bool]]:
    """``{lower-case header name: (value, always)}`` of every ``add_header`` in *snippet*."""
    return {
        name.lower(): (value, bool(always)) for name, value, always in _ADD_HEADER.findall(_strip_comments(snippet))
    }


def _locations(conf: str) -> list[tuple[str, str]]:
    """Every ``location <match> { body }`` as ``(match, body)`` (one nested level, e.g. ``types``)."""
    return [(match.strip(), body) for match, body in _LOCATION.findall(_strip_comments(conf))]


def _helm_frontend_configmaps() -> dict[str, dict[str, str]]:
    """Every values file's enabled ``frontend-nginx`` ConfigMap data."""
    found: dict[str, dict[str, str]] = {}
    for values in sorted(HELM_DIR.glob("values*.yaml")):
        data = yaml.safe_load(values.read_text(encoding="utf-8")) or {}
        entry = (data.get("configMaps") or {}).get("frontend-nginx") or {}
        if entry.get("enabled", True) and (entry.get("data") or {}).get("default.conf"):
            # bjw-s renders every value as a template; a `{{ ... }}` expression (the body limits) carries
            # braces nginx never sees, so it is reduced to a placeholder before the block parser runs.
            found[values.name] = {key: _HELM_EXPR.sub("HELM_EXPR", text) for key, text in entry["data"].items()}
    return found


def _location_findings(conf: str, where: str, *, server_level_headers_allowed: bool) -> list[str]:
    """THE inheritance detector: every location includes the snippet; nothing pretends to cover it."""
    stripped = _strip_comments(conf)
    findings: list[str] = []
    locations = _locations(stripped)
    keywords = len(_LOCATION_KEYWORD.findall(stripped))
    if keywords != len(locations):
        findings.append(f"{where}: {keywords} `location` keywords but {len(locations)} parsed blocks — selector gap")
    if not locations:
        findings.append(f"{where}: no location block found")
    for match, body in locations:
        includes = [pathlib.PurePosixPath(path).name for path in _INCLUDE.findall(body)]
        if SNIPPET_NAME not in includes:
            findings.append(f"{where}: `location {match}` does not include {SNIPPET_NAME}")
        own = {name for name in _headers(body) if name != "cache-control"}
        if own:
            findings.append(f"{where}: `location {match}` sets security headers itself: {sorted(own)}")
    if not server_level_headers_allowed:
        outside = stripped
        for _match, body in locations:
            outside = outside.replace(body, "", 1)
        if _ADD_HEADER.search(outside):
            findings.append(f"{where}: server-level add_header — dropped by every location that sets its own")
    return findings


def _parity_findings(chart_snippet: str, image_snippet: str, where: str) -> list[str]:
    """THE drift detector: the chart's header set is the image's, minus HSTS."""
    chart, image = _headers(chart_snippet), _headers(image_snippet)
    findings: list[str] = []
    if HSTS in chart:
        findings.append(f"{where}: the pod sends HSTS — the Ingress owns it (TLS terminates there)")
    expected = {name: spec for name, spec in image.items() if name != HSTS}
    for name in sorted(set(expected) | set(chart) - {HSTS}):
        if chart.get(name) != expected.get(name):
            findings.append(f"{where}: {name} is {chart.get(name)!r}, the image sends {expected.get(name)!r}")
    return findings


def _plain_http_findings(snippet: str, where: str) -> list[str]:
    """The CSP must work over ``http://localhost`` (port-forward) as well as through the TLS Ingress."""
    policy = _headers(snippet).get("content-security-policy")
    if policy is None:
        return [f"{where}: no Content-Security-Policy"]
    findings: list[str] = []
    for directive in (d.strip() for d in policy[0].split(";") if d.strip()):
        name, *sources = directive.split()
        if name in ("upgrade-insecure-requests", "block-all-mixed-content"):
            findings.append(f"{where}: CSP carries {name} — breaks plain-HTTP port-forward access")
        findings += [
            f"{where}: CSP {name} has the https-only source {src}"
            for src in sources
            if src.lower() == "https:" or src.lower().startswith("https://")
        ]
    return findings


def test_the_selector_finds_every_copy() -> None:
    assert IMAGE_CONF.is_file()
    assert IMAGE_SNIPPET.is_file()
    assert "values.yaml" in _helm_frontend_configmaps(), "the base chart's frontend-nginx ConfigMap left the scan"
    assert _headers(IMAGE_SNIPPET.read_text(encoding="utf-8")), "the image snippet's headers left the parser"


def test_every_image_location_includes_the_snippet() -> None:
    conf = IMAGE_CONF.read_text(encoding="utf-8")
    assert _location_findings(conf, "src/frontend/nginx.conf", server_level_headers_allowed=False) == []


@pytest.mark.parametrize("name", sorted(_helm_frontend_configmaps()))
def test_every_chart_location_includes_the_snippet(name: str) -> None:
    conf = _helm_frontend_configmaps()[name]["default.conf"]
    assert _location_findings(conf, f"helm:{name}", server_level_headers_allowed=False) == []


@pytest.mark.parametrize("name", sorted(_helm_frontend_configmaps()))
def test_the_chart_snippet_equals_the_image_snippet_minus_hsts(name: str) -> None:
    chart = _helm_frontend_configmaps()[name].get(SNIPPET_NAME, "")
    assert _parity_findings(chart, IMAGE_SNIPPET.read_text(encoding="utf-8"), f"helm:{name}") == []


def test_the_csp_works_over_plain_http() -> None:
    assert _plain_http_findings(IMAGE_SNIPPET.read_text(encoding="utf-8"), SNIPPET_NAME) == []


# ── Red first, through the same detectors: a mutated copy of the real config is refused. ──

_INCLUDE_LINE = "include /etc/nginx/conf.d/nginx-security-headers.inc;"


def _chart_conf() -> str:
    return _helm_frontend_configmaps()["values.yaml"]["default.conf"]


def _chart_snippet() -> str:
    return _helm_frontend_configmaps()["values.yaml"][SNIPPET_NAME]


@pytest.mark.parametrize("location", ["location / {", "location /api/ {", "location = /sw.js {"])
def test_the_detector_sees_a_location_without_the_snippet(location: str) -> None:
    conf = _chart_conf()
    start = conf.index(location)
    include_at = conf.index(_INCLUDE_LINE, start)
    mutated = conf[:include_at] + conf[include_at + len(_INCLUDE_LINE) :]
    assert _location_findings(mutated, "mutated", server_level_headers_allowed=False) != []


def test_the_detector_sees_a_server_level_header() -> None:
    conf = _chart_conf()
    anchor = "client_max_body_size"
    assert anchor in conf
    mutated = conf.replace(anchor, 'add_header X-Content-Type-Options "nosniff" always;\n    ' + anchor, 1)
    assert _location_findings(mutated, "mutated", server_level_headers_allowed=False) != []


def test_the_detector_sees_a_location_setting_its_own_security_header() -> None:
    conf = _chart_conf()
    assert _INCLUDE_LINE in conf
    mutated = conf.replace(_INCLUDE_LINE, _INCLUDE_LINE + '\nadd_header Referrer-Policy "no-referrer" always;', 1)
    assert _location_findings(mutated, "mutated", server_level_headers_allowed=False) != []


def test_the_detector_sees_an_unparsed_location() -> None:
    """A location the block regex cannot parse is a selector gap, not a silent pass."""
    conf = _chart_conf() + "\nlocation /extra/ { a { b { c; } } }\n"
    assert _location_findings(conf, "mutated", server_level_headers_allowed=False) != []


_IMAGE = IMAGE_SNIPPET.read_text(encoding="utf-8") if IMAGE_SNIPPET.is_file() else ""

_PARITY_MUTATIONS = [
    ("csp-drift", "worker-src 'self';", "worker-src 'self' blob:;"),
    ("csp-dropped", 'add_header Content-Security-Policy "', 'add_header X-Dropped-Policy "'),
    ("nosniff-dropped", 'add_header X-Content-Type-Options "nosniff" always;', ""),
    (
        "always-dropped",
        'add_header Referrer-Policy "strict-origin-when-cross-origin" always;',
        'add_header Referrer-Policy "strict-origin-when-cross-origin";',
    ),
    (
        "extra-header",
        'add_header X-Frame-Options "DENY" always;',
        'add_header X-Frame-Options "DENY" always;\nadd_header X-Extra "1" always;',
    ),
    (
        "hsts-in-pod",
        'add_header X-Frame-Options "DENY" always;',
        'add_header X-Frame-Options "DENY" always;\nadd_header Strict-Transport-Security "max-age=1" always;',
    ),
]


@pytest.mark.parametrize(("mutation", "old", "new"), _PARITY_MUTATIONS, ids=[m[0] for m in _PARITY_MUTATIONS])
def test_the_detector_sees_chart_drift(mutation: str, old: str, new: str) -> None:
    snippet = _chart_snippet()
    # Mutation precondition: the literal it replaces must be present verbatim, else the mutation is a no-op.
    assert old in snippet, f"mutation {mutation} no longer applies — update it"
    assert _parity_findings(snippet.replace(old, new, 1), _IMAGE, "mutated") != []


_HTTP_MUTATIONS = [
    ("upgrade-insecure", "; manifest-src 'self'", "; manifest-src 'self'; upgrade-insecure-requests"),
    ("mixed-content-block", "; manifest-src 'self'", "; manifest-src 'self'; block-all-mixed-content"),
    ("https-scheme-source", "; object-src 'none'", " https:; object-src 'none'"),
    ("https-host-source", "img-src 'self' data: blob:", "img-src 'self' data: blob: https://cdn.example.com"),
]


@pytest.mark.parametrize(("mutation", "old", "new"), _HTTP_MUTATIONS, ids=[m[0] for m in _HTTP_MUTATIONS])
def test_the_detector_sees_a_csp_that_breaks_plain_http(mutation: str, old: str, new: str) -> None:
    # Mutation precondition: the literal it replaces must be present verbatim.
    assert old in _IMAGE, f"mutation {mutation} no longer applies — update it"
    assert _plain_http_findings(_IMAGE.replace(old, new, 1), "mutated") != []
