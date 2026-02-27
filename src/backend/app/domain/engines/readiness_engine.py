# Stage-to-score mapping
STAGE_SCORES = {
    "immature": 0,
    "approaching": 50,
    "peak": 100,
    "overripe": 80,
}


class ReadinessEngine:
    """Pure logic for harvest readiness assessment -- no DB access."""

    def assess_readiness(
        self,
        observations: list[dict],
        indicator_reliabilities: dict[str, float],
    ) -> dict:
        """Assess harvest readiness from multiple indicator observations.

        Args:
            observations: List of dicts with keys:
                - indicator_key: str
                - ripeness_assessment: str (immature|approaching|peak|overripe)
                - days_to_harvest_estimate: int | None
            indicator_reliabilities: Dict mapping indicator_key to
                reliability_score (0-1).

        Returns:
            Dict with overall_score, recommendation, estimated_days,
            and per-indicator breakdown.
        """
        if not observations:
            return {
                "overall_score": 0,
                "recommendation": "immature",
                "estimated_days": None,
                "indicators": [],
            }

        total_weight = 0.0
        weighted_score = 0.0
        day_estimates = []
        indicators = []

        for obs in observations:
            indicator_key = obs.get("indicator_key", "")
            reliability = indicator_reliabilities.get(indicator_key, 0.5)
            stage = obs.get("ripeness_assessment", "immature")
            score = STAGE_SCORES.get(stage, 0)

            weighted_score += score * reliability
            total_weight += reliability

            est_days = obs.get("days_to_harvest_estimate")
            if est_days is not None:
                day_estimates.append(est_days)

            indicators.append({
                "indicator_key": indicator_key,
                "stage": stage,
                "score": score,
                "reliability": reliability,
                "weighted_contribution": score * reliability,
            })

        overall = weighted_score / total_weight if total_weight > 0 else 0
        estimated_days = (
            round(sum(day_estimates) / len(day_estimates))
            if day_estimates
            else None
        )

        if overall >= 90:
            recommendation = "optimal"
        elif overall >= 70:
            recommendation = "approaching"
        elif overall >= 50:
            recommendation = "developing"
        else:
            recommendation = "immature"

        return {
            "overall_score": round(overall, 1),
            "recommendation": recommendation,
            "estimated_days": estimated_days,
            "indicators": indicators,
        }
