#!/usr/bin/env python3
"""Compute the golden outputs of one pinned model image (#1763).

    scripts/ci/compute_model_golden_outputs.py embedding <target> <image>
    scripts/ci/compute_model_golden_outputs.py reranker <target> <image>

writes ``docker/<kind>-service/golden/<target>.json``, the file
``scripts/ci/probe_model_service_contract.py`` compares a running image
against. Run it only when a ``revision=`` pin in ``docker/<kind>-service/Dockerfile``
changes — the guard
``src/backend/tests/unit/guards/test_model_golden_outputs_match_pins.py`` fails
until the golden file names the new pin and the new sha256 values.

HOW THE VALUES ARE COMPUTED — AND WHY NOT BY ASKING THE SERVICE. The golden
values must be right independently of the code they check, or a defect in that
code is written into the file that is meant to catch it. So this script does
not call ``/embed`` or ``/rerank``. It starts the image with its entrypoint
replaced and runs ``REFERENCE`` below inside it: the model files the image
ships (the bytes the Dockerfile's ``sha256sum -c`` verified), loaded with
``tokenizers.Tokenizer.from_file`` and ``onnxruntime`` directly, one input per
``session.run`` with ONE intra-op thread, then:

- embedding: mean pooling over the attention mask and L2 normalisation — the
  pooling every one of the four models was published with (the
  sentence-transformers ``1_Pooling/config.json`` of each source repository:
  ``pooling_mode_mean_tokens``);
- reranker: the pair's single logit. The service answers ``sigmoid(logit)``;
  the probe inverts that (``log(s) - log1p(-s)``) and compares logits, because
  the sigmoid squashes every clearly irrelevant document to ~1e-5, where an
  absolute tolerance on the score could not tell -11 from -9.

None of ``main.py``, ``feed.py`` or ``tokenization.py`` is imported. The
reference shares only the libraries with the service; the one-time cross-check
against the model authors' PyTorch weights recorded in each file's
``reference_check`` block is what shows the libraries are right too.

The fixed inputs are ``EMBEDDING_CASES`` / ``RERANKER_CASES``: a normal English
sentence, a German one (the language the pre-#1758 MiniLM image turned into
``<unk>``), a mixed-language one, and a text past the 512-token window, whose
untruncated token count is recorded so the guard can check it still exceeds
512 for that model's tokenizer.

Standard library only on the host, like the probe it feeds; it imports the
probe's reduction so the stored view and the compared view cannot drift.

THE ONE-TIME CROSS-CHECK. ``reference-check`` recomputes the same inputs from
the model authors' PyTorch weights — sentence-transformers for the embedding
models, ``AutoModelForSequenceClassification`` for the rerankers, both through
transformers 4.57.6 (the last line whose tokenizer the #1758 measurement found
identical to ``tokenizers`` for every model) — and records the max |Δ| against
the stored values in the file's ``reference_check`` block. It needs torch, so it
runs from a throwaway environment, never in CI::

    uv venv /tmp/xcheck && VIRTUAL_ENV=/tmp/xcheck uv pip install \
        --index-url https://download.pytorch.org/whl/cpu torch
    VIRTUAL_ENV=/tmp/xcheck uv pip install transformers==4.57.6 sentence-transformers==5.1.2
    /tmp/xcheck/bin/python scripts/ci/compute_model_golden_outputs.py \
        reference-check embedding minilm sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2 <sha>

``<source repository>`` is where the PyTorch weights live: the pinned repository
itself for the e5 models and ms-marco (the same commit carries both exports),
the original the ONNX export was made from for MiniLM (Xenova's) and bge
(onnx-community's).
"""

from __future__ import annotations

import datetime
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

import probe_model_service_contract as probe

#: The long input. ~15 tokens a sentence in every shipped tokenizer, 48 times:
#: well past 512 tokens (the count is measured and stored per model), well under
#: the 16384-character bound of docker/*/limits.py.
_LONG_SENTENCES = (
    "Die Wurzeln einer Tomatenpflanze brauchen Luft, Wasser und Nährstoffe im Substrat. "
    "Roots of a tomato plant need air, water and nutrients in the growing medium. "
    "Staunässe verdrängt den Sauerstoff, und die Feinwurzeln sterben ab. "
)
LONG_TEXT = (_LONG_SENTENCES * 16).strip()

