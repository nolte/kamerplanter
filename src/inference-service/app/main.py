"""Inference Service -- DINOv2 embedding extraction + pgvector species matching.

Internal (ClusterIP) microservice. NOT publicly exposed. Owns the
species_embeddings pgvector table and the ONNX DINOv2 model. Backend talks to
it over HTTP only (REQ-029-A 3.1, plan D-3).
"""

import json
from contextlib import asynccontextmanager
from pathlib import Path

import structlog
from fastapi import FastAPI, File, Form, HTTPException, Query, UploadFile

from app.confidence import cosine_to_confidence
from app.config import settings
from app.embedder import Embedder, ModelNotReadyError
from app.schemas import (
    BatchEmbedResponse,
    DeleteReferenceResponse,
    EmbedResponse,
    HealthResponse,
    MatchResponse,
    MatchSuggestion,
    ModelInfoResponse,
    ReferenceResponse,
)
from app.vectordb.connection import VectorDbConnection
from app.vectordb.repository import SpeciesEmbeddingRepository
from app.vectordb.schema import ensure_vectordb_schema

logger = structlog.get_logger(__name__)

_embedder: Embedder | None = None
_repo: SpeciesEmbeddingRepository | None = None
_vec_conn: VectorDbConnection | None = None
_model_checksum: str | None = None


