# ZG-006: Hydroponik- und Vertical-Farming-Betreiber

**Version:** 1.0
**Datum:** 2026-03-30
**Kategorie:** Sekundaere Zielgruppe (teilweise adressiert)
**Quelle:** `spec/requirements-analysis/target-audience-analysis.md`

---

## 1. Profil

| Dimension | Beschreibung |
|-----------|-------------|
| **Bezeichnung** | Semi-professioneller Hydroponik-Betreiber / Urban Farm |
| **Altersgruppe** | 28-50 Jahre |
| **Betriebsgroesse** | 50-500 Pflanzen, 1-3 Systeme, vollautomatische Bewaesserung |
| **Technische Affinitaet** | Hoch |
| **Botanisches Vorwissen** | Hoch (spezialisiert auf Hydroponik) |
| **Primaere Nutzungsumgebung** | Desktop (Planung, Monitoring), Tablet (vor Ort) |
| **Abdeckungsgrad** | Teilweise -- Dashboard und Kostenanalyse noch nicht implementiert |

## 2. Persona

**Name:** Kai, 35, Mechatroniker und Indoor-Farming-Enthusiast
**Situation:** Betreibt im Keller ein NFT-System (Nutrient Film Technique) fuer Salat und Kraeuter sowie ein DWC-System (Deep Water Culture) fuer Chili. Hat Home Assistant mit pH-, EC-, Temperatur- und Fuellstand-Sensoren im Einsatz. Verkauft ueberschuessigen Salat an ein lokales Restaurant. Moechte seinen Ertrag pro Watt/Liter optimieren und die Kosten pro Kopfsalat berechnen koennen.

**Motivation:**
- Automatisierte EC/pH-Regelung ueber Home Assistant
- Tank-Management: Naehrloesung mischen, nachfuellen, wechseln
- Ertrag-pro-Ressource-Optimierung (Gramm/Watt, Gramm/Liter)
- Batch-Rotation: Immer eine Ernte bereit (Sukzession)
- Kosten-Controlling: Was kostet ein Kopfsalat in Strom/Naehrstoffe/Substrat?

## 3. Kernbeduerfnisse

### 3.1 Tank-Management (REQ-014)
- Tank-Typen: NFT-Reservoir, DWC-Tank, Rezirkulationssystem, Stammloesung
- Tank-States: Fuellstand, EC, pH, Temperatur (live oder manuell)
- Automatische Misch-Berechnung: Konzentrat -> Arbeits-Loesung
- Naehrloesung-Wechsel-Intervall und Erinnerung
- Rezirkulations-Monitoring: EC-Drift ueber Zeit
- Wasserquellen-Mix: RO-Wasser + Leitungswasser Verhaeltnis

### 3.2 Sensor-Integration (REQ-005)
- Home Assistant als primaere Datenquelle (REST API)
- MQTT fuer Echtzeit-Sensordaten
- Sensor-Typen: pH, EC, Wassertemperatur, Fuellstand, Raumtemperatur, Luftfeuchte
- Fallback-Kette: automatisch (IoT) -> semi-automatisch (HA) -> manuell
- Alarm-Schwellwerte: EC zu hoch, pH ausser Bereich, Fuellstand niedrig

### 3.3 Umgebungssteuerung (REQ-018)
- VPD-Regelkreis mit Hysterese (kein Oszillieren)
- Phase-spezifische Profile (Setzling vs. Wachstum vs. Ernte)
- Aktor-Steuerung: Pumpen, Luefter, Befeuchter, LED-Dimmer
- Prioritaets-System: Manual Override > Safety Rules > Sensor Rules > Schedule
- Graceful Degradation bei HA-Ausfall (Fallback-Tasks)

### 3.4 Naehrstoff-Praezision (REQ-004)
- Multi-Part-Duenger (A+B oder 3-Part-Systeme)
- EC-Budget: Ziel-EC minus Basis-Wasser-EC
- pH-Korrektur: pH-Up/pH-Down Dosierung
- CalMag-Korrektur basierend auf Wasserhaerte
- Naehrstoffplan pro Wachstumsphase
- Runoff-Analyse (bei Drain-to-Waste)

### 3.5 Ertragstracking (REQ-007, REQ-009)
- Yield per Watt (g/W): Ernte-Gewicht / Energieverbrauch
- Yield per Liter (g/L): Ernte-Gewicht / Wasser-Verbrauch
- Yield per Plant: Durchschnittsertrag pro Pflanze
- Batch-Vergleich: Welcher Naehrstoffplan liefert mehr?
- Resource Dashboard: Kosten pro Einheit

### 3.6 Sukzessions-Anbau (REQ-013)
- Gestaffelte Pflanzungen: Alle 2 Wochen neue Setzlinge einsetzen
- Ernte-Planung: Wann ist welche Charge bereit?
- System-Rotation: NFT-Kanal nach Ernte reinigen und neu bepflanzen
- Kontinuierliche Produktion (keine Leerlaufzeiten)

### 3.7 Substrat-Management (REQ-019)
- Hydroponik-Substrate: Steinwolle (Slabs + Plugs), Clay Pebbles, Perlite
- Substrat-Wiederverwendung: Steinwolle-Slabs 2-3 Zyklen, Tonkugeln unbegrenzt
- Vorbehandlung dokumentieren (Steinwolle waessern/pH-korrigieren)
- Substrat-Kosten im Kostenmodell

## 4. Typische Workflows

### 4.1 Tank-Management (taeglich)
1. Dashboard: Tank-Fuellstand, EC, pH pruefen (Live-Sensoren)
2. Bei EC-Drift: Naehrloesung korrigieren (Nachfuellen oder Verdunnen)
3. pH-Korrektur wenn ausserhalb Toleranz
4. Woechentlich: Voller Naehrloesung-Wechsel (Tank leeren, reinigen, neu mischen)
5. Misch-Kalkulator: A+B+CalMag fuer Zielvolumen berechnen

