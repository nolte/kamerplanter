"""The embedding service's tokenizer: Rust ``tokenizers``, not transformers (#1752).

Kept apart from ``main.py`` and importing only the standard library and
``tokenizers``, so the backend's unit tests
(src/backend/tests/unit/test_embedding_service_feed.py) load THIS file — the one
``main.py`` imports — by path, without onnxruntime or a model on disk, and
exercise the fail-loud paths below. docker/reranker-service/main.py carries the
same two functions since #1480; they are copies, because the two images are
separate build contexts.
"""

from __future__ import annotations

import json
from pathlib import Path

from tokenizers import Tokenizer

#: Every shipped model was trained on sequences of at most 512 tokens; this is
#: the ``max_length`` the service passed per call when it still tokenized
#: through transformers.
MAX_LENGTH = 512


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
    truncation to ``MAX_LENGTH`` and padding to the longest sequence with the
    model's own pad token and id.

    Measured 2026-09-25, tokenizers 0.23.2 configured exactly like this against
    ``AutoTokenizer`` from transformers 5.17.0 (the version the lock held), for
    a normal batch, a >512-token text, a ragged batch, a single text and the
    empty string, batched and per text:

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
            vocabulary does not contain.
    """
    tokenizer = Tokenizer.from_file(str(model_dir / "tokenizer.json"))
    pad = pad_token(model_dir)
    pad_id = tokenizer.token_to_id(pad)
    if pad_id is None:
        raise ValueError(f"pad_token {pad!r} is not in the vocabulary of {model_dir / 'tokenizer.json'}")
    tokenizer.enable_truncation(max_length=MAX_LENGTH)
    tokenizer.enable_padding(pad_id=pad_id, pad_token=pad)
    return tokenizer
