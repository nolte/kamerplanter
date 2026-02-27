# Spezifikation: REQ-012 - Stammdaten-Import via CSV-Upload

```yaml
ID: REQ-012
Titel: Stammdaten-Import via CSV-Upload
Kategorie: Stammdaten
Fokus: Beides
Technologie: Python, FastAPI, ArangoDB, React, MUI
Status: Entwurf
Version: 1.0
```

## 1. Business Case

**User Story:** "Als Systemadministrator möchte ich Stammdaten (Species, Cultivar, BotanicalFamily) per CSV-Datei importieren können, um die Erstbefüllung des Systems, Migrationen und Batch-Aktualisierungen effizient durchzuführen, anstatt jeden Datensatz einzeln anlegen zu müssen."

**Beschreibung:**
Das System ermöglicht den Bulk-Import von Stammdaten über CSV-Dateien. Der Import folgt einem **Zwei-Phasen-Prozess** (Upload → Preview → Confirm → Import), der dem Nutzer volle Kontrolle über die zu importierenden Daten gibt. Vor dem finalen Import werden alle Zeilen validiert und als Vorschau angezeigt — fehlerhafte Zeilen können korrigiert oder übersprungen werden.

**Grundprinzipien:**

- **Vorschau vor Import:** Kein Datensatz wird ohne explizite Bestätigung in die Datenbank geschrieben
- **Transparente Validierung:** Jede Zeile wird einzeln validiert, Fehler werden pro Zeile und Feld gemeldet
- **Konfigurierbare Duplikatbehandlung:** Der Nutzer wählt pro Import die Strategie (skip/update/fail)
- **Atomarität:** Ein bestätigter Import wird als Ganzes ausgeführt — bei kritischen Fehlern Rollback
- **Nachvollziehbarkeit:** Jeder Import-Lauf wird mit Ergebnis-Statistiken protokolliert

### 1.1 Unterstützte Entitäten

| Entität | Identifikationsmerkmal | Typischer Anwendungsfall |
|---------|----------------------|--------------------------|
| **Species** | `scientific_name` | Erstbefüllung botanischer Arten |
| **Cultivar** | `name` + `parent_species` | Sortenkatalogeinfuhr, Züchterlisten |
| **BotanicalFamily** | `name` | Pflanzenfamilien mit Fruchtfolge-Kategorien |

### 1.2 Duplikatbehandlung

| Strategie | Verhalten | Default |
|-----------|-----------|---------|
| **skip** | Existierende Datensätze werden übersprungen, nur neue eingefügt | ✓ |
| **update** | Existierende Datensätze werden mit CSV-Werten aktualisiert (Merge) | |
| **fail** | Import bricht ab, sobald ein Duplikat erkannt wird | |

Duplikaterkennung erfolgt anhand des Identifikationsmerkmals der jeweiligen Entität (siehe Tabelle 1.1).

## 2. Datenmodell-Erweiterung (ArangoDB)

### Neue Collection:

**`import_jobs` (Document Collection):**
```json
{
  "_key": "job_20260226_143022_species",
  "entity_type": "species",
  "status": "preview_ready",
  "duplicate_strategy": "skip",
  "original_filename": "mein_artenkatalog.csv",
  "file_size_bytes": 24576,
  "encoding": "utf-8",
  "delimiter": ",",
  "total_rows": 150,
  "valid_rows": 142,
  "invalid_rows": 5,
  "duplicate_rows": 3,
  "preview_data": [
    {
      "row_number": 1,
      "status": "valid",
      "data": {
        "scientific_name": "Solanum lycopersicum",
        "common_names": "Tomate,Tomato",
        "family": "Solanaceae",
        "genus": "Solanum"
      },
      "errors": [],
      "is_duplicate": false
    },
    {
      "row_number": 2,
      "status": "invalid",
      "data": {
        "scientific_name": "",
        "common_names": "Basilikum",
        "family": "Lamiaceae",
        "genus": "Ocimum"
      },
      "errors": [
        {
          "field": "scientific_name",
          "code": "REQUIRED_FIELD",
          "message": "scientific_name ist ein Pflichtfeld"
        }
      ],
      "is_duplicate": false
    },
    {
      "row_number": 3,
      "status": "duplicate",
      "data": {
        "scientific_name": "Cannabis sativa",
        "common_names": "Hanf,Hemp",
        "family": "Cannabaceae",
        "genus": "Cannabis"
      },
      "errors": [],
      "is_duplicate": true,
      "existing_key": "species_42"
    }
  ],
  "import_result": null,
  "created_at": "2026-02-26T14:30:22Z",
  "confirmed_at": null,
  "completed_at": null,
  "created_by": "admin"
}
```

**Status-Übergänge:**
```
uploaded → validating → preview_ready → confirmed → importing → completed
                ↓                                        ↓
              failed                                   failed
```

| Status | Beschreibung |
|--------|-------------|
| `uploaded` | CSV empfangen, noch nicht verarbeitet |
| `validating` | Validierung und Duplikatprüfung läuft |
| `preview_ready` | Vorschau bereit, wartet auf Bestätigung |
| `confirmed` | Nutzer hat Import bestätigt |
| `importing` | Import läuft (Schreiboperationen aktiv) |
| `completed` | Import abgeschlossen |
| `failed` | Validierung oder Import fehlgeschlagen |

**Import-Ergebnis (nach Abschluss):**
```json
{
  "import_result": {
    "records_created": 142,
    "records_updated": 0,
    "records_skipped": 3,
    "records_failed": 5,
    "duration_ms": 2340,
    "errors": [
      {
        "row_number": 2,
        "field": "scientific_name",
        "code": "REQUIRED_FIELD",
        "message": "scientific_name ist ein Pflichtfeld"
      }
    ]
  }
}
```

### AQL-Beispielabfragen:

**Import-Job mit Statistiken laden:**
```aql
FOR job IN import_jobs
  FILTER job._key == @job_key
  RETURN {
    _key: job._key,
    entity_type: job.entity_type,
    status: job.status,
    total_rows: job.total_rows,
    valid_rows: job.valid_rows,
    invalid_rows: job.invalid_rows,
    duplicate_rows: job.duplicate_rows,
    import_result: job.import_result,
    created_at: job.created_at,
    completed_at: job.completed_at
  }
```

**Import-Historie (letzte 20 Jobs):**
```aql
FOR job IN import_jobs
  SORT job.created_at DESC
  LIMIT 20
  RETURN {
    _key: job._key,
    entity_type: job.entity_type,
    status: job.status,
    original_filename: job.original_filename,
    total_rows: job.total_rows,
    valid_rows: job.valid_rows,
    created_at: job.created_at,
    completed_at: job.completed_at
  }
```

