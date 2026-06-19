# Security Requirements Review — REQ-034 Pflanzenfoto-Galerie

> Erstellt 2026-06-19 vom Agenten `nolte-shared:security-requirements-reviewer` im Rahmen
> von Phase A (Spec-first) des Pflanzenfoto-Galerie-Features. Dieser Bericht begründet die
> Änderungen an den Fundament-Specs REQ-024, REQ-025 und REQ-029-A. **Status der Findings
> siehe Spalte „Erledigt".**

## Verdikt (Original-Review)

REQ-034 v1.0 war konzeptionell stark (Tenant-/Cross-Category-Guard, EXIF, Kuratierungs-Gate,
„Original verlässt die Instanz nicht"-Garantie, Erasure-Vererbung), aber **noch nicht
umsetzungsreif**: drei Critical-Findings waren Konsistenz-Brüche zu referenzierten Fundament-
Specs, die dort faktisch nicht existierten und je ein zentrales Akzeptanzkriterium
undurchführbar machten.

## Findings-Status nach Einarbeitung (REQ-034 v1.1)

| ID | Sev | Kurzbeschreibung | Erledigt in |
|----|-----|------------------|-------------|
| **SR-001** | Critical | Consent-Purpose `reference_contribution` fehlte in REQ-025 `ConsentEngine.PURPOSES` | ✅ REQ-025 v1.4 §3.1 (Purpose ergänzt, Art. 6(1)(a), global pro Nutzer); REQ-034 §4.4 |
| **SR-002** | Critical | RBAC-Permission `attachment:create` existierte nicht in REQ-024 Permission-Matrix | ✅ REQ-024 v1.5 §1a.1 (Matrix-Zeile „Plant Instance Photos"); REQ-034 §6 (Mapping auf `CREATE_/UPDATE_/DELETE_RESOURCE` + §1a.5) |
| **SR-003** | Critical | `species_embeddings` trug kein `tenant_key`/`contributed_by` → Erasure undurchführbar; pgvector-Store nicht in Erasure-Pipeline | ✅ REQ-029-A v1.2 §5.1 (Provenienz-Felder + Migration 003); REQ-025 v1.4 Erasure-Phase 0.5 `_reference_index_cleanup` + AK-OS-05; REQ-034 §5 |
| **SR-004** | High | Galerie-Quota unspezifiziert (O-01 offen) → DoS/Storage-Exhaustion | ✅ REQ-034 §3 (`STORAGE_MAX_PHOTOS_PER_INSTANCE` Default 50 + Tenant-Quota), AC-15, O-01 gelöst |
| **SR-005** | High | Reference-Hook ohne Backlog-/Rate-Limit (Poisoning); Light-Mode-Consent-Konflikt | ✅ REQ-034 §4.1 Guard 2 (Light-Mode-Hook deaktiviert) + Guard 5/§4.3 (`REFERENCE_CONTRIBUTION_PENDING_LIMIT` Default 100), AC-16 |
| **SR-006** | Suggestion | Interner Bildtransfer zum Inferenz-Service nicht als ClusterIP/TLS-only gekennzeichnet | ✅ REQ-034 §4.2 (ClusterIP REQ-029-A §3.1 + TLS NFR-013 §5.3) |
| **SR-007** | Suggestion | `InferenceServiceClient.reference()` ohne Endpunkt-Vertrag im Ziel-Dokument | ✅ REQ-029-A v1.2 §3.3 (`POST /reference`-Vertrag, erzwingt `is_active=false` + Provenienz bei user_contributed) |
| SR-008..SR-011 | Info | EXIF-Doppelsicherung, Scope-Begründung, Cross-Category-Guard, Stable-URI — keine Lücken | — (positiv vermerkt) |

## Verbleibende Caller-/DPO-Follow-ups (nicht autonom entscheidbar)

1. **SR-009 / REQ-034 O-05:** Scope-Wahl im **persönlichen** Tenant — `user_diary_attachments`
   (bleibt) vs. `user_personal` (Hard-Delete). Empfehlung in REQ-034 O-05: tenant-typ-abhängige
   Klassifizierung. DPO-Entscheidung ausstehend.
2. **Consent-Text-Freigabe (SR-001):** Der `reference_contribution`-Einwilligungstext sollte vom
   DPO gegengelesen werden, bevor er produktiv geht.
3. **Light-Mode-Datenbeitrag (SR-005):** In v1.1 wurde der Hook im Light-Modus deaktiviert — die
   Produkt-/DPO-Entscheidung, ob ein Community-Datenbeitrag unter der Haushaltsausnahme überhaupt
   gewollt ist, ist damit konservativ vorbeantwortet (kann später revidiert werden).

## Bewertung nach Einarbeitung

Alle drei Critical- und beide High-Findings sind in den jeweiligen Fundament-Specs geschlossen;
SR-006/SR-007 ebenfalls. REQ-034 v1.1 ist damit sicherheits-/datenschutzseitig **umsetzungsreif**,
mit den oben gelisteten DPO-Follow-ups als nicht-blockierende Rechtsfragen.
