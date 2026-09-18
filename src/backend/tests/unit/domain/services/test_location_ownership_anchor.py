"""The shared Location/Slot ownership anchor, and that it has no private copies left (#1397).

``Location`` and ``Slot`` carry a ``tenant_key`` the write path never fills:
``LocationCreate`` may not declare one (``check_tenant_body_field``, #1000) and
``create_location`` does ``Location(**body.model_dump())``. Nine sites read that
empty field as if it meant something, failing in three directions — five refusing
the tenant's own data, two holding a condition that can never be true, one
projection answering ``null`` where a name belongs.

Two things are asserted here, and the second is the one that matters in a year:

1. The anchor answers correctly in both directions, with a control against the
   over-rejecting failure that made the whole class invisible (#706, #1352) — a
   guard that refuses everything passes every negative test ever written for it.
2. No module resolves ownership against ``location.tenant_key`` or
   ``slot.tenant_key`` again. That is a source sweep, not a behaviour test,
   because the failure mode is a *new* call site rather than a changed one.
"""

import ast
import pathlib
import re
from collections.abc import Callable

import pytest

from app.common.exceptions import NotFoundError
from app.domain.models.site import Location, Site, Slot
from app.domain.services.location_ownership import (
    find_owned_location,
    require_owned_site,
    resolve_owned_location,
    resolve_owned_slot,
)

TENANT = "tenant_own"
OTHER = "tenant_other"


class FakeSiteSource:
    """Sites, locations and slots shaped the way the application stores them.

    Locations and slots are built **without** a ``tenant_key`` on purpose: a
    double that invents one lets an ownership check written against that field
    pass, which is exactly how nine broken sites stayed green. Name an input this
    accepts and the real repository would not, and the double is wrong — there is
    none, because the rows here are the rows ``create_location`` writes.
    """

    def __init__(self) -> None:
        self.sites = {
            "site_own": Site(_key="site_own", tenant_key=TENANT, name="Zuhause", type="indoor"),
            "site_other": Site(_key="site_other", tenant_key=OTHER, name="Woanders", type="indoor"),
        }
        self.locations = {
            "loc_own": Location(_key="loc_own", name="Beet A", area_m2=1.0, site_key="site_own"),
            "loc_other": Location(_key="loc_other", name="Beet B", area_m2=1.0, site_key="site_other"),
            "loc_orphan": Location(_key="loc_orphan", name="Beet C", area_m2=1.0, site_key=""),
        }
        self.slots = {
            "slot_own": Slot(_key="slot_own", location_key="loc_own", slot_id="LOCOWN_A1"),
            "slot_other": Slot(_key="slot_other", location_key="loc_other", slot_id="LOCOTHER_B1"),
        }

    def get_site_by_key(self, key):
        return self.sites.get(key)

    def get_location_by_key(self, key):
        return self.locations.get(key)

    def get_slot_by_key(self, key):
        return self.slots.get(key)


@pytest.fixture
def source() -> FakeSiteSource:
    return FakeSiteSource()


class TestResolveOwnedLocation:
    def test_the_tenants_own_location_is_found(self, source):
        """The control, and the case that was red before #1397.

        Without this assertion the three refusals below are satisfied by a guard
        that refuses *everything* — which is what five sites actually did.
        """
        assert resolve_owned_location(source, "loc_own", TENANT).key == "loc_own"

    def test_a_foreign_location_is_refused(self, source):
        with pytest.raises(NotFoundError):
            resolve_owned_location(source, "loc_other", TENANT)

    def test_an_absent_location_is_refused(self, source):
        with pytest.raises(NotFoundError):
            resolve_owned_location(source, "loc_missing", TENANT)

    def test_a_location_without_a_site_is_refused(self, source):
        """There is nothing to anchor against, so the answer is no, not yes."""
        with pytest.raises(NotFoundError):
            resolve_owned_location(source, "loc_orphan", TENANT)

    def test_absent_and_foreign_answer_identically(self, source):
        """Otherwise the message is the existence oracle the 404 exists to prevent."""
        with pytest.raises(NotFoundError) as absent:
            resolve_owned_location(source, "loc_missing", TENANT)
        with pytest.raises(NotFoundError) as foreign:
            resolve_owned_location(source, "loc_other", TENANT)
        assert str(absent.value).replace("loc_missing", "X") == str(foreign.value).replace("loc_other", "X")

    def test_the_refusal_never_names_the_site(self, source):
        """A message naming ``site_other`` would disclose the site behind the wall."""
        with pytest.raises(NotFoundError) as exc:
            resolve_owned_location(source, "loc_other", TENANT)
        assert "site_other" not in str(exc.value)


