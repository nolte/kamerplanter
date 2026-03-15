# Scoring weights
APPEARANCE_WEIGHT = 0.30
AROMA_WEIGHT = 0.25
COLOR_WEIGHT = 0.20
BASE_WEIGHT = 1.0 - APPEARANCE_WEIGHT - AROMA_WEIGHT - COLOR_WEIGHT  # 0.25 for defect-free baseline

# Defect penalties (subtracted from weighted score)
DEFECT_PENALTIES = {
    "mold": 50,
    "pests": 30,
    "nutrient_burn": 15,
    "light_burn": 15,
    "hermaphrodite": 40,
    "seeded": 25,
    "foxtailing": 10,
    "discoloration": 10,
    "mechanical_damage": 5,
}

# Grade thresholds
GRADE_THRESHOLDS = [
    (90, "a_plus"),
    (75, "a"),
    (55, "b"),
    (35, "c"),
    (0, "d"),
]


class QualityScoringEngine:
    """Pure logic for harvest quality scoring -- no DB access."""

    def calculate_overall_score(
        self,
        appearance: float,
        aroma: float,
        color: float,
        defects: list[str],
    ) -> tuple[float, str]:
        """Calculate overall quality score and grade.

        Args:
            appearance: Score 0-100
            aroma: Score 0-100
            color: Score 0-100
            defects: List of defect identifiers

        Returns:
            (overall_score, quality_grade) where grade is a_plus/a/b/c/d
        """
        weighted = appearance * APPEARANCE_WEIGHT + aroma * AROMA_WEIGHT + color * COLOR_WEIGHT + 100 * BASE_WEIGHT

        total_penalty = sum(DEFECT_PENALTIES.get(d, 5) for d in defects)

        score = max(0, min(100, weighted - total_penalty))

        grade = "d"
        for threshold, g in GRADE_THRESHOLDS:
            if score >= threshold:
                grade = g
                break

        return round(score, 1), grade