### 4.2 Ernte-Rotation
1. Charge 1 ernten (Gewicht dokumentieren)
2. NFT-Kanal reinigen und desinfizieren
3. Neue Setzlinge einsetzen (aus Anzucht-Station)
4. Naehrstoffplan fuer Setzlings-Phase aktivieren
5. Ernte-Daten mit vorherigen Chargen vergleichen

### 4.3 Sensor-Alarm reagieren
1. Alarm: "EC im DWC-Tank ueber 2.5 mS/cm"
2. Ursache pruefen: Verdunstung? Naehrstoff-Aufnahme ungleich?
3. Korrekturmassnahme: Wasser nachfuellen oder Loesung verduennen
4. Dokumentation: Korrektur-Event loggen
5. Trend pruefen: Passiert das regelmaessig? Naehrstoffplan anpassen?

### 4.4 Kosten-Analyse (monatlich)
1. Strom-Verbrauch: kWh * Tarif (LED, Pumpen, Luefter)
2. Naehrstoff-Verbrauch: Liter Konzentrat * Preis
3. Substrat-Kosten: Steinwolle-Plugs * Preis / Wiederverwendungszyklen
4. Wasser-Kosten: Liter * Tarif (inkl. RO-Verschnitt)
5. Ertrag: kg Ernte * Verkaufspreis
6. Deckungsbeitrag pro Kultur berechnen

## 5. Relevante Anforderungsdokumente

| REQ | Relevanz | Kernfunktion fuer diese Zielgruppe |
|-----|----------|-----------------------------------|
| REQ-004 | Kritisch | EC-Budget, Multi-Part, CalMag, pH-Korrektur |
| REQ-005 | Kritisch | HA/MQTT-Integration, Echtzeit-Sensoren, Alarme |
| REQ-007 | Hoch | Ernte-Dokumentation, Yield-Tracking |
| REQ-009 | Hoch | Resource Dashboard, Cost per Gram, kWh-Tracking |
| REQ-013 | Hoch | Sukzessions-Anbau, Batch-Rotation |
| REQ-014 | Kritisch | Tank-Management (NFT, DWC, Rezirkulation) |
| REQ-018 | Kritisch | VPD-Regelkreis, Aktor-Steuerung, Hysterese |
| REQ-019 | Hoch | Hydroponik-Substrate, Wiederverwendung |

## 6. Abgrenzung zu anderen Zielgruppen

| Merkmal | ZG-006 (Hydroponik) | ZG-001 (Cannabis) | ZG-002 (Freiland) |
|---------|:-:|:-:|:-:|
| Substrat | Soilless (Steinwolle, Ton, NFT) | Coco/Hydro gemischt | Erde |
| Tank-Management | Kritisch | Teilweise | Irrelevant |
| Automatisierung | Vollautomatisch | Teilweise | Gering |
| Ertrag/Kosten-Optimierung | Kritisch (gewerblich) | Nice-to-have | Irrelevant |
| Sensor-Dichte | Hoch (pH, EC, Fuellstand, Temp) | Mittel (VPD, Temp) | Gering (Wetter) |
| Sukzession | Kritisch (kontinuierlich) | Nein (zyklisch) | Saisonal |
| Rezirkulation | Ja (NFT, DWC) | Selten | Nein |

## 7. Evaluationskriterien

1. **Tank-Management:** Kann eine Naehrloesung fuer NFT/DWC korrekt berechnet werden?
2. **Sensor-Live-Daten:** Werden pH, EC, Fuellstand aus HA korrekt angezeigt?
3. **EC-Drift-Monitoring:** Wird ein EC-Trend ueber Zeit dargestellt?
4. **Alarm-System:** Werden Schwellwert-Ueberschreitungen als Alarm ausgeloest?
5. **VPD-Regelung:** Wird der VPD-Sollwert ueber Aktor-Steuerung gehalten?
6. **Sukzession:** Werden gestaffelte Pflanzungen korrekt geplant?
7. **Yield-Tracking:** Werden Ertrag-pro-Watt und Ertrag-pro-Liter berechnet?
8. **Kosten-Kalkulation:** Koennen Produktionskosten pro Einheit berechnet werden?
9. **Rezirkulation:** Wird der Naehrloesung-Wechsel-Intervall ueberwacht?
10. **Substrat-Lifecycle:** Wird die Wiederverwendbarkeit von Steinwolle getrackt?

## 8. Sprachstil und Fachbegriffe

Hochtechnische Fachsprache, oft englisch:

- **NFT** (Nutrient Film Technique), **DWC** (Deep Water Culture)
- **Ebb and Flow** / **Flood and Drain**, **Aeroponics**, **Drip**
- **EC** (mS/cm), **PPM** (Parts per Million), **pH**
- **Rezirkulation** (Recirculating), **Drain-to-Waste** (DTW)
- **Stammloesung** (Stock Solution), **Arbeits-Loesung** (Working Solution)
- **PPFD** (umol/m2/s), **DLI** (Daily Light Integral)
- **Tonkugeln** (Clay Pebbles / Hydroton), **Steinwolle** (Rockwool)
- **Fuellstand** (Water Level), **Reservoir** (Tank)
- **Yield per Watt** (g/W), **Yield per Liter** (g/L)
- **RO-Wasser** (Reverse Osmosis / Umkehrosmose)
- **Dosierpumpe** (Dosing Pump), **Peristaltikpumpe**
- **Biofilm** (unerwuenschter Belag im System)