## 3. Technische Umsetzung (Python)

### 3.1 CSV-Spalten-Definitionen

**Species-CSV:**

| Spalte | Pflicht | Typ | Beispiel | Hinweis |
|--------|---------|-----|---------|---------|
| `scientific_name` | ✓ | string | `Solanum lycopersicum` | Binomiale Nomenklatur |
| `common_names` | ✓ | string (`;`-separiert) | `Tomate;Tomato;Pomodoro` | Mindestens ein Name |
| `family` | ✓ | string | `Solanaceae` | Muss gültige Familie sein |
| `genus` | ✓ | string | `Solanum` | Aus scientific_name ableitbar |
| `cycle_type` | ✓ | enum | `annual` | `annual`, `biennial`, `perennial` |
| `photoperiod_type` | | enum | `day_neutral` | `short_day`, `long_day`, `day_neutral` |
| `growth_habit` | | enum | `herb` | `herb`, `shrub`, `tree`, `vine`, `groundcover` |
| `root_type` | | enum | `fibrous` | `fibrous`, `taproot`, `tuberous`, `bulbous` |
| `hardiness_zones` | | string (`;`-separiert) | `7a;7b;8a` | USDA Hardiness Zones |
| `allelopathy_score` | | float | `0.3` | -1.0 bis 1.0 |
| `native_habitat` | | string | `Südamerika` | Freitext |

**Cultivar-CSV:**

| Spalte | Pflicht | Typ | Beispiel | Hinweis |
|--------|---------|-----|---------|---------|
| `name` | ✓ | string | `San Marzano` | Sortenname |
| `parent_species` | ✓ | string | `Solanum lycopersicum` | scientific_name der Stammspezies |
| `breeder` | | string | `INRA` | Züchter/Institut |
| `breeding_year` | | int | `1926` | 1800–2100 |
| `traits` | | string (`;`-separiert) | `disease_resistant;high_yield` | Gültige Trait-Keys |
| `days_to_maturity` | | int | `78` | 1–365 |
| `disease_resistances` | | string (`;`-separiert) | `fusarium;verticillium` | Resistenz-Keys |
| `patent_status` | | string | `public_domain` | Freitext |

**BotanicalFamily-CSV:**

| Spalte | Pflicht | Typ | Beispiel | Hinweis |
|--------|---------|-----|---------|---------|
| `name` | ✓ | string | `Solanaceae` | Eindeutiger Familienname |
| `typical_nutrient_demand` | ✓ | enum | `heavy` | `light`, `medium`, `heavy` |
| `common_pests` | | string (`;`-separiert) | `Blattläuse;Weiße Fliege` | Typische Schädlinge |
| `rotation_category` | | string | `Nachtschattengewächse` | Fruchtfolge-Kategorie |

**CSV-Format-Anforderungen:**
- Zeichenkodierung: UTF-8 (mit oder ohne BOM)
- Trennzeichen: Komma (`,`) als Default, konfigurierbar (`;`, `\t`)
- Multiwert-Felder: Semikolon (`;`) als Trennzeichen innerhalb einer Zelle
- Header-Zeile: Pflicht (Spaltennamen müssen exakt übereinstimmen)
- Maximale Dateigröße: 10 MB
- Maximale Zeilenanzahl: 10.000

### 3.2 Import-Models

```python
from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class EntityType(str, Enum):
    SPECIES = "species"
    CULTIVAR = "cultivar"
    BOTANICAL_FAMILY = "botanical_family"


class DuplicateStrategy(str, Enum):
    SKIP = "skip"
    UPDATE = "update"
    FAIL = "fail"


class ImportJobStatus(str, Enum):
    UPLOADED = "uploaded"
    VALIDATING = "validating"
    PREVIEW_READY = "preview_ready"
    CONFIRMED = "confirmed"
    IMPORTING = "importing"
    COMPLETED = "completed"
    FAILED = "failed"


class RowValidationError(BaseModel):
    """Validierungsfehler für eine einzelne Zeile/Feld."""

    field: str
    code: str
    message: str


class RowStatus(str, Enum):
    VALID = "valid"
    INVALID = "invalid"
    DUPLICATE = "duplicate"


class PreviewRow(BaseModel):
    """Vorschau-Zeile mit Validierungsergebnis."""

    row_number: int
    status: RowStatus
    data: dict[str, Any]
    errors: list[RowValidationError] = Field(default_factory=list)
    is_duplicate: bool = False
    existing_key: str | None = None


class ImportResult(BaseModel):
    """Ergebnis eines abgeschlossenen Imports."""

    records_created: int = 0
    records_updated: int = 0
    records_skipped: int = 0
    records_failed: int = 0
    duration_ms: int = 0
    errors: list[RowValidationError] = Field(default_factory=list)


class ImportJob(BaseModel):
    """Vollständiger Import-Job mit Preview und Ergebnis."""

    key: str | None = None
    entity_type: EntityType
    status: ImportJobStatus = ImportJobStatus.UPLOADED
    duplicate_strategy: DuplicateStrategy = DuplicateStrategy.SKIP
    original_filename: str
    file_size_bytes: int
    encoding: str = "utf-8"
    delimiter: str = ","
    total_rows: int = 0
    valid_rows: int = 0
    invalid_rows: int = 0
    duplicate_rows: int = 0
    preview_data: list[PreviewRow] = Field(default_factory=list)
    import_result: ImportResult | None = None
    created_at: datetime | None = None
    confirmed_at: datetime | None = None
    completed_at: datetime | None = None
    created_by: str | None = None
```

### 3.3 CSV-Parser

