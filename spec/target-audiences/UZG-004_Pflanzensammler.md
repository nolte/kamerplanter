# UZG-004: Orchideen-/Bromelien-/Kakteen-Sammler

**Version:** 1.0
**Datum:** 2026-03-30
**Kategorie:** Unterversorgte Zielgruppe -- Mittleres Potenzial
**Quelle:** `spec/requirements-analysis/target-audience-analysis.md`

---

## 1. Profil

| Dimension | Beschreibung |
|-----------|-------------|
| **Bezeichnung** | Leidenschaftlicher Pflanzensammler mit Spezialisierung auf eine Gattung |
| **Altersgruppe** | 35-70 Jahre |
| **Betriebsgroesse** | 50-500 Exemplare einer oder weniger Gattungen |
| **Technische Affinitaet** | Gering bis Mittel |
| **Botanisches Vorwissen** | Sehr Hoch (Gattungs-Spezialist) |
| **Primaere Nutzungsumgebung** | Desktop (Dokumentation), Smartphone (Foto-Dokumentation) |
| **Abdeckungsgrad** | Minimal adressiert -- CITES-Doku, Bluete-Kalender, Tauschboerse fehlen |
| **Marktpotenzial** | Mittelgross mit hoher Zahlungsbereitschaft |

## 2. Persona

**Name:** Brigitte, 58, pensionierte Apothekerin und Orchideen-Sammlerin
**Situation:** Sammelt seit 25 Jahren Orchideen, besitzt 180 Exemplare in einem Wintergarten und einem klimatisierten Orchideen-Raum (temperiert, warm, kalt). Dokumentiert akribisch: Kaufdatum, Herkunft, Umtopf-Datum, Bluetezeitpunkte. Hat CITES-Bescheinigungen fuer 12 Wildfang-Orchideen die sie importiert hat. Ist aktives Mitglied der Deutschen Orchideen-Gesellschaft (DOG) und tauscht regelmaessig Pflanzen und Setzlinge mit anderen Sammlern. Plant Kreuzungen und dokumentiert deren Ergebnisse ueber Jahre.

**Motivation:**
- Lueckenlose Dokumentation jedes Exemplars (Herkunft, Kauf, Pflege-Historie)
- Bluete-Tracking: Wann hat welche Orchidee geblueht? Wie lange? Wie oft?
- Kreuzungs-Dokumentation: Elternpflanzen, Saemlings-Entwicklung, Phaenotyen
- CITES-Nachweis-Verwaltung (Import-Dokumente, Herkunfts-Zertifikate)
- Tausch- und Verkaufs-Management (mit anderen Sammlern)

## 3. Kernbeduerfnisse

### 3.1 Exemplar-Dokumentation (REQ-001, REQ-003)
- Jede Pflanze als individuelles Exemplar mit eindeutiger Nummer
- Herkunft: Gaertnerei, Wildstandort, Import, Tausch (von wem?)
- Kaufdatum, Kaufpreis, CITES-Nummer (falls relevant)
- Foto-Galerie pro Exemplar (Habitus, Bluete, Wurzeln, Krankheiten)
- Umtopf-Historie: Datum, neues Substrat, Topfgroesse
- Standort-Wechsel-Historie (welcher Raum/Bereich wann?)

### 3.2 Bluete-Tracking (Fehlend)
- Bluete-Kalender: Wann beginnt/endet die Bluete jedes Exemplars?
- Bluete-Dauer in Tagen
- Bluete-Qualitaet: Anzahl Bluetenstaengel, Anzahl Blueten, Groesse
- Jahresvergleich: Blueht diese Orchidee dieses Jahr besser/schlechter?
- Aggregierte Ansicht: "Im Maerz bluehen 15 Orchideen"
- Bluete-Foto mit Datum (Dokumentation der Farb-Variationen)

### 3.3 Kreuzungs-Dokumentation (REQ-017)
- Elternpflanzen: Vater (Pollenspender) x Mutter (Samentraeger)
- Kreuzungs-Datum, Bestaeubungs-Methode
- Samenkapsel-Entwicklung tracken (Monate bis Reife)
- Aussaat-Dokumentation (Naehloesung, Flasche, Datum)
- Saemlings-Entwicklung ueber Jahre (erste Bluete nach 3-7 Jahren)
- Phaenotyp-Bewertung: Farbe, Form, Groesse, Duft
- Genetischer Stammbaum (descended_from Graph)