class TestResolveOwnedSlot:
    def test_the_tenants_own_slot_is_found_with_its_location(self, source):
        slot, location = resolve_owned_slot(source, "slot_own", TENANT)
        assert slot.key == "slot_own"
        assert location.key == "loc_own"

    def test_a_slot_in_a_foreign_location_is_refused(self, source):
        with pytest.raises(NotFoundError):
            resolve_owned_slot(source, "slot_other", TENANT)

    def test_an_absent_slot_is_refused(self, source):
        with pytest.raises(NotFoundError):
            resolve_owned_slot(source, "slot_missing", TENANT)

    def test_a_refused_slot_is_named_as_a_slot_not_as_its_location(self, source):
        """A slot whose location is foreign must not disclose that location's key."""
        with pytest.raises(NotFoundError) as exc:
            resolve_owned_slot(source, "slot_other", TENANT)
        assert "loc_other" not in str(exc.value)


class TestRequireOwnedSite:
    def test_own_site_passes_and_returns_it(self, source):
        assert require_owned_site(source, "site_own", TENANT, "Location", "loc_own").key == "site_own"

    def test_foreign_site_refuses_under_the_callers_entity_name(self, source):
        with pytest.raises(NotFoundError) as exc:
            require_owned_site(source, "site_other", TENANT, "Location", "loc_x")
        assert "Location" in str(exc.value)
        assert "loc_x" in str(exc.value)

    def test_an_empty_site_key_refuses(self, source):
        with pytest.raises(NotFoundError):
            require_owned_site(source, "", TENANT, "Location", "loc_orphan")


class TestFindOwnedLocation:
    """The non-raising reader, for the label and the system-task filter."""

    def test_true_for_the_tenants_own(self, source):
        assert find_owned_location(source, "loc_own", TENANT) is not None

    @pytest.mark.parametrize("key", ["loc_other", "loc_missing", "loc_orphan"])
    def test_false_for_foreign_absent_and_site_less(self, source, key):
        assert find_owned_location(source, key, TENANT) is None


# ── The sweep ────────────────────────────────────────────────────────────────

_APP_ROOT = pathlib.Path(__file__).resolve().parents[4] / "app"

#: Files allowed to read the field, each with *why* and with the predicate that
#: says when that reason stops holding. One structure rather than two parallel
#: dicts: an entry added to only one of them used to kill
#: :func:`test_every_allowlisted_file_still_contains_what_it_excuses` with a bare
#: ``KeyError`` instead of the message it was written to give.
#:
#: One entry, since this PR retired the repository's. The comment above said "two
#: places" for one commit after that.
_ALLOWED: dict[str, tuple[str, Callable[[pathlib.Path], bool]]] = {
    "domain/models/site.py": (
        "declares the field; the model is where it lives",
        lambda p: "tenant_key: str" in p.read_text(),
    ),
}


#: Any ``<identifier>.tenant_key`` in AQL. Which of them is an offence is decided
#: by :func:`_holds_location_or_slot` below, not by the pattern.
#:
#: Deliberately **not** a list of three literal names, which was the first version
#: and had three blind spots, each verified:
#:
#: * ``slot_location.tenant_key`` — an alias *this rule's own repair* introduces,
#:   holding a ``Location``. ``_`` is a word character, so ``\b`` failed before the
#:   embedded ``location`` and the read went unseen.
#: * ``LET t = location.tenant_key`` — a bare read. The Python branch of this sweep
#:   flags one; the AQL branch did not, because it demanded a comparison operator
#:   immediately after.
#: * ``l.tenant_key`` — any alias outside the three literal names.
#:
#: A name list that cannot name the aliases in the file it guards is the same shape
#: of hole as the one this sweep exists to close.
_AQL_TENANT_KEY_READ = re.compile(r"\b([A-Za-z_][A-Za-z0-9_]*)\.tenant_key\b")

