"""The frontend nginx access log stays redacted, and its two copies stay identical (#1795 review SEC-010).

#1795 replaced nginx's ``combined`` format — full request line, full client
address, user agent, referrer, ``X-Forwarded-For`` — by ``kp_redacted`` in both
places that configure the frontend's nginx: the image's ``src/frontend/nginx.conf``
and the ``frontend-nginx`` ConfigMap in ``helm/kamerplanter/values.yaml``, which
*replaces* the image's ``conf.d`` in a Helm install. Two hand-maintained copies
drift; a later edit that adds ``$http_user_agent`` for debugging, or reverts the
map to ``$uri``, would bring the leak back without any test noticing.

ONE detector, :func:`_findings`, runs over every enabled frontend-nginx config
and over the mutated copies of the self-test:

* every ``log_format`` may reference none of :data:`_FORBIDDEN_LOG_VARIABLES`
  (the request line, query, raw client address, user agent, referrer, forwarded
  chain, cookies, authorization) — ``$request_uri`` is legitimate only as the
  *input* of the path ``map``, never in a format;
* every ``access_log`` names ``kp_redacted`` (or is ``off``);
* the ``error_log`` level is ``crit`` (nginx's error-log format cannot be
  redacted and writes ``client:`` plus the request line).

:func:`_redaction_block` extracts the ``map`` blocks, the ``log_format`` and the
log directives, normalised per line; the two copies must be equal.

**Not seen**: a config file outside these two (the dev overlays disable the
ConfigMap and render no frontend — measured with ``helm template`` on #1795),
and an ``include`` pulling a format in from elsewhere.
"""

from __future__ import annotations

import pathlib
import re

import pytest
import yaml

REPO_ROOT = pathlib.Path(__file__).resolve().parents[5]
IMAGE_CONF = REPO_ROOT / "src/frontend/nginx.conf"
HELM_DIR = REPO_ROOT / "helm/kamerplanter"

_FORBIDDEN_LOG_VARIABLES = {
    "request",
    "request_uri",
    "request_body",
    "args",
    "query_string",
    "uri",
    "document_uri",
    "remote_addr",
    "binary_remote_addr",
    "realip_remote_addr",
    "proxy_add_x_forwarded_for",
    "http_user_agent",
    "http_referer",
    "http_x_forwarded_for",
    "http_x_real_ip",
    "http_authorization",
    "http_cookie",
}
_FORBIDDEN_PREFIXES = ("arg_", "cookie_", "sent_http_set_cookie")

_VARIABLE = re.compile(r"\$\{?([A-Za-z0-9_]+)")
_LOG_FORMAT = re.compile(r"^\s*log_format\s+(\S+)\s+(.*?);", re.MULTILINE | re.DOTALL)
_ACCESS_LOG = re.compile(r"^\s*access_log\s+([^;]+);", re.MULTILINE)
_ERROR_LOG = re.compile(r"^\s*error_log\s+([^;]+);", re.MULTILINE)
_MAP_BLOCK = re.compile(r"^\s*map\s+\S+\s+\S+\s*\{.*?^\s*\}", re.MULTILINE | re.DOTALL)
_LOG_NOT_FOUND = re.compile(r"^\s*log_not_found\s+[^;]+;", re.MULTILINE)


def _strip_comments(conf: str) -> str:
    return "\n".join(line.split("#", 1)[0] if not line.lstrip().startswith("#") else "" for line in conf.splitlines())


