"""Regression guard against f-string LIMIT interpolation (SEC-B5).

``LIMIT {offset}, {limit}`` built with an f-string is an injection-shaped
disciplin break even when the values are ``int``-typed today. All list queries
must bind offset/limit (``LIMIT @offset, @limit`` / ``LIMIT @__offset,
@__limit``). This cheap source scan fails if the pattern ever returns.
"""

import pathlib
import re

DATA_ACCESS_DIR = pathlib.Path(__file__).resolve().parents[3] / "app" / "data_access"
FSTRING_LIMIT = re.compile(r"LIMIT \{")


def test_no_fstring_limit_in_data_access():
    offenders: list[str] = []
    for path in DATA_ACCESS_DIR.rglob("*.py"):
        if FSTRING_LIMIT.search(path.read_text(encoding="utf-8")):
            offenders.append(str(path))

    assert not offenders, f"f-string LIMIT interpolation found (SEC-B5): {offenders}"