```python
import csv
import io
from typing import Any

import chardet
import structlog

logger = structlog.get_logger()

# Spaltendefinitionen pro Entität
COLUMN_DEFINITIONS: dict[str, dict[str, dict[str, Any]]] = {
    "species": {
        "scientific_name": {"required": True, "type": "string"},
        "common_names": {"required": True, "type": "list", "separator": ";"},
        "family": {"required": True, "type": "string"},
        "genus": {"required": True, "type": "string"},
        "cycle_type": {
            "required": True,
            "type": "enum",
            "values": ["annual", "biennial", "perennial"],
        },
        "photoperiod_type": {
            "required": False,
            "type": "enum",
            "values": ["short_day", "long_day", "day_neutral"],
        },
        "growth_habit": {
            "required": False,
            "type": "enum",
            "values": ["herb", "shrub", "tree", "vine", "groundcover"],
        },
        "root_type": {
            "required": False,
            "type": "enum",
            "values": ["fibrous", "taproot", "tuberous", "bulbous"],
        },
        "hardiness_zones": {"required": False, "type": "list", "separator": ";"},
        "allelopathy_score": {
            "required": False,
            "type": "float",
            "min": -1.0,
            "max": 1.0,
        },
        "native_habitat": {"required": False, "type": "string"},
    },
    "cultivar": {
        "name": {"required": True, "type": "string"},
        "parent_species": {"required": True, "type": "string"},
        "breeder": {"required": False, "type": "string"},
        "breeding_year": {
            "required": False,
            "type": "int",
            "min": 1800,
            "max": 2100,
        },
        "traits": {"required": False, "type": "list", "separator": ";"},
        "days_to_maturity": {"required": False, "type": "int", "min": 1, "max": 365},
        "disease_resistances": {"required": False, "type": "list", "separator": ";"},
        "patent_status": {"required": False, "type": "string"},
    },
    "botanical_family": {
        "name": {"required": True, "type": "string"},
        "typical_nutrient_demand": {
            "required": True,
            "type": "enum",
            "values": ["light", "medium", "heavy"],
        },
        "common_pests": {"required": False, "type": "list", "separator": ";"},
        "rotation_category": {"required": False, "type": "string"},
    },
}


class CsvParser:
    """Parst und validiert CSV-Dateien für den Stammdaten-Import."""

    def __init__(self, entity_type: str) -> None:
        self._entity_type = entity_type
        self._columns = COLUMN_DEFINITIONS[entity_type]

    def detect_encoding(self, raw_bytes: bytes) -> str:
        """Erkennt Zeichenkodierung der CSV-Datei."""
        if raw_bytes[:3] == b"\xef\xbb\xbf":
            return "utf-8-sig"
        result = chardet.detect(raw_bytes)
        return result.get("encoding", "utf-8") or "utf-8"

    def detect_delimiter(self, first_line: str) -> str:
        """Erkennt Trennzeichen anhand der Header-Zeile."""
        sniffer = csv.Sniffer()
        try:
            dialect = sniffer.sniff(first_line, delimiters=",;\t")
            return dialect.delimiter
        except csv.Error:
            return ","

    def parse(
        self,
        raw_bytes: bytes,
        delimiter: str | None = None,
    ) -> tuple[list[dict[str, Any]], list[dict]]:
        """
        Parst CSV-Bytes und gibt (rows, errors) zurück.

        Returns:
            rows: Liste von Dictionaries mit geparsten Zeilen
            errors: Liste von Fehlern bei der Grundstruktur-Prüfung
        """
        encoding = self.detect_encoding(raw_bytes)
        text = raw_bytes.decode(encoding)
        lines = text.strip().splitlines()

        if not lines:
            return [], [{"code": "EMPTY_FILE", "message": "CSV-Datei ist leer"}]

        if delimiter is None:
            delimiter = self.detect_delimiter(lines[0])

        reader = csv.DictReader(io.StringIO(text), delimiter=delimiter)
        if reader.fieldnames is None:
            return [], [{"code": "NO_HEADER", "message": "Keine Header-Zeile gefunden"}]

        # Header-Validierung
        unknown_cols = set(reader.fieldnames) - set(self._columns.keys())
        missing_required = {
            col
            for col, defn in self._columns.items()
            if defn["required"]
        } - set(reader.fieldnames)

        structure_errors = []
        if missing_required:
            structure_errors.append({
                "code": "MISSING_COLUMNS",
                "message": f"Fehlende Pflichtspalten: {', '.join(sorted(missing_required))}",
            })
        if unknown_cols:
            logger.warning(
                "csv_unknown_columns",
                columns=sorted(unknown_cols),
                entity_type=self._entity_type,
            )

        rows = []
        for i, row in enumerate(reader, start=2):  # Zeile 1 = Header
            parsed = {}
            for col, defn in self._columns.items():
                raw_value = row.get(col, "").strip()
                parsed[col] = self._convert_value(raw_value, defn)
            parsed["_row_number"] = i
            rows.append(parsed)

        return rows, structure_errors

    def _convert_value(self, raw: str, defn: dict) -> Any:
        """Konvertiert Rohwert anhand der Spaltendefinition."""
        if not raw:
            return None

        match defn["type"]:
            case "string":
                return raw
            case "int":
                try:
                    return int(raw)
                except ValueError:
                    return raw  # Validierung meldet Fehler später
            case "float":
                try:
                    return float(raw)
                except ValueError:
                    return raw
            case "enum":
                return raw.lower().strip()
            case "list":
                separator = defn.get("separator", ";")
                return [item.strip() for item in raw.split(separator) if item.strip()]
            case _:
                return raw
```

### 3.4 Zeilen-Validator

