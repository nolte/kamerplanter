"""#1543 — the Nuclei template set is pinned by DIGEST, and Renovate can move it.

**The defect this is written against.** ``.github/renovate-pins.yaml`` used to
carry a pair: ``nuclei_templates_version`` (a tag, matched by the custom manager
in ``renovate.json5``) and ``nuclei_templates_commit`` (the commit that tag
pointed at when a human reviewed it, matched by nothing — it sat some thirty
lines of prose below the datasource comment, and the manager's regex requires the
key on the line immediately after it). Renovate could therefore only ever move
one half, and every bump shipped a pair whose halves disagreed: #1280 merged that
way and the nightly scan failed to start for two nights until #1312 recorded the
right commit; #1454 was caught before the merge. Three occurrences of one class.

**What is asserted here, and why textually.** The property is not "the two keys
exist" — that is what the old shape satisfied while being broken. It is that the
regex Renovate actually runs, taken out of ``renovate.json5`` itself, matches the
pins file exactly once for the template set and yields BOTH ``currentDigest`` and
``currentValue`` from it. That measures the wiring rather than describing it: a
renamed key, a reordered pair, a comment slipped between the two lines, or a
dropped capture group all redden here, offline, in the same expression Renovate
evaluates. The mirror-image half is asserted too — the version-only matchString
must NOT match the same block, because if it did the template set would be raised
as two dependencies and bumped by two pull requests.

``renovate.json5`` is read TEXTUALLY for the same reason
``test_uv_pin_manager_covers_every_pin.py`` gives: it is JSON5, and no JSON5
parser is in the backend's locked dependency set. Every step of the extraction is
asserted rather than trusted, so a silently empty extraction is red rather than
vacuously green.

**Residual, stated rather than implied.** Renovate evaluates these patterns with
RE2/JS semantics and Python's ``re`` is not byte-identical to either; the
constructs used here (character classes, ``\\s``, counted repetition, named
groups) are common to all three, and the group syntax is translated below. This
test therefore shows the pattern *can* extract both fields — the proof that
Renovate itself does so is the ``task renovate:dry-run`` excerpt in the pull
request. What this test adds over that dry-run is that the property is measured
on every run of the suite rather than when somebody remembers to ask Docker.

Traces to #1543 (no TC-ID: CI configuration is not a user-facing case).
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from tests.support.renovate_config import array_value, strip_comments
from tests.support.repo_scripts import find_repo_root

_REPO_ROOT = find_repo_root(Path(__file__).resolve())
if _REPO_ROOT is None:  # pragma: no cover — only outside a full checkout
    pytest.skip("checkout root not found", allow_module_level=True)

_CONFIG = _REPO_ROOT / "renovate.json5"
_PINS = _REPO_ROOT / ".github" / "renovate-pins.yaml"

#: The manager block is located by the file pattern that is unique to it.
_MANAGER_ANCHOR = "'/^\\\\.github/renovate-pins\\\\.yaml$/'"

#: A single-quoted JSON5 string literal that starts with `#` — every
#: matchString of this manager anchors on the datasource comment.
_LITERAL = re.compile(r"'(#(?:[^'\\]|\\.)*)'")


def _manager_block() -> str:
    """The one `customManagers` entry whose file list names the pins file.

    Split on `customType:` and selected by content rather than sliced from the
    anchor to the next key: the file promises no key ORDER, and a block that put
    `matchStrings` before `managerFilePatterns` would otherwise have yielded an
    empty slice — or the *next* manager's array, which is worse because it reads
    as a working measurement (review finding S-3, the same reasoning
    `tests.support.renovate_config.array_value` carries).
    """
    config = _CONFIG.read_text(encoding="utf-8")
    section = config[config.index("customManagers:") :]
    blocks = [
        b
        for b in strip_comments(section).split("customType:")
        if _MANAGER_ANCHOR in (array_value(b, "managerFilePatterns") or "")
    ]
    assert len(blocks) == 1, (
        f"expected exactly one custom manager in {_CONFIG} whose managerFilePatterns names "
        f"{_MANAGER_ANCHOR}, found {len(blocks)}. Zero means this guard located nothing and would "
        "otherwise measure nothing; two means the pins file is read by two managers."
    )
    return blocks[0]


def _manager_match_strings() -> list[str]:
    """The `matchStrings` of the `.github/renovate-pins.yaml` custom manager."""
    array = array_value(_manager_block(), "matchStrings")
    assert array, f"the manager in {_CONFIG} has no matchStrings array — the extraction broke, not the config."
    patterns = [literal for (literal,) in (m.groups() for m in _LITERAL.finditer(array))]
    assert patterns, f"no matchString literal extracted from {_CONFIG} — the extraction broke, not the config."
    return patterns


def _to_python(pattern: str) -> re.Pattern[str]:
    """Renovate's `(?<name>…)` group syntax spelled the way Python wants it."""
    unescaped = pattern.replace("\\\\", "\\")
    return re.compile(re.sub(r"\(\?<(?![=!])", "(?P<", unescaped))


