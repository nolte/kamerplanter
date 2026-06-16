"""Unit tests for repository helpers that need no live database."""

from app.vectordb.repository import SpeciesMatch, _to_vector_literal


def test_vector_literal_format():
    """Vector literal renders as a bracketed comma-separated list."""
    assert _to_vector_literal([1.0, 2.5, -3.0]) == "[1.0,2.5,-3.0]"


def test_vector_literal_coerces_to_float():
    """Integer inputs are coerced to float in the literal."""
    literal = _to_vector_literal([1, 2, 3])
    assert literal == "[1.0,2.0,3.0]"


def test_species_match_dataclass():
    """SpeciesMatch carries species_key, scientific_name and score."""
    m = SpeciesMatch("species_x", "Genus species", 0.87)
    assert m.species_key == "species_x"
    assert m.scientific_name == "Genus species"
    assert m.score == 0.87
