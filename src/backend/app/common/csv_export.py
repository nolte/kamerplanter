"""One CSV writer for every export of the application (REQ-053 SR-016, GP-FR-104/145; WP 8.4, #2647).

The rules, in one place so the tenant archive (``timeseries/readings.csv``) and the care-log download hold the same
line:

* **Formula hardening (SR-016).** A *text* cell that starts with ``=``, ``+``, ``-``, ``@``, a tab or a carriage
  return is prefixed with ``'`` so a spreadsheet opening the file does not run it as a formula
  (:func:`csv_text`). A *number* is never prefixed (``-3.25`` stays a number): numbers go through
  :func:`csv_number`, never through the text rule. A reader strips one leading ``'`` before such a character.
* **Encoding.** :func:`encode_csv` writes UTF-8 **with a BOM** (Excel reads the encoding from it) and RFC 4180
  quoting (``"`` doubled, a cell with the delimiter, a quote or a line break quoted, ``CRLF`` line ends).
* **Delimiter.** ``,`` (default) or ``;`` (the Excel variant of locales that use the comma as decimal mark; the
  caller then also writes its numbers with :func:`csv_number`'s ``decimal=","``).
"""

from __future__ import annotations

import csv
import io
from collections.abc import Iterable, Sequence

#: The first characters a spreadsheet reads as the start of a formula (CSV injection).
FORMULA_PREFIXES: tuple[str, ...] = ("=", "+", "-", "@", "\t", "\r")

#: The byte order mark Excel needs to read the file as UTF-8.
BOM = "﻿"

#: The delimiters a download may use.
DELIMITERS: tuple[str, ...] = (",", ";")


def csv_text(value: str | None) -> str:
    """A text cell, neutralised: ``None`` and ``""`` are an empty cell, a formula-looking value gets a leading ``'``."""
    if not value:
        return ""
    return f"'{value}" if value.startswith(FORMULA_PREFIXES) else value


def csv_number(value: float | int | None, *, decimal: str = ".") -> str:
    """A number cell; ``None`` is an empty cell. Never prefixed, whatever its sign.

    ``decimal`` is the decimal mark: ``,`` for the Excel variant of locales with a decimal comma, where a ``2.5`` would
    be read as text or as a date.
    """
    if value is None:
        return ""
    text: str = str(value) if isinstance(value, int) else repr(value)
    if decimal == ".":
        return text
    whole, _, fraction = text.partition(".")
    return f"{whole}{decimal}{fraction}" if fraction else whole


def encode_csv(header: Sequence[str], rows: Iterable[Sequence[str]], *, delimiter: str = ",") -> bytes:
    """The whole file: BOM, the header row and every row, RFC 4180 quoted, ``CRLF`` line ends.

    Cells must already be neutralised (:func:`csv_text`); this function quotes, it does not interpret.
    """
    if delimiter not in DELIMITERS:
        raise ValueError(f"The delimiter must be one of {DELIMITERS!r}.")
    buffer = io.StringIO()
    out = csv.writer(buffer, delimiter=delimiter, lineterminator="\r\n", quoting=csv.QUOTE_MINIMAL)
    out.writerow(list(header))
    out.writerows(list(row) for row in rows)
    text: str = BOM + buffer.getvalue()
    return text.encode("utf-8")
