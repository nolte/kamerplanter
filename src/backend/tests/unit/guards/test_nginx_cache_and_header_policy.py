"""The frontend nginx's cache headers and header policy cannot silently regress (#3025, M17).

``test_nginx_security_headers_parity.py`` holds the chart's header snippet equal to the image's and
every location on the snippet. This guard holds *what* the snippet and the locations say, in the
image's ``nginx.conf`` and in every enabled chart ``default.conf``:

* **index.html is revalidated** (W-25) — ``location /`` (the SPA fallback that serves index.html
  for every deep route) sends ``Cache-Control: no-cache``. Without it a browser keeps a
  heuristic-fresh index.html that names the previous build's hashed bundles after a deploy.
* **Only content-hashed files are immutable** (W-24) — a year-long ``immutable`` lives only in
  ``location ^~ /assets/`` (Vite's hashed output); the regex location for files with a stable name
  (``/icons/*.png``) is not cacheable for a year. No ``expires`` anywhere: next to an
  ``add_header Cache-Control`` it sent a second ``Cache-Control`` header (W-25).
* **Header policy** (W-22) — no ``X-XSS-Protection``; ``X-Frame-Options: DENY`` agrees with
  ``frame-ancestors 'none'``; ``object-src 'none'``, ``Permissions-Policy``, COOP and CORP present;
  ``script-src`` without ``'unsafe-inline'`` (``style-src`` keeps it, W-20, reason in the snippet).
* **The tracker origin reaches connect-src** (W-21) — ``connect-src`` is ``'self'`` plus the map
  variable and nothing else; every configuration defines the map and includes the runtime
  directory the entrypoint script writes; in the chart the init container runs that script into an
  emptyDir the nginx container mounts at that directory. Before #3025 the chart's pod never ran
  the script (suppressed ``/docker-entrypoint.d``, read-only ``conf.d``), so error tracking was
  CSP-blocked in every Kubernetes release.

**Not seen**: the headers an Ingress or CDN adds or strips, and the browser's reaction — the
``curl -I`` through a port-forward is the runtime check (docs/de/deployment/helm.md).
"""

from __future__ import annotations

import fnmatch
import re
import subprocess
from pathlib import Path

import pytest
import yaml

from tests.support.repo_scripts import load_repo_script
from tests.unit.guards.test_nginx_security_headers_parity import (
    HELM_DIR,
    IMAGE_CONF,
    IMAGE_SNIPPET,
    REPO_ROOT,
    SNIPPET_NAME,
    _headers,
    _helm_frontend_configmaps,
    _locations,
    _strip_comments,
)

SCRIPT = REPO_ROOT / "src/frontend/docker-entrypoint.d/30-error-tracking-csp.sh"
RUNTIME_DIR = "/etc/nginx/runtime"
VARIABLE = "kp_csp_connect_extra"
YEAR = 31536000

_source_text = load_repo_script("source_text")

_MAP = re.compile(r"\bmap\s+\$\S+\s+\$" + VARIABLE + r"\s*\{([^{}]*)\}")
_EXPIRES = re.compile(r"\bexpires\b")
_MAX_AGE = re.compile(r"max-age=(\d+)")


def _configs() -> dict[str, str]:
    """``{where: default.conf}`` — the image's and every enabled chart release's."""
    found = {"src/frontend/nginx.conf": IMAGE_CONF.read_text(encoding="utf-8")}
    for name, data in _helm_frontend_configmaps().items():
        found[f"helm:{name}"] = data["default.conf"]
    return found


def _snippets() -> dict[str, str]:
    found = {SNIPPET_NAME: IMAGE_SNIPPET.read_text(encoding="utf-8")}
    for name, data in _helm_frontend_configmaps().items():
        found[f"helm:{name}"] = data.get(SNIPPET_NAME, "")
    return found


def _cache_controls(body: str) -> list[str]:
    return [
        value
        for name, value in re.findall(r'\badd_header\s+([A-Za-z0-9-]+)\s+"([^"]*)"', _strip_comments(body))
        if name.lower() == "cache-control"
    ]


def _cache_findings(conf: str, where: str) -> list[str]:
    """THE cache detector over one default.conf."""
    findings: list[str] = []
    if _EXPIRES.search(_strip_comments(conf)):
        findings.append(f"{where}: `expires` — beside add_header Cache-Control it sends a second Cache-Control")
    by_match = dict(_locations(conf))
    for match, body in by_match.items():
        values = _cache_controls(body)
        if len(values) > 1:
            findings.append(f"{where}: `location {match}` sends {len(values)} Cache-Control headers")
        for value in values:
            long_lived = any(int(age) >= YEAR for age in _MAX_AGE.findall(value))
            if ("immutable" in value or long_lived) and match != "^~ /assets/":
                findings.append(f"{where}: `location {match}` caches for a year ({value!r}) without a content hash")
    spa = by_match.get("/")
    if spa is None:
        findings.append(f"{where}: no SPA fallback `location /`")
    elif not any("no-cache" in value or "no-store" in value for value in _cache_controls(spa)):
        findings.append(f"{where}: `location /` (index.html) is not revalidated — no Cache-Control: no-cache")
    assets = by_match.get("^~ /assets/")
    if assets is None:
        findings.append(f"{where}: no `location ^~ /assets/` for the hashed build output")
    elif "=404" not in assets:
        findings.append(f"{where}: a missing /assets/ file must be a 404, not index.html")
    return findings