### 3.4 CITES-Dokumentation (Fehlend)
- CITES-Anhang I/II/III pro Art
- Import-Genehmigung: Nummer, Ausstellungsdatum, Behoerde
- Herkunfts-Nachweis: Wildsammlung vs. Kuenstliche Vermehrung
- Dokument-Scan/Foto speichern
- Warnung bei Verkauf/Tausch: "CITES-pflichtig -- Papiere beilegen!"

### 3.5 Substrat-Spezialisierung (REQ-019)
- Orchideen-Substrate: Rinden-Mix, Sphagnum, Kork, Lava, Bims
- Mischverhaeltnisse dokumentieren (z.B. 60% Rinde, 20% Sphagnum, 20% Perlite)
- Umtopf-Zyklen: Orchideen alle 2-3 Jahre, Kakteen seltener
- Substrate pro Gattung/Art unterschiedlich

### 3.6 Klimazonen-Management (REQ-002)
- Verschiedene Klimabereiche: temperiert (15-18°C), warm (18-25°C), kalt (10-15°C)
- Pflanzen dem passenden Klimabereich zuordnen
- Saisonale Temperatur-Anpassung (Kuehl-Phase als Bluete-Trigger)
- Luftfeuchte-Anforderungen pro Gattung

### 3.7 Tausch und Verkauf (Fehlend)
- Tausch-Angebot erstellen: Pflanze mit Foto, Beschreibung, Groesse
- Tausch-Partner verwalten (Name, Kontakt, bisherige Tausche)
- Verkaufs-Historie: Wer hat was wann erhalten?
- Community-Integration: Vereins-Mitglieder als Tausch-Netzwerk

### 3.8 Pflege-Kalender (REQ-022)
- Orchideen-Preset: Tauchen statt Giessen, Nebeln, Duengen (1x/Woche Sommer, 1x/Monat Winter)
- Kakteen-Preset: Trockenpause (November-Februar), volle Sonne
- Bromelien-Preset: Trichter fuellen, Nebeln
- Art-spezifische Sonderpflege (z.B. Dendrobium-Kuehlphase als Bluete-Trigger)

## 4. Typische Workflows

### 4.1 Neue Pflanze registrieren
1. Pflanze erhalten (Kauf, Tausch, Import)
2. Im System anlegen: Art, Herkunft, Preis, Datum
3. Foto-Dokumentation (Habitus, Wurzeln, Etikett)
4. CITES-Dokument scannen und anhaengen (falls zutreffend)
5. Standort zuweisen (Klimabereich)
6. Pflege-Profil wird automatisch vorgeschlagen

### 4.2 Bluete dokumentieren
1. Orchidee beginnt zu bluehen
2. Bluete-Start erfassen (Datum, Anzahl Staengel)
3. Foto der Bluete aufnehmen
4. Woechentlich: Bluete-Entwicklung dokumentieren
5. Bluete-Ende erfassen (Gesamtdauer)
6. Qualitaets-Bewertung: Anzahl Blueten, Groesse, Duft
7. Vergleich mit Vorjahren

### 4.3 Kreuzung durchfuehren
1. Vater- und Mutterpflanze auswaehlen
2. Bestaeubung durchfuehren und dokumentieren
3. Samenkapsel-Entwicklung ueber Monate tracken
4. Aussaat dokumentieren (in vitro oder konventionell)
5. Saemlings-Wachstum ueber Jahre verfolgen
6. Erste Bluete: Phaenotyp bewerten und dokumentieren
7. Beste Saemblinge fuer weitere Kreuzungen auswaehlen

### 4.4 Sammlung verwalten (monatlich)
1. Alle Exemplare durchgehen: Zustand pruefen
2. Umtopf-Faellige identifizieren
3. Bluete-Kalender pruefen: Wer blueht bald?
4. Tausch-Angebote erstellen (Ableger, ueberzaehlige Pflanzen)
5. Statistik: Sammlung nach Gattung, Herkunft, Wert

