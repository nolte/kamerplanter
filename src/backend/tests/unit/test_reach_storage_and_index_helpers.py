"""The parsing halves of the Art. 17 storage and reference-index reach helpers (#1745).

Sibling of ``test_reach_observation_helpers.py`` and pinned the same way: the
proof of ``scripts/reach/observe_storage_residue.py`` and
``scripts/reach/observe_reference_index.py`` is the real run against the reach
stack; what is pinned here is the part that can be checked without it — reading
a stored JPEG's marker segments, turning measured state into member lines — and
the property every observation helper keeps: **it prints an observation, never a
verdict, and never nothing** (the runner reads silence as *not probed*).

The JPEGs these tests read are real ones. The seed's generator writes them, and
the "stripped" case is the output of the production EXIF stripper, not a
hand-made byte string: an EXIF detector that agreed with a fixture but not with
what the product writes would certify nothing.

Unlike the sibling file, the helpers are loaded per test through a fixture that
first asserts the script exists. ``load_repo_script`` skips the calling module
when a script is missing (a partial checkout), and a skipped module is not a
failing one: a deleted helper would turn these tests silent instead of red.
"""

from __future__ import annotations

import io
import re
from pathlib import Path
from types import ModuleType

import pytest
from PIL import Image

from app.domain.engines.storage.exif_stripper import strip_exif
from tests.support.repo_scripts import find_repo_root, load_repo_script

REPO_ROOT = find_repo_root(Path(__file__).resolve())


def _load(stem: str) -> ModuleType:
    assert REPO_ROOT is not None, "checkout root not found"
    path = REPO_ROOT / "scripts" / f"{stem}.py"
    assert path.is_file(), f"{path} is missing"
    return load_repo_script(stem)


@pytest.fixture(scope="module")
def storage() -> ModuleType:
    return _load("reach/observe_storage_residue")


@pytest.fixture(scope="module")
def seed_files() -> ModuleType:
    return _load("reach/seed_stored_files")


@pytest.fixture(scope="module")
def index() -> ModuleType:
    return _load("reach/observe_reference_index")


@pytest.fixture(scope="module")
def vectordb() -> ModuleType:
    return _load("reach/vectordb")


def _plain_jpeg() -> bytes:
    buffer = io.BytesIO()
    Image.new("RGB", (8, 8), (1, 2, 3)).save(buffer, format="JPEG")
    return buffer.getvalue()


# ── observe_storage_residue: reading a stored JPEG ─────────────────────────


def test_the_seeded_image_carries_exif_with_a_gps_pointer(storage, seed_files):
    data = seed_files.seed_jpeg(0)
    assert storage.jpeg_has_exif(data)
    assert storage.jpeg_has_gps(data)


def test_the_production_stripper_output_reads_as_without_exif(storage, seed_files):
    stripped = strip_exif(seed_files.seed_jpeg(0), "image/jpeg")
    assert not storage.jpeg_has_exif(stripped)
    assert not storage.jpeg_has_gps(stripped)


def test_seed_images_differ_per_category_so_upload_dedup_cannot_merge_them(seed_files):
    assert len({seed_files.seed_jpeg(position) for position in range(12)}) == 12


def test_exif_without_gps_is_still_exif(storage):
    exif = Image.Exif()
    exif[0x010F] = "camera"
    buffer = io.BytesIO()
    Image.new("RGB", (8, 8)).save(buffer, format="JPEG", exif=exif)
    assert storage.jpeg_has_exif(buffer.getvalue())
    assert not storage.jpeg_has_gps(buffer.getvalue())


def test_an_app1_segment_that_is_not_exif_does_not_count(storage):
    plain = _plain_jpeg()
    xmp = b"http://ns.adobe.com/xap/1.0/\x00<x/>"
    segment = b"\xff\xe1" + (len(xmp) + 2).to_bytes(2, "big") + xmp
    assert not storage.jpeg_has_exif(plain[:2] + segment + plain[2:])


def test_exif_bytes_inside_the_entropy_coded_data_do_not_count(storage):
    """Only the header segments before SOS are metadata; scan data is pixels."""
    plain = _plain_jpeg()
    end = plain.rindex(b"\xff\xd9")
    assert not storage.jpeg_has_exif(plain[:end] + b"Exif\x00\x00MM" + plain[end:])


@pytest.mark.parametrize("data", [b"", b"not a jpeg", b"\xff\xd8\xff\xe1\x00"])
def test_bytes_that_are_not_a_readable_jpeg_carry_no_exif(storage, data):
    assert not storage.jpeg_has_exif(data)


# ── observe_storage_residue: members ───────────────────────────────────────


def test_storage_members_name_the_state_of_each_seeded_file(storage):
    findings = [
        storage.Finding("plant", present=True, exif=False, gps=False),
        storage.Finding("diary", present=True, exif=True, gps=True),
        storage.Finding("pest_reference", present=False, exif=False, gps=False),
    ]
    assert storage.members(findings, seeded_total=3) == [
        "exif/diary",
        "deleted/pest_reference",
        "stripped/plant",
        "seeded/3",
    ]