def _load_model_checksum() -> str | None:
    """Read the sha256 checksum from modelinfo.json next to the ONNX file."""
    info_path = Path(settings.model_path) / "modelinfo.json"
    if not info_path.exists():
        return None
    try:
        data = json.loads(info_path.read_text(encoding="utf-8"))
        return data.get("checksum") or data.get("sha256")
    except (json.JSONDecodeError, OSError):  # fmt: skip
        return None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Connect to pgvector, start non-blocking model load, cleanup on shutdown."""
    global _embedder, _repo, _vec_conn, _model_checksum

    _vec_conn = VectorDbConnection(settings)
    pool = _vec_conn.connect()
    ensure_vectordb_schema(pool)
    _repo = SpeciesEmbeddingRepository(pool)
    logger.info("vectordb_ready")

    _embedder = Embedder(
        model_path=settings.model_path,
        input_size=settings.input_size,
        expected_dim=settings.model_dim,
    )
    _embedder.start_load()  # non-blocking; readiness reported via /ready
    _model_checksum = _load_model_checksum()

    logger.info("inference_service_starting", model=settings.model_name)

    yield

    if _vec_conn:
        _vec_conn.close()
    logger.info("inference_service_shutdown")


app = FastAPI(
    title="Kamerplanter Inference Service",
    description="DINOv2 embedding extraction and pgvector species matching",
    version="1.0.0",
    lifespan=lifespan,
)


# -- dependency-style accessors --------------------------------------------


def _require_embedder() -> Embedder:
    if _embedder is None:
        raise HTTPException(status_code=503, detail="Inference service not initialized.")
    return _embedder


def _require_repo() -> SpeciesEmbeddingRepository:
    if _repo is None:
        raise HTTPException(status_code=503, detail="Vector store not initialized.")
    return _repo


async def _read_upload(image: UploadFile) -> bytes:
    """Read an uploaded file, rejecting empty bodies."""
    data = await image.read()
    if not data:
        raise HTTPException(status_code=400, detail="Empty image upload.")
    return data


# -- health / introspection ------------------------------------------------


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    """Liveness probe -- always responds, reports component readiness."""
    model_loaded = _embedder is not None and _embedder.is_ready()
    vectordb = _vec_conn is not None and _vec_conn.is_connected()
    return HealthResponse(
        status="ok" if (model_loaded and vectordb) else "degraded",
        model_loaded=model_loaded,
        vectordb=vectordb,
    )


@app.get("/ready")
def ready() -> dict:
    """Readiness probe -- 503 until the model is loaded and the DB reachable."""
    if _embedder is None or not _embedder.is_ready():
        detail = "model not loaded"
        if _embedder is not None and _embedder.load_error:
            detail = f"model load failed: {_embedder.load_error}"
        raise HTTPException(status_code=503, detail=detail)
    if _vec_conn is None or not _vec_conn.is_connected():
        raise HTTPException(status_code=503, detail="vectordb not reachable")
    return {"status": "ok"}


@app.get("/modelinfo", response_model=ModelInfoResponse)
def modelinfo() -> ModelInfoResponse:
    """Static model metadata (REQ-029-A 3.3)."""
    return ModelInfoResponse(
        model=settings.model_name,
        dim=settings.model_dim,
        input_size=settings.input_size,
        license="Apache-2.0",
        checksum=_model_checksum,
    )


# -- embedding -------------------------------------------------------------


@app.post("/embed", response_model=EmbedResponse)
async def embed(image: UploadFile = File(...)) -> EmbedResponse:
    """Embed a single image -> normalised DINOv2 vector."""
    embedder = _require_embedder()
    data = await _read_upload(image)
    try:
        vector = embedder.embed(data)
    except ModelNotReadyError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return EmbedResponse(
        embedding=vector.tolist(),
        dim=int(vector.shape[0]),
        model=settings.model_name,
    )


@app.post("/embed/batch", response_model=BatchEmbedResponse)
async def embed_batch(images: list[UploadFile] = File(...)) -> BatchEmbedResponse:
    """Embed multiple images (reference indexing path)."""
    embedder = _require_embedder()
    if not images:
        raise HTTPException(status_code=400, detail="No images provided.")
    payloads = [await _read_upload(img) for img in images]
    try:
        vectors = embedder.embed_batch(payloads)
    except ModelNotReadyError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    dim = int(vectors[0].shape[0]) if vectors else settings.model_dim
    return BatchEmbedResponse(
        embeddings=[v.tolist() for v in vectors],
        dim=dim,
        model=settings.model_name,
        count=len(vectors),
    )


# -- matching --------------------------------------------------------------


@app.post("/match", response_model=MatchResponse)
async def match(
    image: UploadFile = File(...),
    k: int = Query(default=5, ge=1, le=50),
) -> MatchResponse:
    """Embed an image and return the top-k matching species with confidence."""
    embedder = _require_embedder()
    repo = _require_repo()
    data = await _read_upload(image)
    try:
        vector = embedder.embed(data)
    except ModelNotReadyError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    matches = repo.match(vector.tolist(), k=k, model=settings.model_name)
    suggestions = [
        MatchSuggestion(
            rank=i + 1,
            species_key=m.species_key,
            scientific_name=m.scientific_name,
            score=round(m.score, 6),
            confidence=cosine_to_confidence(
                m.score,
                auto_accept=settings.confidence_auto_accept,
                show_results=settings.confidence_show_results,
            ),
        )
        for i, m in enumerate(matches)
    ]
    return MatchResponse(
        suggestions=suggestions,
        is_plant=bool(suggestions),
        model=settings.model_name,
    )


# -- reference index management --------------------------------------------


@app.post("/reference", response_model=ReferenceResponse)
async def upsert_reference(
    species_key: str = Form(...),
    scientific_name: str = Form(...),
    source: str = Form(...),
    organ: str | None = Form(default=None),
    source_record_id: str | None = Form(default=None),
    license: str | None = Form(default=None),
    attribution: str | None = Form(default=None),
    source_url: str | None = Form(default=None),
    image: UploadFile | None = File(default=None),
    embedding: str | None = Form(default=None),
) -> ReferenceResponse:
    """Index a reference embedding for a species.

    Accepts EITHER a multipart ``image`` (embedded here) OR a precomputed
    ``embedding`` (JSON array of floats, e.g. produced by /embed/batch). Only
    the vector + provenance are persisted; no original image is stored
    (REQ-029-A 4.4).
    """
    repo = _require_repo()

    if image is not None:
        embedder = _require_embedder()
        data = await _read_upload(image)
        try:
            vector = embedder.embed(data).tolist()
        except ModelNotReadyError as exc:
            raise HTTPException(status_code=503, detail=str(exc)) from exc
    elif embedding is not None:
        try:
            vector = [float(v) for v in json.loads(embedding)]
        except (json.JSONDecodeError, TypeError, ValueError) as exc:
            raise HTTPException(status_code=400, detail="embedding must be a JSON array of floats.") from exc
        if len(vector) != settings.model_dim:
            raise HTTPException(
                status_code=400,
                detail=f"embedding dim {len(vector)} != model dim {settings.model_dim}.",
            )
    else:
        raise HTTPException(status_code=400, detail="Provide either an image or a precomputed embedding.")

    repo.upsert_reference(
        species_key=species_key,
        scientific_name=scientific_name,
        embedding=vector,
        organ=organ,
        model=settings.model_name,
        source=source,
        source_record_id=source_record_id,
        license=license,
        attribution=attribution,
        source_url=source_url,
    )
    return ReferenceResponse(
        status="ok",
        species_key=species_key,
        dim=len(vector),
        model=settings.model_name,
    )


@app.delete("/reference/{species_key}", response_model=DeleteReferenceResponse)
def delete_reference(species_key: str) -> DeleteReferenceResponse:
    """Delete all reference embeddings for a species (re-index support)."""
    repo = _require_repo()
    deleted = repo.delete_by_species(species_key)
    return DeleteReferenceResponse(status="ok", species_key=species_key, deleted=deleted)
