# UZG-005: Professioneller Gewaechshaus-Betrieb

**Version:** 1.0
**Datum:** 2026-03-30
**Kategorie:** Unterversorgte Zielgruppe -- Mittleres Potenzial
**Quelle:** `spec/requirements-analysis/target-audience-analysis.md`

---

## 1. Profil

| Dimension | Beschreibung |
|-----------|-------------|
| **Bezeichnung** | Gewerbliche Zierpflanzen-Produktion (Gaertnerei, Baumschule, Blumenhandel) |
| **Altersgruppe** | 30-60 Jahre |
| **Betriebsgroesse** | 500-10.000 Pflanzen, mehrere Gewaechshaeuser, 5-50 Mitarbeiter |
| **Technische Affinitaet** | Mittel (etablierte Branchensoftware gewohnt) |
| **Botanisches Vorwissen** | Sehr Hoch (Gaertnermeister, Fachpersonal) |
| **Primaere Nutzungsumgebung** | Desktop (Buero), Tablet (Gewaechshaus), Scanner (Logistik) |
| **Abdeckungsgrad** | Nicht adressiert -- Chargen-Management, Pflanzenpasse, Warenwirtschaft fehlen |
| **Marktpotenzial** | Gross aber schwer zugaenglich (etablierte Branchensoftware) |

## 2. Persona

**Name:** Stefan, 45, Gaertnermeister und Inhaber einer Zierpflanzen-Gaertnerei
**Situation:** Betreibt 3 Gewaechshaeuser (je 500 m2) fuer Beet- und Balkonpflanzen. Produziert saisonal 15.000 Pflanzen fuer Grosshandel und Endkunden. Hat 8 Mitarbeiter, einen Bewaesserungscomputer und eine einfache Warenwirtschaft. Muss seit 2020 Pflanzenpasse (EU-Pflanzengesundheits-VO) ausstellen. Nutzt aktuell Hortisystems fuer Bestellwesen und Excel fuer Kulturplanung. Sucht eine guenstigere Alternative.

**Motivation:**
- Chargen-Management: Anzucht -> Kultur -> Verkauf als Charge
- Pflanzenpasse nach EU-VO 2016/2031 generieren
- Lieferschein-Erstellung mit EAN-Barcodes
- Bewaesserungscomputer-Anbindung (Senmatic, Priva)
- Kosten-Controlling pro Charge und Kultur

## 3. Kernbeduerfnisse

### 3.1 Chargen-Management (Teilweise via REQ-013)
- PlantingRun als Produktions-Charge (Sorte, Menge, Aussaat-Datum)
- Chargen-Nummer: Eindeutig, druckbar als Barcode
- Status-Tracking: Aussaat -> Pikieren -> Topfen -> Kulturfertig -> Versandfertig
- Qualitaets-Sortierung: A-Ware, B-Ware, Ausschuss
- Schwund-Tracking: Ausfallquote pro Charge

### 3.2 Pflanzenpasse (Fehlend)
- EU-VO 2016/2031 konforme Pflanzenpaesse
- Pflichtfelder: Botanischer Name, Registriernummer, Rueckverfolgbarkeits-Code, Ursprungsland
- QR-Code auf Pflanzenpass
- Batch-Druck: 500 Pflanzenpasse pro Charge
- Verknuepfung mit Chargen-Nummer

### 3.3 Lieferschein und Logistik (Fehlend)
- Lieferschein generieren: Kunde, Artikel, Menge, Chargen-Nr., Pflanzenpass-Nr.
- EAN-13 Barcodes pro Artikel
- Kommissionierung: Pickliste fuer Gewaechshaus-Mitarbeiter
- CC-Container (Danish Trolley) Verwaltung: Pflanzen pro Wagen
- Versand-Etiketten drucken

### 3.4 Warenwirtschafts-Integration (REQ-016)
- InvenTree fuer Betriebsmittel (Toepfe, Substrate, Duenger, Pflanzenschutz)
- Bestandsfuehrung: Mindestbestand-Warnung
- Verbrauchs-Zuordnung: Welche Charge hat wieviel Material verbraucht?
- Einkaufs-Integration: Bestellvorschlaege basierend auf Kulturplan

### 3.5 Bewaesserungscomputer-Anbindung (Fehlend)
- Integration mit Senmatic, Priva, Ridder (gaengige Gewaechshaus-Steuerungen)
- EC/pH-Daten aus dem Bewaesserungscomputer lesen
- Klima-Daten: Temperatur, Luftfeuchte, Schirm-Position, Lueftung
- Bidirektional: Sollwerte aus Kamerplanter an Steuerung senden

### 3.6 Kosten-Controlling
- Kosten pro Charge: Substrat + Toepfe + Jungpflanzen + Duenger + Energie + Arbeit
- Gestehungskosten pro Pflanze
- Deckungsbeitrag pro Kultur
- Energie-Kostenverteilung pro Gewaechshaus
- Saisonale Auswertung

### 3.7 Pflanzenschutz-Dokumentation (REQ-010)
- Pflanzenschutzmittel-Anwendung dokumentieren (Pflicht nach PflSchG)
- Wartefrist (Karenz) bei Schnittrosen etc.
- Nuetzlings-Einsatz dokumentieren
- Bio-Betrieb: Nur zugelassene Mittel

## 4. Typische Workflows