def test_storage_output_is_never_empty(storage):
    assert storage.members([], seeded_total=0) == ["seeded/0"]


def test_inspect_reads_each_file_under_the_storage_root(storage, seed_files, tmp_path):
    (tmp_path / "t" / "k").mkdir(parents=True)
    (tmp_path / "t" / "k" / "a.jpg").write_bytes(seed_files.seed_jpeg(1))
    (tmp_path / "t" / "k" / "b.jpg").write_bytes(strip_exif(seed_files.seed_jpeg(2), "image/jpeg"))
    files = [
        {"category": "diary", "storage_key": "t/k/a.jpg"},
        {"category": "plant", "storage_key": "t/k/b.jpg"},
        {"category": "pest_reference", "storage_key": "t/k/gone.jpg"},
    ]
    assert storage.inspect(tmp_path, files) == [
        storage.Finding("diary", present=True, exif=True, gps=True),
        storage.Finding("plant", present=True, exif=False, gps=False),
        storage.Finding("pest_reference", present=False, exif=False, gps=False),
    ]


def test_a_storage_key_cannot_leave_the_storage_root(storage, tmp_path):
    with pytest.raises(storage.ReachError):
        storage.inspect(tmp_path, [{"category": "diary", "storage_key": "../outside.jpg"}])


def test_the_counts_mode_prints_raw_state(storage):
    findings = [storage.Finding("diary", present=True, exif=True, gps=False)]
    assert storage.count_lines(findings) == ["diary present=1 exif=1 gps=0"]


# ── observe_reference_index ────────────────────────────────────────────────


def test_a_removed_contribution_with_no_attributed_row_left_is_erased(index):
    state = index.IndexState(contributed_present=False, attributed=0, curated_present=True)
    assert index.members(state, seeded_total=2) == ["erased/species_embeddings", "kept/curated", "seeded/2"]


def test_a_surviving_contribution_is_residue_with_its_attributed_count(index):
    state = index.IndexState(contributed_present=True, attributed=1, curated_present=True)
    assert index.members(state, seeded_total=2) == ["residue/species_embeddings=1", "kept/curated", "seeded/2"]


def test_a_contribution_kept_without_its_attribution_is_still_residue(index):
    """The vector survives with ``contributed_by`` cleared: not erased, zero rows attributed."""
    state = index.IndexState(contributed_present=True, attributed=0, curated_present=True)
    assert index.members(state, seeded_total=2)[0] == "residue/species_embeddings=0"


def test_another_attributed_row_keeps_the_index_from_counting_as_erased(index):
    state = index.IndexState(contributed_present=False, attributed=2, curated_present=False)
    assert index.members(state, seeded_total=2) == ["residue/species_embeddings=2", "deleted/curated", "seeded/2"]


@pytest.mark.parametrize(
    ("line", "expected"),
    [("t|1|t", (True, 1, True)), ("f|0|f", (False, 0, False)), ("f|3|t\n", (False, 3, True))],
)
def test_parse_state_reads_the_one_psql_row(index, line, expected):
    assert index.parse_state(line) == index.IndexState(*expected)


@pytest.mark.parametrize("line", ["", "t|1", "x|1|t", "t|n|t"])
def test_parse_state_refuses_an_answer_it_cannot_read(index, line):
    with pytest.raises(index.ReachError):
        index.parse_state(line)


# ── vectordb: the seeded rows ──────────────────────────────────────────────


def test_the_vector_literal_is_384_finite_components_and_deterministic(vectordb):
    literal = vectordb.vector_literal("reach")
    assert literal == vectordb.vector_literal("reach")
    assert literal != vectordb.vector_literal("curated")
    components = [float(value) for value in literal.strip("[]").split(",")]
    assert len(components) == 384
    assert abs(sum(value * value for value in components) - 1.0) < 1e-6


def test_the_seed_row_uses_exactly_the_columns_the_inference_service_writes(vectordb):
    """The contributed row has the shape ``upsert_reference`` writes; a drift there breaks this."""
    assert REPO_ROOT is not None
    source = (REPO_ROOT / "src/inference-service/app/vectordb/repository.py").read_text(encoding="utf-8")
    match = re.search(r"INSERT INTO species_embeddings\s*\(([^)]*)\)", source)
    assert match is not None
    written = [name.strip() for name in match.group(1).split(",")]
    # contributed_at is set by the repository from the clock; the seed sets it with now().
    assert list(vectordb.CONTRIBUTION_COLUMNS) == written


def test_the_seed_sql_takes_subject_and_tenant_as_psql_variables_not_text(vectordb):
    sql = vectordb.SEED_SQL
    assert ":'subject'" in sql and ":'tenant_key'" in sql
    assert "reach-subject" not in sql