```python
import re

from app.models.import_models import PreviewRow, RowStatus, RowValidationError


class RowValidator:
    """Validiert einzelne CSV-Zeilen gegen die Spaltendefinitionen."""

    SCIENTIFIC_NAME_PATTERN = re.compile(r"^[A-Z][a-z]+\s[a-z]+(\s(var\.|subsp\.)\s[a-z]+)?$")
    HARDINESS_ZONE_PATTERN = re.compile(r"^\d{1,2}[ab]$")
    VALID_TRAITS = {
        "disease_resistant", "pest_resistant", "high_yield", "compact",
        "drought_tolerant", "cold_hardy", "heat_tolerant", "early_maturing",
        "long_season", "ornamental", "heirloom", "hybrid", "f1",
    }

    def __init__(self, entity_type: str, columns: dict) -> None:
        self._entity_type = entity_type
        self._columns = columns

    def validate_row(self, row: dict, row_number: int) -> PreviewRow:
        """Validiert eine einzelne Zeile und gibt PreviewRow zurück."""
        errors: list[RowValidationError] = []

        for col, defn in self._columns.items():
            value = row.get(col)
            col_errors = self._validate_field(col, value, defn)
            errors.extend(col_errors)

        # Entity-spezifische Cross-Field-Validierung
        errors.extend(self._cross_validate(row))

        status = RowStatus.INVALID if errors else RowStatus.VALID
        return PreviewRow(
            row_number=row_number,
            status=status,
            data={k: v for k, v in row.items() if not k.startswith("_")},
            errors=errors,
        )

    def _validate_field(
        self, col: str, value: object, defn: dict
    ) -> list[RowValidationError]:
        """Validiert ein einzelnes Feld."""
        errors = []

        # Pflichtfeld-Prüfung
        if defn["required"] and (value is None or value == "" or value == []):
            errors.append(RowValidationError(
                field=col,
                code="REQUIRED_FIELD",
                message=f"{col} ist ein Pflichtfeld",
            ))
            return errors

        if value is None or value == "":
            return errors

        # Typ-spezifische Validierung
        match defn["type"]:
            case "int":
                if not isinstance(value, int):
                    errors.append(RowValidationError(
                        field=col,
                        code="INVALID_TYPE",
                        message=f"{col} muss eine Ganzzahl sein",
                    ))
                else:
                    if "min" in defn and value < defn["min"]:
                        errors.append(RowValidationError(
                            field=col,
                            code="VALUE_TOO_LOW",
                            message=f"{col} muss >= {defn['min']} sein",
                        ))
                    if "max" in defn and value > defn["max"]:
                        errors.append(RowValidationError(
                            field=col,
                            code="VALUE_TOO_HIGH",
                            message=f"{col} muss <= {defn['max']} sein",
                        ))
            case "float":
                if not isinstance(value, (int, float)):
                    errors.append(RowValidationError(
                        field=col,
                        code="INVALID_TYPE",
                        message=f"{col} muss eine Zahl sein",
                    ))
                else:
                    if "min" in defn and value < defn["min"]:
                        errors.append(RowValidationError(
                            field=col,
                            code="VALUE_TOO_LOW",
                            message=f"{col} muss >= {defn['min']} sein",
                        ))
                    if "max" in defn and value > defn["max"]:
                        errors.append(RowValidationError(
                            field=col,
                            code="VALUE_TOO_HIGH",
                            message=f"{col} muss <= {defn['max']} sein",
                        ))
            case "enum":
                if value not in defn.get("values", []):
                    errors.append(RowValidationError(
                        field=col,
                        code="INVALID_ENUM",
                        message=f"{col} muss einer der Werte {defn['values']} sein",
                    ))
            case "list":
                if col == "hardiness_zones" and isinstance(value, list):
                    for zone in value:
                        if not self.HARDINESS_ZONE_PATTERN.match(zone):
                            errors.append(RowValidationError(
                                field=col,
                                code="INVALID_FORMAT",
                                message=f"Ungültige Hardiness Zone: '{zone}' (erwartet z.B. '7a')",
                            ))
                if col == "traits" and isinstance(value, list):
                    invalid = set(value) - self.VALID_TRAITS
                    if invalid:
                        errors.append(RowValidationError(
                            field=col,
                            code="INVALID_TRAIT",
                            message=f"Ungültige Traits: {', '.join(sorted(invalid))}",
                        ))

        return errors

    def _cross_validate(self, row: dict) -> list[RowValidationError]:
        """Entity-übergreifende Validierungsregeln."""
        errors = []

        if self._entity_type == "species":
            sci_name = row.get("scientific_name")
            if sci_name and isinstance(sci_name, str):
                if not self.SCIENTIFIC_NAME_PATTERN.match(sci_name):
                    errors.append(RowValidationError(
                        field="scientific_name",
                        code="INVALID_FORMAT",
                        message="Wissenschaftlicher Name muss binomialer Nomenklatur folgen (z.B. 'Solanum lycopersicum')",
                    ))
                # Genus-Konsistenz: genus muss erstem Wort von scientific_name entsprechen
                genus = row.get("genus")
                if genus and sci_name and " " in sci_name:
                    expected_genus = sci_name.split()[0]
                    if genus != expected_genus:
                        errors.append(RowValidationError(
                            field="genus",
                            code="GENUS_MISMATCH",
                            message=f"genus '{genus}' stimmt nicht mit scientific_name überein (erwartet: '{expected_genus}')",
                        ))

        return errors
```

### 3.5 Import-Engine

