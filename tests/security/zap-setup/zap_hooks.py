"""ZAP hook — loads the Kamerplanter scan scripts into the running ZAP.

Spec: spec/nfr/NFR-015_OWASP-ZAP-Security-Scanning.md §3.2, §3.3

The packaged scans (`zap-full-scan.py` and friends) expose no command-line way to
register a script, so `--hook=/zap/wrk/zap_hooks.py` is the documented path: ZAP
imports this module and calls the hook functions below with a live API client.

Two scripts are registered:

* ``jwt-httpsender.js`` — attaches the Bearer token to every outgoing request.
* ``cross-tenant-passive.js`` — raises a High alert when a token for one tenant
  gets a 2xx from another tenant's URL space.

Both failures are made loud on purpose. A scan that runs without the HttpSender
script silently scans the anonymous surface while reporting as authenticated, and
one that runs without the passive rule silently loses the cross-tenant check —
each is a scan that measures less than it claims (NFR-018 §1). So a script that
does not load raises, which fails the scan rather than quietly degrading it.
"""

import os

WRK = "/zap/wrk"
SCRIPTS = [
    ("kp-jwt-httpsender", "httpsender", f"{WRK}/jwt-httpsender.js"),
    ("kp-cross-tenant", "passive", f"{WRK}/cross-tenant-passive.js"),
]


def _require(result, what):
    if result != "OK":
        raise RuntimeError(f"ZAP refused to {what}: {result!r}")


def zap_started(zap, target):
    """Register the scripts and seed the globals the HttpSender script reads."""
    for name, script_type, path in SCRIPTS:
        if not os.path.exists(path):
            raise RuntimeError(f"{path} is missing — refusing to scan without {name}.")
        _require(
            zap.script.load(
                scriptname=name,
                scripttype=script_type,
                scriptengine="ECMAScript : Graal.js",
                filename=path,
            ),
            f"load {name}",
        )
        _require(zap.script.enable(scriptname=name), f"enable {name}")

    for var in ("KP_ZAP_TOKEN", "KP_ZAP_LOGIN_URL", "KP_ZAP_LOGIN_BODY"):
        value = os.environ.get(var, "")
        if var == "KP_ZAP_TOKEN" and not value:
            raise RuntimeError(
                "KP_ZAP_TOKEN is empty — the scan would run anonymously while "
                "reporting as authenticated."
            )
        _require(zap.script.set_global_var(varkey=var, varvalue=value), f"set {var}")

    loaded = [s["name"] for s in zap.script.list_scripts]
    for name, _, _ in SCRIPTS:
        if name not in loaded:
            raise RuntimeError(f"{name} is not in ZAP's script list after loading.")
    print(f"[zap_hooks] registered: {', '.join(n for n, _, _ in SCRIPTS)}")

    return zap, target
