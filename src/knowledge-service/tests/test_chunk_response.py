"""SCR-006: the VectorChunk -> KnowledgeChunkResponse projection helper.

``/search`` and ``/ask`` both project retrieved chunks through the shared
``_to_chunk_response`` helper. This locks the field mapping so a future schema
change cannot silently drop a field on one endpoint but not the other.
"""

from app import main
from app.vectordb.repository import VectorChunk


def test_to_chunk_response_maps_all_fields():
    chunk = VectorChunk(
        source_key="tomato-care",
        source_type="plant",
        title="Tomato Care",
        content="Water regularly.",
        metadata={"topic": "watering"},
        score=0.87,
        language="en",
    )

    response = main._to_chunk_response(chunk)

    assert response.source_key == "tomato-care"
    assert response.source_type == "plant"
    assert response.title == "Tomato Care"
    assert response.content == "Water regularly."
    assert response.metadata == {"topic": "watering"}
    assert response.score == 0.87
    assert response.language == "en"


def test_to_chunk_response_uses_dataclass_defaults():
    chunk = VectorChunk(
        source_key="basil",
        source_type="plant",
        title="Basil",
        content="Likes warmth.",
        metadata={},
    )

    response = main._to_chunk_response(chunk)

    assert response.score == 0.0
    assert response.language == "de"
    assert response.metadata == {}