## 5. Relevante Anforderungsdokumente

| REQ | Relevanz | Kernfunktion fuer diese Zielgruppe |
|-----|----------|-----------------------------------|
| REQ-001 | Kritisch | Stammdaten mit Gattungs-spezifischen Feldern |
| REQ-002 | Hoch | Klimazonen als Standorte |
| REQ-003 | Hoch | Perenniale Zyklen, Bluete-Phasen |
| REQ-010 | Mittel | Schaedlinge (Schildlaeuse, Wollaeuse an Orchideen) |
| REQ-017 | Kritisch | Kreuzungs-Dokumentation, Genetischer Stammbaum |
| REQ-019 | Hoch | Spezial-Substrate (Orchideenrinde, Sphagnum) |
| REQ-022 | Hoch | Orchideen/Kakteen/Bromelien-Presets |

## 6. Abgrenzung zu anderen Zielgruppen

| Merkmal | UZG-004 (Sammler) | ZG-003 (Zimmer-Enthusiast) | ZG-001 (Cannabis) |
|---------|:-:|:-:|:-:|
| Artenvielfalt | Gering (1-3 Gattungen) | Hoch (viele Arten) | Minimal (1 Art) |
| Exemplar-Zahl | Hoch (50-500) | Mittel (5-80) | Gering (4-50) |
| Dokumentations-Tiefe | Sehr Hoch (akribisch) | Gering | Hoch |
| Bluete-Tracking | Kritisch | Irrelevant | Irrelevant |
| Kreuzungen | Wichtig | Selten | Teilweise |
| CITES | Teilweise relevant | Irrelevant | Irrelevant |
| Tausch/Verkauf | Wichtig | Nein | Nein |
| Zeitskala | Jahre bis Jahrzehnte | Monate | Wochen bis Monate |

## 7. Evaluationskriterien

1. **Exemplar-Dokumentation:** Kann jedes Exemplar mit Herkunft, Kaufdatum und Foto erfasst werden?
2. **Bluete-Tracking:** Kann Bluete-Start/Ende/Dauer pro Exemplar dokumentiert werden?
3. **Bluete-Kalender:** Gibt es eine Monatsansicht welche Pflanzen wann bluehen?
4. **Kreuzungs-Stammbaum:** Ist der Pedigree einer Kreuzung ueber Generationen darstellbar?
5. **CITES-Nachweis:** Koennen Import-Dokumente an ein Exemplar angehaengt werden?
6. **Foto-Galerie:** Kann eine chronologische Foto-Serie pro Exemplar gefuehrt werden?
7. **Klimabereich-Zuordnung:** Koennen verschiedene Temperaturbereiche als Standorte verwaltet werden?
8. **Tausch-Dokumentation:** Kann ein Tausch mit Partner-Name und Datum erfasst werden?
9. **Substrat-Mix:** Kann ein individueller Substrat-Mix pro Pflanze dokumentiert werden?
10. **Sammlungs-Statistik:** Gibt es eine Uebersicht der Sammlung nach Gattung/Herkunft/Wert?

## 8. Sprachstil und Fachbegriffe

Tiefe botanische Fachsprache, lateinische Artennamen gelaefuig:

- **Epiphyt** (auf Baeumen wachsend), **Lithophyt** (auf Felsen), **Terrestrisch** (im Boden)
- **Infloreszenz** (Bluetenstand), **Rispe, Traube, Aehre** (Bluetenstand-Typen)
- **Pollen** (Bluetenstaub), **Pollinie** (Orchideen-spezifisch)
- **Meristem** (Wachstumsgewebe), **In-vitro** (Laborvermehrung)
- **CITES** (Washingtoner Artenschutzabkommen)
- **Habitat / Wildstandort** (natuerlicher Fundort)
- **Klon** (vegetativ identisch), **Grex** (Orchideen-Kreuzungsname)
- **Nomenklatur** (Artbezeichnung nach ICBN-Regeln)
- **Photoperiodismus** (Blueteinduktion durch Licht)
- **Vernalisation** (Kuehl-Phase als Bluete-Trigger)
- **Velamen** (Orchideen-Wurzelhuelle)
- **Pseudobulbe** (Orchideen-Speicherorgan)
