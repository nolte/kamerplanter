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
import inspect
from pathlib import Path
from unittest.mock import patch

import pytest

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

    def test_the_vocabulary_is_exactly_the_four_documented_values(self) -> None:
        """Named literally, so growing it is a deliberate edit here and in the docs."""
        assert [m.value for m in OidcProviderType] == ["google", "github", "apple", "oidc"]

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


def _provider_type_comparisons(module) -> set[str]:
    """Every value a `provider_type` expression is compared against in this module.

    Reads the module source rather than its behaviour: a dispatch branch that no
    test exercises is precisely the one that drifts. Both spellings count — a bare
    string literal and an `OidcProviderType` member — because a future edit may
    use either, and the failure mode is the same when the value is not one the
    boundary admits.
    """
    tree = ast.parse(Path(inspect.getfile(module)).read_text())
    found: set[str] = set()

    def is_provider_type(node: ast.AST) -> bool:
        if isinstance(node, ast.Name):
            return node.id == "provider_type"
        if isinstance(node, ast.Attribute):
            return node.attr == "provider_type"
        return False

    def resolved(node: ast.AST) -> str | None:
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            return node.value
        # `OidcProviderType.APPLE` and `OidcProviderType.APPLE.value`
        if isinstance(node, ast.Attribute) and node.attr == "value":
            node = node.value
        if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name) and node.value.id == "OidcProviderType":
            member = getattr(OidcProviderType, node.attr, None)
            return member.value if member is not None else f"OidcProviderType.{node.attr}"
        return None

    for node in ast.walk(tree):
        if not isinstance(node, ast.Compare):
            continue
        operands = [node.left, *node.comparators]
        if not any(is_provider_type(operand) for operand in operands):
            continue
        for operand in operands:
            value = resolved(operand)
            if value is not None:
                found.add(value)
    return found


class TestNoDispatchValueEscapesTheVocabulary:
    @pytest.mark.parametrize("module", [oauth_engine_module, oidc_config_module])
    def test_every_compared_value_is_a_member(self, module) -> None:
        found = _provider_type_comparisons(module)
        assert found <= VOCABULARY, f"{module.__name__} compares provider_type against {found - VOCABULARY}"

    def test_the_sweep_actually_finds_something(self) -> None:
        """Otherwise an empty result would certify the engine forever.

        `extract_user_info` dispatches Apple on its own branch; if this set is
        empty the walker stopped matching the source and the check above passes
        while seeing nothing.
        """
        assert "apple" in _provider_type_comparisons(oauth_engine_module)

    def test_a_literal_outside_the_vocabulary_would_be_caught(self) -> None:
        """The falsification: the same expression, against a module that has one."""
        source = 'if config.provider_type == "azure":\n    pass\n'
        path = Path(inspect.getfile(oauth_engine_module))
        with patch.object(Path, "read_text", lambda self, *a, **k: source):
            found = _provider_type_comparisons(oauth_engine_module)
        assert path.exists()
        assert found == {"azure"}
        assert not found <= VOCABULARY


class TestDispatchByLookupIsCoveredToo:
    """`==` is not the only spelling of dispatch; a dict lookup is the other one."""

    def test_the_auth_provider_table_is_keyed_from_the_vocabulary(self) -> None:
        assert set(_AUTH_PROVIDER_BY_TYPE) <= VOCABULARY

    def test_every_member_but_the_generic_one_maps_explicitly(self) -> None:
        """`oidc` is the `.get` fallback, which is what the generic branch means."""
        assert VOCABULARY - set(_AUTH_PROVIDER_BY_TYPE) == {OidcProviderType.OIDC.value}
