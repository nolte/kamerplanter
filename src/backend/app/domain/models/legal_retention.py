"""Domain models for the NFR-011 R-16/R-17/R-18 retention purge (#1789).

Harvest documentation (R-16, CanG), treatment applications (R-17, PflSchG §11)
and inspections (R-18) survive a tenant or account deletion pseudonymised, for
their legal period counted from the date NFR-011 names. These models declare one
rule each (:class:`LegalRetentionRule`) and carry what one purge run removed
(:class:`LegalRetentionPurgeCount`).
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

type LegalRetentionRuleId = Literal["R-16", "R-17", "R-18"]


class LegalRetentionChild(BaseModel):
    """A collection kept, and purged, with its parent row (``quality_assessments.batch_key``)."""

    model_config = {"frozen": True}

    collection: str
    parent_field: str


class LegalRetentionRule(BaseModel):
    """One NFR-011 §2.3 rule: which rows, counted from which date, with which children."""

    model_config = {"frozen": True}

    rule: LegalRetentionRuleId
    collection: str
    #: The instant the period counts from (NFR-011 §2.3 Q-R1: ``harvest_date``,
    #: ``applied_at``, ``inspected_at``) — never ``inherited_at`` (ADR-001).
    date_field: str
    children: tuple[LegalRetentionChild, ...] = ()


class LegalRetentionPurgeCount(BaseModel):
    """What one run removed for one rule. Counts only — no key, no tenant."""

    rows: int = Field(default=0, ge=0)
    children: int = Field(default=0, ge=0)
    edges: int = Field(default=0, ge=0)