```python
import time
from datetime import datetime, timezone

import structlog

from app.models.import_models import (
    DuplicateStrategy,
    ImportJob,
    ImportJobStatus,
    ImportResult,
    PreviewRow,
    RowStatus,
    RowValidationError,
)
from app.repositories.import_job_repository import ImportJobRepository
from app.repositories.species_repository import SpeciesRepository
from app.repositories.cultivar_repository import CultivarRepository
from app.repositories.botanical_family_repository import BotanicalFamilyRepository
from app.services.csv_parser import CsvParser
from app.services.row_validator import RowValidator

logger = structlog.get_logger()

# Lookup-Felder pro Entität für Duplikaterkennung
DUPLICATE_LOOKUP_FIELDS: dict[str, list[str]] = {
    "species": ["scientific_name"],
    "cultivar": ["name", "parent_species"],
    "botanical_family": ["name"],
}


class ImportEngine:
    """Orchestriert den CSV-Import-Prozess."""

    def __init__(
        self,
        import_job_repo: ImportJobRepository,
        species_repo: SpeciesRepository,
        cultivar_repo: CultivarRepository,
        family_repo: BotanicalFamilyRepository,
    ) -> None:
        self._import_job_repo = import_job_repo
        self._species_repo = species_repo
        self._cultivar_repo = cultivar_repo
        self._family_repo = family_repo

    async def upload_and_validate(
        self,
        raw_bytes: bytes,
        entity_type: str,
        filename: str,
        duplicate_strategy: str = "skip",
        delimiter: str | None = None,
    ) -> ImportJob:
        """
        Phase 1: CSV hochladen, parsen, validieren und Vorschau erstellen.

        Returns:
            ImportJob im Status 'preview_ready' oder 'failed'
        """
        job = ImportJob(
            entity_type=entity_type,
            status=ImportJobStatus.VALIDATING,
            duplicate_strategy=duplicate_strategy,
            original_filename=filename,
            file_size_bytes=len(raw_bytes),
            created_at=datetime.now(tz=timezone.utc),
        )

        # CSV parsen
        parser = CsvParser(entity_type)
        encoding = parser.detect_encoding(raw_bytes)
        job.encoding = encoding

        rows, structure_errors = parser.parse(raw_bytes, delimiter=delimiter)
        if delimiter:
            job.delimiter = delimiter
        else:
            text = raw_bytes.decode(encoding)
            first_line = text.strip().splitlines()[0] if text.strip() else ""
            job.delimiter = parser.detect_delimiter(first_line)

        if structure_errors:
            job.status = ImportJobStatus.FAILED
            job.import_result = ImportResult(
                errors=[
                    RowValidationError(field="__structure__", code=e["code"], message=e["message"])
                    for e in structure_errors
                ]
            )
            return await self._import_job_repo.save(job)

        # Zeilen validieren
        validator = RowValidator(entity_type, CsvParser(entity_type)._columns)
        preview_rows: list[PreviewRow] = []

        for row in rows:
            row_number = row.pop("_row_number", 0)
            preview = validator.validate_row(row, row_number)
            preview_rows.append(preview)

        # Duplikate prüfen
        await self._check_duplicates(preview_rows, entity_type)

        job.total_rows = len(preview_rows)
        job.valid_rows = sum(1 for r in preview_rows if r.status == RowStatus.VALID)
        job.invalid_rows = sum(1 for r in preview_rows if r.status == RowStatus.INVALID)
        job.duplicate_rows = sum(1 for r in preview_rows if r.is_duplicate)
        job.preview_data = preview_rows
        job.status = ImportJobStatus.PREVIEW_READY

        return await self._import_job_repo.save(job)

    async def confirm_import(self, job_key: str) -> ImportJob:
        """
        Phase 2: Bestätigten Import ausführen.

        Importiert nur Zeilen mit status 'valid' (und ggf. 'duplicate' bei update-Strategie).
        """
        job = await self._import_job_repo.get(job_key)
        if not job:
            raise ValueError(f"Import-Job '{job_key}' nicht gefunden")
        if job.status != ImportJobStatus.PREVIEW_READY:
            raise ValueError(
                f"Import-Job hat Status '{job.status}', erwartet: 'preview_ready'"
            )

        job.status = ImportJobStatus.IMPORTING
        job.confirmed_at = datetime.now(tz=timezone.utc)
        await self._import_job_repo.update_status(job)

        start_time = time.monotonic()
        result = ImportResult()

        repo = self._get_repo(job.entity_type)

        for row in job.preview_data:
            if row.status == RowStatus.INVALID:
                result.records_failed += 1
                continue

            if row.is_duplicate:
                if job.duplicate_strategy == DuplicateStrategy.SKIP:
                    result.records_skipped += 1
                    continue
                elif job.duplicate_strategy == DuplicateStrategy.FAIL:
                    result.records_failed += 1
                    result.errors.append(RowValidationError(
                        field="__duplicate__",
                        code="DUPLICATE_FOUND",
                        message=f"Zeile {row.row_number}: Duplikat gefunden (Strategie: fail)",
                    ))
                    continue
                elif job.duplicate_strategy == DuplicateStrategy.UPDATE:
                    try:
                        await repo.update(row.existing_key, row.data)
                        result.records_updated += 1
                    except Exception as exc:
                        result.records_failed += 1
                        result.errors.append(RowValidationError(
                            field="__import__",
                            code="UPDATE_FAILED",
                            message=f"Zeile {row.row_number}: {exc}",
                        ))
                    continue

            # Neuer Datensatz
            try:
                await repo.create(row.data)
                result.records_created += 1
            except Exception as exc:
                result.records_failed += 1
                result.errors.append(RowValidationError(
                    field="__import__",
                    code="CREATE_FAILED",
                    message=f"Zeile {row.row_number}: {exc}",
                ))

        result.duration_ms = int((time.monotonic() - start_time) * 1000)
        job.import_result = result
        job.status = ImportJobStatus.COMPLETED
        job.completed_at = datetime.now(tz=timezone.utc)

        logger.info(
            "import_completed",
            job_key=job_key,
            entity_type=job.entity_type,
            created=result.records_created,
            updated=result.records_updated,
            skipped=result.records_skipped,
            failed=result.records_failed,
        )

        return await self._import_job_repo.update_result(job)

    async def _check_duplicates(
        self,
        rows: list[PreviewRow],
        entity_type: str,
    ) -> None:
        """Prüft Zeilen auf existierende Duplikate in der Datenbank."""
        repo = self._get_repo(entity_type)
        lookup_fields = DUPLICATE_LOOKUP_FIELDS[entity_type]

        for row in rows:
            if row.status == RowStatus.INVALID:
                continue

            lookup_values = {f: row.data.get(f) for f in lookup_fields}
            if all(v for v in lookup_values.values()):
                existing = await repo.find_by_lookup(lookup_values)
                if existing:
                    row.is_duplicate = True
                    row.status = RowStatus.DUPLICATE
                    row.existing_key = existing["_key"]

    def _get_repo(self, entity_type: str):
        """Gibt das passende Repository für den Entitätstyp zurück."""
        repos = {
            "species": self._species_repo,
            "cultivar": self._cultivar_repo,
            "botanical_family": self._family_repo,
        }
        return repos[entity_type]
```

### 3.6 REST-API Endpunkte

```python
from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile

from app.models.import_models import DuplicateStrategy, EntityType, ImportJob
from app.services.import_engine import ImportEngine

router = APIRouter(prefix="/api/v1/import", tags=["import"])


@router.post("/upload", response_model=ImportJob)
async def upload_csv(
    file: UploadFile = File(...),
    entity_type: EntityType = Query(..., description="Ziel-Entität"),
    duplicate_strategy: DuplicateStrategy = Query(
        DuplicateStrategy.SKIP, description="Duplikatbehandlung"
    ),
    delimiter: str | None = Query(None, description="CSV-Trennzeichen (auto-detect wenn leer)"),
    engine: ImportEngine = Depends(get_import_engine),
) -> ImportJob:
    """
    Phase 1: CSV-Datei hochladen und validieren.
    Gibt Import-Job mit Vorschau zurück.
    """
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(400, "Nur CSV-Dateien erlaubt")

    raw_bytes = await file.read()

    if len(raw_bytes) > 10 * 1024 * 1024:  # 10 MB
        raise HTTPException(413, "Datei überschreitet maximale Größe von 10 MB")

    if len(raw_bytes) == 0:
        raise HTTPException(400, "Leere Datei")

    job = await engine.upload_and_validate(
        raw_bytes=raw_bytes,
        entity_type=entity_type.value,
        filename=file.filename,
        duplicate_strategy=duplicate_strategy.value,
        delimiter=delimiter,
    )
    return job


@router.post("/jobs/{job_key}/confirm", response_model=ImportJob)
async def confirm_import(
    job_key: str,
    engine: ImportEngine = Depends(get_import_engine),
) -> ImportJob:
    """
    Phase 2: Validierten Import bestätigen und ausführen.
    Nur möglich wenn Job im Status 'preview_ready'.
    """
    try:
        return await engine.confirm_import(job_key)
    except ValueError as exc:
        raise HTTPException(400, str(exc))


@router.get("/jobs/{job_key}", response_model=ImportJob)
async def get_import_job(
    job_key: str,
    import_job_repo=Depends(get_import_job_repo),
) -> ImportJob:
    """Gibt den aktuellen Status eines Import-Jobs zurück."""
    job = await import_job_repo.get(job_key)
    if not job:
        raise HTTPException(404, f"Import-Job '{job_key}' nicht gefunden")
    return job


@router.get("/jobs", response_model=list[ImportJob])
async def list_import_jobs(
    entity_type: EntityType | None = Query(None),
    limit: int = Query(20, ge=1, le=100),
    import_job_repo=Depends(get_import_job_repo),
) -> list[ImportJob]:
    """Listet Import-Jobs (optional gefiltert nach Entitätstyp)."""
    return await import_job_repo.list_jobs(entity_type=entity_type, limit=limit)


@router.delete("/jobs/{job_key}")
async def cancel_import_job(
    job_key: str,
    import_job_repo=Depends(get_import_job_repo),
) -> dict:
    """
    Bricht einen Import-Job ab (nur im Status 'preview_ready').
    Löscht den Job aus der Datenbank.
    """
    job = await import_job_repo.get(job_key)
    if not job:
        raise HTTPException(404, f"Import-Job '{job_key}' nicht gefunden")
    if job.status not in ("uploaded", "validating", "preview_ready"):
        raise HTTPException(
            409,
            f"Job im Status '{job.status}' kann nicht abgebrochen werden",
        )
    await import_job_repo.delete(job_key)
    return {"deleted": job_key}


@router.get("/templates/{entity_type}")
async def download_csv_template(
    entity_type: EntityType,
) -> dict:
    """
    Gibt CSV-Template-Header und Beispielzeile für eine Entität zurück.
    Der Client generiert daraus eine herunterladbare CSV-Datei.
    """
    templates = {
        EntityType.SPECIES: {
            "headers": [
                "scientific_name", "common_names", "family", "genus",
                "cycle_type", "photoperiod_type", "growth_habit", "root_type",
                "hardiness_zones", "allelopathy_score", "native_habitat",
            ],
            "example": [
                "Solanum lycopersicum", "Tomate;Tomato", "Solanaceae", "Solanum",
                "annual", "day_neutral", "herb", "fibrous",
                "7a;7b;8a", "0.0", "Südamerika",
            ],
        },
        EntityType.CULTIVAR: {
            "headers": [
                "name", "parent_species", "breeder", "breeding_year",
                "traits", "days_to_maturity", "disease_resistances", "patent_status",
            ],
            "example": [
                "San Marzano", "Solanum lycopersicum", "INRA", "1926",
                "disease_resistant;high_yield", "78", "fusarium;verticillium", "public_domain",
            ],
        },
        EntityType.BOTANICAL_FAMILY: {
            "headers": [
                "name", "typical_nutrient_demand", "common_pests", "rotation_category",
            ],
            "example": [
                "Solanaceae", "heavy", "Blattläuse;Weiße Fliege", "Nachtschattengewächse",
            ],
        },
    }
    return templates[entity_type]
```

