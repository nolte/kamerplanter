# ZG-003: Zimmerpflanzen-Enthusiast

**Version:** 1.0
**Datum:** 2026-03-30
**Kategorie:** Primaere Zielgruppe (stark adressiert)
**Quelle:** `spec/analysis/target-audience-analysis.md`

---

## 1. Profil

| Dimension | Beschreibung |
|-----------|-------------|
| **Bezeichnung** | Zimmerpflanzen-Liebhaber (Casual bis Sammler) |
| **Altersgruppe** | 25-55 Jahre (breite Streuung) |
| **Betriebsgroesse** | 5-80 Pflanzen, Wohnung/Haus |
| **Technische Affinitaet** | Gering bis Mittel |
| **Botanisches Vorwissen** | Mittel (kennt die meisten Pflanzennamen, unsicher bei Spezialthemen) |
| **Primaere Nutzungsumgebung** | Smartphone (primaer), Desktop (gelegentlich) |
| **Abdeckungsgrad** | Vollstaendig auf Funktionsebene -- Onboarding-Barrieren bleiben (kein Foto-Einstieg) |

## 2. Persona

**Name:** Julia, 31, Marketing-Managerin
**Situation:** Hat 25 Zimmerpflanzen in einer 3-Zimmer-Wohnung. Monstera, Calathea, diverse Sukkulenten, zwei Orchideen und eine Strelitzia. Kennt die meisten Pflanzennamen, ist aber unsicher bei Substrat-Wahl und Umtopf-Zeitpunkten. Giesst nach Gefuehl, hat aber schon zwei Calathea verloren weil sie die Dormanz nicht beachtet hat. Moechte Erinnerungen fuer artspezifische Pflege und Tipps zur Vermehrung (Ableger von der Monstera verschenken).

**Motivation:**
- Einfache, artspezifische Pflege-Erinnerungen mit minimaler Eingabe
- Saisonale Hinweise (Dormanz im Winter, weniger giessen)
- Vermehrungs-Anleitung (Stecklinge, Teilung, Ableger)
- Substrat-Empfehlung beim Umtopfen
- Schaedlings-Identifikation und Behandlung (Spinnmilben, Thripse)

## 3. Kernbeduerfnisse

### 3.1 Pflege-Erinnerungen (REQ-022)
- 9 Care-Style-Presets: tropical, succulent, orchid, calathea, fern, cactus, citrus, bonsai, carnivorous
- Artspezifische Giess-Intervalle (Monstera: 7-10 Tage, Kaktus: 21-30 Tage)
- Saisonale Anpassung (Winter: laengere Intervalle, Dormanz-Modus)
- Giessmethoden-Anleitung (Tauchen fuer Orchideen, Untersetzer fuer Calathea)
- Ein-Tap-Bestaetigung ("gegossen")
- Adaptive Learning: Intervall passt sich dem Bestaeteigungsverhalten an (+-1 Tag, +-30% Cap)

### 3.2 Onboarding (REQ-020)
- 5-Schritt-Wizard: Erfahrungsstufe -> Pflanzen-Typ -> Standort -> Starter-Kit -> Zusammenfassung
- 9 Starter-Kits (z.B. "Tropische Zimmerpflanzen", "Sukkulenten & Kakteen")
- Schneller Einstieg ohne botanisches Vorwissen
- Erfahrungsstufen-Auswahl: Einsteiger, Fortgeschritten, Experte

### 3.3 Erfahrungsstufen (REQ-021)
- Beginner-Modus: Nur 5 Navigations-Elemente, vereinfachte Formulare
- Fortgeschritten: 8 Navigations-Elemente, mehr Detail-Felder
- Experte: Alle Funktionen sichtbar
- Progressive Disclosure: Komplexe Felder erst bei hoeherer Stufe
- ShowAllFields-Toggle fuer gelegentlichen Zugriff auf Experten-Felder

