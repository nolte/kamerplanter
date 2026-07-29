"""Inference Service -- DINOv2 embedding extraction + pgvector species matching.

Internal (ClusterIP) microservice. NOT publicly exposed. Owns the
species_embeddings pgvector table and the ONNX DINOv2 model. Backend talks to
it over HTTP only (REQ-029-A 3.1, plan D-3).
"""

import json
from contextlib import asynccontextmanager
from pathlib import Path

import structlog
from fastapi import Depends, FastAPI, File, Form, HTTPException, Query, UploadFile

from app.auth import check_insecure_config, require_service_token
from app.confidence import cosine_to_confidence
from app.config import settings
from app.disease_classifier import DiseaseClassifier, DiseaseModelNotReadyError
from app.embedder import Embedder, ModelNotReadyError
from app.observability.error_tracking import init_error_tracking, resolve_release
from app.phenotype_engine import PhenotypeEngine, PhenotypeUnavailableError
from app.schemas import (
    BatchEmbedResponse,
    DeleteReferenceResponse,
    DiseaseClassificationItem,
    DiseaseClassifyResponse,
    DiseaseModelMeta,
    DiseaseStatusResponse,
    EmbedResponse,
    HealthResponse,
    MatchResponse,
    MatchSuggestion,
    ModelInfoResponse,
    PestCoverageItem,
    PestCoverageResponse,
    PestDetectResponse,
    PestFindingItem,
    PestPrototypeItem,
    PestPrototypeListResponse,
    PestReferenceResponse,
    PestSetActiveRequest,
    PestSetActiveResponse,
    PestStatusResponse,
    PhenotypeMetricsItem,
    ReferenceImageItem,
    ReferenceListResponse,
    ReferenceResponse,
    SetReferenceActiveRequest,
    SetReferenceActiveResponse,
)
from app.vectordb.config import VectorDbConfig
from app.vectordb.connection import VectorDbConnection
from app.vectordb.pest_repository import PestEmbeddingRepository
from app.vectordb.repository import SpeciesEmbeddingRepository
from app.vectordb.schema import run_migrations

logger = structlog.get_logger(__name__)

#: Single source for the version reported to OpenAPI and used as the release
#: fallback, so the two can never disagree about which build is running.
SERVICE_VERSION = "1.0.0"

# Optional error tracking (#777), at process entry and before any request is
# served. No-op without SENTRY_DSN.
init_error_tracking(
    component="inference-service",
    release=resolve_release("kamerplanter-inference-service", SERVICE_VERSION),
)

_VECTORDB_MIGRATIONS_DIR = Path(__file__).resolve().parent / "vectordb" / "migrations"

# REQ-038 -- a CV diagnosis is ALWAYS a hypothesis, never an accepted verdict. An
# automated test asserts this string is non-empty and present on every response.
DEFAULT_DISEASE_DISCLAIMER = (
    "Nur eine Einschätzung der Bilderkennung — keine gesicherte Diagnose. "
    "Bitte den Verdacht fachlich prüfen, bevor du behandelst; bei Unsicherheit "
    "einen zweiten Blick einholen."
)

_embedder: Embedder | None = None
_repo: SpeciesEmbeddingRepository | None = None
_pest_repo: PestEmbeddingRepository | None = None
_vec_conn: VectorDbConnection | None = None
_model_checksum: str | None = None
_disease_classifier: DiseaseClassifier | None = None
_phenotype_engine: PhenotypeEngine | None = None
_disease_model_meta: dict | None = None


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