### 4.1 Saison-Planung (Winter)
1. Kulturplan erstellen: Welche Sorten in welchen Mengen?
2. Gewaechshaus-Belegung planen (Tischflaechen pro Kultur)
3. Jungpflanzen-Bestellung aufgeben
4. Substrat- und Topf-Bedarf kalkulieren
5. Energie-Budget planen (Heizkosten pro Gewaechshaus)

### 4.2 Produktion (Saison)
1. Chargen anlegen: Jungpflanzen empfangen, Charge starten
2. Topfen: Jungpflanze in Verkaufstopf umsetzen
3. Kultur-Massnahmen: Stutzen, Bewurzelung, Bewaesserung, Duengung
4. Pflanzenschutz: Inspektionen, Behandlungen dokumentieren
5. Qualitaets-Sortierung: A/B/Ausschuss
6. Versandfertig: Pflanzenpass drucken, Etikettieren

### 4.3 Auslieferung
1. Bestellung erfassen (Grosshandel oder Endkunde)
2. Kommissionierung: Pickliste erstellen
3. CC-Container beladen
4. Lieferschein generieren
5. Pflanzenpass-Nummern auf Lieferschein
6. Versand

### 4.4 Monats-Controlling
1. Chargen-Auswertung: Schwund, Kosten, Ertrag
2. Gewaechshaus-Kosten: Energie, Wasser, Arbeit
3. Deckungsbeitrag pro Kultur
4. Vergleich Plan vs. Ist
5. Naechsten Monat anpassen

## 5. Relevante Anforderungsdokumente

| REQ | Relevanz | Kernfunktion fuer diese Zielgruppe |
|-----|----------|-----------------------------------|
| REQ-001 | Hoch | Stammdaten (Zierpflanzen-Sorten) |
| REQ-002 | Hoch | Gewaechshaus-Flaechen, Tisch-Management |
| REQ-004 | Hoch | Duenge-Logik (fuer Substrat-Kultur) |
| REQ-010 | Kritisch | Pflanzenschutz-Dokumentation (PflSchG) |
| REQ-013 | Kritisch | Chargen/Batch-Management |
| REQ-016 | Hoch | InvenTree/Warenwirtschaft |
| REQ-023 | Hoch | Service Accounts (Bewaesserungscomputer) |
| REQ-024 | Hoch | Multi-User (Inhaber, Meister, Mitarbeiter) |

## 6. Abgrenzung zu anderen Zielgruppen

| Merkmal | UZG-005 (Gewaechshaus) | ZG-006 (Hydroponik) | UZG-002 (Marktgaertner) |
|---------|:-:|:-:|:-:|
| Pflanzen-Zahl | 500-10.000 | 50-500 | 200-5.000 |
| Produkt | Zierpflanzen | Gemuese/Kraeuter | Gemuese |
| Pflanzenpasse | Kritisch (EU-VO) | Nein | Nein |
| Warenwirtschaft | Kritisch | Nein | Teilweise |
| Logistik | Kritisch (CC-Container, Lieferschein) | Minimal | Abo-Kiste |
| Bewaesserungscomputer | Ja (Senmatic, Priva) | Nein (HA/MQTT) | Nein |

## 7. Evaluationskriterien

1. **Chargen-Management:** Kann eine Produktions-Charge mit Status-Tracking angelegt werden?
2. **Pflanzenpass:** Kann ein EU-konformer Pflanzenpass generiert und gedruckt werden?
3. **Lieferschein:** Kann ein Lieferschein mit Chargen-Nummern erstellt werden?
4. **Barcode:** Koennen EAN-Barcodes fuer Artikel generiert werden?
5. **Kosten-pro-Pflanze:** Koennen Gestehungskosten pro Pflanze berechnet werden?
6. **Pflanzenschutz-Nachweis:** Sind Behandlungen PflSchG-konform dokumentiert?
7. **Warenwirtschaft:** Kann der Bestand an Betriebsmitteln verwaltet werden?
8. **Schwund-Tracking:** Wird die Ausfallquote pro Charge berechnet?
9. **Gewaechshaus-Belegung:** Kann die Tischflaechen-Belegung geplant werden?
10. **Bewaesserungscomputer:** Koennen Daten aus Senmatic/Priva importiert werden?

## 8. Sprachstil und Fachbegriffe

Professionelle Gaertner-Fachsprache plus Logistik-Terminologie:

- **Charge / Los** (Batch), **Partie** (Liefereinheit)
- **Pflanzenpass** (Plant Passport -- EU-VO 2016/2031)
- **CC-Container / Daenischer Wagen** (Danish Trolley)
- **Tischkultur** (Bench Culture), **Tischflaeche** (Bench Area)
- **Topfen** (Potting), **Stutzen** (Pinching), **Bewurzeln** (Rooting)
- **Kulturfertig / Versandfertig** (Production stages)
- **Gestehungskosten** (Cost of Goods), **Deckungsbeitrag** (Contribution Margin)
- **PflSchG** (Pflanzenschutzgesetz), **Sachkunde** (Certified Applicator)
- **Nuetzlings-Einsatz** (Biological Control), **Raubmilbe**, **Schlupfwespe**
- **Senmatic / Priva / Ridder** (Gewaechshaus-Steuerungssysteme)
- **EAN** (European Article Number), **Lieferschein** (Delivery Note)
