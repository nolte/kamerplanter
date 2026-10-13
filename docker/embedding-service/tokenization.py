"""The embedding service's tokenizer: Rust ``tokenizers``, not transformers (#1752).

Kept apart from ``main.py`` and importing only the standard library and
``tokenizers``, so the backend's unit tests
(src/backend/tests/unit/test_embedding_service_feed.py) load THIS file — the one
``main.py`` imports — by path, without onnxruntime or a model on disk, and
exercise the fail-loud paths below. docker/reranker-service/main.py carries
copies of ``pad_token`` and ``load_tokenizer`` since #1480, because the two
images are separate build contexts; it truncates both rerankers at a fixed 512.
Only this service reads the window per model (``max_seq_length``, #1774).
"""

from __future__ import annotations

import json
from pathlib import Path

from tokenizers import Tokenizer

#: The file a sentence-transformers model publishes its truncation window in.
SENTENCE_BERT_CONFIG = "sentence_bert_config.json"


def max_seq_length(model_dir: Path) -> int:
    """Read the truncation window the model was published with (#1774).

    ``sentence_bert_config.json`` → ``max_seq_length``: the number of tokens
    sentence-transformers truncates this model at, and so the window its
    published vectors were computed over. Until #1774 the service truncated
    every model at a hard-coded 512. That was right for the e5 models and wrong
    for MiniLM:

    - multilingual-e5-small, -base, -large: 512 — ``sentence_bert_config.json``
      of each pinned intfloat revision (the Dockerfile fetches it with the model).
    - paraphrase-multilingual-MiniLM-L12-v2: 128 — the model authors'
      ``sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`` at
      e8f8c211226b894fcb81acc59f3b34ba3efd5f42. The Xenova export the image
      ships carries no ``sentence_bert_config.json`` (its
      ``tokenizer_config.json`` says ``model_max_length`` 512, the position
      limit, not the trained window), so the Dockerfile fetches this one file
      from the authors' repository, pinned and sha256-verified.

    Nothing is defaulted: a guessed window is different vectors, not an error.
    A bool is refused although it is an ``int`` in Python — ``true`` is no
    window.

    Raises:
        ValueError: If the file is missing or not JSON, or carries no positive
            integer ``max_seq_length``. The message names the file.
    """
    config_file = model_dir / SENTENCE_BERT_CONFIG
    try:
        config = json.loads(config_file.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ValueError(f"{config_file} is missing: the model's max_seq_length is unknown") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"{config_file} is not JSON: {exc}") from exc
    value = config.get("max_seq_length") if isinstance(config, dict) else None
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ValueError(f"{config_file} declares no positive integer max_seq_length (got {value!r})")
    return value


def pad_token(model_dir: Path) -> str:
    """Read the padding token the model was published with.

    ``tokenizer_config.json`` spells it either as a plain string or as an
    AddedToken dict (``{"content": "<pad>", ...}``), depending on which
    transformers version wrote the file. All four revisions pinned in the
    Dockerfile use the plain string ``"<pad>"``; the dict form is read so that a
    re-pin to a file written the other way does not break startup. A missing or
    empty pad token is an error, never a default: a guessed token that happens
    to be a real word piece would shift every vector without failing.

    Raises:
        ValueError: If the file declares no usable ``pad_token``.
    """
    config_file = model_dir / "tokenizer_config.json"
    config = json.loads(config_file.read_text(encoding="utf-8"))
    pad = config.get("pad_token")
    if isinstance(pad, dict):
        pad = pad.get("content")
    if not isinstance(pad, str) or not pad:
        raise ValueError(f"{config_file} declares no pad_token")
    return pad


def load_tokenizer(model_dir: Path) -> Tokenizer:
    """Load the fast tokenizer straight from ``tokenizer.json`` (#1752).

    THIS REPLACES ``transformers.AutoTokenizer``, AND THE CONFIGURATION BELOW
    IS WHAT MAKES IT A REPLACEMENT RATHER THAN AN APPROXIMATION. What
    transformers added on top of this Rust tokenizer was the call-time
    ``padding=True, truncation=True, max_length=512``; those are set here once:
    truncation to the model's published window (``max_seq_length``, #1774) and
    padding to the longest sequence with the model's own pad token and id.

    THE WINDOW IS PER MODEL SINCE #1774. The #1752 swap kept the old call-time
    ``max_length=512`` for every model, and the measurement below was taken at
    that 512. It is the published window of the e5 models (512) but not of
    MiniLM, whose authors publish 128 — see ``max_seq_length`` for the values
    and their sources. At 512 MiniLM pooled tokens past the window it was
    trained on; it is now truncated where sentence-transformers truncates it.

    Measured 2026-09-25 (#1752), tokenizers 0.23.2 configured like this with
    ``max_length=512`` against ``AutoTokenizer`` from transformers 5.17.0 (the
    version the lock held), for a normal batch, a >512-token text, a ragged
    batch, a single text and the empty string, batched and per text:

    - multilingual-e5-small, -base, -large: 39 tensors each, 0 differ.
      tokenizers always returns ``type_ids`` (all zeros here) where
      transformers omitted ``token_type_ids``; ``main.py`` does not pass them
      on, so ``feed.build_feed`` keeps feeding zeros exactly as before.
    - paraphrase-multilingual-MiniLM-L12-v2 (the Xenova export): the swap
      FIXES A DEFECT. Its ``tokenizer_config.json`` says
      ``"tokenizer_class": "BertTokenizer"`` while its ``tokenizer.json`` is a
      Unigram (XLM-R SentencePiece) model; transformers 5.17.0 built a
      WordPiece backend from that vocabulary and mapped almost every word to
      ``<unk>`` — "Tomaten sind Starkzehrer" became ``[0, 3, 3, 3, 2]``
      (``<s> <unk> <unk> <unk> </s>``), where this tokenizer yields
      ``▁Tomat en ▁sind ▁Star k ze hr er``. transformers 4.57.6
      (BertTokenizerFast, which reads ``tokenizer.json``) is identical to this
      tokenizer on all three tensors, so the swap restores the reference
      tokenization. For a single sequence this tokenizer's ``type_ids`` are all
      zeros, so feeding zeros stays identical for MiniLM too.

    Raises:
        ValueError: If the model declares no pad token, or declares one its
            vocabulary does not contain, or publishes no usable
            ``max_seq_length``.
    """
    window = max_seq_length(model_dir)
    tokenizer = Tokenizer.from_file(str(model_dir / "tokenizer.json"))
    pad = pad_token(model_dir)
    pad_id = tokenizer.token_to_id(pad)
    if pad_id is None:
        raise ValueError(f"pad_token {pad!r} is not in the vocabulary of {model_dir / 'tokenizer.json'}")
    tokenizer.enable_truncation(max_length=window)
    tokenizer.enable_padding(pad_id=pad_id, pad_token=pad)
    return tokenizer