#: An alias bound to a locations or slots collection, in either spelling AQL offers.
#:
#: Name heuristics stop at ``l``: a one-letter alias is in no list of plausible
#: names, and :func:`_holds_location_or_slot` correctly answers "no" for it.
#: Reading what the query binds the alias to closes that for names nobody has
#: thought of yet.
#:
#: **Both forms, because the first version only had the one this repository does
#: not use.** It matched ``FOR <alias> IN @@<col>`` alone — and ``app/`` contains no
#: such loop over locations or slots at all; every binding is
#: ``LET <alias> = … DOCUMENT(@<col>, …)``, usually inside a ternary. Review
#: measured it: the #1397 defect rewritten as
#: ``LET l = DOCUMENT(@location_col, …)`` … ``l.tenant_key == @tenant_key`` left
#: this module entirely green, while the docstring above claimed the mechanism
#: "closes that by construction". A guard that cannot fire against the shape its
#: own subject is written in — the failure this sweep exists to catch, one level up.
_AQL_COLLECTION_BINDINGS = (
    re.compile(r"\bFOR\s+([A-Za-z_][A-Za-z0-9_]*)\s+IN\s+@@?([A-Za-z_][A-Za-z0-9_]*)", re.IGNORECASE),
    # ``[^\n]*?`` spans the ternary condition that sits between ``=`` and the call.
    re.compile(
        r"\bLET\s+([A-Za-z_][A-Za-z0-9_]*)\s*=[^\n]*?\bDOCUMENT\(\s*@@?([A-Za-z_][A-Za-z0-9_]*)",
        re.IGNORECASE,
    ),
)


#: A string constant is scanned only if it reads like a query.
#:
#: Without this the sweep reads *every* string in ``app/``, so
#: ``logger.info("refusing: location.tenant_key mismatch")`` is reported as an
#: offence — the trap the docstring exclusion was added for, one expression type
#: further along: prose about the rule read as a breach of it. A log line or error
#: message naming the forbidden spelling would turn the lane red over a defect that
#: is not there, and the quickest way to quiet that is to narrow the sweep back to
#: where it started.
_AQL_KEYWORD = re.compile(r"\b(FOR|LET|FILTER|RETURN|INSERT|UPDATE|REMOVE)\s", re.IGNORECASE)
#: ``(?<![A-Za-z0-9_])`` so an e-mail address is not a bind parameter: review
#: measured ``"contact support@kamerplanter.local"`` satisfying the old pattern,
#: which — paired with an ordinary English "for" — put prose back through the
#: gate that exists to keep it out.
_AQL_BIND_PARAMETER = re.compile(r"(?<![A-Za-z0-9_])@@?[A-Za-z_]")


def _looks_like_aql(text: str) -> bool:
    """Whether a string constant is a query rather than prose about one.

    **A keyword alone is not enough**, which is what the first version required:
    ``FOR``, ``RETURN`` and ``UPDATE`` are ordinary English words, so
    ``log.warning("no site found for location.tenant_key anchoring")`` was scanned
    and reported — precisely the false alarm this gate exists to prevent. The three
    probes in `_PROSE_NOT_SCANNED` happened to contain none of those words, so the
    table certified a protection that did not hold for the most natural phrasing;
    the probes now include both spellings that break it.

    A bind parameter as well. Every query in this repository binds something, and
    the offence being looked for compares against ``@tenant_key`` by definition, so
    requiring one costs no detection.
    """
    return bool(_AQL_KEYWORD.search(text) and _AQL_BIND_PARAMETER.search(text))


def _holds_location_or_slot(identifier: str) -> bool:
    """Whether an AQL alias plausibly holds a ``Location`` or ``Slot`` document.

    Decided on the name's components rather than on the whole string, so
    ``slot_location`` is caught and ``location_site`` is not. The trailing component
    says what the variable holds: ``location_site`` and ``slot_site`` name the
    **site** the anchor resolves to, which is exactly where the tenant does live, so
    reading ``tenant_key`` off them is the repair rather than the defect.
    """
    parts = identifier.lower().split("_")
    if parts[-1] == "site":
        return False
    return any(part in {"location", "loc", "slot"} for part in parts)


