# UZG-002: Marktgaertner / CSA-Betrieb / Mikro-Farm

**Version:** 1.0
**Datum:** 2026-03-30
**Kategorie:** Unterversorgte Zielgruppe -- Hohes Potenzial (nicht adressiert)
**Quelle:** `spec/requirements-analysis/target-audience-analysis.md`

---

## 1. Profil

| Dimension | Beschreibung |
|-----------|-------------|
| **Bezeichnung** | Kleinbetrieb mit Direktvermarktung (Wochenmarkt, Abo-Kiste, Restaurant) |
| **Altersgruppe** | 28-55 Jahre |
| **Betriebsgroesse** | 0,1-2 ha, 200-5.000 Pflanzen, 1-5 Mitarbeiter |
| **Technische Affinitaet** | Mittel |
| **Botanisches Vorwissen** | Sehr Hoch (professionell) |
| **Primaere Nutzungsumgebung** | Tablet (Feld), Desktop (Buero/Planung) |
| **Abdeckungsgrad** | Nicht adressiert -- Betriebswirtschaftliche Funktionen fehlen |
| **Marktpotenzial** | Wachsend: 8.000-12.000 Kleinstbetriebe in DE, 15-20% Wachstum/Jahr |

## 2. Persona

**Name:** Moritz, 40, Bio-Gaertner und Marktgaertner
**Situation:** Betreibt seit 5 Jahren eine 0,5 ha Marktgaertnerei am Stadtrand. Produziert 30 Gemuesekulturen fuer Wochenmarkt und 25 Abo-Kisten. Hat 2 Saisonkraefte und arbeitet nach Permakultur-Prinzipien (Mischkultur, Gruenduengung, minimale Bodenbearbeitung). Plant aktuell auf Papier und in Excel-Tabellen. Braucht eine Flaechenbelegungsplanung die ihm sagt wann welches Beet frei wird und was er wann ernten kann. Muss seinen Abo-Kisten-Kunden zuverlaessig Ware liefern.

**Motivation:**
- Flaechenbelegungsplan: Welche Kultur steht wann auf welchem Beet?
- Mengenplanung: Wann kann ich wieviel ernten? Reicht es fuer die Abo-Kisten?
- Deckungsbeitragsrechnung: Lohnt sich Radicchio oder soll ich mehr Salat anbauen?
- Team-Koordination: Wer erntet heute was?
- Betriebsmittel-Kontrolle: Saatgut, Jungpflanzen, Duenger, Mulch-Verbrauch

## 3. Kernbeduerfnisse

### 3.1 Flaechenbelegungsplanung (Fehlend)
- Gantt-Ansicht pro Beet: Welche Kultur belegt wann welche Flaeche?
- Vor- und Nachkultur automatisch beruecksichtigen
- Anbauluecken erkennen und Vorschlaege fuer Zwischenkulturen
- Grafische Beetplan-Ansicht (2D-Layout)
- Integration mit Fruchtfolge (REQ-002): Familien-Rotation ueber Jahre

### 3.2 Mengenplanung und Ernteprognose (Teilweise vorhanden)
- Rueckwaerts-Rechnung: Wie viele Pflanzen brauche ich fuer X kg Ernte?
- Ernte-Fenster-Prognose basierend auf Aussaat-Datum und GDD
- Sukzessions-Planung (REQ-013): Alle 2 Wochen 100 Salate
- Kunden-Bedarf abgleichen: Reicht die Ernte fuer 25 Abo-Kisten?
- Ausfallquote einkalkulieren (10-20% Reserve)

### 3.3 Deckungsbeitragsrechnung (Fehlend -- empfohlen als REQ-031)
- Kostentraeger pro Kultur: Saatgut + Jungpflanzen + Duenger + Substrat + Wasser + Strom + Arbeitszeit
- Saatgut-Einkaufspreise in Stammdaten (REQ-001)
- Arbeitszeit-Erfassung pro Aufgabe (Stundensaetze)
- Energiekosten-Kalkulator (Gewaechshaus-Heizung, Bewaesserung)
- Erloese: Kg-Preis pro Kultur
- Deckungsbeitrag = Erloes - Variable Kosten
- ROI-Vergleich: Welche Kulturen sind am rentabelsten?
- Monats-/Saison-Auswertung