def _findings(conf: str, where: str) -> list[str]:
    """THE detector: every way *conf* could write a secret or personal datum into nginx's logs."""
    conf = _strip_comments(conf)
    findings: list[str] = []
    formats = _LOG_FORMAT.findall(conf)
    if not formats:
        findings.append(f"{where}: no log_format — nginx would fall back to 'combined'")
    for name, body in formats:
        for variable in _VARIABLE.findall(body):
            if variable in _FORBIDDEN_LOG_VARIABLES or variable.startswith(_FORBIDDEN_PREFIXES):
                findings.append(f"{where}: log_format {name} references ${variable}")
    access_logs = _ACCESS_LOG.findall(conf)
    if not access_logs:
        findings.append(f"{where}: no access_log — the inherited default uses 'combined'")
    for directive in access_logs:
        parts = directive.split()
        if parts != ["off"] and (len(parts) < 2 or parts[1] != "kp_redacted"):
            findings.append(f"{where}: access_log {directive!r} does not use kp_redacted")
    error_logs = _ERROR_LOG.findall(conf)
    if not error_logs:
        findings.append(f"{where}: no error_log — the inherited level writes client address and request line")
    for directive in error_logs:
        if directive.split()[-1] != "crit":
            findings.append(f"{where}: error_log {directive!r} is not at crit")
    return findings


def _redaction_block(conf: str) -> list[str]:
    """The map blocks, the log_format and the log directives of *conf*, normalised line by line."""
    conf = _strip_comments(conf)
    parts = [*_MAP_BLOCK.findall(conf), *(m.group(0) for m in _LOG_FORMAT.finditer(conf))]
    parts += _ACCESS_LOG.findall(conf) + _ERROR_LOG.findall(conf) + _LOG_NOT_FOUND.findall(conf)
    return [" ".join(line.split()) for part in parts for line in part.splitlines() if line.strip()]


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
    assert "values.yaml" in _helm_configs(), "the base chart's frontend-nginx ConfigMap left the scan"


@pytest.mark.parametrize("name", ["src/frontend/nginx.conf", *(f"helm:{n}" for n in _helm_configs())])
def test_every_frontend_nginx_config_logs_redacted(name: str) -> None:
    conf = IMAGE_CONF.read_text(encoding="utf-8") if name.startswith("src/") else _helm_configs()[name[5:]]
    assert _findings(conf, name) == []


def test_the_image_and_the_chart_carry_the_same_redaction() -> None:
    image = _redaction_block(IMAGE_CONF.read_text(encoding="utf-8"))
    for name, conf in _helm_configs().items():
        assert _redaction_block(conf) == image, f"{name} drifted from src/frontend/nginx.conf"
    assert len(image) > 10, "the extracted block is too small to mean anything"


_MUTATIONS = [
    ("user-agent", "$request_time';", "$request_time $http_user_agent';"),
    ("referrer", "$request_time';", '$request_time "$http_referer"\';'),
    ("xff", "$request_time';", "$request_time $http_x_forwarded_for';"),
    ("request-line", '"$request_method $kp_log_path"', '"$request"'),
    ("request-uri", '"$request_method $kp_log_path"', '"$request_method $request_uri"'),
    ("raw-client", "'$kp_log_client -", "'$remote_addr -"),
    ("args", "$request_time';", "$request_time $args';"),
    ("combined", "access_log /dev/stdout kp_redacted;", "access_log /dev/stdout combined;"),
    ("default-format", "access_log /dev/stdout kp_redacted;", "access_log /dev/stdout;"),
    ("error-level", "error_log /dev/stderr crit;", "error_log /dev/stderr warn;"),
]


@pytest.mark.parametrize(("mutation", "old", "new"), _MUTATIONS, ids=[m[0] for m in _MUTATIONS])
def test_the_detector_sees_each_regression(mutation: str, old: str, new: str) -> None:
    """Red first, through the same detector: a mutated copy of the real config is refused."""
    conf = IMAGE_CONF.read_text(encoding="utf-8")
    # prose-permeable: mutation precondition: the literal it replaces must be present verbatim, else the mutation
    # is a no-op and the red case proves nothing
    assert old in conf, f"mutation {mutation} no longer applies — update it"
    assert _findings(conf.replace(old, new, 1), "mutated") != []


def test_the_drift_check_sees_a_changed_map_line() -> None:
    conf = IMAGE_CONF.read_text(encoding="utf-8")
    drifted = conf.replace('"~^/api/"', '"~^/ap/"', 1)
    assert drifted != conf
    assert _redaction_block(drifted) != _redaction_block(conf)
