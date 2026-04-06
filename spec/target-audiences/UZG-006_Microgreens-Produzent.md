# UZG-006: Kraeuter- und Microgreens-Produzent

**Version:** 1.0
**Datum:** 2026-03-30
**Kategorie:** Unterversorgte Zielgruppe -- Mittleres Potenzial
**Quelle:** `spec/analysis/target-audience-analysis.md`

---

## 1. Profil

| Dimension | Beschreibung |
|-----------|-------------|
| **Bezeichnung** | Microgreens-/Kraeuter-Produzent fuer Gastronomie |
| **Altersgruppe** | 25-45 Jahre |
| **Betriebsgroesse** | 50-500 Trays, Multi-Shelf-Regal, Keller/Container/Gewaechshaus |
| **Technische Affinitaet** | Hoch |
| **Botanisches Vorwissen** | Mittel bis Hoch (spezialisiert auf Kurzzeit-Kulturen) |
| **Primaere Nutzungsumgebung** | Tablet (vor Ort), Desktop (Planung/Bestellungen) |
| **Abdeckungsgrad** | Nicht adressiert -- Rueckwaerts-Planung, Kunden-CRM fehlen |
| **Marktpotenzial** | Wachsend (Gastronomie-Trend seit 2018) |

## 2. Persona

**Name:** Leonie, 30, Ernaehrungswissenschaftlerin und Microgreens-Produzentin
**Situation:** Betreibt seit 2 Jahren eine Microgreens-Produktion in einem umgebauten 20-Fuss-Container. 4 Regale mit je 6 Ebenen, LED-beleuchtet. Produziert Erbsensprossen, Sonnenblumen-Microgreens, Kresse, Radieschen-Microgreens und Brokkoli-Sprossen fuer 8 Restaurants und 3 Cafes. Liefert 2x pro Woche. Die groesste Herausforderung: Timing. Microgreens sind nur 1-2 Tage erntereif, danach zu gross. Muss rueckwaerts vom Liefertag planen.

**Motivation:**
- Rueckwaerts-Planung: Liefertag -> Erntetag -> Aussaattag
- Batch-Rotation: Immer frische Trays bereit, keine Luecken
- Kunden-Bestellungen verwalten und Mengen abgleichen
- Ertrag pro Tray und Kosten pro Tray optimieren
- Klima-Kontrolle: Temperatur und Luftfeuchte pro Regal-Ebene

## 3. Kernbeduerfnisse

### 3.1 Rueckwaerts-Planung (Fehlend)
- Liefertermin als Startpunkt (z.B. Mittwoch und Samstag)
- Kulturdauer rueckwaerts berechnen: Ernte 1 Tag vor Lieferung, Aussaat X Tage vorher
- Verschiedene Kulturdauern pro Art: Kresse 7 Tage, Erbse 12 Tage, Sonnenblume 10 Tage
- Automatische Aussaat-Termine aus Lieferplan ableiten
- Puffer fuer Temperatur-Schwankungen (+-1 Tag)

### 3.2 Batch-Rotation und Sukzession (REQ-013)
- Taeglich neue Trays aussaeen (gestaffelt)
- Ebenen-Belegung: Welches Tray steht auf welcher Ebene?
- Rotation: Nach Ernte -> Reinigen -> Neu saeen
- Keine Leerlaufzeiten: Jede Ebene permanent belegt
- Tray-Status: Ausgesaet -> Dunkelphase -> Lichtphase -> Erntereif -> Geerntet

### 3.3 Kunden-Management (Fehlend)
- Kunden-Stammdaten: Restaurant-Name, Ansprechpartner, Liefertag
- Wiederkehrende Bestellungen: "Restaurant X bekommt jeden Mittwoch 5 Trays Erbsensprossen"
- Ad-hoc-Bestellungen: "Zusaetzlich 3 Trays Kresse diese Woche"
- Mengen-Abgleich: Produktion vs. Bestellungen -> Ueberschuss/Unterdeckung
- Einfache Rechnungs-Grundlage (Menge x Preis)

### 3.4 Kosten und Ertrag (Teilweise)
- Kosten pro Tray: Saatgut + Substrat + Wasser + Strom
- Ertrag pro Tray in Gramm (Ernte-Gewicht)
- Preis pro 100g pro Kultur
- Deckungsbeitrag pro Kultur und pro Kunde
- Strom-Verbrauch: kWh pro Regal-Ebene (LED-Licht)

### 3.5 Klima-Kontrolle (REQ-005, REQ-018)
- Temperatur und Luftfeuchte pro Regal oder pro Raum
- Dunkelphase (24-48h nach Aussaat): Keine Beleuchtung, hohe Feuchte
- Lichtphase: 12-16h Licht, moderate Feuchte
- Sensor-Anbindung via HA/MQTT
- Alarm bei Temperatur-Abweichung (Microgreens sind temperaturempfindlich)

### 3.6 Substrat-Management (REQ-019)
- Typische Substrate: Kokosmatten, Hanfmatten, Vermiculit, Erde
- Substrat pro Kultur: Erbsen auf Kokos, Kresse auf Hanf
- Einweg vs. Kompostierbar
- Substrat-Bestand verwalten (Mindest-Vorrat)

### 3.7 Hygiene und Qualitaet
- Reinigung nach Ernte dokumentieren
- Schimmel-Monitoring (groesstes Risiko bei Microgreens)
- Keimrate pro Charge (Saatgut-Qualitaet)
- Ernte-Foto fuer Qualitaets-Dokumentation

