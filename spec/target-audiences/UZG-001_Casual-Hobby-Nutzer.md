# UZG-001: Casual Hobby-Nutzer (Pflanzennamen unbekannt)

**Version:** 1.0
**Datum:** 2026-03-30
**Kategorie:** Unterversorgte Zielgruppe -- Hohes Potenzial (nicht adressiert)
**Quelle:** `spec/analysis/target-audience-analysis.md`

---

## 1. Profil

| Dimension | Beschreibung |
|-----------|-------------|
| **Bezeichnung** | Casual Zimmerpflanzen-Besitzer ohne botanisches Vorwissen |
| **Altersgruppe** | 20-35 Jahre |
| **Betriebsgroesse** | 2-15 Pflanzen, Wohnung |
| **Technische Affinitaet** | Mittel (Smartphone-nativ, App-affin) |
| **Botanisches Vorwissen** | Gering bis Keines |
| **Primaere Nutzungsumgebung** | Smartphone (ausschliesslich) |
| **Abdeckungsgrad** | Nicht adressiert -- Foto-basierte Identifikation fehlt als Einstieg |
| **Marktpotenzial** | Sehr gross: 15-20 Mio. Haushalte in Deutschland mit Zimmerpflanzen |

## 2. Persona

**Name:** Lena, 26, UX-Designerin
**Situation:** Hat 6 Zimmerpflanzen in ihrer Einzimmer-Wohnung. Eine davon hat sie von der Oma geerbt (weiss nicht was es ist), zwei vom IKEA (Etikett verloren), eine Sukkulente vom Flohmarkt und zwei geschenkt bekommen. Kennt keinen einzigen botanischen Namen. Giesst alle Pflanzen gleich (einmal pro Woche) und wundert sich warum die Sukkulente fault und die Calathea braune Blattspitzen hat. Hat schon 3 Pflanzen "umgebracht" und fuehlt sich schlecht deswegen. Will einfach nur dass ihre Pflanzen ueberleben.

**Motivation:**
- Pflanze fotografieren und sofort erfahren was es ist und wie man sie pflegt
- Minimaler Aufwand: "Sag mir einfach wann ich giessen soll"
- Kein Fachjargon: Versteht nicht was "Dormanz", "Substrat" oder "EC" bedeutet
- Erfolgserlebnisse: "Meine Pflanze lebt noch!" als Motivator
- Social Sharing: Pflanzen-Fotos in Stories teilen

## 3. Kernbeduerfnisse

### 3.1 Foto-basierte Identifikation (Fehlend -- empfohlen als REQ-029)
- Pflanze fotografieren -> Art wird erkannt -> Pflegeanleitung erscheint
- Konfidenz-Schwelle: >90% automatisch, <90% manuelle Bestaetigung aus Vorschlaegen
- Adapter-Pattern (REQ-011): PlantNet API, Google Vision, PictureThis API
- Integration in Onboarding-Wizard als Step 0 ("Pflanze fotografieren")
- Auch nachtraeglich: "Was ist das fuer eine Pflanze?" mit Foto-Upload

### 3.2 Minimaler Onboarding-Aufwand (REQ-020, REQ-027)
- Light-Modus: Nutzung OHNE Registrierung/Login
- Maximal 3 Schritte bis zur ersten Pflegeerinnerung
- Starter-Kit wird automatisch basierend auf Foto-Erkennung vorgeschlagen
- Keine Abfrage von Erfahrungsstufe -- immer Beginner-Modus
- Keine komplexen Formulare: Nur Name (optional) + Foto + Standort (Sonnig/Halbschattig/Schattig)

### 3.3 Einfachste Pflege-Erinnerungen (REQ-022)
- Push-Benachrichtigung: "Deine Monstera braucht Wasser" (mit Pflanzenfoto)
- Ein-Tap-Bestaetigung: "Gegossen" (kein Formular, kein Kommentar)
- Visueller Ampel-Status: Gruen (alles gut), Gelb (bald faellig), Rot (ueberfaellig)
- Saisonale Anpassung automatisch (kein manueller Eingriff)
- Maximal 3 Aufgaben-Typen: Giessen, Duengen, Umtopfen

### 3.4 Verstaendliche Sprache (REQ-021, UI-NFR-011)
- Kein Fachjargon: "Weniger giessen im Winter" statt "Dormanzphase beachten"
- Einfache Erklaerungen mit Bildern/Icons
- Tooltips fuer jeden nicht-offensichtlichen Begriff
- Fehlermeldungen als Hilfe: "Die Erde ist zu nass" statt "Staunaesse detektiert"

### 3.5 Gamification und Motivation
- Pflanzen-Gesundheits-Score: "Deiner Monstera geht es gut (85%)"
- Streak-Counter: "Du pflegst seit 14 Tagen regelmaessig"
- Meilensteine: "Erste Pflanze 3 Monate am Leben!"
- Neue-Blatt-Tracker: Wachstum dokumentieren (Foto-Vergleich)

### 3.6 Problem-Diagnose (vereinfacht)
- "Meine Pflanze sieht schlecht aus" -> Guided Troubleshooting
- Fragen-Baum: Blaetter gelb? Braune Spitzen? Haengende Blaetter? Weisse Punkte?
- Einfache Antworten: "Wahrscheinlich zu viel Wasser. Giess seltener."
- Optionaler Foto-Upload fuer Schaedlings-Erkennung (Zukunft: KI-basiert)

### 3.7 Social und Sharing
- Pflanzenprofil teilen (Link oder Social Media)
- Vorher/Nachher-Fotos (Wachstums-Fortschritt)
- "Meine Pflanzen-Sammlung" als oeffentliches Profil