#: Names a local variable holding a ``Location`` or ``Slot`` plausibly goes by.
#: A name list rather than a type inference: the latter is the right answer and a
#: much larger one, and this list is checked by the two-direction falsification
#: below rather than trusted.
_LOCATION_LIKE = {"location", "loc", "slot"}
#: Kept as the seed of :func:`_holds_location_or_slot`, which is what both branches
#: of the sweep now ask. They did not always: the component check was introduced for
#: AQL only, so ``slot_location.tenant_key`` — the alias this very repair
#: introduces, and one `_AQL_PROBES` pins as an offence — was a violation inside a
#: query string and invisible in Python. One spelling, two answers, in one sweep.


def _ownership_reads(path: pathlib.Path) -> list[str]:
    """Reads of ``tenant_key`` on a name that looks like a location or slot.

    An AST walk rather than a grep: a grep matches the pattern inside a comment
    explaining that the pattern is wrong, and this repository has three such
    comments — one sweep already reported a fixed defect as open that way.

    **Two forms, because the first version of this only caught one.** It matched
    `ast.Attribute` and therefore missed `getattr(location, "tenant_key", "")`,
    which is what two live sites actually used — one fail-open
    (`nutrient_plan_service`, where ``"" in ("", tenant_key)`` made the guard
    unfireable) and one over-rejecting (`fertilizer_service`). Both were invisible
    to the sweep while its failure message claimed no module reads the field. The
    class is eleven sites, not the nine the first pass found.
    """
    tree = ast.parse(path.read_text())
    # Docstrings are prose, and in this repository the prose about this very rule
    # quotes the broken expression: three modules explain why
    # ``location.tenant_key`` must not be compared. Scanning them reported the
    # documentation of the fix as the defect — the comment-in-the-perfect-tense
    # trap named in this module's own docstring, walked into while extending the
    # sweep to AQL. Collected by identity rather than by position so a module,
    # class and function docstring are all excluded the same way.
    docstrings = {
        id(node.body[0].value)
        for node in ast.walk(tree)
        if isinstance(node, ast.Module | ast.ClassDef | ast.FunctionDef | ast.AsyncFunctionDef)
        and node.body
        and isinstance(node.body[0], ast.Expr)
        and isinstance(node.body[0].value, ast.Constant)
        and isinstance(node.body[0].value.value, str)
    }
    hits = []
    for node in ast.walk(tree):
        # `location.tenant_key`
        if isinstance(node, ast.Attribute) and node.attr == "tenant_key":
            target = node.value
            if isinstance(target, ast.Name) and _holds_location_or_slot(target.id):
                hits.append(f"{path.name}:{node.lineno} {ast.unparse(node)}")
            continue
        # `getattr(location, "tenant_key", …)` — the form the first pass missed.
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "getattr"
            and len(node.args) >= 2
            and isinstance(node.args[0], ast.Name)
            and _holds_location_or_slot(node.args[0].id)
            and isinstance(node.args[1], ast.Constant)
            and node.args[1].value == "tenant_key"
        ):
            hits.append(f"{path.name}:{node.lineno} {ast.unparse(node)}")
            continue
        # AQL in a string constant. Attribute analysis cannot see inside a query
        # string, which is why the C-group of #1397 — three label projections
        # comparing ``location.tenant_key == @tenant_key`` — sat behind an
        # allowlist entry instead of being caught here. Removing that entry alone
        # changed nothing: measured, the sweep stayed green with the old
        # projection restored. This form is what makes the exemption's removal
        # mean something.
        #
        # ``//`` comments are stripped first. Both repaired queries explain the
        # rule in a comment that names the old expression, and matching those
        # would report the documentation of the fix as the defect — the
        # comment-in-the-perfect-tense trap this module's own docstring warns about.
        if isinstance(node, ast.Constant) and isinstance(node.value, str) and id(node) not in docstrings:
            body = re.sub(r"//[^\n]*", "", node.value)
            if not _looks_like_aql(body):
                continue
            # Aliases this query itself binds to a locations/slots collection count
            # as location-like however they are spelled, so neither a one-letter
            # `FOR l IN @@location_col` nor a `LET l = DOCUMENT(@location_col, …)`
            # is a way out of the rule.
            bound = {
                alias
                for pattern in _AQL_COLLECTION_BINDINGS
                for alias, collection in pattern.findall(body)
                if _holds_location_or_slot(collection)
            }
            for match in _AQL_TENANT_KEY_READ.finditer(body):
                alias = match.group(1)
                if _holds_location_or_slot(alias) or alias in bound:
                    hits.append(f"{path.name}:{node.lineno} (AQL) {match.group(0)}")
    return hits


