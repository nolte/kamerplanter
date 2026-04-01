from enum import StrEnum


class PrintTemplateType(StrEnum):
    NUTRIENT_PLAN = "nutrient_plan"
    CARE_CHECKLIST = "care_checklist"
    PLANT_LABEL = "plant_label"


class PrintFormat(StrEnum):
    PDF = "pdf"
    CSV = "csv"
