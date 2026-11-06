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
ERROR_TOO_MANY_COLUMNS = "csv.too_many_columns"

#: The leading run :func:`neutralise` drops: formula characters (``\t`` and ``\r`` are among ``\s``) and the
#: whitespace between them. A character class with one quantifier: no backtracking.
_LEADING_FORMULA = re.compile(r"[=+\-@\s]+")

#: A plain unsigned decimal: digits, optionally one decimal mark (``,`` or ``.``) and more digits.
_DECIMAL = re.compile(r"^(?P<whole>\d{1,7})(?:[.,](?P<fraction>\d{1,6}))?$")

#: The longest cell the reader keeps. A longer one is not a value of any column an import knows; the importing
#: service refuses it with its own length rule, and the reader does not carry megabytes through the report.
MAX_CELL_CHARS = 4000
#: The widest header the reader accepts (trailing empty cells not counted). A bed list has seven columns; a file
#: of hundreds is no bed list, and every cell of a row would otherwise be carried through the report.
MAX_COLUMNS = 100


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


def _trimmed(cells: tuple[str, ...]) -> tuple[str, ...]:
    """``cells`` without the empty cells at the end (a spreadsheet's ``Name;Typ;;;``)."""
    end = len(cells)
    while end and not cells[end - 1].strip():
        end -= 1
    return cells[:end]


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

    The header ends at its last non-empty cell and may hold at most :data:`MAX_COLUMNS` (``csv.too_many_columns``);
    a data row keeps the cells under the header only. ``max_records`` stops the read one record past the bound:
    the caller reports "too many" without the reader walking whatever else the file holds. Refuses an empty file
    (``csv.empty``), a header without ``;`` (``csv.invalid_delimiter``) and a file the CSV module cannot read
    (``csv.malformed``: a NUL byte, an unclosed quote at the end).
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
                header = _trimmed(cells)
                if len(header) > MAX_COLUMNS:
                    raise CsvReadError(ERROR_TOO_MANY_COLUMNS, f"The header holds more than {MAX_COLUMNS} columns.")
                if len(header) < 2:  # noqa: PLR2004 - one column = the delimiter was not ``;``
                    raise CsvReadError(ERROR_INVALID_DELIMITER, "The columns must be separated by a semicolon (;).")
                continue
            # A cell right of the last header column belongs to no column: it is not kept.
            records += (CsvRecord(line=reader.line_num, cells=cells[: len(header)]),)
            if max_records is not None and len(records) > max_records:
                break
    except csv.Error as exc:
        raise CsvReadError(ERROR_MALFORMED, "The file is not a readable CSV file.") from exc
    if header is None:
        raise CsvReadError(ERROR_EMPTY, "The file holds no header row.")
    return CsvTable(header=header, records=records)


def neutralise(value: str) -> tuple[str, bool]:
    """A text cell as an import stores it, and whether a formula prefix of SR-016 was removed - in one pass.

    Trimmed, then one ``'`` that :func:`csv_export.csv_text` put before a formula character dropped, then the whole
    leading run of formula characters and whitespace between them dropped. ``'=SUM(A1)`` (an exported, already
    neutralised cell) and ``=SUM(A1)`` both become ``SUM(A1)``; ``-- Beet`` becomes ``Beet``. A ``'`` that precedes
    no formula character is part of the value (``'s Gartl``). Linear in the cell's length, whatever the prefix chain
    (a cell of 4 000 ``=`` costs what a cell of 4 000 letters costs).
    """
    text: str = value.strip()
    body = text[1:] if text.startswith("'") and text[1:].startswith(FORMULA_PREFIXES) else text
    if body.startswith(FORMULA_PREFIXES):
        match = _LEADING_FORMULA.match(body)
        body = body[match.end() :] if match is not None else body
    return body, body != text


def neutralised_text(value: str) -> str:
    """:func:`neutralise` without the flag."""
    return neutralise(value)[0]


def had_formula_prefix(value: str) -> bool:
    """Whether :func:`neutralise` removed a formula prefix (and not just whitespace)."""
    return neutralise(value)[1]


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
