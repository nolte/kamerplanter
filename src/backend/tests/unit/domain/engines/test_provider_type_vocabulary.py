"""The provider-type vocabulary and the code that dispatches on it cannot drift (#1497).

`OidcProviderType` is the single source: the request schemas validate against it,
`_PROVIDER_ENDPOINTS` is keyed from it, and the engine dispatches on its members.
Two spellings of the same fact is exactly how a provider typed `GitHub` came to be
stored and then served by the generic OIDC branch without a complaint anywhere.

The AST sweep below is the part that survives the next edit: a new
`provider_type == "azure"` branch in the engine goes red here even though every
behavioural test still passes, because "azure" is not a member the boundary lets
through, so the branch would be unreachable.
"""

import ast
import importlib
import inspect
from pathlib import Path
from types import ModuleType
from unittest.mock import patch

import pytest

import app
from app.api.v1.admin.oidc_providers.schemas import (
    OidcProviderCreateRequest,
    OidcProviderUpdateRequest,
)
from app.common.enums import OidcProviderType
from app.domain.engines import oauth_engine as oauth_engine_module
from app.domain.engines.oauth_engine import _AUTH_PROVIDER_BY_TYPE, _PROVIDER_ENDPOINTS
from app.domain.models import oidc_config as oidc_config_module
from app.domain.models.oidc_config import (
    GITHUB_PROVIDER_TYPE,
    KNOWN_PROVIDER_TYPES,
    is_github_provider,
    is_known_provider_type,
)

VOCABULARY = {member.value for member in OidcProviderType}


class TestTheVocabularyIsOneSource:
    def test_every_endpoint_key_is_a_member(self) -> None:
        """A well-known endpoint set the boundary refuses would be dead weight."""
        assert set(_PROVIDER_ENDPOINTS) <= VOCABULARY

    def test_every_member_but_the_generic_one_has_well_known_endpoints(self) -> None:
        """`oidc` is the generic branch and resolves through discovery instead."""
        assert VOCABULARY - set(_PROVIDER_ENDPOINTS) == {OidcProviderType.OIDC.value}

    def test_the_github_constant_is_the_member(self) -> None:
        assert OidcProviderType.GITHUB.value == GITHUB_PROVIDER_TYPE

    def test_the_cached_set_is_the_enum(self) -> None:
        """`KNOWN_PROVIDER_TYPES` is built once; a stale copy is a second source."""
        assert KNOWN_PROVIDER_TYPES == VOCABULARY

    def test_the_vocabulary_is_exactly_the_four_documented_values(self) -> None:
        """The anchor for the prose copies of this list, which no test can assert.

        The four values are repeated in text in four places, and text cannot be
        checked mechanically — so this test names them in its failure message,
        which is what an editor sees at the moment they extend the enum.
        """
        assert [m.value for m in OidcProviderType] == ["google", "github", "apple", "oidc"], (
            "The vocabulary changed. Four PROSE copies of this list have to change with it, "
            "and nothing else will tell you: docs/de/user-guide/admin.md and "
            "docs/en/user-guide/admin.md (admonition 'Der Provider-Typ ist auf vier Werte "
            "festgelegt' / 'The provider type is limited to four values'), "
            "spec/req/REQ-023_Benutzerverwaltung-Authentifizierung.md (the Datenmodell "
            "`Literal[...]` and the #1497 paragraph), and this file's module docstring."
        )

    def test_local_is_not_a_member(self) -> None:
        """`AuthProviderType.LOCAL` names the one kind that has no federation."""
        assert "local" not in VOCABULARY


class TestThePredicates:
    def test_is_github_provider_is_still_exact(self) -> None:
        """#1477's scope gate compares case-sensitively and must keep doing so.

        The boundary now enforces the spelling, so this is no longer a hole; a
        pre-gate record typed `GitHub` still takes the generic branch, and the
        gate must not refuse it for a scope that branch never uses.
        """
        assert is_github_provider("github") is True
        assert is_github_provider("GitHub") is False
        assert is_github_provider("GITHUB") is False

    @pytest.mark.parametrize("spelling", ["google", "github", "apple", "oidc"])
    def test_a_member_is_known(self, spelling: str) -> None:
        assert is_known_provider_type(spelling) is True

    @pytest.mark.parametrize("spelling", ["GitHub", "GOOGLE", "Apple", "twitter", "local", "", " github"])
    def test_anything_else_is_not(self, spelling: str) -> None:
        assert is_known_provider_type(spelling) is False


