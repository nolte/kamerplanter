"""uvicorn's access log without the question text and without the full client IP (#1796 review GDPR-003).

``GET /search?q=<question>`` puts free text a person typed into the query
string, and uvicorn's default access log writes the full request target and
the full client address. This service cannot import the backend's
``app.common.log_privacy`` (separate image, separate package), so the small part
it needs lives here, self-contained: the query string becomes ``?<redacted>``
(the routes have no path parameters, so the path itself carries nothing), and
the client address is truncated the NFR-011 R-03 way (IPv4 /24, IPv6 /48,
port dropped).
"""

from __future__ import annotations

import ipaddress
import logging

_UVICORN_ACCESS_LOGGER = "uvicorn.access"
#: ``client_addr, method, path_with_query, http_version, status_code`` — what
#: uvicorn's HTTP protocols hand to ``uvicorn.access``.
_ACCESS_ARGS_LEN = 5


def loggable_client_addr(client_addr: object) -> str:
    """uvicorn's ``host:port`` reduced to the truncated host; ``0.0.0.0`` for anything unparsable."""
    text = str(client_addr or "")
    if not text:
        return text
    host, _sep, port = text.rpartition(":")
    if not host or not port.isdigit():
        host = text
    try:
        addr = ipaddress.ip_address(host)
    except ValueError:
        return "0.0.0.0"
    prefix = 24 if addr.version == 4 else 48
    return str(ipaddress.ip_network(f"{addr}/{prefix}", strict=False).network_address)


class AccessLogRedactionFilter(logging.Filter):
    """Rewrites a ``uvicorn.access`` record's arguments before uvicorn's ``AccessFormatter`` renders them.

    A record of another shape is dropped rather than passed on unredacted.
    """

    def filter(self, record: logging.LogRecord) -> bool:
        args = record.args
        if not isinstance(args, tuple) or len(args) != _ACCESS_ARGS_LEN:
            return False
        client_addr, method, path, http_version, status_code = args
        target, has_query, _query = str(path).partition("?")
        record.args = (
            loggable_client_addr(client_addr),
            method,
            target + ("?<redacted>" if has_query else ""),
            http_version,
            status_code,
        )
        return True


_FILTER = AccessLogRedactionFilter()


def install_access_log_redaction() -> None:
    """Put the redacting filter on ``uvicorn.access``. Idempotent.

    Called when ``app.main`` is imported — uvicorn configures its loggers before
    it imports the application, and ``dictConfig`` never removes a logger's
    filters — and again from the lifespan.
    """
    logging.getLogger(_UVICORN_ACCESS_LOGGER).addFilter(_FILTER)