EMBEDDING_CASES: list[dict[str, str]] = [
    {"name": "normal-en", "text": "Tomato plants need deep, regular watering while their fruit is setting."},
    {"name": "german", "text": "Tomaten sind Starkzehrer und brauchen während der Fruchtbildung viel Kalium."},
    {
        "name": "multilingual",
        "text": "Basil (Ocimum basilicum) liebt Wärme; el suelo debe drenar bien et rester légèrement humide.",
    },
    {"name": "long-over-512-tokens", "text": LONG_TEXT},
]

RERANKER_CASES: list[dict[str, Any]] = [
    {
        "name": "normal-en",
        "query": "How often should I water my tomato plants?",
        "documents": [
            "Car engines need regular oil changes to keep running smoothly.",
            "Tomato plants need deep, regular watering, especially while their fruit is setting.",
            "The stock market closed higher on Friday after a volatile week.",
        ],
    },
    {
        "name": "german",
        "query": "Wie oft muss ich Tomaten gießen?",
        "documents": [
            "Tomaten sollten gleichmäßig und durchdringend gegossen werden, am besten morgens.",
            "Der Motor des Autos ist kaputt und muss in die Werkstatt.",
            "Tomatoes should be watered deeply and evenly, ideally in the morning.",
        ],
    },
    {
        "name": "long-over-512-tokens",
        "query": "Warum sterben die Wurzeln bei Staunässe ab?",
        "documents": [LONG_TEXT, "Die Börse schloss am Freitag im Plus."],
    },
]

#: Runs INSIDE the image (its own interpreter and wheels), reading
#: {"kind", "model_dir", "cases", "prefix"} on stdin and printing one JSON object.
REFERENCE = r"""
import hashlib, json, pathlib, sys
import numpy as np, onnxruntime as ort, tokenizers
spec = json.load(sys.stdin)
model_dir = pathlib.Path(spec["model_dir"])
tokenizer = tokenizers.Tokenizer.from_file(str(model_dir / "tokenizer.json"))
untruncated = tokenizers.Tokenizer.from_file(str(model_dir / "tokenizer.json"))
untruncated.no_truncation()
tokenizer.enable_truncation(max_length=512)
options = ort.SessionOptions()
options.intra_op_num_threads = 1
options.inter_op_num_threads = 1
session = ort.InferenceSession(str(model_dir / "model.onnx"), options, providers=["CPUExecutionProvider"])
names = [graph_input.name for graph_input in session.get_inputs()]
fields = {"input_ids": "ids", "attention_mask": "attention_mask", "token_type_ids": "type_ids"}

def feed(encoding, zero_types):
    feed = {}
    for name in names:
        values = getattr(encoding, fields[name])
        if name == "token_type_ids" and zero_types:
            values = [0] * len(values)
        feed[name] = np.asarray([values], dtype=np.int64)
    return feed

outputs, tokens = [], []
for case in spec["cases"]:
    if spec["kind"] == "embedding":
        text = spec["prefix"] + case["text"]
        encoding = tokenizer.encode(text)
        hidden = session.run(None, feed(encoding, zero_types=True))[0][0]
        mask = np.asarray(encoding.attention_mask, dtype=np.float32)[:, None]
        pooled = (hidden * mask).sum(axis=0) / mask.sum()
        outputs.append((pooled / np.linalg.norm(pooled)).astype(np.float32).tolist())
        tokens.append(len(untruncated.encode(text).ids))
    else:
        scores, counts = [], []
        for document in case["documents"]:
            encoding = tokenizer.encode(case["query"], document)
            logit = np.asarray(session.run(None, feed(encoding, zero_types=False))[0]).reshape(-1)[0]
            scores.append(float(logit))
            counts.append(len(untruncated.encode(case["query"], document).ids))
        outputs.append(scores)
        tokens.append(max(counts))
files = {
    path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in sorted(model_dir.iterdir()) if path.is_file()
}
cpu = next(
    (line.split(":", 1)[1].strip() for line in open("/proc/cpuinfo") if line.startswith("model name")), "unknown"
)
print(json.dumps({
    "outputs": outputs,
    "untruncated_tokens": tokens,
    "files_sha256": files,
    "runtime": {"onnxruntime": ort.__version__, "tokenizers": tokenizers.__version__, "numpy": np.__version__},
    "cpu": cpu,
}))
"""

_STAGE = re.compile(r"^FROM\s+\S+\s+AS\s+(?P<stage>\S+)\s*$", re.IGNORECASE | re.MULTILINE)


def dockerfile_stages(text: str) -> dict[str, str]:
    """``{stage name: the text of that stage}`` for every named ``FROM ... AS`` stage."""
    matches = list(_STAGE.finditer(text))
    return {
        match.group("stage"): text[match.end() : matches[i + 1].start() if i + 1 < len(matches) else len(text)]
        for i, match in enumerate(matches)
    }