class TestTheRequestSchemasCarryTheVocabulary:
    """The annotation itself, so widening it back to `str` goes red here too."""

    def test_create(self) -> None:
        field = OidcProviderCreateRequest.model_fields["provider_type"]
        assert field.annotation is OidcProviderType

    def test_update(self) -> None:
        field = OidcProviderUpdateRequest.model_fields["provider_type"]
        assert OidcProviderType in getattr(field.annotation, "__args__", (field.annotation,))


def _dispatch_modules() -> list[ModuleType]:
    """Every backend module that names `OidcProviderConfig` — importers and its own.

    Derived, not enumerated (#1497 review): a new module that dispatches on
    `provider_type` would simply be absent from a hand-written list, and the sweep
    would keep reporting green about the modules it happens to name. Naming the
    configuration is the necessary condition for reading its `provider_type`.

    The first version of this required an `oidc_config` IMPORT and therefore
    missed the module that DEFINES the model — which is one of the two that
    actually dispatch. The control below is what found that.
    """
    package = Path(inspect.getfile(app)).parent
    modules: list[ModuleType] = []
    for path in sorted(package.rglob("*.py")):
        source = path.read_text()
        if "OidcProviderConfig" not in source:
            continue
        dotted = ".".join(path.relative_to(package.parent).with_suffix("").parts)
        modules.append(importlib.import_module(dotted))
    return modules


def _provider_type_comparisons(module: ModuleType) -> set[str]:
    """Every value a `provider_type` expression is dispatched on in this module.

    Reads the module source rather than its behaviour: a dispatch branch that no
    test exercises is precisely the one that drifts.

    Four spellings of the same dispatch count, because a future edit may use any
    of them and the consequence is identical when the value is not one the
    boundary admits: a bare literal, an `OidcProviderType` member, a module-level
    string constant (`GITHUB_PROVIDER_TYPE`), and a membership test against a
    tuple/set/list of any of those. `match`/`case` is read too — it is `==` with
    different punctuation.

    What it still does not see is recorded in the tests below rather than left to
    be discovered: a value reached through a helper call, and a comparison after
    `.lower()`. Both are named by a test that asserts the limit, so the sweep does
    not read as more complete than it is.
    """
    path = Path(inspect.getfile(module))
    tree = ast.parse(path.read_text())
    constants = _module_string_constants(tree)
    found: set[str] = set()

    def is_provider_type(node: ast.AST) -> bool:
        if isinstance(node, ast.Name):
            return node.id == "provider_type"
        if isinstance(node, ast.Attribute):
            return node.attr == "provider_type"
        return False

    def resolved(node: ast.AST) -> set[str]:
        if isinstance(node, ast.Constant):
            return {node.value} if isinstance(node.value, str) else set()
        if isinstance(node, ast.Tuple | ast.List | ast.Set):
            return {value for element in node.elts for value in resolved(element)}
        if isinstance(node, ast.Name) and node.id in constants:
            return {constants[node.id]}
        member = node
        if isinstance(member, ast.Attribute) and member.attr == "value":
            member = member.value
        if (
            isinstance(member, ast.Attribute)
            and isinstance(member.value, ast.Name)
            and member.value.id == "OidcProviderType"
        ):
            resolved_member = getattr(OidcProviderType, member.attr, None)
            return {resolved_member.value if resolved_member is not None else f"OidcProviderType.{member.attr}"}
        return set()

    for node in ast.walk(tree):
        if isinstance(node, ast.Compare):
            operands = [node.left, *node.comparators]
            if any(is_provider_type(operand) for operand in operands):
                for operand in operands:
                    found |= resolved(operand)
        elif isinstance(node, ast.Match) and is_provider_type(node.subject):
            for case in node.cases:
                for pattern in ast.walk(case.pattern):
                    if isinstance(pattern, ast.MatchValue):
                        found |= resolved(pattern.value)
    return found


def _module_string_constants(tree: ast.Module) -> dict[str, str]:
    """Module-level `NAME = "literal"` assignments, so a named constant resolves."""
    constants: dict[str, str] = {}
    for node in tree.body:
        targets: list[ast.expr] = []
        value: ast.expr | None = None
        if isinstance(node, ast.Assign):
            targets, value = node.targets, node.value
        elif isinstance(node, ast.AnnAssign) and node.value is not None:
            targets, value = [node.target], node.value
        if value is None:
            continue
        for target in targets:
            if not isinstance(target, ast.Name):
                continue
            if isinstance(value, ast.Constant) and isinstance(value.value, str):
                constants[target.id] = value.value
            elif (
                isinstance(value, ast.Attribute)
                and value.attr == "value"
                and isinstance(value.value, ast.Attribute)
                and isinstance(value.value.value, ast.Name)
                and value.value.value.id == "OidcProviderType"
            ):
                member = getattr(OidcProviderType, value.value.attr, None)
                if member is not None:
                    constants[target.id] = member.value
    return constants