### 3.7 Validierungsregeln (Zusammenfassung)

| Regel | Beschreibung | Fehlercode |
|-------|-------------|------------|
| Pflichtfelder | Fehlende Werte in Pflichtfeldern | `REQUIRED_FIELD` |
| Typen | Integer/Float nicht parsbar | `INVALID_TYPE` |
| Wertebereiche | Numerische Werte außerhalb der Grenzen | `VALUE_TOO_LOW` / `VALUE_TOO_HIGH` |
| Enum-Werte | Wert nicht in erlaubter Menge | `INVALID_ENUM` |
| Scientific Name | Binomiale Nomenklatur (z.B. "Genus species") | `INVALID_FORMAT` |
| Genus-Konsistenz | `genus` muss erstem Wort von `scientific_name` entsprechen | `GENUS_MISMATCH` |
| Hardiness Zones | Format `\d{1,2}[ab]` (z.B. "7a") | `INVALID_FORMAT` |
| Traits | Nur vordefinierte Trait-Keys erlaubt | `INVALID_TRAIT` |
| Duplikate (DB) | Datensatz existiert bereits in der Datenbank | `DUPLICATE_FOUND` |
| Header-Spalten | Pflichtspalten fehlen in CSV-Header | `MISSING_COLUMNS` |
| Dateistruktur | Leere Datei oder fehlender Header | `EMPTY_FILE` / `NO_HEADER` |

## 4. Frontend-Spezifikation

### 4.1 Upload-Dialog

**Route:** `/import`

**Komponente:** `ImportUploadPage`

```
┌──────────────────────────────────────────────────────────┐
│  Stammdaten-Import                                        │
│                                                           │
│  ┌─────────────────────────────────────────────────────┐  │
│  │           Entitätstyp auswählen                     │  │
│  │  ○ Species   ○ Cultivar   ○ BotanicalFamily        │  │
│  └─────────────────────────────────────────────────────┘  │
│                                                           │
│  ┌─────────────────────────────────────────────────────┐  │
│  │  Duplikatbehandlung                                 │  │
│  │  [  Skip (Überspringen)           ▼]               │  │
│  └─────────────────────────────────────────────────────┘  │
│                                                           │
│  ┌ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ┐  │
│  │                                                     │  │
│  │    CSV-Datei hierher ziehen                         │  │
│  │    oder klicken zum Auswählen                       │  │
│  │                                                     │  │
│  │    Max. 10 MB, UTF-8                                │  │
│  └ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ┘  │
│                                                           │
│  [CSV-Template herunterladen]                             │
│                                                           │
│                              [Hochladen und Validieren]   │
└──────────────────────────────────────────────────────────┘
```

**Verhalten:**
- Drag & Drop oder Dateiauswahl-Dialog
- Nur `.csv`-Dateien akzeptiert
- Nach Upload: automatische Weiterleitung zur Preview-Seite
- "CSV-Template herunterladen" ruft `GET /api/v1/import/templates/{entity_type}` auf und generiert Download

### 4.2 Preview-Tabelle

**Route:** `/import/jobs/:jobKey/preview`

**Komponente:** `ImportPreviewPage`

```
┌──────────────────────────────────────────────────────────────────┐
│  Import-Vorschau: mein_artenkatalog.csv                          │
│                                                                   │
│  Zusammenfassung:                                                 │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐        │
│  │   150    │  │   142    │  │    5     │  │    3     │        │
│  │  Gesamt  │  │  Gültig  │  │ Fehler   │  │ Duplikate│        │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘        │
│                                                                   │
│  Filter: [Alle ▼]  [Nur Fehler]  [Nur Duplikate]                │
│                                                                   │
│  ┌────┬──────────────────────┬────────────┬────────┬──────────┐  │
│  │ #  │ scientific_name      │ family     │ Status │ Fehler   │  │
│  ├────┼──────────────────────┼────────────┼────────┼──────────┤  │
│  │  1 │ Solanum lycopersicum │ Solanaceae │ ✓ OK   │          │  │
│  │  2 │ (leer)               │ Lamiaceae  │ ✗ Err  │ Pflicht- │  │
│  │    │                      │            │        │ feld     │  │
│  │  3 │ Cannabis sativa      │ Cannabacea │ ⚠ Dup  │ Exists:  │  │
│  │    │                      │            │        │ species_ │  │
│  │    │                      │            │        │ 42       │  │
│  │ .. │ ...                  │ ...        │ ...    │ ...      │  │
│  └────┴──────────────────────┴────────────┴────────┴──────────┘  │
│                                                                   │
│  Strategie: Skip (3 Duplikate werden übersprungen)               │
│                                                                   │
│  [Abbrechen]                             [Import bestätigen (142)]│
└──────────────────────────────────────────────────────────────────┘
```