def _policy_findings(snippet: str, where: str) -> list[str]:
    """THE header-policy detector over one snippet."""
    headers = {name: value for name, (value, _always) in _headers(snippet).items()}
    findings: list[str] = []
    if "x-xss-protection" in headers:
        findings.append(f"{where}: X-XSS-Protection is deprecated and a cross-site leak where it still works")
    for required in ("permissions-policy", "cross-origin-opener-policy", "cross-origin-resource-policy"):
        if required not in headers:
            findings.append(f"{where}: {required} missing")
    directives = {
        name: sources
        for name, *sources in (d.split() for d in headers.get("content-security-policy", "").split(";") if d.strip())
    }
    if directives.get("object-src") != ["'none'"]:
        findings.append(f"{where}: CSP object-src is {directives.get('object-src')!r}, not 'none'")
    if "'unsafe-inline'" in directives.get("script-src", []) or "'unsafe-eval'" in directives.get("script-src", []):
        findings.append(f"{where}: CSP script-src admits inline or eval script")
    if directives.get("connect-src") != ["'self'${" + VARIABLE + "}"]:
        findings.append(f"{where}: CSP connect-src is {directives.get('connect-src')!r}, not 'self' + the map variable")
    if directives.get("frame-ancestors") == ["'none'"] and headers.get("x-frame-options") != "DENY":
        findings.append(f"{where}: X-Frame-Options {headers.get('x-frame-options')!r} contradicts frame-ancestors")
    return findings


def _map_findings(conf: str, where: str) -> list[str]:
    stripped = _strip_comments(conf)
    match = _MAP.search(stripped)
    if match is None:
        return [f"{where}: no `map … ${VARIABLE}` — nginx refuses to start on the snippet's variable"]
    if f"include {RUNTIME_DIR}/*.conf;" not in " ".join(match.group(1).split()):
        return [f"{where}: the map does not include {RUNTIME_DIR}/*.conf, where the entrypoint script writes"]
    return []


# ── The real configuration passes. ──


def test_the_selector_finds_every_config() -> None:
    configs = _configs()
    assert "src/frontend/nginx.conf" in configs
    assert "helm:values.yaml" in configs, "the base chart's default.conf left the scan"


@pytest.mark.parametrize("where", sorted(_configs()))
def test_cache_headers(where: str) -> None:
    assert _cache_findings(_configs()[where], where) == []


@pytest.mark.parametrize("where", sorted(_snippets()))
def test_header_policy(where: str) -> None:
    assert _policy_findings(_snippets()[where], where) == []


@pytest.mark.parametrize("where", sorted(_configs()))
def test_every_config_defines_the_connect_src_variable(where: str) -> None:
    assert _map_findings(_configs()[where], where) == []


def test_the_script_writes_where_the_map_includes(tmp_path: Path) -> None:
    """Its default directory is the map's, and the file it writes matches the map's glob."""
    script = _source_text.executable_source(SCRIPT.read_text(encoding="utf-8"), language="shell")
    assert f'RUNTIME_DIR="${{KP_NGINX_RUNTIME_DIR:-{RUNTIME_DIR}}}"' in script

    subprocess.run(  # noqa: S603
        ["sh", str(SCRIPT)],  # noqa: S607
        env={"PATH": "/usr/bin:/bin", "KP_NGINX_RUNTIME_DIR": str(tmp_path), "SENTRY_DSN": "https://k@t.example/1"},
        check=True,
        capture_output=True,
    )
    written = [p.name for p in tmp_path.iterdir()]
    assert written, "the script wrote nothing for a valid DSN"
    assert all(fnmatch.fnmatch(name, "*.conf") for name in written), f"{written} escape the map's *.conf glob"


def test_the_dockerfile_gives_nginx_a_writable_runtime_dir() -> None:
    dockerfile = _source_text.executable_source(
        (REPO_ROOT / "src/frontend/Dockerfile").read_text(encoding="utf-8"), language="dockerfile"
    )
    assert f"mkdir -p {RUNTIME_DIR}" in dockerfile
    assert re.search(r"chown -R 101:101 [^\n]*" + re.escape(RUNTIME_DIR), dockerfile)