### 3.4 Vermehrung (REQ-017)
- Zimmerpflanzen-relevante Methoden: Blattsteckling, Stamm-Steckling, Teilung, Kindel/Ableger, Wasser-Bewurzelung
- Einfache Anleitung pro Methode (kein Genetik-Graph noetig)
- Tracking: Welche Pflanze wurde von welcher Mutterpflanze vermehrt?

### 3.5 Substrat-Empfehlung (REQ-019)
- Substrattypen: orchid_bark, pon_mineral, sphagnum, peat, standard_soil
- Mischverhaeltnisse pro Art (Monstera: Erde/Perlite/Orchideenrinde 60/20/20)
- Umtopf-Erinnerung basierend auf Wachstumszyklus

### 3.6 Schaedlings-Erkennung (REQ-010)
- Haeufige Zimmerpflanzen-Schaedlinge: Spinnmilben, Thripse, Wollaeuse, Schildlaeuse, Trauermucken
- Einfache Inspektions-Checkliste (Blaetter umdrehen, Substrat pruefen)
- Behandlungs-Empfehlung (Neem-Oel, Gelbtafeln, Raubmilben)
- Praevention: Quarantaene-Hinweis fuer neue Pflanzen

### 3.7 Perenniale Zyklen (REQ-003)
- Aktiv/Dormanz-Zyklus fuer Zimmerpflanzen
- Saisonale Anpassung: Winter = weniger Wasser, kein Duengen
- Halbschattige vs. sonnige Standorte dokumentieren
- Umstellen im Sommer (z.B. Zitrus raus auf Balkon)

### 3.8 Standort-Verwaltung (REQ-002)
- Einfache Hierarchie: Wohnung -> Raum -> Fenster/Regal
- Lichtverhaeltnisse pro Standort (Sudfenster, Nordfenster, kuenstlich)
- Raumtemperatur und Luftfeuchte (geschaetzt oder aus Sensor)

## 4. Typische Workflows

### 4.1 Erste Einrichtung
1. Onboarding-Wizard durchlaufen (Einsteiger-Level, "Tropische Zimmerpflanzen"-Kit)
2. Raeume/Fenster als Standorte anlegen
3. Erste Pflanzen eintragen (Art auswaehlen, Standort zuweisen)
4. Care-Profile werden automatisch vorgeschlagen (tropical-Preset fuer Monstera)

### 4.2 Taegliche Nutzung
1. App oeffnen -> Pflege-Dashboard zeigt faellige Aufgaben
2. "Monstera giessen" -> Ein-Tap-Bestaetigung
3. Optional: Zustand notieren ("Neue Blatt-Oeffnung")
4. Naechste Erinnerung wird automatisch berechnet

### 4.3 Problem loesen
1. Gelbe Blaetter an Calathea bemerkt
2. Pflanzen-Detail oeffnen -> Diagnose-Hilfe (Standort? Wasser? Schaedlinge?)
3. IPM-Inspektion loggen (Schaedlings-Check)
4. Behandlung dokumentieren (Neem-Oel angewendet)

### 4.4 Pflanze vermehren
1. Monstera-Ableger schneiden
2. Vermehrung im System anlegen (Methode: Stammsteckling, Wasser-Bewurzelung)
3. Bewurzelungs-Phase tracken
4. Nach erfolgreicher Bewurzelung: Neue Pflanze im System (verknuepft mit Mutterpflanze)

### 4.5 Saisonwechsel (Herbst)
1. System zeigt: "5 Pflanzen gehen in Dormanz"
2. Giess-Intervalle werden automatisch verlaengert
3. Erinnerung: "Duengung einstellen bis Maerz"
4. Kuebelpflanzen vom Balkon reinholen (Ueberwinterungs-Hinweis)

## 5. Relevante Anforderungsdokumente

