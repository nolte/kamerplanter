"""Confidence calibration (REQ-029-A 3.5).

Cosine similarity is NOT a probability. We map the per-species best cosine
similarity (already in [0, 1] for L2-normalised, non-negative-dominated
embeddings; clamped defensively) onto a calibrated confidence using the
configured thresholds:

    >= confidence_auto_accept  (default 0.85): propose the species directly
    >= confidence_show_results (default 0.10): show in the suggestion list
    <  confidence_show_results               : "uncertain" -> manual / fallback

The thresholds are SETTINGS, not literature values -- they are to be justified
by the own-species evaluation (WS-7 / REQ-029-A 7). The mapping itself is a
piecewise-linear rescale so that the auto-accept boundary lands exactly on
0.85 confidence and the show-results boundary on 0.10, giving the UI a stable,
interpretable scale regardless of the raw cosine distribution.
"""


def cosine_to_confidence(
    cosine_score: float,
    *,
    auto_accept: float,
    show_results: float,
) -> float:
    """Map a raw cosine similarity to a displayed confidence in [0, 1].

    Args:
        cosine_score: Raw cosine similarity (1 - cosine distance), typically [0, 1].
        auto_accept: Cosine threshold at/above which we are highly confident.
        show_results: Cosine threshold below which results are "uncertain".

    Returns:
        Calibrated confidence in [0, 1]:
          * cosine >= auto_accept    -> linearly mapped into [0.85, 1.0]
          * show_results <= cosine   -> linearly mapped into [0.10, 0.85)
          * cosine <  show_results   -> linearly mapped into [0.0, 0.10)
    """
    score = max(0.0, min(1.0, float(cosine_score)))

    # Guard against degenerate / inverted threshold configuration.
    lo = max(0.0, min(show_results, auto_accept))
    hi = max(lo + 1e-6, max(show_results, auto_accept))

    if score >= hi:
        # Map [hi, 1.0] -> [0.85, 1.0]
        span = max(1e-6, 1.0 - hi)
        return round(0.85 + 0.15 * (score - hi) / span, 4)
    if score >= lo:
        # Map [lo, hi) -> [0.10, 0.85)
        span = max(1e-6, hi - lo)
        return round(0.10 + 0.75 * (score - lo) / span, 4)
    # Map [0.0, lo) -> [0.0, 0.10)
    span = max(1e-6, lo)
    return round(0.10 * score / span, 4)