class TestNoDispatchValueEscapesTheVocabulary:
    @pytest.mark.parametrize("module", _dispatch_modules(), ids=lambda m: m.__name__)
    def test_every_dispatched_value_is_a_member(self, module: ModuleType) -> None:
        found = _provider_type_comparisons(module)
        assert found <= VOCABULARY, f"{module.__name__} dispatches provider_type on {found - VOCABULARY}"

    def test_the_module_list_is_derived_and_covers_the_two_that_dispatch(self) -> None:
        """A hand-written list would silently omit the next module that dispatches."""
        names = {module.__name__ for module in _dispatch_modules()}
        assert "app.domain.engines.oauth_engine" in names
        assert "app.domain.models.oidc_config" in names

    @pytest.mark.parametrize(
        ("module", "anchor"),
        [
            (oauth_engine_module, "apple"),
            # `is_github_provider` compares against the module constant, which the
            # sweep resolves. Anchoring a real hit here is what stops this module's
            # membership assertion from passing on an EMPTY set.
            (oidc_config_module, "github"),
        ],
        ids=["oauth_engine", "oidc_config"],
    )
    def test_the_sweep_actually_finds_something_in_each_module(self, module: ModuleType, anchor: str) -> None:
        """Otherwise an empty result would certify a module forever.

        This is the control the first version of this file lacked: it asserted
        membership for both modules but anchored a hit in only one, so the
        `oidc_config` case passed on the empty set.
        """
        assert anchor in _provider_type_comparisons(module)

    @pytest.mark.parametrize(
        ("source", "expected"),
        [
            ('if config.provider_type == "azure":\n    pass\n', {"azure"}),
            ('if provider_type in ("azure", "github"):\n    pass\n', {"azure", "github"}),
            ('if provider_type in {"azure"}:\n    pass\n', {"azure"}),
            ('if provider_type in ["azure"]:\n    pass\n', {"azure"}),
            ('AZURE = "azure"\nif provider_type == AZURE:\n    pass\n', {"azure"}),
            (
                "match config.provider_type:\n    case 'azure':\n        pass\n",
                {"azure"},
            ),
            ("if provider_type == OidcProviderType.GITHUB:\n    pass\n", {"github"}),
        ],
        ids=["literal", "tuple", "set", "list", "module-constant", "match-case", "enum-member"],
    )
    def test_each_spelling_of_dispatch_is_seen(self, source: str, expected: set[str]) -> None:
        """The falsification, one mutation per spelling the sweep claims to read.

        Each asserts the SAME expression the rule asserts — the resolved set and
        its membership in the vocabulary — against a source that carries the
        spelling, so a walker that stops matching one of them goes red here.
        """
        with patch.object(Path, "read_text", lambda self, *a, **k: source):
            found = _provider_type_comparisons(oauth_engine_module)
        assert found == expected
        assert (found <= VOCABULARY) == expected.issubset(VOCABULARY)

    @pytest.mark.parametrize(
        "source",
        [
            'if provider_type.lower() == "azure":\n    pass\n',
            "if _is_azure(provider_type):\n    pass\n",
        ],
        ids=["normalised-comparison", "behind-a-helper"],
    )
    def test_the_sweep_names_its_own_blind_spots(self, source: str) -> None:
        """Measured, not assumed: these two spellings are NOT seen.

        Recording them is the point. A sweep whose limits are undocumented reads
        as complete, and the review question — *name a spelling of the same thing
        my pattern does not match* — has an answer here. Neither shape exists in
        the code today; if one is introduced, the behavioural 422 tests still hold
        the boundary, which is where the vocabulary is actually enforced.
        """
        with patch.object(Path, "read_text", lambda self, *a, **k: source):
            assert _provider_type_comparisons(oauth_engine_module) == set()


class TestDispatchByLookupIsCoveredToo:
    """`==` is not the only spelling of dispatch; a dict lookup is the other one."""

    def test_the_auth_provider_table_is_keyed_from_the_vocabulary(self) -> None:
        assert set(_AUTH_PROVIDER_BY_TYPE) <= VOCABULARY

    def test_every_member_but_the_generic_one_maps_explicitly(self) -> None:
        """`oidc` is the `.get` fallback, which is what the generic branch means."""
        assert VOCABULARY - set(_AUTH_PROVIDER_BY_TYPE) == {OidcProviderType.OIDC.value}
