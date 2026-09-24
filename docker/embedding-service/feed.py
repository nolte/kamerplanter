"""Build the ONNX Runtime input feed from what the GRAPH declares (#1724).

Kept apart from ``main.py`` and importing only numpy, so it can be unit-tested
without onnxruntime, transformers or a model on disk.

**The defect this is written against, measured 2026-09-24** on the develop
image ``--target e5-small``: ``/ready`` answered 200, and every ``POST /embed``
was a 500 — ``ValueError: Required inputs (['token_type_ids']) are missing from
input feed (['input_ids', 'attention_mask'])``. The e5-small ONNX graph declares
``input_ids``, ``attention_mask`` and ``token_type_ids``; its XLM-RoBERTa
tokenizer (``model_input_names = ['input_ids', 'attention_mask']``) never
returns ``token_type_ids``, and the feed was built from what the tokenizer
returned. The graphs do not share one signature (e5-base declares only the
first two), so the feed is built from the graph's declared input names, and a
name this service cannot produce is refused when the model loads — keeping
``/ready`` at 503 — rather than on every request. The reranker fixed the same
class in #1480.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

import numpy as np

#: Every graph input this service can produce. ``token_type_ids`` is always
#: producible: from the tokenizer when it returns one, else as zeros (see
#: ``build_feed``).
FEEDABLE_INPUTS = frozenset({"input_ids", "attention_mask", "token_type_ids"})


def unfeedable_inputs(input_names: Sequence[str]) -> list[str]:
    """The graph inputs in *input_names* this service cannot feed, sorted."""
    return sorted(set(input_names) - FEEDABLE_INPUTS)


def build_feed(input_names: Sequence[str], encoded: Mapping[str, Any]) -> dict[str, np.ndarray]:
    """The ``session.run`` feed for exactly the graph's *input_names*.

    Args:
        input_names: The graph's declared inputs (``session.get_inputs()``),
            already checked with ``unfeedable_inputs`` at load time.
        encoded: The tokenizer output; must hold ``input_ids`` and
            ``attention_mask`` and may hold ``token_type_ids``.

    Returns:
        One int64 array per declared input name — no more, no fewer: feeding a
        name the graph does not declare is an ``INVALID_ARGUMENT`` from
        onnxruntime, omitting one it does declare is the 500 described above.

    Raises:
        ValueError: If *input_names* holds a name outside ``FEEDABLE_INPUTS``.
    """
    unknown = unfeedable_inputs(input_names)
    if unknown:
        raise ValueError(f"graph inputs this service cannot feed: {unknown}")
    input_ids = np.asarray(encoded["input_ids"], dtype=np.int64)
    feed: dict[str, np.ndarray] = {}
    for name in input_names:
        if name == "token_type_ids" and "token_type_ids" not in encoded:
            # NOT AN APPROXIMATION. When `token_type_ids` is omitted, the
            # PyTorch model substitutes zeros (BertModel and XLMRobertaModel
            # alike), and omitting it is exactly what the model's reference
            # pipeline does: its XLM-RoBERTa tokenizer never produces the
            # field. e5-base/-large are `xlm-roberta` with `type_vocab_size: 1`
            # (0 is the only segment id); e5-small is `bert` with
            # `type_vocab_size: 2`, but ships the same tokenizer, so zeros are
            # its reference behaviour too (configs read at the pinned
            # revisions, 2026-09-24).
            feed[name] = np.zeros_like(input_ids)
        elif name == "input_ids":
            feed[name] = input_ids
        else:
            feed[name] = np.asarray(encoded[name], dtype=np.int64)
    return feed