def test_the_chart_init_container_feeds_the_runtime_dir() -> None:
    """The pod's nginx never runs /docker-entrypoint.d; the init container must run the script."""
    values = yaml.safe_load((HELM_DIR / "values.yaml").read_text(encoding="utf-8"))
    init = values["controllers"]["frontend"]["initContainers"]["init-runtime-config"]
    args = "\n".join(init["args"])
    found = re.search(r"KP_NGINX_RUNTIME_DIR=(\S+) sh \"\$csp_script\"", args)
    assert found, "the init container no longer runs 30-error-tracking-csp.sh"
    assert "csp_script=/docker-entrypoint.d/30-error-tracking-csp.sh" in args
    assert "SENTRY_DSN" in init["env"], "the init container must see the DSN it derives the origin from"

    mounts = {
        name: entry["advancedMounts"]["frontend"]
        for name, entry in values["persistence"].items()
        if entry.get("type") == "emptyDir" and "frontend" in (entry.get("advancedMounts") or {})
    }
    feeding = [
        name
        for name, by_container in mounts.items()
        if any(m["path"] == found.group(1) for m in by_container.get("init-runtime-config", []))
        and any(m["path"] == RUNTIME_DIR and m.get("readOnly") is True for m in by_container.get("main", []))
    ]
    assert feeding, f"no emptyDir mounts the init container's {found.group(1)} read-only at {RUNTIME_DIR} in nginx"
    # Tracking is optional: a failing script must not hold the pod in Init:CrashLoopBackOff.
    assert re.search(r"sh \"\$csp_script\"\s*\\?\s*\|\|", args), (
        "the init container must not fail when the CSP script fails"
    )


# ── Red first, through the same detectors: a mutated copy of the real config is refused. ──

_IMAGE_CONF = IMAGE_CONF.read_text(encoding="utf-8") if IMAGE_CONF.is_file() else ""
_IMAGE_SNIPPET = IMAGE_SNIPPET.read_text(encoding="utf-8") if IMAGE_SNIPPET.is_file() else ""

_INC = "include /etc/nginx/conf.d/nginx-security-headers.inc;\n    }\n}"  # the last location's tail
_CACHE_MUTATIONS = [
    ("index-html-cached", '        add_header Cache-Control "no-cache";\n        include', "        include"),
    (
        "icons-immutable",
        'add_header Cache-Control "no-cache";\n        ' + _INC,
        'add_header Cache-Control "public, immutable";\n        ' + _INC,
    ),
    ("expires-back", "try_files $uri =404;", "try_files $uri =404;\n        expires 1y;"),
    ("assets-fallback-to-index", "try_files $uri =404;", "try_files $uri /index.html;"),
]


@pytest.mark.parametrize(("mutation", "old", "new"), _CACHE_MUTATIONS, ids=[m[0] for m in _CACHE_MUTATIONS])
def test_the_cache_detector_sees(mutation: str, old: str, new: str) -> None:
    # Mutation precondition: the literal it replaces must be present verbatim, else it is a no-op.
    assert old in _IMAGE_CONF, f"mutation {mutation} no longer applies — update it"
    assert _cache_findings(_IMAGE_CONF.replace(old, new, 1), "mutated") != []


_POLICY_MUTATIONS = [
    (
        "xss-back",
        'add_header X-Content-Type-Options "nosniff" always;',
        'add_header X-Content-Type-Options "nosniff" always;\nadd_header X-XSS-Protection "1; mode=block" always;',
    ),
    ("frame-sameorigin", 'X-Frame-Options "DENY"', 'X-Frame-Options "SAMEORIGIN"'),
    ("object-src-dropped", " object-src 'none';", ""),
    ("connect-wildcard", "connect-src 'self'${kp_csp_connect_extra};", "connect-src 'self' https:;"),
    ("script-inline", "script-src 'self';", "script-src 'self' 'unsafe-inline';"),
    ("coop-dropped", 'add_header Cross-Origin-Opener-Policy "same-origin" always;', ""),
]


@pytest.mark.parametrize(("mutation", "old", "new"), _POLICY_MUTATIONS, ids=[m[0] for m in _POLICY_MUTATIONS])
def test_the_policy_detector_sees(mutation: str, old: str, new: str) -> None:
    assert old in _IMAGE_SNIPPET, f"mutation {mutation} no longer applies — update it"
    assert _policy_findings(_IMAGE_SNIPPET.replace(old, new, 1), "mutated") != []


def test_the_map_detector_sees_a_missing_map() -> None:
    start = _IMAGE_CONF.index(f"map $host ${VARIABLE}")
    end = _IMAGE_CONF.index("}", start) + 1
    assert _map_findings(_IMAGE_CONF[:start] + _IMAGE_CONF[end:], "mutated") != []