## 4. Typische Workflows

### 4.1 Allererster Kontakt
1. App herunterladen (oder Web oeffnen)
2. KEIN Login noetig (Light-Modus)
3. "Fotografiere deine erste Pflanze" (Kamera oeffnet sich)
4. KI erkennt: "Das ist eine Monstera deliciosa!"
5. "Moechtest du Pflege-Erinnerungen?" -> Ja
6. "Wo steht sie?" -> Helles Fenster / Dunkle Ecke / Draussen
7. Fertig: Erste Pflege-Erinnerung in 7 Tagen

### 4.2 Taegliche Nutzung (passiv)
1. Push-Notification: "Deine Monstera braucht Wasser"
2. App oeffnen -> Grossen gruenen Button "Gegossen" druecken
3. Optional: Foto machen ("Neues Blatt!")
4. App schliesst sich -- Gesamtdauer: 10 Sekunden

### 4.3 Problemfall
1. Pflanze sieht schlecht aus
2. App oeffnen -> Pflanze waehlen -> "Hilfe, meine Pflanze sieht krank aus"
3. Guided Troubleshooting: "Sind die Blaetter gelb?" -> Ja
4. "Gelbe untere Blaetter = zu viel Wasser. Warte bis die Erde trocken ist."
5. Giess-Intervall wird automatisch verlaengert

### 4.4 Neue Pflanze hinzufuegen
1. Im Laden eine Pflanze gekauft (kein Etikett)
2. App oeffnen -> "+" -> Foto machen
3. KI: "Das ist wahrscheinlich eine Epipremnum aureum (Efeutute)"
4. Bestaetigen -> Pflege-Profil wird automatisch angelegt
5. Standort waehlen -> Fertig

## 5. Relevante Anforderungsdokumente

| REQ | Relevanz | Kernfunktion fuer diese Zielgruppe |
|-----|----------|-----------------------------------|
| REQ-011 | Kritisch | Adapter-Pattern fuer KI-Bildidentifikation (PlantNet, Google Vision) |
| REQ-020 | Kritisch | Onboarding-Wizard (vereinfacht, Foto-Einstieg als Step 0) |
| REQ-021 | Kritisch | Beginner-Modus (Progressive Disclosure, minimale UI) |
| REQ-022 | Kritisch | Pflege-Erinnerungen (Push, Ein-Tap, Ampel-Status) |
| REQ-027 | Kritisch | Light-Modus (kein Login erforderlich) |
| UI-NFR-011 | Hoch | Fachbegriff-Erklaerungen, Tooltips |

## 6. Abgrenzung zu anderen Zielgruppen

| Merkmal | UZG-001 (Casual) | ZG-003 (Zimmer-Enthusiast) | ZG-002 (Freiland) |
|---------|:-:|:-:|:-:|
| Botanisches Wissen | Keines | Mittel | Mittel-Hoch |
| Pflanzenzahl | 2-15 | 5-80 | 20-200 |
| Interaktions-Frequenz | 10 Sek/Tag (passiv) | 5 Min/Tag | Saisonal intensiv |
| Funktions-Tiefe | Minimal (Giessen only) | Mittel | Hoch |
| Login bereit | Nein (Light-Modus) | Ja | Ja |
| Foto-Identifikation | Kritisch (Einstiegstor) | Nice-to-have | Irrelevant |
| Fachsprache | Unverstaendlich | Teilweise | Gelaefuig |

## 7. Evaluationskriterien

1. **Foto-Identifikation:** Wird eine Pflanze korrekt per Foto erkannt (>90% Top-3-Accuracy)?
2. **Onboarding-Zeit:** Kann die erste Pflanze in unter 2 Minuten angelegt werden?
3. **Light-Modus:** Ist die App OHNE Login nutzbar?
4. **Push-Erinnerung:** Erhaelt der Nutzer eine Push-Benachrichtigung zum Giessen?
5. **Ein-Tap-Bestaetigung:** Kann "Gegossen" mit einem Tap bestaetigt werden?
6. **Keine Fachsprache:** Sind alle Texte fuer einen Nicht-Botaniker verstaendlich?
7. **Ampel-Status:** Ist der Pflegezustand als einfache Ampel (gruen/gelb/rot) dargestellt?
8. **Troubleshooting:** Wird bei "Pflanze sieht schlecht aus" eine einfache Diagnose angeboten?
9. **Automatische Anpassung:** Werden Giess-Intervalle im Winter ohne Nutzer-Eingriff angepasst?
10. **Minimaler UI-Umfang:** Sieht der Nutzer maximal 5 Navigations-Elemente?

## 8. Sprachstil und Fachbegriffe

Diese Zielgruppe verwendet KEINE Fachbegriffe. Die App muss in Alltagssprache kommunizieren:

- "Giessen" (nie "Bewaessern" oder "Irrigation")
- "Duenger geben" (nie "Naehrstoffversorgung" oder "Fertilisierung")
- "Sonnig / Hell / Dunkel" (nie "PPFD", "Lux", "DLI")
- "Erde" (nie "Substrat", "Growing Medium")
- "Umtopfen" (nie "Repotting" oder "Substratwechsel")
- "Pflanze sieht schlecht aus" (nie "Chlorose", "Nekrose", "Oedem")
- "Schaedlinge" (nie "IPM", "Intervention", "Praevention")
- "Winter" / "Sommer" (nie "Dormanz", "Vegetationsperiode")
- "Ableger" (nie "Steckling", "vegetative Vermehrung")
- "Die Erde ist zu nass" (nie "Staunaesse", "Wurzelfaeule", "Asphyxie")
