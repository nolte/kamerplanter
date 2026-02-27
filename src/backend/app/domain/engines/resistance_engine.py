from datetime import datetime, timedelta

MAX_CONSECUTIVE = 3
ROTATION_WINDOW_DAYS = 90

# IPM hierarchy: prefer cultural > biological > mechanical > chemical
IPM_HIERARCHY = {"cultural": 0, "biological": 1, "mechanical": 2, "chemical": 3}


class ResistanceManager:
    """Pure logic for resistance risk management -- no DB access."""

    def validate_treatment(
        self,
        recent_applications: list[dict],
        proposed_ingredient: str | None,
    ) -> tuple[bool, str]:
        """Check if applying a treatment risks resistance development.

        Args:
            recent_applications: List of dicts with keys:
                - active_ingredient: str | None
                - applied_at: datetime | str
            proposed_ingredient: The active ingredient to validate.

        Returns:
            (is_safe, warning_message)
        """
        if not proposed_ingredient:
            return True, ""

        cutoff = datetime.now() - timedelta(days=ROTATION_WINDOW_DAYS)
        consecutive = 0
        for app in recent_applications:
            applied_at = app["applied_at"]
            if isinstance(applied_at, str):
                applied_at = datetime.fromisoformat(applied_at)
            if applied_at < cutoff:
                continue
            if app.get("active_ingredient") == proposed_ingredient:
                consecutive += 1

        if consecutive >= MAX_CONSECUTIVE:
            return False, (
                f"Resistance risk: '{proposed_ingredient}' has been applied "
                f"{consecutive} times in the last {ROTATION_WINDOW_DAYS} days. "
                f"Maximum consecutive applications is {MAX_CONSECUTIVE}."
            )
        if consecutive >= MAX_CONSECUTIVE - 1:
            return True, (
                f"Warning: '{proposed_ingredient}' has been applied "
                f"{consecutive} times. One more application will reach the limit."
            )
        return True, ""

    def suggest_alternatives(
        self,
        recent_applications: list[dict],
        available_treatments: list[dict],
    ) -> list[dict]:
        """Suggest alternative treatments sorted by IPM hierarchy.

        Args:
            recent_applications: Recent applications with active_ingredient.
            available_treatments: List of dicts with keys:
                - name: str
                - treatment_type: str
                - active_ingredient: str | None

        Returns:
            Sorted list of treatments, preferring IPM hierarchy and
            excluding overused ingredients.
        """
        cutoff = datetime.now() - timedelta(days=ROTATION_WINDOW_DAYS)
        ingredient_counts: dict[str, int] = {}
        for app in recent_applications:
            applied_at = app["applied_at"]
            if isinstance(applied_at, str):
                applied_at = datetime.fromisoformat(applied_at)
            if applied_at < cutoff:
                continue
            ingredient = app.get("active_ingredient")
            if ingredient:
                ingredient_counts[ingredient] = ingredient_counts.get(ingredient, 0) + 1

        scored = []
        for t in available_treatments:
            ingredient = t.get("active_ingredient")
            usage = ingredient_counts.get(ingredient, 0) if ingredient else 0
            hierarchy = IPM_HIERARCHY.get(t.get("treatment_type", "chemical"), 3)
            if usage >= MAX_CONSECUTIVE:
                continue
            scored.append({
                **t,
                "_hierarchy_score": hierarchy,
                "_usage_count": usage,
            })

        scored.sort(key=lambda x: (x["_hierarchy_score"], x["_usage_count"]))
        return [
            {k: v for k, v in item.items() if not k.startswith("_")}
            for item in scored
        ]