def test_no_module_decides_ownership_from_location_or_slot_tenant_key():
    """The sweep: a new site reading the empty field fails here rather than in production.

    This is the half that survives. The behaviour tests above prove the anchor is
    right today; this one is what stops a tenth site from being written, which is
    how the first nine appeared — each individually reasonable, none aware of the
    others.
    """
    offenders: list[str] = []
    for path in sorted(_APP_ROOT.rglob("*.py")):
        relative = path.relative_to(_APP_ROOT).as_posix()
        if relative in _ALLOWED:
            continue
        offenders.extend(_ownership_reads(path))

    assert not offenders, (
        "These read Location.tenant_key / Slot.tenant_key, which the write path never fills "
        "(#1397). Use app.domain.services.location_ownership instead:\n  " + "\n  ".join(offenders)
    )


@pytest.mark.parametrize("relative", sorted(_ALLOWED))
def test_every_allowlisted_file_still_contains_what_it_excuses(relative: str):
    """An obsolete exemption fails, the way check_layer_imports already does.

    Without this the allowlist silently grows into a list of files nobody may
    check — the shape that lets the next drift in.
    """
    path = _APP_ROOT / relative
    reason, still_applies = _ALLOWED[relative]
    assert path.exists(), f"{relative} is allowlisted but does not exist: {reason}"
    assert still_applies(path), f"{relative} no longer contains what its entry excuses; drop it ({reason})"


#: Every AQL spelling the sweep must see, and every one it must leave alone.
#:
#: A table rather than prose, because the AQL branch shipped with three blind spots
#: that all looked covered: the first version matched three literal names followed
#: by a comparison operator, and review found it could not see ``slot_location``
#: (an alias the repair itself introduces, holding a ``Location``), a bare
#: ``LET t = location.tenant_key``, or any alias the query binds itself.
_AQL_PROBES: list[tuple[str, bool, str]] = [
    ("FOR p IN @@col FILTER location.tenant_key == @tenant_key RETURN p", True, "the plain form"),
    ("FOR p IN @@col FILTER slot.tenant_key != @tenant_key RETURN p", True, "the slot form"),
    (
        "FOR p IN @@col FILTER slot_location.tenant_key == @tenant_key RETURN p",
        True,
        "an alias holding a Location, spelled with an underscore — the blind spot the "
        "repair's own `slot_location` variable would have walked into",
    ),
    ("FOR p IN @@col LET t = location.tenant_key RETURN t", True, "a bare read, no comparison operator"),
    (
        "FOR l IN @@location_col FILTER l.tenant_key == @tenant_key",
        True,
        "an alias no name list can guess, bound to the locations collection",
    ),
    (
        "FOR s IN @@slot_col FILTER s.tenant_key != @tenant_key",
        True,
        "the same, over slots",
    ),
    (
        "LET l = DOCUMENT(@location_col, p.location_key) FILTER l.tenant_key == @tenant_key",
        True,
        "the binding form this repository actually uses — review measured the sweep green "
        "against exactly this while its docstring claimed the mechanism closed it",
    ),
    (
        "LET l = p.location_key != null ? DOCUMENT(@location_col, p.location_key) : null "
        "RETURN l.tenant_key == @tenant_key",
        True,
        "the same, inside the ternary every real query wraps it in",
    ),
    (
        "LET s = DOCUMENT(@site_col, location.site_key) FILTER s.tenant_key == @tenant_key",
        False,
        "an alias bound to the sites collection: that is the anchor, not the defect",
    ),
    (
        "FOR p IN @@col FILTER location_site.tenant_key == @tenant_key RETURN p",
        False,
        "the repair: the site the anchor resolves to is where the tenant does live",
    ),
    ("FOR p IN @@col FILTER slot_site.tenant_key == @tenant_key RETURN p", False, "the same, for a slot's site"),
    (
        "FOR p IN @@col FILTER p.tenant_key == @tenant_key",
        False,
        "an ordinary tenant-scoped filter on a collection that does carry the key",
    ),
    (
        "FOR x IN @@site_col FILTER x.tenant_key == @tenant_key",
        False,
        "a site alias bound to the sites collection",
    ),
]


