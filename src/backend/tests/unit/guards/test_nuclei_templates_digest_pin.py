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


def _manager_match_strings() -> list[str]:
    """The `matchStrings` of the `.github/renovate-pins.yaml` custom manager."""
    config = _CONFIG.read_text(encoding="utf-8")
    anchor = config.find(_MANAGER_ANCHOR)
    assert anchor != -1, (
        f"{_CONFIG} no longer contains the managerFilePatterns entry "
        f"{_MANAGER_ANCHOR} — this guard located the manager by it and would "
        "otherwise be measuring nothing."
    )
    start = config.index("matchStrings: [", anchor)
    end = config.index("],", start)
    block = config[start:end]
    # Drop `//` comment lines before extracting literals: a comment containing a
    # quote would otherwise be read as part of a pattern.
    code = "\n".join(line for line in block.splitlines() if not line.strip().startswith("//"))
    patterns = [literal for (literal,) in (m.groups() for m in _LITERAL.finditer(code))]
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
        for pattern in _version_only_patterns():
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
            workflow = (_REPO_ROOT / ".github" / "workflows" / f"security-nuclei-{lane}.yml").read_text(
                encoding="utf-8"
            )
            assert "yq e '.nuclei_templates_commit' .github/renovate-pins.yaml" in workflow, (
                f"security-nuclei-{lane}.yml no longer reads the pinned digest from the pins file."
            )


class TestNoLaneResolvesATagAtScanTime:
    """The whole point of #1543: a movable tag is not consulted anywhere."""

    #: Everything a lane could use to turn the tag label back into a commit.
    _TAG_RESOLUTION = re.compile(
        r"""
        ls-remote                      # server-side ref lookup
        | refs/tags                    # an explicit tag ref
        | git\ (?:-C\ \S+\ )?(?:fetch|checkout|clone)[^\n]*\$\{?\w*VERSION   # fetching the label
        | git\ (?:-C\ \S+\ )?(?:fetch|checkout|clone)[^\n]*\$\{?version      # …lower-cased
        """,
        re.VERBOSE,
    )

    @pytest.mark.parametrize("lane", ["nightly", "postmerge", "templates"])
    def test_the_lane_does_not_resolve_the_template_tag(self, lane: str) -> None:
        path = _REPO_ROOT / ".github" / "workflows" / f"security-nuclei-{lane}.yml"
        # Comments are prose about the retired assertion and say `ls-remote` on
        # purpose; only executable lines are measured.
        code = "\n".join(
            line for line in path.read_text(encoding="utf-8").splitlines() if not line.lstrip().startswith(("#", "//"))
        )
        offenders = [m.group(0) for m in self._TAG_RESOLUTION.finditer(code)]
        assert not offenders, (
            f"security-nuclei-{lane}.yml resolves the template tag again: {offenders}. Under a digest "
            "pin that value is a label; anything asserting about it can only raise a false alarm (#1543)."
        )

    @pytest.mark.parametrize("lane", ["nightly", "postmerge", "templates"])
    def test_the_lane_fetches_the_pinned_digest(self, lane: str) -> None:
        """The other direction: absence of a tag lookup must not mean absence of a pin."""
        path = _REPO_ROOT / ".github" / "workflows" / f"security-nuclei-{lane}.yml"
        text = path.read_text(encoding="utf-8")
        if lane == "templates":
            # This lane never clones the set; it checks the digest exists upstream.
            assert "git/commits" in text and "$commit" in text, (
                "the pull-request lane no longer checks the pinned digest against upstream."
            )
            return
        assert 'fetch --depth=1 origin "$COMMIT"' in text, (
            f"security-nuclei-{lane}.yml no longer fetches the pinned commit directly."
        )