**Verhalten:**
- MUI `DataGrid` mit Sortierung und Filterung
- Farbkodierung: Grün (valid), Rot (invalid), Gelb (duplicate)
- Fehler-Details per Tooltip oder expandierbare Zeile
- "Import bestätigen" nur aktiv wenn `valid_rows > 0`
- Zahl in Button zeigt Anzahl der tatsächlich zu importierenden Datensätze

### 4.3 Ergebnis-Anzeige

**Route:** `/import/jobs/:jobKey/result`

**Komponente:** `ImportResultPage`

```
┌──────────────────────────────────────────────────────────┐
│  Import abgeschlossen                                     │
│                                                           │
│  ┌──────────────────────────────────────────────────────┐│
│  │  ✓  142 Datensätze erstellt                          ││
│  │  ↻    0 Datensätze aktualisiert                      ││
│  │  →    3 Datensätze übersprungen (Duplikate)           ││
│  │  ✗    5 Datensätze fehlgeschlagen                    ││
│  │  ⏱  2.340 ms                                         ││
│  └──────────────────────────────────────────────────────┘│
│                                                           │
│  Fehlerdetails (5):                                       │
│  ┌────┬──────────────┬────────────────────────────────┐  │
│  │  # │ Feld         │ Fehler                          │  │
│  ├────┼──────────────┼────────────────────────────────┤  │
│  │  2 │ scientific_  │ scientific_name ist ein         │  │
│  │    │ name         │ Pflichtfeld                     │  │
│  │ .. │ ...          │ ...                             │  │
│  └────┴──────────────┴────────────────────────────────┘  │
│                                                           │
│  [Neuer Import]                    [Zur Stammdatenliste]  │
└──────────────────────────────────────────────────────────┘
```

**Verhalten:**
- Automatische Anzeige nach Abschluss des Imports
- Fehler-Tabelle nur sichtbar wenn `records_failed > 0`
- "Neuer Import" führt zurück zu Upload-Dialog
- "Zur Stammdatenliste" navigiert zur entsprechenden Entitäts-Listenseite

### 4.4 Import-Historie

**Route:** `/import/history`

**Komponente:** `ImportHistoryPage`

```
┌──────────────────────────────────────────────────────────────────┐
│  Import-Historie                                                  │
│                                                                   │
│  Filter: [Alle Entitäten ▼]                                      │
│                                                                   │
│  ┌──────────┬──────────┬──────────┬────────┬──────────┬────────┐ │
│  │ Datum    │ Datei    │ Entität  │ Status │ Erstellt │ Fehler │ │
│  ├──────────┼──────────┼──────────┼────────┼──────────┼────────┤ │
│  │ 26.02.  │ arten.   │ Species  │ ✓ Done │   142    │   5    │ │
│  │ 14:30   │ csv      │          │        │          │        │ │
│  │ 25.02.  │ sorten.  │ Cultivar │ ✓ Done │    38    │   0    │ │
│  │ 09:15   │ csv      │          │        │          │        │ │
│  │ 24.02.  │ familien │ Botan.   │ ✗ Fail │     0    │  12    │ │
│  │ 16:00   │ .csv     │ Family   │        │          │        │ │
│  └──────────┴──────────┴──────────┴────────┴──────────┴────────┘ │
└──────────────────────────────────────────────────────────────────┘
```

### 4.5 Hinweistexte (Helper Texts)

Alle Eingabefelder im Upload-Dialog müssen mit einem erklärenden Hinweistext versehen sein (MUI `helperText`-Prop). Die Texte werden per i18n bereitgestellt (DE/EN).

| Feld | Hinweistext (DE) | Hinweistext (EN) |
|------|-----------------|------------------|
| Entitätstyp | "Welche Stammdaten-Entität soll importiert werden?" | "Which master data entity should be imported?" |
| Duplikatbehandlung | "Legt fest, wie mit bereits existierenden Datensätzen umgegangen wird. Skip = überspringen, Update = aktualisieren, Fail = Abbruch." | "Defines how existing records are handled. Skip = ignore, Update = merge, Fail = abort." |
| CSV-Datei (Dropzone) | "CSV-Datei mit Header-Zeile. Multiwert-Felder mit Semikolon trennen. Max. 10 MB, UTF-8." | "CSV file with header row. Separate multi-value fields with semicolons. Max 10 MB, UTF-8." |
| Trennzeichen | "Wird automatisch erkannt. Nur bei Fehlern manuell setzen (Komma, Semikolon, Tab)." | "Auto-detected. Only set manually if detection fails (comma, semicolon, tab)." |

**Umsetzungsregel:** Kein Eingabefeld darf ohne `helperText` gerendert werden. Dies gilt auch für zukünftige Erweiterungen des Upload-Dialogs.

### 4.6 Navigation

- Neuer Menüpunkt "Import" in der Sidebar unter "Stammdaten"
- Import-Historie als Untermenüpunkt
- i18n-Keys für DE/EN:
  - `import.title` → "Stammdaten-Import" / "Master Data Import"
  - `import.upload` → "Hochladen und Validieren" / "Upload and Validate"
  - `import.preview` → "Import-Vorschau" / "Import Preview"
  - `import.confirm` → "Import bestätigen" / "Confirm Import"
  - `import.result` → "Import abgeschlossen" / "Import Completed"
  - `import.history` → "Import-Historie" / "Import History"
  - `import.duplicate.skip` → "Überspringen" / "Skip"
  - `import.duplicate.update` → "Aktualisieren" / "Update"
  - `import.duplicate.fail` → "Abbrechen bei Duplikat" / "Fail on Duplicate"

## 5. Authentifizierung & Autorisierung

> **Hinweis (SEC-H-001):** Dieser Abschnitt wurde nachträglich ergänzt, um die Auth-Anforderungen
> gemäß REQ-023 (Authentifizierung) und REQ-024 (Mandantenverwaltung) zu dokumentieren.

**Standardregel:** Alle Endpunkte dieses REQ erfordern Authentifizierung (JWT Bearer Token)
und Tenant-Mitgliedschaft, sofern nicht anders angegeben.

| Ressource/Endpoint-Gruppe | Lesen | Schreiben | Löschen |
|---------------------------|-------|-----------|---------|
| CSV-Import (Upload & Ausführung) | — | Admin | — |
| Import-Validierung (Dry-Run) | — | Admin | — |
| Import-History | Admin | — | — |
| Template-Download | Ja | — | — |

## 6. Abhängigkeiten