| REQ | Relevanz | Kernfunktion fuer diese Zielgruppe |
|-----|----------|-----------------------------------|
| REQ-001 | Hoch | Species/Cultivar-Stammdaten fuer Zimmerpflanzen |
| REQ-002 | Mittel | Standorte (Raum, Fenster, Lichtverhaeltnisse) |
| REQ-003 | Hoch | Perennialer Aktiv/Dormanz-Zyklus |
| REQ-010 | Hoch | Zimmerpflanzen-Schaedlinge, einfache Behandlung |
| REQ-017 | Mittel | Vermehrung (Stecklinge, Teilung, Ableger) |
| REQ-019 | Mittel | Substrat-Empfehlungen beim Umtopfen |
| REQ-020 | Kritisch | Onboarding-Wizard, Starter-Kits |
| REQ-021 | Kritisch | Erfahrungsstufen, Progressive Disclosure |
| REQ-022 | Kritisch | Pflege-Erinnerungen, Care-Style-Presets, Dormanz |
| REQ-027 | Hoch | Light-Modus (Einzelnutzer ohne Login) |

## 6. Abgrenzung zu anderen Zielgruppen

| Merkmal | ZG-003 (Zimmer) | ZG-001 (Cannabis) | ZG-002 (Freiland) |
|---------|:-:|:-:|:-:|
| Pflanzenvielfalt | Hoch (viele Arten) | Niedrig (1 Art) | Mittel |
| Pflege-Komplexitaet | Einfach (Giessen/Duengen) | Hoch (EC/VPD/PPFD) | Mittel |
| Ernte-Relevanz | Keine | Kritisch | Hoch |
| Vermehrung | Gelegentlich, einfach | Systematisch, Genetik | Saatgut-Gewinnung |
| Saisonalitaet | Dormanz-Anpassung | Keine (kuenstlich) | Volle Saison |
| Automatisierung | Nicht erwartet | Hoch erwartet | Gering |
| App-Nutzung | Smartphone, kurz | Desktop + Mobil | Saisonal intensiv |

## 7. Evaluationskriterien

1. **Onboarding:** Kann ein Einsteiger in unter 5 Minuten seine ersten 3 Pflanzen anlegen?
2. **Pflege-Erinnerungen:** Werden artspezifische Giess-Intervalle korrekt berechnet?
3. **Dormanz:** Werden Intervalle im Winter automatisch angepasst?
4. **Ein-Tap-Bestaetigung:** Kann eine Pflege-Aufgabe mit einem Tap bestaetigt werden?
5. **Schaedlings-Hilfe:** Werden haeufige Zimmerpflanzen-Schaedlinge mit Behandlung angezeigt?
6. **Vermehrung:** Kann eine einfache Stecklings-Vermehrung dokumentiert werden?
7. **Substrat-Empfehlung:** Wird beim Umtopfen das richtige Substrat vorgeschlagen?
8. **Erfahrungsstufe:** Sind im Einsteiger-Modus nur relevante Felder sichtbar?
9. **Standort-Licht:** Werden Pflanzen anhand ihrer Lichtbeduerfnisse dem richtigen Standort zugeordnet?
10. **Light-Modus:** Kann die App ohne Login/Registrierung genutzt werden?

## 8. Sprachstil und Fachbegriffe

Diese Zielgruppe nutzt ueberwiegend Alltagssprache:

- **Giessen** (nicht "Bewaessern"), **Duengen** (nicht "Naehrstoffversorgung")
- **Umtopfen** (Repotting), **Ableger** (Cutting/Offset)
- **Sonnig/Halbschattig/Schattig** (statt PPFD-Werte)
- **Blumenerde/Kakteenerde/Orchideenerde** (statt Substrat-Codes)
- **Gelbe Blaetter** (Chlorose), **Braune Spitzen** (Tip Burn)
- **Spinnmilben, Thripse, Trauermucken** (haeufigste Schaedlinge)
- **Neem-Oel, Gelbtafeln** (gaengige Hausmittel)
- **Fensterbank, Regal, Blumenampel** (typische Standorte)
- **Winterruhe/Ruheperiode** (statt "Dormanz")
- **Kindel** (Offsets bei Sukkulenten/Bromelie)
- **Luftwurzeln** (Aerial Roots bei Monstera, Philodendron)
- **Staunasse** (Waterlogging -- haeufigster Fehler)
