# Spezifikation: REQ-019 - Substratverwaltung

```yaml
ID: REQ-019
Titel: Substrat-Konfiguration und Lebenszyklusverwaltung
Kategorie: Infrastruktur
Fokus: Beides
Technologie: Python, ArangoDB
Status: Entwurf
Version: 4.0
```

## 1. Business Case

**User Story:** "Als Gärtner möchte ich Substrate und deren Chargen verwalten, um pH/EC-Verlauf, Wiederverwendbarkeit und Aufbereitungsbedarf im Blick zu behalten."

**Beschreibung:**
Das System verwaltet Substrate als wiederverwendbare Definitionen mit konkreten Chargen (Batches). Jede Charge trackt ihren Zustand über Zyklen hinweg und liefert Empfehlungen zur Wiederverwendung und Aufbereitung.

**Substrat-Typen:**
- **Erdmischungen** (Zusammensetzung, pH-Pufferung, Nährstoff-Vorrat)
- **Hydro/Inert-Medien** (Steinwolle, Cocos, Blähton, Perlite)
- **Living Soil** (Mikrobiom-Tracking, No-Till-Strategien)

**Kernfunktionen:**
- Batch-Tracking mit pH/EC-Verlauf über Anbauzyklen
- Wiederverwendbarkeits-Prüfung (pH-Drift, Salzakkumulation, Zyklen)
- Aufbereitungs-Anleitungen je Substrattyp (Entsalzung, Pufferung, Mikrobiom-Reaktivierung)
- Zuordnung von Chargen zu Slots (über `filled_with`-Edge)

## 2. ArangoDB-Modellierung

### Nodes:

- **`:Substrate`** - Substrat-Definition
  - Properties:
    - `type: Literal['soil', 'coco', 'rockwool', 'clay_pebbles', 'perlite', 'living_soil', 'hydro_solution']`
    - `brand: Optional[str]`
    - `ph_base: float`
    - `ec_base_ms: float` (Vorgedüngt oder inert)
    - `water_retention: Literal['low', 'medium', 'high']`
    - `air_porosity_percent: float`
    - `composition: dict[str, float]` (z.B. {"peat": 0.4, "compost": 0.3, "perlite": 0.3})
    - `buffer_capacity: Literal['low', 'medium', 'high']`
    - `reusable: bool`

- **`:SubstrateBatch`** - Konkrete Substrat-Charge
  - Properties:
    - `batch_id: str`
    - `volume_liters: float`
    - `mixed_on: date`
    - `last_amended: Optional[date]`
    - `cycles_used: int`
    - `ph_current: Optional[float]`
    - `ec_current_ms: Optional[float]`

### Edges (ArangoDB Edge Collections):
```
filled_with:     slots → substrate_batches              (Slot nutzt Substrat-Charge)
uses_type:       substrate_batches → substrates          (Charge basiert auf Substrat-Definition)
grown_in:        plant_instances → substrate_batches      (Pflanze wächst in Charge)
```

## 3. Technische Umsetzung (Python)

### Logik-Anforderungen:

**1. Substrat-Recycling-Tracker:**
```python
from datetime import date, timedelta
from typing import Optional
from pydantic import BaseModel, Field

class SubstrateLifecycleManager(BaseModel):
    """Tracking von Substrat-Wiederverwendung und Erschöpfung"""

    substrate_type: str
    initial_volume_liters: float
    max_reuse_cycles: int = Field(default=3)
    current_cycle: int = Field(default=0)
    ph_history: list[float] = Field(default_factory=list)
    ec_history: list[float] = Field(default_factory=list)

    def can_reuse(self) -> tuple[bool, Optional[str]]:
        """Prüft ob Substrat wiederverwendbar ist"""

        # Einweg-Substrat
        if self.substrate_type in ['rockwool', 'peat_plugs']:
            return False, "Einweg-Substrat nicht wiederverwendbar"

        # Max Zyklen erreicht
        if self.current_cycle >= self.max_reuse_cycles:
            return False, f"Maximale Wiederverwendung ({self.max_reuse_cycles} Zyklen) erreicht"

        # pH-Drift-Check
        if len(self.ph_history) >= 2:
            ph_drift = abs(self.ph_history[-1] - self.ph_history[0])
            if ph_drift > 1.5:
                return False, f"Zu starke pH-Drift ({ph_drift:.1f} Einheiten)"

        # Salzakkumulation-Check (EC-Anstieg)
        if len(self.ec_history) >= 2:
            if self.substrate_type in ['coco', 'living_soil']:
                ec_increase = self.ec_history[-1] - self.ec_history[0]
                if ec_increase > 1.0:
                    return False, f"Salzakkumulation kritisch (EC +{ec_increase:.1f})"

        return True, None

    def prepare_for_reuse(self) -> dict:
        """Gibt Anweisungen zur Substrat-Aufbereitung"""

        treatments = []

        if self.substrate_type == 'coco':
            treatments.append({
                'step': 'Puffern',
                'action': 'Mit CalMag-Lösung (EC 1.2) durchspülen',
                'duration_hours': 24
            })

        if self.substrate_type in ['living_soil', 'compost_mix']:
            treatments.append({
                'step': 'Nachkompostierung',
                'action': 'Mit Wurm-Kompost und Gesteinsmehl mischen',
                'duration_days': 14
            })
            treatments.append({
                'step': 'Mikrobiom-Reaktivierung',
                'action': 'Komposttee-Gabe (500ml/10L Substrat)',
                'duration_hours': 0
            })

        if any(ec > 2.0 for ec in self.ec_history[-3:]):
            treatments.insert(0, {
                'step': 'Entsalzung',
                'action': 'Mit pH-neutralem Wasser durchspülen (3x Volumen)',
                'duration_hours': 2
            })

        return {
            'treatments': treatments,
            'estimated_prep_time': sum(
                t.get('duration_hours', 0) for t in treatments
            ) + sum(t.get('duration_days', 0) * 24 for t in treatments),
            'ready_date': date.today() + timedelta(
                days=max([t.get('duration_days', 0) for t in treatments] or [0])
            )
        }
```