def _digest_pattern() -> re.Pattern[str]:
    candidates = [p for p in _manager_match_strings() if "currentDigest" in p]
    assert len(candidates) == 1, (
        f"expected exactly one digest-capturing matchString in {_CONFIG}, found {len(candidates)}: {candidates}"
    )
    return _to_python(candidates[0])


def _version_only_patterns() -> list[re.Pattern[str]]:
    return [_to_python(p) for p in _manager_match_strings() if "currentDigest" not in p]


def _lane_code(lane: str) -> str:
    """A workflow with its `#` comment lines removed.

    Used by BOTH directions of the tag sweep, and that is the point. In this
    file's first draft the NEGATIVE test stripped comments and the POSITIVE one
    did not, so `assert "git/commits" in text` was satisfiable by the comment
    block that merely *explains* the endpoint: replacing the whole step with
    `echo skipped` would have left the guard green (review finding W-2). Prose
    answering for configuration is the failure this repository pays for most
    often; `tests.support.renovate_config.strip_comments` carries the same note
    for the JSON5 side.
    """
    path = _REPO_ROOT / ".github" / "workflows" / f"security-nuclei-{lane}.yml"
    return "\n".join(
        line for line in path.read_text(encoding="utf-8").splitlines() if not line.lstrip().startswith("#")
    )


class TestTheDigestPinIsManaged:
    """The manager Renovate runs extracts the digest AND its label, once."""

    def test_the_digest_matchstring_matches_the_pins_file_exactly_once(self) -> None:
        pins = _PINS.read_text(encoding="utf-8")
        matches = list(_digest_pattern().finditer(pins))
        assert len(matches) == 1, (
            f"the digest matchString matched {len(matches)} block(s) in {_PINS}; exactly one is the "
            "template set. Zero means the pin is unmanaged again — the #1280/#1454 shape."
        )

    def test_the_single_match_carries_the_digest_its_label_and_the_upstream(self) -> None:
        pins = _PINS.read_text(encoding="utf-8")
        match = _digest_pattern().search(pins)
        assert match is not None, "the digest matchString does not match the pins file at all."
        groups = match.groupdict()
        assert groups["depName"] == "projectdiscovery/nuclei-templates"
        assert groups["datasource"] == "github-tags"
        assert re.fullmatch(r"[0-9a-f]{40}", groups["currentDigest"]), (
            f"currentDigest captured {groups['currentDigest']!r}, which is not a commit digest."
        )
        assert groups["currentValue"].startswith("v"), (
            f"currentValue captured {groups['currentValue']!r} — the tag label is expected on the line "
            "directly below the digest, with nothing in between."
        )

    def test_the_version_only_matchstring_does_not_raise_the_same_block_twice(self) -> None:
        """Two managers over one block would mean two pull requests for one bump."""
        pins = _PINS.read_text(encoding="utf-8")
        patterns = _version_only_patterns()
        # An empty list would make the loop below green without comparing
        # anything (review finding W-4), and it becomes empty exactly when the
        # version-only matchString is removed or a future one stops anchoring on
        # the datasource comment — i.e. when the extraction stops seeing it, not
        # when the risk goes away.
        assert patterns, (
            f"no version-only matchString extracted from {_CONFIG}; this test compares against them, so "
            "an empty list means it measured nothing rather than that nothing collides."
        )
        for pattern in patterns:
            for match in pattern.finditer(pins):
                assert match.groupdict().get("depName") != "projectdiscovery/nuclei-templates", (
                    "the version-only matchString also matches the template-set block, so Renovate "
                    f"would extract it twice: {match.group(0)!r}"
                )

    def test_the_digest_the_workflows_read_is_the_digest_the_manager_moves(self) -> None:
        """`yq` and the manager must address the same key, or one of them ages alone."""
        pins = _PINS.read_text(encoding="utf-8")
        match = _digest_pattern().search(pins)
        assert match is not None
        digest = match.group("currentDigest")
        assert f"nuclei_templates_commit: {digest}" in pins
        for lane in ("nightly", "postmerge", "templates"):
            # Comment-stripped: every one of these lanes explains the pin in
            # prose directly above the step that reads it (W-2).
            assert "yq e '.nuclei_templates_commit' .github/renovate-pins.yaml" in _lane_code(lane), (
                f"security-nuclei-{lane}.yml no longer reads the pinned digest from the pins file."
            )


