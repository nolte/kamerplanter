"""Unit tests for the shared hybrid-catalog tenant-union predicate (F-4, #808).

The helper :func:`app.data_access.arango.tenant_scope.tenant_union_predicate` is
the single source of truth for the ``tenant_key == @tenant OR "" OR null`` read
predicate that fertilizer / nutrient-plan / task repositories duplicated inline
and that ``ai_provider_configs`` reads two-armed.

These tests pin two properties acceptance-3 depends on:

* the **default three-arm** fragment is *byte-identical* to the string the three
  catalog repositories used to inline (the hybrid-catalog union fake tests assert
  that exact string via substring match, so any drift here would silently break
  them); and
* with ``include_empty_string=False`` the fragment collapses to exactly the
  **two-arm** variant ``ai_repository`` needs — no ``== ""`` arm — so folding ai
  into the helper does not widen its read scope.

A structural guard also asserts that no verbatim inline copy of the predicate
survives in the four rewired repositories (acceptance-2).
"""

from __future__ import annotations

from pathlib import Path

from app.data_access.arango.tenant_scope import tenant_union_predicate

#: The exact three-arm string the catalog repositories inlined before F-4, and
#: the string the hybrid-catalog union fakes match on. Kept as a literal here so
#: this test fails loudly if the helper's output ever drifts from it.
_THREE_ARM = '(doc.tenant_key == @tenant_key OR doc.tenant_key == "" OR doc.tenant_key == null)'
_TWO_ARM = "(doc.tenant_key == @tenant_key OR doc.tenant_key == null)"


class TestThreeArmDefault:
    """The default (empty-string arm on) is the full hybrid-catalog union."""

    def test_fragment_is_byte_identical_to_the_inlined_catalog_predicate(self) -> None:
        fragment, _ = tenant_union_predicate("tenant_a")
        assert fragment == _THREE_ARM

    def test_bind_var_carries_the_tenant_key(self) -> None:
        _, bind_vars = tenant_union_predicate("tenant_a")
        assert bind_vars == {"tenant_key": "tenant_a"}

    def test_all_three_arms_are_present(self) -> None:
        fragment, _ = tenant_union_predicate("tenant_a")
        assert "== @tenant_key" in fragment
        assert '== ""' in fragment
        assert "== null" in fragment
        assert fragment.count(" OR ") == 2


class TestTwoArmVariant:
    """With the empty-string arm off, ai keeps its exact two-arm read scope."""

    def test_fragment_drops_only_the_empty_string_arm(self) -> None:
        fragment, _ = tenant_union_predicate("tenant_a", include_empty_string=False)
        assert fragment == _TWO_ARM

    def test_two_arm_has_no_empty_string_arm(self) -> None:
        fragment, _ = tenant_union_predicate("tenant_a", include_empty_string=False)
        assert '== ""' not in fragment
        assert "== @tenant_key" in fragment
        assert "== null" in fragment
        assert fragment.count(" OR ") == 1

    def test_bind_var_is_identical_regardless_of_the_arm_toggle(self) -> None:
        _, three = tenant_union_predicate("t1")
        _, two = tenant_union_predicate("t1", include_empty_string=False)
        assert three == two == {"tenant_key": "t1"}


class TestOverrides:
    """The doc var, field, and bind name are overridable for hand-written AQL."""

    def test_custom_doc_var_and_bind_name(self) -> None:
        fragment, bind_vars = tenant_union_predicate(
            "t1",
            doc_var="wt",
            bind_name="own_tenant",
        )
        assert fragment == '(wt.tenant_key == @own_tenant OR wt.tenant_key == "" OR wt.tenant_key == null)'
        assert bind_vars == {"own_tenant": "t1"}

    def test_custom_field(self) -> None:
        fragment, _ = tenant_union_predicate("t1", field="owner_tenant_key")
        assert fragment == (
            '(doc.owner_tenant_key == @tenant_key OR doc.owner_tenant_key == "" OR doc.owner_tenant_key == null)'
        )


class TestNoVerbatimInlineCopyRemains:
    """acceptance-2 — no rewired repository holds a verbatim copy of the predicate."""

    _REPO_DIR = Path(__file__).resolve().parents[4] / "app" / "data_access" / "arango"
    _REWIRED = (
        "fertilizer_repository.py",
        "nutrient_plan_repository.py",
        "task_repository.py",
        "ai_repository.py",
    )

    def test_three_arm_copy_is_gone_from_every_rewired_repository(self) -> None:
        for name in self._REWIRED:
            source = (self._REPO_DIR / name).read_text(encoding="utf-8")
            assert _THREE_ARM not in source, f"verbatim 3-arm predicate still inlined in {name}"

    def test_two_arm_copy_is_gone_from_ai_repository(self) -> None:
        source = (self._REPO_DIR / "ai_repository.py").read_text(encoding="utf-8")
        # The bare (unparenthesised) two-arm string the ai repository used to inline.
        assert "doc.tenant_key == @tenant_key OR doc.tenant_key == null" not in source

    def test_every_rewired_repository_calls_the_helper(self) -> None:
        for name in self._REWIRED:
            source = (self._REPO_DIR / name).read_text(encoding="utf-8")
            assert "tenant_union_predicate(" in source, f"{name} does not route through the shared helper"

    def test_task_repository_preserves_the_sort_tie_break(self) -> None:
        # acceptance-2: list_for_run's SORT tie-break must survive the extraction.
        source = (self._REPO_DIR / "task_repository.py").read_text(encoding="utf-8")
        assert "SORT (doc.tenant_key == @tenant_key ? 0 : 1) ASC, doc.created_at DESC" in source