def _load_disease_model_meta() -> dict:
    """Read the REQ-038 model card from ``diseasemodelinfo.json`` (never bakes in defaults).

    PlantVillage is deliberately excluded from the provenance card; the loader
    surfaces whatever the mounted artifact declares. Missing file => empty card.
    """
    info_path = Path(settings.disease_model_path) / "diseasemodelinfo.json"
    if not info_path.exists():
        return {}
    try:
        return json.loads(info_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        logger.warning("disease_model_meta_unreadable", path=str(info_path), error=str(exc))
        return {}


def _build_disease_model_meta(class_count: int) -> DiseaseModelMeta:
    """Compose the response model card from the sidecar + live class count."""
    meta = _disease_model_meta or {}
    return DiseaseModelMeta(
        model_name=meta.get("model_name", settings.disease_model_name),
        training_base=meta.get("training_base"),
        fine_tuned_on=meta.get("fine_tuned_on", []),
        onnx_checksum=meta.get("onnx_checksum") or meta.get("checksum") or meta.get("sha256"),
        model_version=meta.get("model_version"),
        class_count=class_count,
    )


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Connect to pgvector, start non-blocking model load, cleanup on shutdown."""
    global _embedder, _repo, _pest_repo, _vec_conn, _model_checksum

    # Fail-fast on default/missing secrets before touching any dependency (AP-4,
    # INF-S4). Skipped in debug mode for local development / tests.
    if not settings.debug:
        insecure = check_insecure_config()
        if insecure:
            logger.critical("insecure_defaults", fields=insecure)
            raise SystemExit(
                "FATAL: Default or missing secrets detected for: "
                f"{', '.join(insecure)}. Set proper values via environment "
                "variables before running in production."
            )

    _vec_conn = VectorDbConnection(
        VectorDbConfig(
            host=settings.vectordb_host,
            port=settings.vectordb_port,
            database=settings.vectordb_database,
            username=settings.vectordb_username,
            password=settings.vectordb_password,
            pool_min_size=settings.vectordb_pool_min_size,
            pool_max_size=settings.vectordb_pool_max_size,
        )
    )
    pool = _vec_conn.connect()
    run_migrations(pool, _VECTORDB_MIGRATIONS_DIR, migrations_table="inference_schema_migrations")
    _repo = SpeciesEmbeddingRepository(pool)
    _pest_repo = PestEmbeddingRepository(pool)
    logger.info("vectordb_ready")

    _embedder = Embedder(
        model_path=settings.model_path,
        input_size=settings.input_size,
        expected_dim=settings.model_dim,
    )
    _embedder.start_load()  # non-blocking; readiness reported via /ready
    _model_checksum = _load_model_checksum()

    # REQ-038 -- optional disease classifier + phenotype pipeline. Both degrade
    # gracefully: the classifier only starts loading when explicitly enabled, and
    # the phenotype engine probes PlantCV lazily. Neither blocks startup.
    global _disease_classifier, _phenotype_engine, _disease_model_meta
    _phenotype_engine = PhenotypeEngine(enabled=settings.phenotype_enabled)
    if settings.disease_classifier_enabled:
        _disease_classifier = DiseaseClassifier(
            model_path=settings.disease_model_path,
            input_size=settings.disease_input_size,
        )
        _disease_classifier.start_load()  # non-blocking
        _disease_model_meta = _load_disease_model_meta()
        logger.info("disease_classifier_enabled", model=settings.disease_model_name)

    logger.info("inference_service_starting", model=settings.model_name)

    yield

    if _vec_conn:
        _vec_conn.close()
    logger.info("inference_service_shutdown")


app = FastAPI(
    title="Kamerplanter Inference Service",
    description="DINOv2 embedding extraction and pgvector species matching",
    version=SERVICE_VERSION,
    lifespan=lifespan,
    # Service-token auth on every route; the dependency exempts probe paths
    # (/health, /ready) so kubelet checks keep working (AP-4, INF-S2).
    dependencies=[Depends(require_service_token)],
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


def _require_pest_repo() -> PestEmbeddingRepository:
    if _pest_repo is None:
        raise HTTPException(status_code=503, detail="Pest vector store not initialized.")
    return _pest_repo


async def _read_upload(image: UploadFile) -> bytes:
    """Read an uploaded file, rejecting empty bodies."""
    data = await image.read()
    if not data:
        raise HTTPException(status_code=400, detail="Empty image upload.")
    return data


async def _resolve_vector(image: UploadFile | None, embedding: str | None) -> list[float]:
    """Resolve an embedding vector for a reference upsert (shared trust boundary).

    Accepts EITHER an uploaded ``image`` (embedded here) OR a precomputed
    ``embedding`` (JSON array of floats). The single source of truth for the
    /reference and /pest/reference endpoints:

    - image path -> embed the bytes, mapping ``ModelNotReadyError`` to 503;
    - embedding path -> parse the JSON array (malformed input -> 400) and
      validate its length against ``settings.model_dim`` (mismatch -> 400);
    - neither supplied -> 400.
    """
    if image is not None:
        embedder = _require_embedder()
        data = await _read_upload(image)
        try:
            return embedder.embed(data).tolist()
        except ModelNotReadyError as exc:
            raise HTTPException(status_code=503, detail=str(exc)) from exc
    if embedding is not None:
        try:
            vector = [float(v) for v in json.loads(embedding)]
        except (json.JSONDecodeError, TypeError, ValueError) as exc:
            raise HTTPException(status_code=400, detail="embedding must be a JSON array of floats.") from exc
        if len(vector) != settings.model_dim:
            raise HTTPException(
                status_code=400,
                detail=f"embedding dim {len(vector)} != model dim {settings.model_dim}.",
            )
        return vector
    raise HTTPException(status_code=400, detail="Provide either an image or a precomputed embedding.")


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
    is_active: bool = Form(default=True),
    contributed_by: str | None = Form(default=None),
    tenant_key: str | None = Form(default=None),
    image: UploadFile | None = File(default=None),
    embedding: str | None = Form(default=None),
) -> ReferenceResponse:
    """Index a reference embedding for a species.

    Accepts EITHER a multipart ``image`` (embedded here) OR a precomputed
    ``embedding`` (JSON array of floats, e.g. produced by /embed/batch). Only
    the vector + provenance are persisted; no original image is stored
    (REQ-029-A 4.4).

    ``is_active=False`` writes the row quarantined (SEC-001, issue #447): it is
    excluded from ``/match`` until a platform admin activates it. ``contributed_by``
    / ``tenant_key`` record the provenance of an interactive user contribution so
    it can be attributed and GDPR-erased (SEC-005).
    """
    repo = _require_repo()

    vector = await _resolve_vector(image, embedding)

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
        is_active=is_active,
        contributed_by=contributed_by,
        tenant_key=tenant_key,
    )
    return ReferenceResponse(
        status="ok",
        species_key=species_key,
        dim=len(vector),
        model=settings.model_name,
    )


@app.get("/reference/{species_key}", response_model=ReferenceListResponse)
def list_references(
    species_key: str,
    limit: int = Query(50, ge=1, le=200),
    active_only: bool = Query(False),
    include_contributions: bool = Query(False),
) -> ReferenceListResponse:
    """List stored reference image provenance for a species (gallery source).

    Returns only id + URL + license/attribution/curation metadata — never
    embeddings. With ``active_only`` the deselected images are omitted (public
    gallery); without it all images are returned with their ``is_active`` flag
    so the admin curation view can offer re-inclusion.

    With ``include_contributions`` (admin curation only) the quarantined user
    contributions (``source='user_contributed'``, no ``source_url``) are also
    surfaced with their provenance so a platform admin can activate/reject them
    (issue #447) — otherwise they would be invisible and could never leave the
    quarantine.
    """
    repo = _require_repo()
    rows = repo.list_by_species(
        species_key,
        limit=limit,
        active_only=active_only,
        include_contributions=include_contributions,
    )
    images = [ReferenceImageItem(**row) for row in rows]
    return ReferenceListResponse(species_key=species_key, count=len(images), images=images)


@app.patch(
    "/reference/{species_key}/{embedding_id}",
    response_model=SetReferenceActiveResponse,
)
def set_reference_active(
    species_key: str,
    embedding_id: int,
    body: SetReferenceActiveRequest,
) -> SetReferenceActiveResponse:
    """Activate/deactivate one reference image (manual curation, REQ-029-A).

    Deactivated images are kept (audit trail) but filtered out of /match.
    """
    repo = _require_repo()
    updated = repo.set_active(
        species_key,
        embedding_id,
        is_active=body.is_active,
        reason=body.reason,
    )
    if not updated:
        raise HTTPException(status_code=404, detail="Reference image not found.")
    return SetReferenceActiveResponse(
        status="ok",
        species_key=species_key,
        id=embedding_id,
        is_active=body.is_active,
    )


@app.delete("/reference/{species_key}", response_model=DeleteReferenceResponse)
def delete_reference(species_key: str) -> DeleteReferenceResponse:
    """Delete all reference embeddings for a species (re-index support)."""
    repo = _require_repo()
    deleted = repo.delete_by_species(species_key)
    return DeleteReferenceResponse(status="ok", species_key=species_key, deleted=deleted)


# -- REQ-044 pest few-shot (frozen DINOv2, no separate model) --------------


@app.get("/pest/ready")
def pest_ready() -> dict:
    """Readiness for pest detection -- 503 until model + DB are up."""
    if _embedder is None or not _embedder.is_ready():
        raise HTTPException(status_code=503, detail="model not loaded")
    if _vec_conn is None or not _vec_conn.is_connected():
        raise HTTPException(status_code=503, detail="vectordb not reachable")
    return {"status": "ok"}


@app.get("/pest/status", response_model=PestStatusResponse)
def pest_status() -> PestStatusResponse:
    """Report whether the pest few-shot index is populated."""
    model_ready = _embedder is not None and _embedder.is_ready()
    db_ready = _vec_conn is not None and _vec_conn.is_connected()
    count = _pest_repo.count() if (_pest_repo is not None and db_ready) else 0
    return PestStatusResponse(ready=bool(model_ready and db_ready), index_count=count, model=settings.model_name)


@app.post("/pest/detect", response_model=PestDetectResponse)
async def pest_detect(
    image: UploadFile = File(...),
    mode: str = Query(default="symptom"),
    language: str = Query(default="de"),
    k: int = Query(default=3, ge=1, le=10),
) -> PestDetectResponse:
    """Classify one tile against the few-shot prototype index (Modus 2).

    Returns calibrated findings above the cosine floor; the backend applies the
    final abstention gate and bounding-box merge. No image is persisted.
    """
    embedder = _require_embedder()
    pest_repo = _require_pest_repo()
    data = await _read_upload(image)
    try:
        vector = embedder.embed(data)
    except ModelNotReadyError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    matches = pest_repo.classify(vector.tolist(), k=k, model=settings.model_name)
    findings: list[PestFindingItem] = []
    for m in matches:
        if m.score < settings.pest_show_results:
            continue
        findings.append(
            PestFindingItem(
                label=m.label,
                category=m.category,
                score=round(m.score, 6),
                confidence=cosine_to_confidence(
                    m.score,
                    auto_accept=settings.confidence_auto_accept,
                    show_results=settings.confidence_show_results,
                ),
                mode=mode,
            )
        )
    return PestDetectResponse(findings=findings, model=settings.model_name)


@app.post("/pest/reference", response_model=PestReferenceResponse)
async def upsert_pest_reference(
    label: str = Form(...),
    category: str = Form(...),
    source: str = Form(...),
    source_record_id: str | None = Form(default=None),
    license: str | None = Form(default=None),
    attribution: str | None = Form(default=None),
    source_url: str | None = Form(default=None),
    image: UploadFile | None = File(default=None),
    embedding: str | None = Form(default=None),
) -> PestReferenceResponse:
    """Index one few-shot prototype for a pest/symptom/beneficial class.

    Accepts EITHER a multipart ``image`` (embedded here) OR a precomputed
    ``embedding`` (JSON array). Only the vector + provenance are stored; no
    original image is persisted.
    """
    pest_repo = _require_pest_repo()

    vector = await _resolve_vector(image, embedding)

    pest_repo.upsert_prototype(
        label=label,
        category=category,
        embedding=vector,
        model=settings.model_name,
        source=source,
        source_record_id=source_record_id,
        license=license,
        attribution=attribution,
        source_url=source_url,
    )
    return PestReferenceResponse(
        status="ok",
        label=label,
        category=category,
        dim=len(vector),
        model=settings.model_name,
    )


@app.get("/pest/coverage", response_model=PestCoverageResponse)
def pest_coverage() -> PestCoverageResponse:
    """Per-class prototype counts (gallery/coverage source)."""
    pest_repo = _require_pest_repo()
    rows = pest_repo.coverage()
    return PestCoverageResponse(classes=[PestCoverageItem(**row) for row in rows])


@app.get("/pest/reference/{label}", response_model=PestPrototypeListResponse)
def list_pest_references(
    label: str,
    limit: int = Query(200, ge=1, le=500),
    active_only: bool = Query(False),
) -> PestPrototypeListResponse:
    """List stored prototype provenance for a class (gallery source, no embeddings)."""
    pest_repo = _require_pest_repo()
    rows = pest_repo.list_by_label(label, limit=limit, active_only=active_only)
    images = [PestPrototypeItem(**row) for row in rows]
    active = sum(1 for img in images if img.is_active)
    return PestPrototypeListResponse(label=label, count=len(images), active_count=active, images=images)


@app.patch("/pest/reference/{label}/{prototype_id}", response_model=PestSetActiveResponse)
def set_pest_reference_active(label: str, prototype_id: int, body: PestSetActiveRequest) -> PestSetActiveResponse:
    """Activate/deactivate one prototype (manual curation)."""
    pest_repo = _require_pest_repo()
    updated = pest_repo.set_active(label, prototype_id, is_active=body.is_active, reason=body.reason)
    if not updated:
        raise HTTPException(status_code=404, detail="Prototype not found.")
    return PestSetActiveResponse(status="ok", label=label, id=prototype_id, is_active=body.is_active)


@app.delete("/pest/reference/{label}", response_model=DeleteReferenceResponse)
def delete_pest_reference(label: str) -> DeleteReferenceResponse:
    """Delete all prototypes for a class (re-index support)."""
    pest_repo = _require_pest_repo()
    deleted = pest_repo.delete_by_label(label)
    return DeleteReferenceResponse(status="ok", species_key=label, deleted=deleted)


# -- REQ-038 disease classifier + PlantCV phenotype ------------------------


def _require_disease_classifier() -> DiseaseClassifier:
    """Return the disease classifier or 503 when disabled / not loaded.

    Kept a hard 503 (not a silent empty result) so the backend can distinguish
    "feature off" from "no disease found" and surface the right message.
    """
    if _disease_classifier is None:
        raise HTTPException(status_code=503, detail="Disease classifier is disabled.")
    if not _disease_classifier.is_ready():
        detail = "disease model not loaded"
        if _disease_classifier.load_error:
            detail = f"disease model unavailable: {_disease_classifier.load_error}"
        raise HTTPException(status_code=503, detail=detail)
    return _disease_classifier


@app.get("/disease/ready")
def disease_ready() -> dict:
    """Readiness for disease classification -- 503 until the model is loaded."""
    _require_disease_classifier()
    return {"status": "ok"}


@app.get("/disease/status", response_model=DiseaseStatusResponse)
def disease_status() -> DiseaseStatusResponse:
    """Report classifier availability without failing (admin/status card source)."""
    enabled = _disease_classifier is not None
    ready = _disease_classifier is not None and _disease_classifier.is_ready()
    class_count = _disease_classifier.class_count if (_disease_classifier is not None and ready) else 0
    detail = None
    if _disease_classifier is not None and not ready and _disease_classifier.load_error:
        detail = _disease_classifier.load_error
    phenotype_available = _phenotype_engine is not None and _phenotype_engine.is_available()
    return DiseaseStatusResponse(
        ready=ready,
        enabled=enabled,
        class_count=class_count,
        phenotype_available=phenotype_available,
        model=settings.disease_model_name,
        detail=detail,
    )


@app.post("/classify/disease", response_model=DiseaseClassifyResponse)
async def classify_disease(
    image: UploadFile = File(...),
    k: int = Query(default=5, ge=1, le=20),
    phenotype: bool = Query(default=False),
) -> DiseaseClassifyResponse:
    """Classify one image against the disease/deficiency head.

    Returns the top-k classes above the configured softmax floor, an optional
    PlantCV phenotype block, the model card and an always-present disclaimer. No
    image is persisted here -- the backend owns request storage and EXIF-strip.
    """
    classifier = _require_disease_classifier()
    data = await _read_upload(image)
    try:
        results = classifier.classify(data, k=k)
    except DiseaseModelNotReadyError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    classifications = [
        DiseaseClassificationItem(
            label=r.label,
            category=r.category,
            scientific_name=r.scientific_name,
            probability=r.probability,
            highlight=r.probability >= settings.disease_highlight,
        )
        for r in results
        if r.probability >= settings.disease_show_results
    ]

    phenotype_item: PhenotypeMetricsItem | None = None
    if phenotype and _phenotype_engine is not None and _phenotype_engine.is_available():
        try:
            metrics = _phenotype_engine.measure(data)
            phenotype_item = PhenotypeMetricsItem(
                leaf_area_px=metrics.leaf_area_px,
                green_index=metrics.green_index,
                discolored_area_ratio=metrics.discolored_area_ratio,
                necrotic_area_ratio=metrics.necrotic_area_ratio,
                solidity=metrics.solidity,
                hue_circular_mean_deg=metrics.hue_circular_mean_deg,
                plantcv_version=metrics.plantcv_version,
            )
        except PhenotypeUnavailableError:
            phenotype_item = None
        except Exception as exc:  # noqa: BLE001 -- phenotype is best-effort, never fatal
            logger.warning("phenotype_measurement_failed", reason=str(exc))
            phenotype_item = None

    return DiseaseClassifyResponse(
        classifications=classifications,
        model_meta=_build_disease_model_meta(classifier.class_count),
        phenotype=phenotype_item,
        disclaimer=DEFAULT_DISEASE_DISCLAIMER,
    )
