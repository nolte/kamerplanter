---
name: check-retention
description: "Prueft neue oder geaenderte Domain-Models auf NFR-011-Konformitaet: DSGVO-Retention-Matrix-Eintrag vorhanden, Celery-Enforcement-Tasks existieren, personenbezogene Felder identifiziert, gesetzliche Aufbewahrungsfristen beachtet. Nutze diesen Skill nach Implementierung neuer Entitaeten die personenbezogene Daten enthalten koennten."
argument-hint: "[Model-Name oder REQ-nnn, z.B. PlantDiaryEntry oder REQ-023]"
disable-model-invocation: true
---

# DSGVO-Retention-Check (NFR-011): $ARGUMENTS

## Schritt 1: Relevante Dateien laden

Lade **parallel**:

1. **Model-Datei:** Falls `$ARGUMENTS` ein Modelname — suche via Grep in `src/backend/app/domain/models/`
2. **NFR-011-Retention-Matrix:** Lies `spec/nfr/NFR-011_Vorratsdatenspeicherung-Aufbewahrungsfristen.md` (Abschnitt 2, Retention-Matrix)
3. **Celery-Tasks:** Glob `src/backend/app/tasks/*.py` — filtere nach Retention/Cleanup-Tasks
4. **REQ-025 (falls vorhanden):** `spec/req/REQ-025_Datenschutz-DSGVO.md` erste 40 Zeilen

## Schritt 2: Personenbezogene Felder identifizieren

Analysiere das Model auf Felder die personenbezogene Daten enthalten koennten:

| Feldtyp | Beispiele | Kategorie |
|---------|-----------|-----------|
| **Direkte PBD** | email, name, ip_address, phone | Hart-Personenbezug |
| **Indirekte PBD** | user_key, created_by, assigned_to | Weicher Personenbezug (loeschbar durch Anonymisierung) |
| **Sensor-/Verhaltensdaten** | timestamp + location_key + sensor_value | Indirekt PBD (SEC-K-005) |
| **Kommunikations-Tokens** | verification_token, reset_token, refresh_token | Kurzlebig, sofort nach Ablauf loeschen |

```python
# ❌ Felder die geprüft werden muessen:
email: str
ip_address: str
created_by: str  # user_key
assigned_to: str | None
device_fingerprint: str
```

## Schritt 3: Retention-Matrix-Abdeckung pruefen

Prüfe fuer jedes identifizierte personenbezogene Feld ob es in der Retention-Matrix (NFR-011 §2) enthalten ist:

**Retention-Matrix-Template (falls Eintrag fehlt):**

```markdown
| # | Datenkategorie | Collection(s) | Frist | Aktion nach Frist | Rechtsgrundlage |
|---|----------------|--------------|-------|-------------------|----------------|
| R-XX | {Beschreibung} | {collection_name} | {Frist} | {Loeschen/Anonymisieren} | {DSGVO Art.} |
```

**Entscheidungsbaum fuer Frist:**
- Token/temporaere Daten → Sofort nach Ablauf
- Session-Daten (IP) → 7 Tage, dann anonymisieren
- Nutzer-Account-Daten → 90 Tage nach Soft-Delete
- Einladungen/abgelaufene Tokens → 30 Tage
- Ernte-/Behandlungsdaten (CanG/PflSchG) → 5-10 Jahre (gesetzliche Mindestfrist!)
- Sensor-Rohdaten → 90 Tage → Downsampling Stufe 2/3

## Schritt 4: Celery-Enforcement-Task pruefen

Prüfe ob ein Celery-Task existiert, der die Retention-Fristen durchsetzt:

```python
# ✅ MUSS existieren fuer jede Retention-Kategorie:
@celery_app.task(name="retention.cleanup_{entity}")
async def cleanup_{entity}_expired():
    """
    NFR-011: Enforce retention policy for {entity}.
    Runs daily via beat schedule.
    """
    cutoff = datetime.utcnow() - timedelta(days=RETENTION_DAYS)
    # ... delete/anonymize logic
```

Prüfe ob der Task im Beat-Schedule eingetragen ist (`celery_config.py` oder `beat_schedule.py`).

## Schritt 5: Anonymisierung vs. Loeschung pruefen

**Wann Anonymisierung statt Loeschung (NFR-011 §2.1):**

- Ernte-/Behandlungs-Datensaetze (CanG-Nachweis erforderlich) → User-Referenz anonymisieren, Daten bleiben
- Aufgaben-Bewertungen → `assigned_to: null`, Bewertung bleibt
- Community-Beitraege (Bulletin, Einkaufslisten) → User-Referenz entfernen, Inhalt bleibt

```python
# ✅ Korrekte Anonymisierung:
await collection.update(doc_key, {
    "created_by": None,
    "email": None,
    "_anonymized_at": datetime.utcnow().isoformat()
})

# ❌ Fehler: User-Referenz in aggregierten Daten belassen
# → DSGVO Art. 17 Verletzung
```

## Schritt 6: Gesetzliche Mindestfristen pruefen (CanG, PflSchG)

Falls das Model Ernte-, Behandlungs- oder Pflanzenschutzdaten enthaelt:

| Datenkategorie | Gesetz | Mindestfrist |
|----------------|--------|-------------|
| Erntedaten (Cannabis) | CanG §19 | 5 Jahre |
| Pflanzenschutz-Anwendungen | PflSchG §67 | 3 Jahre |
| Betaeubungsmittel-Protokolle | BtMG | 10 Jahre |

**Prüfe: Retention-Frist ist ≥ gesetzliche Mindestfrist**

## Schritt 7: Report ausgeben

```markdown
# DSGVO-Retention-Review: {Model/REQ}

## Identifizierte personenbezogene Felder
| Feld | Typ | Kategorie | In Retention-Matrix |
|------|-----|-----------|---------------------|
{Zeilen pro PBD-Feld}

## Retention-Matrix-Abdeckung
{N/M Felder abgedeckt}

## Fehlende Retention-Eintraege
{Vorschlaege fuer neue Matrix-Eintraege mit Frist und Aktion}

## Celery-Enforcement
{Task vorhanden: ja/nein | Im Beat-Schedule: ja/nein}

## Gesetzliche Mindestfristen
{Ernte/Behandlung/Pflanzenschutz: Fristen korrekt: ja/nein}

## Violations (priorisiert)
{Nummerierte Liste}

## Bewertung
- ✅ NFR-011-konform / ❌ {N} Luecken — DSGVO-Risiko
```
