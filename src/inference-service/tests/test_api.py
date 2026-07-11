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


def test_reference_user_contribution_quarantined_with_provenance(client, fake_repo):
    # SEC-001/005 (issue #447) — an interactive user contribution is written
    # inactive and carries contributor/tenant provenance.
    vector = [0.0] * 384
    vector[0] = 1.0
    data = {
        "species_key": "species_monstera_deliciosa",
        "scientific_name": "Monstera deliciosa",
        "source": "user_contributed",
        "source_record_id": "sha256:deadbeef",
        "embedding": json.dumps(vector),
        "is_active": "false",
        "contributed_by": "user_anna",
        "tenant_key": "tenant_anna",
    }
    resp = client.post("/reference", data=data)
    assert resp.status_code == 200
    row = fake_repo.rows[0]
    assert row["is_active"] is False
    assert row["contributed_by"] == "user_anna"
    assert row["tenant_key"] == "tenant_anna"


def test_user_contribution_curation_lifecycle(client, fake_repo):
    # SEC-001 (issue #447) — a quarantined user contribution has NO source_url
    # (original image never persisted) yet must still be curatable end to end:
    # invisible to the public gallery, visible to admin curation, activatable,
    # and match-eligible only after activation.
    fake_repo.rows = [
        {
            "id": 1,
            "species_key": "species_a",
            "scientific_name": "Aloe vera",
            "source": "user_contributed",
            "source_url": None,
            "is_active": False,
            "contributed_by": "user_anna",
            "tenant_key": "tenant_anna",
            "contributed_at": "2026-07-11T10:00:00+00:00",
        }
    ]

    # Default (public gallery) — the contribution is NOT surfaced.
    public = client.get("/reference/species_a").json()
    assert public["count"] == 0

    # Admin curation — surfaced with provenance, still inactive.
    curation = client.get("/reference/species_a?include_contributions=true").json()
    assert curation["count"] == 1
    item = curation["images"][0]
    assert item["source"] == "user_contributed"
    assert item["source_url"] is None
    assert item["is_active"] is False
    assert item["contributed_by"] == "user_anna"
    assert item["tenant_key"] == "tenant_anna"

    # Quarantine invariant — not match-eligible while inactive.
    assert "species_a" not in fake_repo.active_species_keys()

    # Admin activates it.
    resp = client.patch("/reference/species_a/1", json={"is_active": True})
    assert resp.status_code == 200
    assert resp.json()["is_active"] is True

    # Now active in curation AND match-eligible (no source_url required by /match).
    curation_after = client.get("/reference/species_a?include_contributions=true").json()
    assert curation_after["images"][0]["is_active"] is True
    assert "species_a" in fake_repo.active_species_keys()


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


def test_list_references_returns_provenance(client, fake_repo):
    fake_repo.rows = [
        {
            "species_key": "species_a",
            "source_url": "http://x/1.jpg",
            "license": "CC-BY",
            "attribution": "Jane Doe",
            "organ": "leaf",
            "source": "gbif",
        },
        {"species_key": "species_a", "source_url": "http://x/2.jpg", "license": "CC0", "source": "wikimedia"},
        {"species_key": "species_a"},  # no source_url → excluded
        {"species_key": "species_b", "source_url": "http://y/9.jpg", "license": "CC0"},
    ]
    resp = client.get("/reference/species_a")
    assert resp.status_code == 200
    body = resp.json()
    assert body["species_key"] == "species_a"
    assert body["count"] == 2
    urls = {img["source_url"] for img in body["images"]}
    assert urls == {"http://x/1.jpg", "http://x/2.jpg"}
    assert body["images"][0]["attribution"] == "Jane Doe"


def test_list_references_empty_for_unknown_species(client, fake_repo):
    resp = client.get("/reference/nope")
    assert resp.status_code == 200
    assert resp.json()["count"] == 0


# -- curation (deselect / re-include) --------------------------------------


def test_set_reference_inactive_marks_image(client, fake_repo):
    fake_repo.upsert_reference(
        species_key="species_a",
        scientific_name="A",
        source="gbif",
        source_url="http://x/1.jpg",
        embedding=[0.0] * 384,
    )
    image_id = fake_repo.rows[0]["id"]

    resp = client.patch(
        f"/reference/species_a/{image_id}",
        json={"is_active": False, "reason": "blurry"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["is_active"] is False
    assert body["id"] == image_id
    assert fake_repo.rows[0]["is_active"] is False
    assert fake_repo.rows[0]["exclusion_reason"] == "blurry"


def test_set_reference_active_clears_reason(client, fake_repo):
    fake_repo.upsert_reference(
        species_key="species_a",
        scientific_name="A",
        source="gbif",
        source_url="http://x/1.jpg",
        embedding=[0.0] * 384,
        is_active=False,
        exclusion_reason="blurry",
    )
    image_id = fake_repo.rows[0]["id"]

    resp = client.patch(
        f"/reference/species_a/{image_id}",
        json={"is_active": True},
    )
    assert resp.status_code == 200
    assert resp.json()["is_active"] is True
    assert fake_repo.rows[0]["is_active"] is True
    assert fake_repo.rows[0]["exclusion_reason"] is None


def test_set_reference_active_unknown_id_is_404(client, fake_repo):
    resp = client.patch("/reference/species_a/999", json={"is_active": False})
    assert resp.status_code == 404


def test_list_references_active_only_hides_excluded(client, fake_repo):
    fake_repo.rows = [
        {"id": 1, "species_key": "species_a", "source_url": "http://x/1.jpg", "is_active": True},
        {"id": 2, "species_key": "species_a", "source_url": "http://x/2.jpg", "is_active": False},
    ]
    # Curation view: both images visible, with flags.
    full = client.get("/reference/species_a").json()
    assert full["count"] == 2
    by_id = {img["id"]: img for img in full["images"]}
    assert by_id[2]["is_active"] is False

    # Public gallery view: excluded image is gone.
    active = client.get("/reference/species_a?active_only=true").json()
    assert active["count"] == 1
    assert active["images"][0]["id"] == 1