### Datenvalidierung:
```python
from typing import Literal

SubstrateType = Literal[
    'soil', 'coco', 'peat', 'rockwool', 'clay_pebbles',
    'perlite', 'vermiculite', 'living_soil', 'hydro_solution'
]
```

## 4. Abhängigkeiten

**Erforderliche Module:**
- REQ-002 (Standort): Slot-Zuordnung via `filled_with`-Edge

**Wird benötigt von:**
- REQ-003 (Phasen): Substrattyp beeinflusst Phasen-Parameter
- REQ-004 (Düngung): **HOCH** — Substrat-EC/pH für Düngeberechnung, `buffer_capacity` für Spül-Empfehlungen
- REQ-005 (Sensorik): Substrat-Messwerte (pH, EC, Feuchtigkeit)

## 5. Akzeptanzkriterien

### Definition of Done (DoD):

- [ ] **Substrat-CRUD:** Substrat-Definitionen anlegen, lesen, aktualisieren, löschen
- [ ] **Batch-Tracking:** Chargen mit pH/EC-Verlauf über Zyklen verfolgen
- [ ] **Wiederverwendbarkeits-Check:** Automatische Prüfung auf pH-Drift, Salzakkumulation und Zyklen
- [ ] **Aufbereitungs-Anleitung:** Substrattyp-spezifische Aufbereitungsschritte generieren
- [ ] **Slot-Zuordnung:** Chargen können Slots zugeordnet werden (`filled_with`-Edge)
- [ ] **Pflanzen-Zuordnung:** Pflanzen werden mit Chargen verknüpft (`grown_in`-Edge)
- [ ] **Substrat-Recycling:** Wiederverwendbarkeits-Check mit Aufbereitungs-Anleitung
- [ ] **Reservoir-Management:** Nährlösungs-Wechsel-Scheduler für Hydro-Substrate

### Testszenarien:

**Szenario 1: Substrat-Recycling**
```
GIVEN: Coco-Substrat nach 2 Zyklen, EC-Historie [1.2, 1.8, 2.5]
WHEN: Nutzer prüft Wiederverwendbarkeit
THEN:
  - System erlaubt Wiederverwendung (max 3 Zyklen)
  - Aufbereitungs-Plan: 1) Entsalzung, 2) CalMag-Pufferung
  - Geschätzte Prep-Zeit: 26 Stunden
```

**Szenario 2: Einweg-Substrat ablehnen**
```
GIVEN: Steinwolle-Substrat (rockwool), 1 Zyklus verwendet
WHEN: Nutzer prüft Wiederverwendbarkeit
THEN:
  - System lehnt ab: "Einweg-Substrat nicht wiederverwendbar"
```

**Szenario 3: pH-Drift-Grenzwert**
```
GIVEN: Coco-Substrat, pH-Historie [5.8, 7.5] (Drift = 1.7)
WHEN: Nutzer prüft Wiederverwendbarkeit
THEN:
  - System lehnt ab: "Zu starke pH-Drift (1.7 Einheiten)"
```

**Szenario 4: Living Soil Aufbereitung**
```
GIVEN: Living Soil nach 1 Zyklus, EC ok, pH ok
WHEN: Nutzer bereitet Substrat zur Wiederverwendung vor
THEN:
  - Aufbereitungs-Plan enthält:
    1) Nachkompostierung (14 Tage)
    2) Mikrobiom-Reaktivierung (Komposttee)
  - Geschätztes Fertigstellungsdatum: heute + 14 Tage
```

---

**Hinweise für RAG-Integration:**
- Keywords: Substrat, Charge, Batch, pH, EC, Wiederverwendung, Recycling, Aufbereitung, Coco, Living Soil, Rockwool, Perlite
- Technische Begriffe: SubstrateLifecycleManager, pH-Drift, Salzakkumulation, CalMag-Pufferung, Mikrobiom-Reaktivierung
- Verknüpfung: Zentral für REQ-004 (Düngung), REQ-005 (Sensorik), abhängig von REQ-002 (Standort)