### 3.4 Team-Koordination (REQ-006, REQ-024)
- Tages-Ernteplan: Wer erntet welches Beet wieviel?
- Aufgaben-Zuweisung an Mitarbeiter
- Einfache mobile Ansicht fuer Saisonkraefte (nur eigene Aufgaben)
- Stunden-Erfassung (Feldarbeit, Ernte, Verpackung, Auslieferung)

### 3.5 Saatgut und Jungpflanzen-Verwaltung
- Saatgut-Bestand: Restmenge, Keimfaehigkeit, Erntejahr
- Jungpflanzen-Anzucht: Aussaat -> Pikieren -> Abhaerten -> Auspflanzen
- Bestellliste generieren: Was muss nachbestellt werden?
- Integration mit Mengenplanung: Saatgut-Bedarf = Pflanzenzahl * (1 + Ausfallquote)

### 3.6 Kunden und Lieferung (Fehlend)
- Abo-Kisten-Kunden verwalten (Name, Adresse, Praeferenzen)
- Wochentliche Kisten-Zusammenstellung planen
- Lieferschein generieren
- Kunden-Kommunikation: "Diese Woche gibt es..." Newsletter

### 3.7 Bio-Dokumentation
- Betriebsmittel-Nachweis fuer Bio-Zertifizierung
- Duenger- und Pflanzenschutz-Dokumentation
- Saatgut-Herkunft (bio-zertifiziert, samenfest)
- Flaechen-Nutzung pro Kultur

## 4. Typische Workflows

### 4.1 Jahresplanung (Winter)
1. Vorjahres-Ertraege auswerten (Was lief gut/schlecht?)
2. Deckungsbeitraege vergleichen (lohnende vs. unlohnende Kulturen)
3. Anbauplan erstellen: Welche Kultur auf welches Beet?
4. Fruchtfolge pruefen (Familien-Rotation)
5. Saatgut-Bestellliste generieren
6. Sukzessions-Plan fuer Salat, Radieschen, Kohlrabi
7. Mischkultur-Kombinationen planen

### 4.2 Ernte-Woche (Saison)
1. Montag: Ernte-Plan pruefen (welche Beete sind erntereif?)
2. Mitarbeitern Ernte-Aufgaben zuweisen
3. Ernte durchfuehren, Gewichte dokumentieren
4. Abo-Kisten zusammenstellen (25 Kisten a 5 kg)
5. Lieferscheine drucken
6. Ueberproduktion auf Wochenmarkt-Plan setzen

### 4.3 Wochenmarkt-Vorbereitung
1. Ernte-Dashboard: Was ist diese Woche verfuegbar?
2. Mengen abschaetzen (nach Abzug der Abo-Kisten)
3. Preisschilder/Etiketten vorbereiten
4. Markt-Ausbeute dokumentieren (verkaufte Mengen, Retouren)

### 4.4 Kosten-Controlling (monatlich)
1. Betriebsmittel-Verbrauch pruefen (Saatgut, Duenger, Mulch)
2. Arbeitszeiten auswerten
3. Erloese aus Wochenmarkt + Abo-Kisten summieren
4. Deckungsbeitrag pro Kultur berechnen
5. Naechsten Monat anpassen (mehr von Kultur X, weniger von Y)

## 5. Relevante Anforderungsdokumente