#: A run: line may be continued with a trailing backslash, and the lanes DO write
#: their git commands that way — `[^\n]*` stopped at the first newline and made
#: the most likely regression invisible (review finding W-3).
_CONTINUED = r"(?:[^\n]|\\\n)*?"

#: Everything a lane could use to turn the tag label back into a commit, one arm
#: per spelling so :class:`TestTheSweepCanGoRed` can show each of them firing.
#: `refs?/tags` rather than `refs/tags`: GitHub's own REST endpoint is the
#: SINGULAR `git/ref/tags/<name>`, which the plural-only form let through.
_TAG_RESOLUTION_ARMS = {
    "ls-remote": re.compile(r"ls-remote"),
    "tag-ref": re.compile(r"refs?/tags"),
    "fetch-the-label": re.compile(
        r"git\s+(?:-C\s+\S+\s+)?(?:fetch|checkout|clone)"
        + _CONTINUED
        + r"(?:\$\{?(?:VERSION|version)\b|\$\{\{[^}]*\.version\b)"
    ),
}


def _tag_resolution_offenders(code: str) -> list[str]:
    """Every tag-resolving construct in *code*, labelled by the arm that caught it."""
    return [f"{name}: {m.group(0)}" for name, arm in _TAG_RESOLUTION_ARMS.items() for m in arm.finditer(code)]


class TestNoLaneResolvesATagAtScanTime:
    """The whole point of #1543: a movable tag is not consulted anywhere."""

    @pytest.mark.parametrize("lane", ["nightly", "postmerge", "templates"])
    def test_the_lane_does_not_resolve_the_template_tag(self, lane: str) -> None:
        # Comments are prose about the retired assertion and say `ls-remote` on
        # purpose; only executable lines are measured.
        offenders = _tag_resolution_offenders(_lane_code(lane))
        assert not offenders, (
            f"security-nuclei-{lane}.yml resolves the template tag again: {offenders}. Under a digest "
            "pin that value is a label; anything asserting about it can only raise a false alarm (#1543)."
        )

    @pytest.mark.parametrize("lane", ["nightly", "postmerge", "templates"])
    def test_the_lane_fetches_the_pinned_digest(self, lane: str) -> None:
        """The other direction: absence of a tag lookup must not mean absence of a pin."""
        code = _lane_code(lane)
        if lane == "templates":
            # This lane never clones the set; it checks the digest exists
            # upstream. Measured on the comment-STRIPPED text: the step's own
            # comment block quotes the endpoint URL, so reading the raw file
            # here would let `echo skipped` pass as an existence check (W-2).
            assert "git/commits" in code and "$commit" in code, (
                "the pull-request lane no longer checks the pinned digest against upstream."
            )
            return
        assert 'fetch --depth=1 origin "$COMMIT"' in code, (
            f"security-nuclei-{lane}.yml no longer fetches the pinned commit directly."
        )


