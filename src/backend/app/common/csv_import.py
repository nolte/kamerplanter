"""The reading half of the CSV rules (REQ-053 GP-FR-174, SR-016; WP 8.26, #2669) - the twin of :mod:`csv_export`.

A CSV file that comes in is untrusted input: it was saved by a spreadsheet, edited by hand, or built to reach what the
caller must not. The rules, in one place so every CSV import holds the same line:

* **Encoding.** UTF-8 only; one leading byte order mark (what Excel writes and :func:`csv_export.encode_csv` writes)
  is dropped. Bytes that are no UTF-8 refuse the whole file (``csv.invalid_encoding``) - a guessed code page would
  turn an umlaut into a different name without anybody noticing.
* **Delimiter.** ``;`` (the German Excel variant). A header row without a ``;`` is a file saved with another delimiter
  and is refused (``csv.invalid_delimiter``) instead of read as one wide column. RFC 4180 quoting is understood.
* **Formula prefixes are discarded on read (SR-016).** A *text* cell loses one ``'`` that :func:`csv_export.csv_text`
  put before a formula character, and then every leading ``=``, ``+``, ``-``, ``@``, tab and carriage return: what
  is stored can never be read as a formula again by the next spreadsheet that exports it (:func:`neutralised_text`).
* **Numbers** accept a decimal comma **and** a decimal point (``2,5`` and ``2.5``) - German Excel writes the first,
  every other tool the second. A thousands separator is refused rather than guessed (``1.250,5`` and ``1,250.5`` are
  the same digits read two ways), and so is anything that is not a plain unsigned decimal (:func:`parse_decimal`).

The reader decides nothing about the domain: it hands back rows of strings with their line numbers; the importing
service maps them.
"""

from __future__ import annotations

import csv
import io
import re
from dataclasses import dataclass

from app.common.csv_export import BOM, FORMULA_PREFIXES

#: The delimiter every CSV import reads (GP-FR-174: "Semikolon (deutsches Excel)").
IMPORT_DELIMITER = ";"

ERROR_INVALID_ENCODING = "csv.invalid_encoding"
ERROR_INVALID_DELIMITER = "csv.invalid_delimiter"
ERROR_EMPTY = "csv.empty"
ERROR_MALFORMED = "csv.malformed"

#: A plain unsigned decimal: digits, optionally one decimal mark (``,`` or ``.``) and more digits.
_DECIMAL = re.compile(r"^(?P<whole>\d{1,7})(?:[.,](?P<fraction>\d{1,6}))?$")

#: The longest cell the reader keeps. A longer one is not a value of any column an import knows; the importing
#: service refuses it with its own length rule, and the reader does not carry megabytes through the report.
MAX_CELL_CHARS = 4000


class CsvReadError(ValueError):
    """The file cannot be read as CSV at all; ``code`` is the published code the importing service raises with."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


@dataclass(frozen=True)
class CsvRecord:
    """One data row: the line it ends on (the header is line 1) and its cells, unmodified."""

    line: int
    cells: tuple[str, ...]


@dataclass(frozen=True)
class CsvTable:
    header: tuple[str, ...]
    records: tuple[CsvRecord, ...]


def _blank(cells: tuple[str, ...]) -> bool:
    """A row of empty or whitespace-only cells (a spreadsheet's trailing ``;;;`` line)."""
    joined: str = "".join(cells)
    return not joined.strip()


def decode_csv(raw: bytes) -> str:
    """The text of the file: strict UTF-8, one leading BOM dropped. ``csv.invalid_encoding`` otherwise."""
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise CsvReadError(ERROR_INVALID_ENCODING, "The file is not UTF-8 encoded.") from exc
    return text.removeprefix(BOM)


def read_table(text: str, *, max_records: int | None = None) -> CsvTable:
    """Header and data rows of a ``;``-delimited file. Rows that hold only empty cells are skipped.

    ``max_records`` stops the read one record past the bound: the caller reports "too many" without the reader
    walking whatever else the file holds. Refuses an empty file (``csv.empty``), a header without ``;``
    (``csv.invalid_delimiter``) and a file the CSV module cannot read (``csv.malformed``: a NUL byte, an unclosed
    quote at the end).
    """
    reader = csv.reader(io.StringIO(text, newline=""), delimiter=IMPORT_DELIMITER, strict=True)
    header: tuple[str, ...] | None = None
    records: tuple[CsvRecord, ...] = ()
    try:
        for row in reader:
            cells: tuple[str, ...] = tuple(cell[:MAX_CELL_CHARS] for cell in row)
            if _blank(cells):
                continue
            if header is None:
                if len(cells) < 2:  # noqa: PLR2004 - one column = the delimiter was not ``;``
                    raise CsvReadError(ERROR_INVALID_DELIMITER, "The columns must be separated by a semicolon (;).")
                header = cells
                continue
            records += (CsvRecord(line=reader.line_num, cells=cells),)
            if max_records is not None and len(records) > max_records:
                break
    except csv.Error as exc:
        raise CsvReadError(ERROR_MALFORMED, "The file is not a readable CSV file.") from exc
    if header is None:
        raise CsvReadError(ERROR_EMPTY, "The file holds no header row.")
    return CsvTable(header=header, records=records)


def neutralised_text(value: str) -> str:
    """A text cell as an import stores it: trimmed, the formula prefixes of SR-016 gone.

    ``'=SUM(A1)`` (an exported, already neutralised cell) and ``=SUM(A1)`` both become ``SUM(A1)``; ``-- Beet``
    becomes ``Beet``. A ``'`` that precedes no formula character is part of the value (``'s Gartl``).
    """
    text: str = value.strip()
    if text.startswith("'") and text[1:].startswith(FORMULA_PREFIXES):
        text = text[1:]
    while text.startswith(FORMULA_PREFIXES):
        text = text[1:].strip()
    return text


def had_formula_prefix(value: str) -> bool:
    """Whether :func:`neutralised_text` removed a formula prefix (and not just whitespace)."""
    stripped = value.strip()
    return bool(stripped) and neutralised_text(value) != stripped


def parse_decimal(value: str) -> float:
    """An unsigned decimal with a ``,`` or a ``.`` as decimal mark; ``ValueError`` for anything else.

    No sign, no exponent, no thousands separator, no unit: ``2,5`` and ``2.5`` are 2.5; ``-2``, ``1e3``,
    ``1.250,5``, ``2,5 m`` and ``=2`` are refused.
    """
    match = _DECIMAL.fullmatch(value.strip())
    if match is None:
        raise ValueError("Not an unsigned decimal number.")
    fraction = match.group("fraction")
    return float(f"{match.group('whole')}.{fraction}" if fraction else match.group("whole"))


def header_key(value: str) -> str:
    """A header cell reduced for matching: neutralised, case-folded, umlauts spelled out, separators unified.

    ``Länge_m``, ``Laenge_m``, ``LÄNGE M`` and ``länge-m`` all read ``laenge_m``.
    """
    text: str = neutralised_text(value).casefold()
    for umlaut, spelled in (("ä", "ae"), ("ö", "oe"), ("ü", "ue"), ("ß", "ss")):
        text = text.replace(umlaut, spelled)
    return re.sub(r"[\s\-_()\[\]]+", "_", text).strip("_")


def label_key(value: str) -> str:
    """A value cell reduced for matching against a label or an enum value (``Volle Sonne`` = ``volle_sonne``)."""
    return header_key(value)