@pytest.mark.parametrize(("aql", "is_offence", "why"), _AQL_PROBES)
def test_the_aql_branch_sees_what_it_claims_to(aql: str, is_offence: bool, why: str, tmp_path: pathlib.Path):
    """Both directions, per spelling, **through the real function**.

    Driven over a module written to disk instead of re-implementing the detection
    here. The first version transcribed the body, and a transcription certifies
    itself: review deleted the whole AQL branch of :func:`_ownership_reads` and
    every test in this file stayed green, this one included. The mechanism built to
    make the allowlist removal enforcement rather than bookkeeping was the one thing
    nothing checked.

    Going through :func:`_ownership_reads` also puts each row through
    :func:`_looks_like_aql`, which is why the rows are whole queries: as bare
    fragments four of them could never have reached the sweep, so the table was
    green about spellings it never tested.

    Both directions matter. A sweep widened until it flags ``location_site`` reports
    the repair as the defect, and the quickest way to silence that is to narrow it
    straight back to where it started.
    """
    module = tmp_path / "probe.py"
    module.write_text(f'QUERY = """{aql}"""\n')

    flagged = _ownership_reads(module)

    assert bool(flagged) is is_offence, f"{aql!r} should {'be flagged' if is_offence else 'be left alone'} — {why}"


#: Strings that name the forbidden spelling without being a query.
#:
#: The sweep reads string constants, and the first version read *every* one of
#: them: a log line or error message quoting ``location.tenant_key`` was reported
#: as an offence — prose about the rule read as a breach of it, the same trap the
#: docstring exclusion was added for, one expression type further along. A lane
#: turning red over a defect that is not there invites narrowing the sweep back to
#: where it started.
_PROSE_NOT_SCANNED = [
    "refusing: location.tenant_key mismatch",
    "the old guard compared location.tenant_key == tenant_key",
    "slot.tenant_key is persisted empty; use the site anchor",
    # The two that broke the keyword-only gate. `FOR`, `RETURN` and `UPDATE` are
    # ordinary English words, and the three probes above avoided all of them by
    # chance — so the table certified a protection that did not hold for the most
    # natural way to phrase either message.
    "no site found for location.tenant_key anchoring; key=%s",
    "we return null when location.tenant_key is empty",
    # And the two that broke the keyword+bind-parameter gate: an ``@`` inside a word
    # is an e-mail address, not a bind parameter, and paired with an ordinary
    # English "for" it put prose straight back through.
    "no site found for location.tenant_key; contact support@kamerplanter.local",
    "e-mail admin@example.com if location.tenant_key stays empty for this record",
]


@pytest.mark.parametrize("text", _PROSE_NOT_SCANNED)
def test_prose_naming_the_forbidden_spelling_is_not_a_query(text: str):
    assert not _looks_like_aql(text), (
        f"{text!r} would be scanned as AQL, so a log or error message naming the rule would be reported as breaking it"
    )


def test_a_real_query_is_still_scanned():
    """The control: a filter narrow enough to exclude prose must not exclude AQL.

    Without this, tightening `_LOOKS_LIKE_AQL` until nothing is scanned would pass
    every test above and disable the sweep's whole AQL branch.
    """
    assert _looks_like_aql("FOR p IN @@col FILTER p.tenant_key == @tenant_key RETURN p")
    assert _looks_like_aql("LET location = DOCUMENT(@location_col, p.location_key)")
