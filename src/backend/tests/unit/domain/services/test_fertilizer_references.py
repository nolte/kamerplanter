"""``fertilizer_references`` — the one write-side visibility check (#1713).

The route tests in ``tests/integration/test_fertilizer_reference_tenant_visibility.py``
run it against a real catalogue; these pin the contract the writers rely on.
"""

from unittest.mock import MagicMock

import pytest

from app.common.exceptions import NotFoundError, ValidationError
from app.domain.services.fertilizer_references import assert_fertilizers_visible, require_visible_fertilizer


def _repo(visible: set[str]) -> MagicMock:
    repo = MagicMock()
    repo.list_visible_keys.side_effect = lambda keys, *, tenant_key: {k for k in keys if k in visible}
    return repo


def test_visible_keys_pass_and_are_asked_once_under_the_writers_tenant() -> None:
    repo = _repo({"own", "global"})

    assert_fertilizers_visible(repo, ["own", "global", "own"], tenant_key="t1", field="fertilizers_used", owner="X")

    repo.list_visible_keys.assert_called_once_with(["global", "own"], tenant_key="t1")


def test_an_invisible_key_is_one_422_naming_only_the_callers_own_input() -> None:
    repo = _repo({"own"})

    with pytest.raises(ValidationError) as caught:
        assert_fertilizers_visible(repo, ["own", "foreign"], tenant_key="t1", field="fertilizers_used", owner="X")

    assert caught.value.status_code == 422
    assert caught.value.details == [{"field": "fertilizers_used", "message": "Unknown fertilizer: foreign"}]


def test_lines_without_a_key_reference_nothing_and_need_no_repository() -> None:
    assert_fertilizers_visible(None, [None, ""], tenant_key="t1", field="fertilizers_used", owner="X")


def test_an_unwired_writer_fails_closed_instead_of_storing_unchecked() -> None:
    with pytest.raises(RuntimeError, match="needs a fertilizer repository"):
        assert_fertilizers_visible(None, ["own"], tenant_key="t1", field="fertilizers_used", owner="X")


def test_the_404_variant_answers_like_the_catalogue() -> None:
    repo = _repo({"own"})

    require_visible_fertilizer(repo, "own", tenant_key="t1", owner="X")
    with pytest.raises(NotFoundError):
        require_visible_fertilizer(repo, "foreign", tenant_key="t1", owner="X")