class TestTheSweepCanGoRed:
    """A positive control for every arm of :data:`_TAG_RESOLUTION_ARMS`.

    Without it, an arm broken by a later edit yields `offenders == []` and the
    parametrised sweep above stays green while measuring nothing — the failure
    mode this repository catalogues as "the measuring instrument has the gap,
    not the guard" (review finding W-3). Each fixture is a construct that really
    stood in one of these lanes before #1543, or a spelling of it that the first
    draft of the sweep missed.
    """

    #: The exact shape the nightly and post-merge lanes carried until #1543 —
    #: and the one the first draft could not see, because the command is spread
    #: over two lines by a trailing backslash.
    _CONTINUED_FETCH = 'git -C ./nuclei-templates fetch --depth=1 \\\n  origin "$VERSION"'

    _ONE_LINE_FETCH = 'git -C ./nuclei-templates fetch --depth=1 origin "$VERSION"'

    #: The pull-request lane's retired assertion.
    _LS_REMOTE = 'refs=$(git ls-remote "$UPSTREAM" "refs/tags/$version")'

    #: GitHub's ref endpoint is singular; the plural-only form let it through.
    _SINGULAR_REF_API = 'curl "https://api.github.com/repos/p/n/git/ref/tags/$version"'

    #: An expression substituted straight into the command, with no shell
    #: variable for a `$VERSION` arm to find.
    _INLINE_EXPRESSION = "git fetch --depth=1 origin ${{ steps.pin.outputs.version }}"

    #: Each fixture names the ARM that has to catch it, not merely that *some*
    #: arm does. Measured, because the looser form was written first and proved
    #: vacuous: `git ls-remote … "refs/tags/$version"` is caught by `tag-ref`
    #: too, so breaking the `ls-remote` arm outright left the control green.
    @pytest.mark.parametrize(
        ("arm", "fixture"),
        [
            ("fetch-the-label", _CONTINUED_FETCH),
            ("fetch-the-label", _ONE_LINE_FETCH),
            ("fetch-the-label", _INLINE_EXPRESSION),
            ("ls-remote", _LS_REMOTE),
            ("tag-ref", _SINGULAR_REF_API),
        ],
    )
    def test_the_named_arm_catches_its_construct(self, arm: str, fixture: str) -> None:
        assert _TAG_RESOLUTION_ARMS[arm].search(fixture), (
            f"the {arm!r} arm no longer catches {fixture!r}. A broken arm makes the sweep over the real "
            "lanes green without measuring anything, which is the shape this control exists to refuse."
        )

    def test_the_digest_fetch_the_lanes_actually_use_is_not_caught(self) -> None:
        """The control's control: an arm matching everything would be no arm."""
        assert not _tag_resolution_offenders('git -C ./nuclei-templates fetch --depth=1 origin "$COMMIT"')

    def test_the_arms_this_sweep_does_not_have(self) -> None:
        """Named, not silently absent — the honest half of the sweep.

        A tag routed through a differently named variable is invisible here:
        nothing distinguishes `TAG=$(yq e '.nuclei_templates_version' …)` from
        any other shell assignment without following the data flow, which a text
        sweep does not do. It is left uncaught ON PURPOSE rather than papered
        over with a pattern that would also flag the `version=` line every lane
        legitimately reads for its log message.

        What closes the practically reachable half is the CONVERSE assertion in
        :class:`TestNoLaneResolvesATagAtScanTime` — a lane that fetched a tag
        instead of the digest loses `fetch … "$COMMIT"` and goes red there — plus
        the comment standing where the retired assertion stood, which is aimed at
        exactly the reader who would write this.
        """
        laundered = "TAG=$(yq e '.nuclei_templates_version' .github/renovate-pins.yaml)\ngit fetch origin \"$TAG\""
        assert not _tag_resolution_offenders(laundered)