## 4. Typische Workflows

### 4.1 Wochenplanung
1. Kunden-Bestellungen fuer naechste Woche pruefen
2. Rueckwaerts-Berechnung: Wann muss was ausgesaet werden?
3. Ebenen-Belegungsplan erstellen
4. Saatgut-Bedarf pruefen (Vorrat ausreichend?)
5. Substrat-Matten vorbereiten

### 4.2 Taegliche Routine
1. Dashboard: Welche Trays sind heute erntereif?
2. Ernte durchfuehren: Gewicht dokumentieren, Foto
3. Verpacken und Kunden zuordnen
4. Neue Trays aussaeen (laut Plan)
5. Trays in Dunkelphase verschieben / Lichtphase starten
6. Klima pruefen: Temperatur, Luftfeuchte
7. Schimmel-Check auf allen Trays

### 4.3 Liefertag
1. Ernte-Auftraege abarbeiten (pro Kunde)
2. Gewichte dokumentieren
3. Verpacken und etikettieren
4. Lieferschein generieren
5. Ausliefern

### 4.4 Wochen-Review
1. Ertraege pro Kultur auswerten
2. Kosten pro Tray berechnen
3. Kunden-Abrechnungen erstellen
4. Schwund-Rate pruefen (Schimmel, Keimversager)
5. Naechste Woche optimieren

## 5. Relevante Anforderungsdokumente

| REQ | Relevanz | Kernfunktion fuer diese Zielgruppe |
|-----|----------|-----------------------------------|
| REQ-001 | Hoch | Stammdaten: Kulturdauer, Keimtemperatur |
| REQ-005 | Hoch | Sensor-Integration (Temperatur, Feuchte) |
| REQ-007 | Kritisch | Ernte-Dokumentation, Yield-Tracking |
| REQ-013 | Kritisch | Sukzession, Batch-Rotation, Tray-Management |
| REQ-015 | Hoch | Kalender (Aussaat/Ernte/Liefertermine) |
| REQ-018 | Mittel | Klima-Kontrolle, LED-Steuerung |
| REQ-019 | Mittel | Substrat-Verwaltung (Kokos/Hanf-Matten) |

## 6. Abgrenzung zu anderen Zielgruppen

| Merkmal | UZG-006 (Microgreens) | ZG-006 (Hydroponik) | UZG-002 (Marktgaertner) |
|---------|:-:|:-:|:-:|
| Kulturdauer | 5-14 Tage | Wochen-Monate | Monate |
| Rotation | Taeglich | Alle paar Wochen | Saisonal |
| Ernte-Fenster | 1-2 Tage (kritisch eng) | Tage-Wochen | Wochen |
| Kunden-CRM | Kritisch (Gastronomie) | Teilweise | Abo-Kiste |
| Rueckwaerts-Planung | Kritisch | Nein | Teilweise |
| Substrat | Einweg-Matten | Steinwolle/Ton | Erde |
| Tray-basiert | Ja (Tray = Charge) | Nein (System-basiert) | Nein (Beet-basiert) |

## 7. Evaluationskriterien

1. **Rueckwaerts-Planung:** Kann aus einem Liefertag der korrekte Aussaat-Termin berechnet werden?
2. **Batch-Rotation:** Koennen gestaffelte Aussaaten taeglich geplant werden?
3. **Ebenen-Belegung:** Kann nachvollzogen werden welches Tray auf welcher Ebene steht?
4. **Tray-Status:** Wird der Status (Aussaat->Dunkel->Licht->Erntereif) korrekt getrackt?
5. **Kunden-Bestellung:** Koennen wiederkehrende Bestellungen pro Kunde hinterlegt werden?
6. **Mengen-Abgleich:** Wird Produktions-Menge vs. Bestell-Menge verglichen?
7. **Kosten-pro-Tray:** Werden Kosten pro Tray (Saatgut+Substrat+Strom) berechnet?
8. **Keimrate:** Wird die Keimrate pro Saatgut-Charge getrackt?
9. **Schimmel-Monitoring:** Kann Schimmel-Befall dokumentiert und als Schwund erfasst werden?
10. **Klima-Alarm:** Wird bei Temperatur-Abweichung ein Alarm ausgeloest?

## 8. Sprachstil und Fachbegriffe

Mischung aus Gaertner-Fachsprache und Gastronomie-Logistik:

- **Tray** (Anzuchtschale), **Rack / Regal** (Growing Shelf)
- **Microgreens** (Jungpflanzen-Gruenzeug), **Sprossen** (Sprouts)
- **Dunkelphase / Blackout** (Dark Period nach Aussaat)
- **Lichtphase / Greening** (Chlorophyll-Bildung unter LED)
- **Erntereif / Harvestable** (typisch 5-14 Tage nach Aussaat)
- **Batch / Charge** (ein Tray = eine Charge)
- **Kulturdauer** (Seed-to-Harvest in Tagen)
- **Keimrate** (Germination Rate, in %)
- **Just-in-Time** (Ernte am Liefertag)
- **Rueckwaerts-Planung** (Backward Scheduling)
- **Kokosmatte / Hanfmatte** (Substrate Mats)
- **Schimmel** (Mold -- Hauptproblem bei Microgreens)
- **Gramm pro Tray** (Yield Metric)