def pin_of(kind: str, target: str) -> dict[str, Any]:
    """What the Dockerfile pins for *target*: model name, download stage, repository, revision, file hashes."""
    dockerfile = probe.REPO_ROOT / "docker" / f"{kind}-service" / "Dockerfile"
    stages = dockerfile_stages(dockerfile.read_text(encoding="utf-8"))
    if target not in stages:
        raise SystemExit(f"{dockerfile} has no stage {target!r} (stages: {sorted(stages)})")
    final = stages[target]
    model = re.search(rf"^ENV\s+{probe.MODEL_ENV[kind]}=(\S+)\s*$", final, re.MULTILINE)
    source = re.search(r"^COPY\s+--from=(\S+)\s+/model/", final, re.MULTILINE)
    if model is None or source is None:
        raise SystemExit(f"stage {target!r} sets no {probe.MODEL_ENV[kind]} or copies no /model/ from a stage")
    download = stages[source.group(1)]
    repo = re.search(r"repo_id='([^']+)'", download)
    revision = re.search(r"revision='([0-9a-f]{40})'", download)
    hashes = {name: digest for digest, name in re.findall(r"([0-9a-f]{64})\s+/model/([^\s'\"]+)", download)}
    if repo is None or revision is None or not hashes:
        raise SystemExit(f"download stage {source.group(1)!r} carries no repo_id / 40-hex revision / sha256 lines")
    return {
        "model": model.group(1),
        "download_stage": source.group(1),
        "repo_id": repo.group(1),
        "revision": revision.group(1),
        "files_sha256": dict(sorted(hashes.items())),
    }


def run_reference(image: str, kind: str, model: str, cases: list[dict[str, Any]], prefix: str) -> dict[str, Any]:
    """Run ``REFERENCE`` inside *image* — hardened, offline — and return its JSON."""
    spec = {"kind": kind, "model_dir": f"/app/models/onnx/{model}", "cases": cases, "prefix": prefix}
    command = ["docker", "run", "--rm", "-i", "--network", "none", *probe.HARDENED_RUN]
    command += ["--entrypoint", "python", image, "-c", REFERENCE]
    result = subprocess.run(command, input=json.dumps(spec), capture_output=True, text=True, timeout=900, check=False)
    if result.returncode != 0:
        raise SystemExit(f"the reference computation failed in {image}:\n{result.stderr}")
    return json.loads(result.stdout)


def _compact_number_lists(text: str) -> str:
    """Put every list of plain numbers on one line — the file stays diffable and small."""
    return re.sub(
        r"\[\s*(-?[0-9][^\[\]{}\"]*?)\s*\]",
        lambda match: "[" + ", ".join(part.strip() for part in match.group(1).split(",")) + "]",
        text,
    )


