"""API endpoint tests with a faked embedder and repository (no model/DB)."""

import json

from app.vectordb.repository import SpeciesMatch
from tests.conftest import make_image_bytes


def _image_part(name: str = "image", fmt: str = "PNG"):
    return {name: (f"img.{fmt.lower()}", make_image_bytes(fmt=fmt), f"image/{fmt.lower()}")}


# -- health / readiness / modelinfo ----------------------------------------


def test_health_ok_when_ready(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert body["model_loaded"] is True
    assert body["vectordb"] is True


def test_ready_returns_ok(client):
    assert client.get("/ready").status_code == 200


def test_ready_503_when_model_not_loaded(client, monkeypatch):
    from app import main

    class _NotReady:
        load_error = None

        def is_ready(self) -> bool:
            return False

    monkeypatch.setattr(main, "_embedder", _NotReady())
    assert client.get("/ready").status_code == 503


def test_modelinfo(client):
    body = client.get("/modelinfo").json()
    assert body["model"] == "dinov2_vits14"
    assert body["dim"] == 384
    assert body["input_size"] == 224
    assert body["license"] == "Apache-2.0"
    assert body["checksum"] == "test-checksum"


# -- embed -----------------------------------------------------------------


def test_embed_returns_normalised_vector(client):
    resp = client.post("/embed", files=_image_part())
    assert resp.status_code == 200
    body = resp.json()
    assert body["dim"] == 384
    assert body["model"] == "dinov2_vits14"
    assert len(body["embedding"]) == 384


def test_embed_rejects_empty_upload(client):
    resp = client.post("/embed", files={"image": ("e.png", b"", "image/png")})
    assert resp.status_code == 400


def test_embed_batch(client):
    files = [
        ("images", ("a.png", make_image_bytes(color=(1, 2, 3)), "image/png")),
        ("images", ("b.png", make_image_bytes(color=(9, 8, 7)), "image/png")),
    ]
    resp = client.post("/embed/batch", files=files)
    assert resp.status_code == 200
    body = resp.json()
    assert body["count"] == 2
    assert len(body["embeddings"]) == 2
    assert body["dim"] == 384


# -- match -----------------------------------------------------------------


def test_match_returns_ranked_suggestions(client, fake_repo):
    fake_repo.matches = [
        SpeciesMatch("species_monstera_deliciosa", "Monstera deliciosa", 0.91),
        SpeciesMatch("species_ficus_lyrata", "Ficus lyrata", 0.42),
    ]
    resp = client.post("/match?k=2", files=_image_part())
    assert resp.status_code == 200
    body = resp.json()
    assert body["is_plant"] is True
    assert body["model"] == "dinov2_vits14"
    assert [s["rank"] for s in body["suggestions"]] == [1, 2]
    top = body["suggestions"][0]
    assert top["species_key"] == "species_monstera_deliciosa"
    # High cosine -> high confidence (auto-accept band)
    assert top["confidence"] >= 0.85
    # Lower cosine -> lower confidence than top
    assert body["suggestions"][1]["confidence"] < top["confidence"]


def test_match_empty_index_is_not_plant(client, fake_repo):
    fake_repo.matches = []
    body = client.post("/match", files=_image_part()).json()
    assert body["is_plant"] is False
    assert body["suggestions"] == []


def test_match_respects_k_clamp(client):
    # k above le=50 is rejected by query validation
    resp = client.post("/match?k=999", files=_image_part())
    assert resp.status_code == 422


# -- reference -------------------------------------------------------------


def test_reference_from_image(client, fake_repo):
    data = {
        "species_key": "species_monstera_deliciosa",
        "scientific_name": "Monstera deliciosa",
        "source": "gbif",
        "organ": "leaf",
        "license": "CC-BY",
        "attribution": "(c) Jane Doe, via GBIF",
        "source_url": "https://example.org/4711",
        "source_record_id": "4711",
    }
    resp = client.post("/reference", data=data, files=_image_part())
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert body["dim"] == 384
    assert len(fake_repo.rows) == 1
    row = fake_repo.rows[0]
    assert row["species_key"] == "species_monstera_deliciosa"
    assert row["license"] == "CC-BY"
    assert len(row["embedding"]) == 384


def test_reference_from_precomputed_embedding(client, fake_repo):
    vector = [0.0] * 384
    vector[0] = 1.0
    data = {
        "species_key": "species_ficus_lyrata",
        "scientific_name": "Ficus lyrata",
        "source": "gbif",
        "embedding": json.dumps(vector),
    }
    resp = client.post("/reference", data=data)
    assert resp.status_code == 200
    assert fake_repo.rows[0]["embedding"] == vector


def test_reference_rejects_wrong_dim_embedding(client):
    data = {
        "species_key": "x",
        "scientific_name": "X",
        "source": "gbif",
        "embedding": json.dumps([0.1, 0.2, 0.3]),
    }
    resp = client.post("/reference", data=data)
    assert resp.status_code == 400


def test_reference_requires_image_or_embedding(client):
    data = {"species_key": "x", "scientific_name": "X", "source": "gbif"}
    resp = client.post("/reference", data=data)
    assert resp.status_code == 400


def test_reference_rejects_invalid_embedding_json(client):
    data = {
        "species_key": "x",
        "scientific_name": "X",
        "source": "gbif",
        "embedding": "not-json",
    }
    resp = client.post("/reference", data=data)
    assert resp.status_code == 400


# -- delete ----------------------------------------------------------------


def test_delete_reference(client, fake_repo):
    fake_repo.rows = [
        {"species_key": "species_a"},
        {"species_key": "species_a"},
        {"species_key": "species_b"},
    ]
    resp = client.delete("/reference/species_a")
    assert resp.status_code == 200
    body = resp.json()
    assert body["deleted"] == 2
    assert body["species_key"] == "species_a"
    assert fake_repo.count() == 1