**Benötigt:**
- **REQ-001** (Stammdatenverwaltung) — Ziel-Entitäten (Species, Cultivar, BotanicalFamily), Validierungsregeln, Datenmodell
- **REQ-011** (Externe Stammdatenanreicherung) — Importierte Datensätze können anschließend extern angereichert werden
- **NFR-006** (API-Fehlerbehandlung) — Einheitliche Fehlerbehandlung und Error-Codes

**Systemabhängigkeiten:**
- ArangoDB (Persistenz der Import-Jobs und Stammdaten)
- `chardet` (Encoding-Erkennung für CSV-Dateien)
- MUI `DataGrid` (Frontend-Vorschautabelle)

**Wird benötigt von:**
- REQ-001 (Stammdaten) — Bulk-Import als Alternative zur Einzelanlage
- REQ-011 (Anreicherung) — Importierte Stammdaten als Sync-Kandidaten

## 7. Akzeptanzkriterien

### Definition of Done (DoD):

- [ ] **CSV-Upload:** Datei-Upload via REST-API mit Encoding- und Delimiter-Erkennung
- [ ] **Drei Entitäten:** Import für Species, Cultivar und BotanicalFamily funktionsfähig
- [ ] **Zwei-Phasen-Prozess:** Upload → Vorschau → Bestätigung → Import
- [ ] **Zeilen-Validierung:** Jede Zeile wird gegen Spaltendefinitionen und Cross-Field-Regeln geprüft
- [ ] **Duplikaterkennung:** Abgleich gegen bestehende Datenbank-Einträge per Identifikationsmerkmale
- [ ] **Konfigurierbare Duplikatstrategie:** skip/update/fail pro Import wählbar
- [ ] **Vorschau-Tabelle:** MUI DataGrid mit Farbkodierung, Filterung, Sortierung
- [ ] **Fehlerdetails:** Pro-Zeile/Pro-Feld-Fehlermeldungen mit Codes
- [ ] **Ergebnis-Anzeige:** Statistiken (created/updated/skipped/failed) nach Abschluss
- [ ] **Import-Historie:** Übersicht aller bisherigen Import-Jobs mit Filterung
- [ ] **CSV-Templates:** Herunterladbare Vorlagen mit Header und Beispielzeile pro Entität
- [ ] **Dateivalidierung:** Größenlimit (10 MB), Dateityp (.csv), Encoding-Prüfung
- [ ] **Abbruch:** Import-Jobs im Status preview_ready können abgebrochen werden
- [ ] **i18n:** Alle UI-Texte in DE/EN über react-i18next
- [ ] **Testabdeckung:** Unit-Tests für Parser, Validator und Engine; Integration-Tests für API-Endpoints

### Testszenarien:

**Szenario 1: Erfolgreicher Species-Import**
```
GIVEN: CSV-Datei mit 10 gültigen Species-Zeilen, keine Duplikate im System
WHEN: Upload + Validierung + Bestätigung
THEN:
  - Phase 1: Job im Status 'preview_ready', 10 valid_rows, 0 invalid_rows
  - Phase 2: 10 records_created, 0 errors
  - Alle 10 Species in der Datenbank auffindbar
```

**Szenario 2: Validierungsfehler in mehreren Zeilen**
```
GIVEN: CSV mit 5 Zeilen, davon 2 mit fehlendem scientific_name und 1 mit ungültigem cycle_type
WHEN: Upload + Validierung
THEN:
  - Preview zeigt 2 valid, 3 invalid
  - Fehler-Details pro Zeile: REQUIRED_FIELD (Zeile 2, 4), INVALID_ENUM (Zeile 5)
  - "Import bestätigen" importiert nur die 2 gültigen Zeilen
```

**Szenario 3: Duplikatbehandlung — Skip (Default)**
```
GIVEN: "Solanum lycopersicum" existiert bereits im System
WHEN: CSV mit 3 Zeilen hochgeladen, davon 1 mit "Solanum lycopersicum"
THEN:
  - Preview: 2 valid, 1 duplicate (status 'duplicate', existing_key angezeigt)
  - Nach Bestätigung: 2 records_created, 1 records_skipped
  - Bestehender Datensatz unverändert
```

**Szenario 4: Duplikatbehandlung — Update**
```
GIVEN: "Ocimum basilicum" mit allelopathy_score=0.0 im System
WHEN: CSV mit "Ocimum basilicum", allelopathy_score=0.5, Strategie "update"
THEN:
  - Preview: Zeile als 'duplicate' markiert
  - Nach Bestätigung: 1 records_updated
  - allelopathy_score im System ist nun 0.5
```

**Szenario 5: Duplikatbehandlung — Fail**
```
GIVEN: "Cannabis sativa" existiert bereits im System
WHEN: CSV mit "Cannabis sativa", Strategie "fail"
THEN:
  - Preview: Zeile als 'duplicate' markiert
  - Nach Bestätigung: 1 records_failed
  - Fehlermeldung "Duplikat gefunden (Strategie: fail)"
```

**Szenario 6: Cultivar-Import mit Fremdschlüssel-Prüfung**
```
GIVEN: Species "Solanum lycopersicum" existiert im System
WHEN: Cultivar-CSV mit parent_species="Solanum lycopersicum" hochgeladen
THEN:
  - Validierung prüft Existenz der parent_species
  - Bei nicht-existierender parent_species: INVALID_FORMAT Fehler
  - Bei existierender parent_species: Cultivar wird erstellt und der Species zugeordnet
```

**Szenario 7: Encoding- und Delimiter-Erkennung**
```
GIVEN: CSV-Datei mit UTF-8 BOM und Semikolon als Trennzeichen
WHEN: Upload ohne explizite Angabe von Encoding/Delimiter
THEN:
  - System erkennt UTF-8-sig Encoding automatisch
  - Semikolon wird als Delimiter erkannt
  - Alle Zeilen werden korrekt geparst
```

**Szenario 8: Genus-Konsistenz bei Species**
```
GIVEN: CSV-Zeile mit scientific_name="Solanum lycopersicum", genus="Capsicum"
WHEN: Validierung
THEN:
  - Fehler GENUS_MISMATCH: "genus 'Capsicum' stimmt nicht mit scientific_name überein (erwartet: 'Solanum')"
  - Zeile wird als 'invalid' markiert
```

---

**Hinweise für RAG-Integration:**
- Keywords: CSV-Import, Bulk-Import, Stammdaten, Upload, Vorschau, Duplikatbehandlung
- Fachbegriffe: Zwei-Phasen-Import, Preview, Duplikatstrategie, Zeilen-Validierung, Cross-Field-Validierung
- Verknüpfung: Erweitert REQ-001, komplementär zu REQ-011, nutzt NFR-006