def _write_golden(path: Path, golden: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(_compact_number_lists(json.dumps(golden, indent=2, ensure_ascii=False)) + "\n", encoding="utf-8")


def reference_check(kind: str, target: str, source_repo: str, source_revision: str) -> int:
    """Recompute the golden inputs from the PyTorch weights and record the max |Δ| (see module docstring)."""
    import torch
    import transformers

    path = probe.GOLDEN_DIRS[kind] / f"{target}.json"
    golden = json.loads(path.read_text(encoding="utf-8"))
    cases = golden["cases"]
    deviation = 0.0
    with torch.inference_mode():
        if kind == "embedding":
            import sentence_transformers

            model = sentence_transformers.SentenceTransformer(source_repo, revision=source_revision, device="cpu")
            # The service's window (tokenization.MAX_LENGTH), not the model
            # card's: the comparison is of the same computation.
            model.max_seq_length = 512
            library = f"sentence-transformers {sentence_transformers.__version__}"
            for case in cases:
                vector = model.encode(golden["prefix"] + case["text"], normalize_embeddings=True).tolist()
                reduced = probe.reduce_embedding(vector)
                deviation = max(
                    deviation,
                    probe.max_deviation(case["sample"], reduced["sample"]),
                    probe.max_deviation(case["projection"], reduced["projection"]),
                )
        else:
            tokenizer = transformers.AutoTokenizer.from_pretrained(source_repo, revision=source_revision)
            model = transformers.AutoModelForSequenceClassification.from_pretrained(
                source_repo, revision=source_revision
            ).eval()
            library = "AutoModelForSequenceClassification"
            for case in cases:
                logits = []
                for document in case["documents"]:
                    encoded = tokenizer(case["query"], document, truncation=True, max_length=512, return_tensors="pt")
                    logits.append(float(model(**encoded).logits.reshape(-1)[0]))
                deviation = max(deviation, probe.max_deviation(case["logits"], logits))
    golden["reference_check"] = {
        "against": f"{source_repo}@{source_revision}",
        "with": f"{library}, transformers {transformers.__version__}, torch {torch.__version__}",
        "on": datetime.datetime.now(tz=datetime.UTC).date().isoformat(),
        "max_abs_delta": float(f"{deviation:.3g}"),
    }
    _write_golden(path, golden)
    print(f"reference-check: {path.relative_to(probe.REPO_ROOT)} max |Δ| {deviation:.3g} against {source_repo}")
    return 0


def main(argv: list[str]) -> int:
    if len(argv) == 6 and argv[1] == "reference-check" and argv[2] in probe.GOLDEN_DIRS:
        return reference_check(*argv[2:])
    if len(argv) != 4 or argv[1] not in probe.GOLDEN_DIRS:
        print(f"usage: {argv[0]} {{{'|'.join(probe.GOLDEN_DIRS)}}} <target> <image>", file=sys.stderr)
        return 2
    kind, target, image = argv[1], argv[2], argv[3]
    pin = pin_of(kind, target)
    declared = probe.image_model(image, kind)
    if declared != pin["model"]:
        raise SystemExit(f"{image} declares {declared!r}, but stage {target!r} ships {pin['model']!r}")

    # The e5 models were trained with "query: " / "passage: " prefixes; the
    # service is called with them. MiniLM was trained without one.
    prefix = "passage: " if kind == "embedding" and pin["model"].startswith("multilingual-e5-") else ""
    cases = EMBEDDING_CASES if kind == "embedding" else RERANKER_CASES
    reference = run_reference(image, kind, pin["model"], cases, prefix)
    if reference["files_sha256"] != pin["files_sha256"]:
        raise SystemExit(
            f"{image} ships {reference['files_sha256']}, the Dockerfile pins {pin['files_sha256']} — rebuild the image"
        )

    golden: dict[str, Any] = {
        "schema": probe.GOLDEN_SCHEMA,
        "service": kind,
        "target": target,
        **pin,
        "computed": {
            "by": "scripts/ci/compute_model_golden_outputs.py",
            "on": datetime.datetime.now(tz=datetime.UTC).date().isoformat(),
            "method": (
                "tokenizers + onnxruntime directly on the image's pinned model files, one input per run, "
                "intra_op_num_threads=1; "
                + (
                    "mean pooling over the attention mask, L2-normalised"
                    if kind == "embedding"
                    else "the pair's logit (the service answers its sigmoid)"
                )
            ),
            "runtime": reference["runtime"],
            "cpu": reference["cpu"],
        },
    }
    if kind == "embedding":
        golden["prefix"] = prefix
        golden["reduction"] = {
            "sample_size": probe.GOLDEN_SAMPLE_SIZE,
            "projections": probe.GOLDEN_PROJECTIONS,
            "decimals": probe.GOLDEN_DECIMALS,
        }
        golden["dimensions"] = len(reference["outputs"][0])
        golden["cases"] = [
            {**case, "untruncated_tokens": tokens, **probe.reduce_embedding(vector)}
            for case, vector, tokens in zip(cases, reference["outputs"], reference["untruncated_tokens"], strict=True)
        ]
    else:
        for logits in reference["outputs"]:
            # float32 sigmoid saturates to exactly 0.0/1.0 past |logit| ~ 17 on
            # the high side; keep well inside so the probe can always invert.
            if any(abs(logit) > probe.GOLDEN_MAX_ABS_LOGIT for logit in logits):
                raise SystemExit(f"a golden logit leaves ±{probe.GOLDEN_MAX_ABS_LOGIT}: {logits} — pick other inputs")
        golden["cases"] = [
            {
                **case,
                "untruncated_tokens": tokens,
                "logits": [round(logit, probe.GOLDEN_DECIMALS) for logit in logits],
            }
            for case, logits, tokens in zip(cases, reference["outputs"], reference["untruncated_tokens"], strict=True)
        ]

    out = probe.GOLDEN_DIRS[kind] / f"{target}.json"
    _write_golden(out, golden)
    print(f"golden: wrote {out.relative_to(probe.REPO_ROOT)} ({pin['repo_id']}@{pin['revision'][:12]})")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