| REQ | Relevanz | Kernfunktion fuer diese Zielgruppe |
|-----|----------|-----------------------------------|
| REQ-001 | Hoch | Stammdaten mit Ertrags-Parametern (Ertrag/m2, Kulturdauer) |
| REQ-002 | Kritisch | Flaechenplanung, Beetbelegung, Fruchtfolge |
| REQ-004 | Hoch | Organische Duengung, Bodenanalyse, flaechenbasiert |
| REQ-006 | Kritisch | Aufgabenplanung, Team-Zuweisung |
| REQ-007 | Kritisch | Ernte-Dokumentation, Mengen-Tracking |
| REQ-012 | Hoch | Stammdaten-Import (Kulturdatenbank) |
| REQ-013 | Kritisch | Sukzessions-Aussaat, Batch-Operationen |
| REQ-015 | Hoch | Kalender (Aussaat-, Pflanz-, Erntetermine) |
| REQ-024 | Hoch | Multi-User (Chef + Mitarbeiter) |
| REQ-028 | Hoch | Mischkultur-Planung |

## 6. Abgrenzung zu anderen Zielgruppen

| Merkmal | UZG-002 (Marktgaertner) | ZG-002 (Hobby-Freiland) | ZG-006 (Hydroponik) |
|---------|:-:|:-:|:-:|
| Gewerblich | Ja | Nein | Teilweise |
| Flaechengroesse | 0,1-2 ha | 10-100 m2 | Indoor |
| Kostenrechnung | Kritisch | Irrelevant | Hoch |
| Team-Betrieb | Ja (1-5 MA) | Nein | Gering |
| Kunden-Verwaltung | Kritisch | Nein | Teilweise |
| Kulturen-Anzahl | 20-40 gleichzeitig | 10-20 | 3-10 |
| Bio-Zertifizierung | Oft | Nein | Selten |

## 7. Evaluationskriterien

1. **Flaechenbelegung:** Kann ein Beet mit Vor-, Haupt- und Nachkultur geplant werden?
2. **Fruchtfolge:** Wird vor Familien-Wiederholung auf demselben Beet gewarnt?
3. **Sukzession:** Werden gestaffelte Aussaaten korrekt fuer die Saison geplant?
4. **Ernteprognose:** Wird eine Ernte-Menge basierend auf Pflanzenzahl und Ertrag/Pflanze geschaetzt?
5. **Deckungsbeitrag:** Koennen variable Kosten einer Kultur den Erloesen gegenubergestellt werden?
6. **Team-Aufgaben:** Koennen Ernte-Aufgaben an bestimmte Mitarbeiter delegiert werden?
7. **Saatgut-Bestand:** Wird der Saatgut-Bestand verwaltet und der Bedarf berechnet?
8. **Mischkultur:** Werden kompatible Kulturen fuer Nachbar-Reihen empfohlen?
9. **Kalender-Uebersicht:** Zeigt der Kalender alle Aussaat/Pflanz/Ernte-Termine ueber die Saison?
10. **Bio-Nachweis:** Koennen Betriebsmittel-Einsaetze fuer die Bio-Kontrolle exportiert werden?

## 8. Sprachstil und Fachbegriffe

Professionelle Garten-Fachsprache plus betriebswirtschaftliche Begriffe:

- **Schlag** (Field Plot), **Beet** (Bed), **Reihe** (Row)
- **Kulturfolge** (Crop Sequence), **Fruchtfolge** (Crop Rotation)
- **Vorkultur/Nachkultur** (Pre-crop/Post-crop), **Zwischenkultur** (Intercrop)
- **Sukzession** (Succession Sowing), **Staffelung**
- **Abo-Kiste / Gemuese-Kiste** (CSA Box / Veggie Box)
- **Deckungsbeitrag** (Contribution Margin), **Variable Kosten**
- **Kulturdauer** (Crop Duration), **Standzeitraum** (Occupation Period)
- **Ertrag/m2** (Yield per Square Meter)
- **Saisonkraft** (Seasonal Worker), **Helfer**
- **Jungpflanze** (Transplant), **Pikieren** (Pricking Out)
- **Bio-Zertifikat** (Organic Certification), **Betriebsmittel-Liste**
- **Marktware** (Market-grade Produce), **Sortierung** (Grading)
- **Lieferschein** (Delivery Note), **Sammelbestellung** (Bulk Order)
