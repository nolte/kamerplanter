# Bewertung: Kamerplanter aus Sicht eines Zimmerpflanzen-Gelegenheitspflegers

```yaml
Reviewer-Persona: "Stefan, 32, Bueroangestellter, 3 Zimmerpflanzen, null Ahnung"
Datum: 2026-02-27
Bewertungsmethode: Systematische Analyse aller 25 REQs, 11 NFRs, 14 UI-NFRs und stack.md
Sprache: Deutsch (Persona-gerecht)
```

---

## 1. Gesamtbewertung

| Kriterium | Bewertung | Kommentar |
|-----------|:---------:|-----------|
| Einstiegshuerden | :star::star: | Onboarding-Wizard (REQ-020) existiert, aber erst nach Registrierung (REQ-023). Zu viele Schritte bis zur ersten Pflanze. |
| Giess-Erinnerungen | :star::star::star::star: | Pflegeerinnerungen (REQ-022) mit Ein-Tap-Bestaetigung, adaptivem Lernen und saisonaler Anpassung sind genau das, was ich brauche. |
| Verstaendlichkeit | :star::star::star: | UI-NFR-011 (Glossar) und REQ-021 (Erfahrungsstufen) adressieren das Problem direkt. Aber noch nicht implementiert und die Menge an Fachbegriffen im System ist erschlagend. |
| Relevanz fuer 3 Pflanzen | :star::star: | 80% der Features sind fuer Profi-Grower. Fuer mich relevant: Erinnerungen, Pflanzen anlegen, Aufgabenliste. |
| Aufwand pro Woche | :star::star::star: | Im Einsteiger-Modus ca. 2-5 Minuten pro Woche realistisch, wenn alles wie spezifiziert funktioniert. |
| Motivation & Gamification | :star: | Keinerlei Gamification, Streaks, Achievements oder positive Verstaerkung spezifiziert. |
| Mobile Nutzung | :star::star: | Responsive Design (UI-NFR-001) und PWA (UI-NFR-012) spezifiziert, aber keine native App. Push-Benachrichtigungen nur ueber PWA/Service Worker, nicht nativ. |
| Konkurrenzfaehigkeit (vs. Planta/Greg) | :star::star: | Deutlich maechtigeres System, aber deutlich schlechtere Einsteiger-UX. |

**Gesamt: 2,5 von 5 Sternen** -- Die App kann theoretisch alles, was ich brauche, aber sie erwartet zu viel von mir.

---

## 2. :red_circle: Dealbreaker -- Ohne das loesche ich die App sofort

### N-001: Kein Foto-basiertes Pflanzen-Erkennen
**Betrifft:** REQ-001, REQ-020

Ich weiss nicht, wie meine Pflanzen heissen. Wirklich nicht. Die eine ist "die grosse mit den Loechern" (Monstera, wie ich jetzt weiss), die andere ist ein Kaktus, und die dritte... keine Ahnung. Planta und Greg lassen mich ein Foto machen und sagen mir, was das ist.

In Kamerplanter muss ich:
1. Botanische Familie kennen oder auswaehlen (BotanicalFamily)
2. Species auswaehlen (wissenschaftlicher Name!)
3. Optional Cultivar angeben

Das Starter-Kit "Zimmerpflanzen" (REQ-020) hilft nur, wenn ich zufaellig genau diese vier Pflanzen habe (Monstera, Ficus, Pothos, Dracaena). Was, wenn meine "gruene Pflanze" ein Philodendron ist? Dann steh ich wieder da.

**Empfehlung:** Foto-Erkennung ueber externe API (z.B. PlantNet, Google Lens API) als REQ-026 spezifizieren. Oder mindestens: Freitext-Suche "grosse gruene Pflanze mit Loechern" -> "Meinst du Monstera deliciosa?"

### N-002: Registrierung als Pflicht vor dem ersten Nutzen
**Betrifft:** REQ-023, REQ-020

Bevor ich irgendetwas tun kann, muss ich:
1. E-Mail und Passwort eingeben (oder Google-Login)
2. E-Mail verifizieren
3. Onboarding-Wizard durchlaufen

Das sind 3+ Minuten bevor ich ueberhaupt eine Pflanze sehe. Planta laesst mich sofort loslegen und fragt spaeter, ob ich ein Konto will.

REQ-020 sagt zwar "in weniger als 3 Minuten meine ersten Pflanzen" -- aber das zaehlt die Registrierung nicht mit. Und das Verhaeltnis "3 Minuten Aufwand fuer 3 Pflanzen" ist fuer mich schon an der Grenze.

**Empfehlung:** Anonymer Gastmodus mit spaeterer Kontoerstellung. Die Onboarding-User-Story erwaehnt "ggf. anonymes System", aber REQ-023 macht Auth ueberall zur Pflicht.

### N-003: Keine Push-Benachrichtigungen (nativ)
**Betrifft:** REQ-022, UI-NFR-012

Die Giess-Erinnerungen (REQ-022) sind der Kern dessen, warum ich die App nutzen wuerde. Aber: Es gibt keine spezifizierte Push-Notification-Strategie fuer mobile Endgeraete.

UI-NFR-012 spezifiziert PWA mit Service Worker, aber PWA-Push-Notifications sind auf iOS notorisch unzuverlaessig und erfordern, dass der Nutzer die PWA installiert hat. Auf Android funktioniert es besser, aber "installier die Webseite auf deinem Homescreen" ist eine Huerde, die 80% der Casual-User nicht nehmen werden.

REQ-022 generiert Tasks/Erinnerungen serverseitig (Celery), aber der Kanal zum Nutzer ist unklar. E-Mail? In-App? Push?

**Empfehlung:** Native Push-Benachrichtigungen als Kernfeature fuer REQ-022 spezifizieren. Entweder ueber PWA-Push (mit Installationsanleitung) oder als nativer Wrapper (Capacitor/TWA). Alternativ: Integration mit Kalender-App (REQ-015 iCal-Feed ist spezifiziert!), damit Erinnerungen im nativen Kalender landen.

### N-004: Kein Symptom-Checker / Pflanzen-Doktor
**Betrifft:** REQ-010 (IPM), kein dediziertes REQ

Meine Pflanze hat gelbe Blaetter. Was mache ich? Im aktuellen System muesste ich:
1. IPM-System oeffnen (REQ-010)
2. Eine Inspektion erstellen
3. Schaderreger oder Krankheit auswaehlen (wissenschaftliche Namen!)
4. Behandlung dokumentieren

Das IPM-System ist fuer professionelle Gaertner mit Wissen ueber Pathogene, Schaedlinge und Behandlungsmethoden. Ich brauche: "Foto machen -> Gelbe Blaetter erkannt -> Moegliche Ursachen: 1) Zu viel Wasser 2) Zu wenig Licht 3) Duengermangel -> Empfehlung: Weniger giessen, hellen Standort waehlen."

**Empfehlung:** "Pflanzen-Doktor"-Modus als vereinfachte Symptom-Checker-Ansicht im Einsteiger-Modus (REQ-021). Entscheidungsbaum statt Freitext-Inspektion.

---

## 3. :orange_circle: Frustrierend -- Funktioniert, nervt aber

### F-001: Standort-Hierarchie ist Overkill
**Betrifft:** REQ-002

Ich habe: eine Fensterbank. Das System erwartet: Site -> Location -> Slot.

Im Einsteiger-Modus (REQ-021) ist `location_key` ausgeblendet, aber der User muss trotzdem einen Site erstellen und benennen. Fuer jemanden mit 3 Pflanzen auf der Fensterbank ist "Standort: Meine Wohnung" alles, was noetig ist.

Das Onboarding (REQ-020) macht das besser -- es erstellt automatisch eine Site und Location. Aber wenn ich spaeter eine 4. Pflanze hinzufuegen will, muss ich das Konzept verstehen.

### F-002: Pflanzdurchlauf fuer 3 Pflanzen?
**Betrifft:** REQ-013

Ein "Pflanzdurchlauf" (PlantingRun) ergibt Sinn fuer "20 Tomaten ins Hochbeet". Fuer meine 3 einzelnen Zimmerpflanzen ist es ein unnoetig komplexes Konzept. Das Onboarding erstellt automatisch einen Run, aber ich weiss nicht mal, was das ist.

Im Einsteiger-Modus taucht "Durchlaeufe" nicht in der Navigation auf (REQ-021, 5 Menuepunkte). Gut. Aber im Hintergrund wird trotzdem einer erstellt, und wenn ich spaeter mal neugierig bin und auf "Fortgeschritten" wechsle, sehe ich ploetzlich Konzepte, die ich nicht verstehe.

### F-003: Mandantenverwaltung und DSGVO-Formulare
**Betrifft:** REQ-024, REQ-025

Beim Registrieren wird automatisch ein "persoenlicher Tenant" erstellt (REQ-024). Ich weiss nicht, was ein Tenant ist, und ich will es nicht wissen. Zusaetzlich muss ich mich mit Consent-Bannern (UI-NFR-013) und Datenschutz-Einstellungen (REQ-025) auseinandersetzen.

Fuer 3 Pflanzen auf der Fensterbank ist das alles Overhead. DSGVO-Konformitaet ist gesetzlich notwendig, aber die UX darf nicht darunter leiden.

### F-004: Zu viele Pflichtfelder bei manueller Pflanzenanlage
**Betrifft:** REQ-001, NFR-010

Wenn ich ausserhalb des Onboarding-Wizards eine Pflanze anlegen will, muss ich auch im Einsteiger-Modus:
- `common_names` (ok, den kenne ich vielleicht)
- `description` (warum?)
- `growth_habit` (was ist das?)

Und hinter den Kulissen braucht das System zwingend eine Species-Referenz, die entweder aus dem Starter-Kit kommt oder manuell gesucht werden muss.

### F-005: Kalender-Integration nur als Read-Only-Feed
**Betrifft:** REQ-015

REQ-015 spezifiziert iCal-Export als Read-Only-Feed. Das ist gut -- ich koennte Giess-Erinnerungen in meinem Google Calendar sehen. Aber: Es ist nicht bidirektional. Wenn ich im Google Calendar "erledigt" tippe, weiss Kamerplanter nichts davon. Und die Einrichtung eines webcal://-Feeds ist fuer einen Casual User nicht trivial.

---

## 4. :yellow_circle: Ueberfordernd -- Das ist fuer Profis, nicht fuer mich

### U-001: Naehrstoff-Engine (REQ-004) -- Komplett irrelevant
EC-Werte, NPK-Ratios, Misch-Reihenfolge, Flushing-Protokolle, Runoff-Analyse... Ich giesse meine Pflanzen mit Leitungswasser. Vielleicht einmal im Monat mit Fluessigduenger, wenn ich dran denke. Dosierung: "ein Schuss".

REQ-021 (Einsteiger-Modus) sagt, dass statt der 4 Kalkulatoren eine vereinfachte Ansicht kommt: "Alle 2 Wochen mit Fluessigduenger (halbe Dosierung)". Das ist genau, was ich brauche. Aber das muss auch wirklich so einfach sein wie beschrieben.

### U-002: Phasensteuerung (REQ-003)
State Machine fuer phaeologische Phasenwechsel. Meine Monstera ist seit 3 Jahren in der gleichen "Phase": steht rum und waechst langsam. Das REQ-020-Zimmerpflanzen-Phasenmodell (acclimatization -> active_growth -> maintenance -> repotting_recovery) ist deutlich sinnvoller, aber immer noch Konzepte, die ich nicht aktiv managen will.

### U-003: Tankmanagement (REQ-014)
Tanks, Reservoirs, Naehrstoffloesungen, Befuellungshistorie -- alles fuer Hydroponik/Indoor-Grow. Fuer mich 100% irrelevant. Im Einsteiger-Modus nicht in der Navigation (gut), aber das System hat 5+ Collections und Dutzende Endpoints dafuer.

### U-004: Sensoren und Umgebungssteuerung (REQ-005, REQ-018)
MQTT, Home Assistant, Hysterese, VPD-Berechnung, Aktorik-Steuerung. Ich habe keine Sensoren. Ich habe nicht mal ein Thermometer in der Wohnung.

### U-005: Erntemanagement und Post-Harvest (REQ-007, REQ-008)
Trichom-Mikroskopie, Brix-Werte, Jar-Curing, Fermentierung. Ich ernte nichts. Meine Pflanzen sind Deko.

### U-006: Vermehrungsmanagement (REQ-017)
Genetische Linien, Mutterpflanzen, Stecklingshistorie, Gewebekultur. Ich habe noch nie eine Pflanze vermehrt und plane das auch nicht.

### U-007: InvenTree-Integration (REQ-016)
Inventar-Management-System. Ich habe eine Giesskanne und eine Flasche Duenger. Brauche kein Inventar.

### U-008: CSV-Import (REQ-012)
Ich habe keine CSV-Dateien mit Pflanzendaten. Niemand mit 3 Zimmerpflanzen hat das.

---

## 5. :green_circle: Gut geloest

### G-001: Onboarding-Wizard (REQ-020)
Der 5-Schritt-Wizard ist der beste Ansatz im ganzen System:
1. Erfahrungsstufe waehlen -- "Einsteiger" mit dem Text "Zeig mir nur das Wichtigste"
2. Starter-Kit waehlen -- "Zimmerpflanzen" mit Monstera, Ficus, Pothos, Dracaena
3. Standort benennen -- "Meine Fensterbank"
4. Pflanzen auswaehlen -- Checkboxen, alle vorausgewaehlt
5. Fertig -- Alles wird automatisch erstellt

Das Konzept der Starter-Kits ist goldrichtig. 9 vorkonfigurierte Szenarien, darunter "Zimmerpflanzen" und "Zimmerpflanzen (haustierfreundlich)" fuer Katzenbesitzer. Toxizitaetswarnungen sind ein nettes Detail.

### G-002: Erfahrungsstufen-Modus (REQ-021)
Die Idee, 80% der Komplexitaet fuer Einsteiger auszublenden, ist exakt das richtige Konzept:
- 5 statt 15 Menuepunkte
- Maximal 5 Felder pro Dialog
- "Mehr anzeigen"-Link fuer Neugierige
- Duenge-Empfehlung in Alltagssprache statt EC/pH-Werten

### G-003: Care-Style-Presets (REQ-022)
9 vordefinierte Pflege-Profile (tropical, succulent, orchid, calathea, etc.) mit:
- Automatischen Giess-Intervallen (7 Tage fuer Tropisch, 21 Tage fuer Kaktus)
- Winter-Multiplikator (Kaktus bekommt im Winter 3x laengere Intervalle)
- Giess-Methode ("Von oben giessen" vs. "Tauchbad")
- Wasserqualitaets-Hinweise ("Kalkarmes Wasser fuer Orchideen")

Das wird automatisch aus der Pflanzenart abgeleitet -- ich muss es nur bestaetigen.

### G-004: Ein-Tap-Bestaetigung (REQ-022)
"Monstera gegossen?" -> [Erledigt] -> Fertig.
Kein Formular, keine Messfelder, kein EC-Wert. Genau so muss das sein.

### G-005: Adaptives Lernen (REQ-022)
Wenn ich meine Monstera konsequent alle 10 statt 7 Tage giesse, passt das System das Intervall automatisch an. Sicherheitsgrenze: maximal 30% Abweichung vom Artstandard. Das ist clever und verhindert, dass ich durch Vergesslichkeit meine Pflanze "tot-trainiere".

### G-006: Fachbegriff-Tooltips (UI-NFR-011)
38 Fachbegriffe mit Erklaerungen in Alltagssprache:
- VPD = "Dampfdruckdefizit -- wie durstig die Luft ist"
- EC = "Leitfaehigkeit -- wie viel Duenger im Wasser ist"
- Substrat = "Das Material, in dem die Pflanze wurzelt"

Inklusive Einsteiger-Tipps: "Im Zimmer normalerweise kein Problem. Nur bei geschlossenen Growzelten relevant."

### G-007: Saisonale Erinnerungen (REQ-022)
Oktober-Erinnerung: "Pflanzen vom Balkon holen". Maerz-Erinnerung: "Duengesaison beginnt". Das sind genau die Dinge, die ich vergesse.

### G-008: i18n in Deutsch (UI-NFR-007)
Deutsch als Default-Sprache. Nicht selbstverstaendlich bei einer Open-Source-App.

---

## 6. :blue_circle: Nice-to-Have -- Waere schoen, brauche ich aber nicht unbedingt

### NH-001: Kalenderansicht (REQ-015)
Eine Monatsansicht mit meinen 3 Giess-Terminen waere nett, ist aber nicht kritisch.

### NH-002: Aufgabenplanung (REQ-006, Zimmerpflanzen-Templates)
Das System hat vordefinierte Workflows: "Tropische Gruenpflanze (Standard)", "Kaktus/Sukkulente", "Umtopf-Workflow". Wenn die automatisch greifen, waere das hilfreich.

### NH-003: Crop Rotation / Mischkultur (REQ-001)
Companion Planting ist fuer Zimmerpflanzen irrelevant, aber wenn ich mal einen Balkonkasten habe, koennte "Tomate + Basilikum passt" nuetzlich sein.

### NH-004: PWA-Installation (UI-NFR-012)
Kamerplanter als App auf dem Homescreen -- schoen, aber nur wenn Push-Notifications dabei funktionieren.

### NH-005: Dark Mode
Ist implementiert (localStorage-basiert). Nettes Detail fuer abendliches Pflanzenchecken.

---

## 7. Aufwand-Analyse: Minuten pro Woche

### Ersteinrichtung (einmalig)

| Schritt | Geschaetzte Dauer | Kommentar |
|---------|:-----------------:|-----------|
| Registrierung (E-Mail/Passwort) | 2 Min | Standard, aber unnoetiger Zwang |
| Consent-Banner | 0,5 Min | DSGVO-Pflicht |
| Onboarding-Wizard (5 Steps) | 2-3 Min | REQ-020: unter 3 Min spezifiziert |
| **Gesamt Ersteinrichtung** | **4,5-5,5 Min** | **Akzeptabel, aber nicht "sofort loslegen"** |

### Woechentlicher Aufwand (Steady State, 3 Pflanzen)

| Aktion | Haeufigkeit/Woche | Dauer pro Mal | Woche gesamt |
|--------|:-----------------:|:-------------:|:------------:|
| Giess-Erinnerung bestaetigen | 2-3x | 5 Sek (1 Tap) | 15 Sek |
| Duenge-Erinnerung bestaetigen | 0-0,5x | 5 Sek | 2,5 Sek |
| Schaedlings-Check bestaetigen | 0-1x | 5 Sek | 5 Sek |
| App oeffnen / Dashboard ansehen | 2-3x | 30 Sek | 1-1,5 Min |
| **Gesamt pro Woche** | | | **ca. 2 Min** |

Das ist im akzeptablen Bereich. Voraussetzung: Alles funktioniert ueber Ein-Tap-Bestaetigung und ich muss nie ein Formular ausfuellen.

### Monatliche Aktionen

| Aktion | Haeufigkeit/Monat | Dauer |
|--------|:-----------------:|:-----:|
| Umtopf-Erinnerung (alle 12-18 Mo.) | 0-0,1x | -- |
| Standort-Check (Marz/Oktober) | 0-0,2x | 1 Min |
| CareProfile anpassen (selten) | 0-0,1x | 2-3 Min |

---

## 8. Fachbegriff-Audit

Bewertung aller im System vorkommenden Fachbegriffe aus Einsteiger-Sicht:

| Fachbegriff | Wo im System | Verstaendlich? | Laien-Alternative vorhanden? | Bewertung |
|-------------|-------------|:--------------:|:---------------------------:|:---------:|
| **EC (mS/cm)** | REQ-004, REQ-014, REQ-019 | Nein | Ja (UI-NFR-011): "Wie viel Duenger im Wasser" | OK wenn Tooltip aktiv |
| **VPD (kPa)** | REQ-005, REQ-009, REQ-018 | Nein | Ja (UI-NFR-011): "Wie durstig die Luft ist" | OK wenn Tooltip aktiv |
| **PPFD** | REQ-005, REQ-018 | Nein | Ja: "Lichtmenge fuer Pflanzen" | OK wenn Tooltip aktiv |
| **NPK** | REQ-004 | Nein | Ja: "Die drei Hauptnaehrstoffe" | OK wenn Tooltip aktiv |
| **Substrat** | REQ-019 | Vielleicht | Ja: "Das Material, in dem die Pflanze wurzelt" | Fast OK |
| **Cultivar** | REQ-001 | Nein | Ja: "Eine gezuechtete Sorte" | Sichtbar in REQ-021 erst ab intermediate |
| **Taxonomie** | REQ-001 | Nein | Nicht direkt | Problematisch -- Stammdaten-Bereich heisst "Stammdaten" mit taxonomischen Unterkategorien |
| **Fertigation** | REQ-004 | Nein | Nicht fuer Einsteiger sichtbar (REQ-021) | OK (ausgeblendet) |
| **Karenzzeit** | REQ-010 | Nein | Ja: "Wartezeit zwischen Spritzmittel und Ernte" | Irrelevant fuer Zimmerpflanzen |
| **Photoperiode** | REQ-003 | Nein | Ja: "Wie die Pflanze auf Tageslaenge reagiert" | OK wenn Tooltip aktiv |
| **GDD** | REQ-003 | Nein | Ja: "Akkumulierte Waerme" | Irrelevant fuer Zimmerpflanzen |
| **DLI** | REQ-005 | Nein | Ja: "Tageslichtmenge" | Irrelevant fuer Zimmerpflanzen |
| **Allelopathie** | REQ-001 | Nein | Ja: "Biochemische Wechselwirkung" | Ausgeblendet fuer Einsteiger (REQ-021) |
| **Dormanz** | REQ-003, REQ-022 | Nein | Ja: "Winterruhe" | Relevant -- gute Erklaerung in UI-NFR-011 |
| **Seneszenz** | REQ-003 | Nein | Ja: "Natuerliches Altern" | Irrelevant fuer Zimmerpflanzen |
| **Vernalisation** | REQ-003 | Nein | Ja: "Kaeltereiz zum Blueehen" | Irrelevant fuer Zimmerpflanzen |
| **Hysterese** | REQ-018 | Nein | Ja: "Schaltschwellen-Abstand" | Irrelevant (kein Sensor-Setup) |
| **Pflanzdurchlauf** | REQ-013 | Nein | Ja: "Gruppe von Pflanzen, die zusammen angebaut werden" | Verwirrend fuer 3 Einzelpflanzen |
| **Tenant** | REQ-024 | Nein | Nein -- wird "Organisation" oder "Garten" genannt, aber intern "Tenant" | Sollte im UI nie sichtbar sein |
| **CareProfile** | REQ-022 | Halbwegs | Ja, kontextuell: "Pflegeeinstellungen" | OK |

**Zusammenfassung:** UI-NFR-011 (Glossar/Tooltips) adressiert das Problem gut mit 38+ erklaerten Begriffen. Das Hauptproblem ist nicht einzelne Begriffe, sondern die *Menge* an Fachkonzepten, die im Hintergrund existieren. Der Einsteiger-Modus (REQ-021) blendet das meiste aus -- die Loesung funktioniert, wenn sie konsequent umgesetzt wird.

---

## 9. Feature-Relevanz-Matrix

Bewertung aller 25 REQs aus Sicht von "Stefan mit 3 Zimmerpflanzen":

| REQ | Titel | Relevanz | Nutzung | Kommentar |
|-----|-------|:--------:|:-------:|-----------|
| REQ-001 | Stammdatenverwaltung | :yellow_circle: Mittel | Passiv | Brauche ich nicht aktiv, aber das System braucht es im Hintergrund fuer meine Pflanzen |
| REQ-002 | Standortverwaltung | :yellow_circle: Mittel | Einmalig | "Meine Wohnung" erstellen und fertig. Site-Location-Slot ist Overkill fuer mich. |
| REQ-003 | Phasensteuerung | :red_circle: Niedrig | Nie | Meine Monstera ist in keiner "Phase". REQ-020 Zimmerpflanzen-Phasen (active_growth/maintenance) sind besser, aber trotzdem unnoetig fuer mich. |
| REQ-004 | Duenge-Logik | :red_circle: Niedrig | Nie | EC-Werte, Mischprotokolle, Flushing -- ich kippe Fluessigduenger ins Wasser. |
| REQ-005 | Hybrid-Sensorik | :red_circle: Irrelevant | Nie | Keine Sensoren, kein Home Assistant, kein MQTT. |
| REQ-006 | Aufgabenplanung | :yellow_circle: Mittel | Passiv | Zimmerpflanzen-Templates (tropische Gruenpflanze, Kaktus) sind nuetzlich, wenn sie automatisch greifen. |
| REQ-007 | Erntemanagement | :red_circle: Irrelevant | Nie | Ich ernte nichts. |
| REQ-008 | Post-Harvest | :red_circle: Irrelevant | Nie | Trocknung, Fermentierung -- hat nichts mit mir zu tun. |
| REQ-009 | Dashboard | :green_circle: Hoch | Taeglich | "Welche Pflanze braucht was?" auf einen Blick. Kernfeature. |
| REQ-010 | IPM-System | :red_circle: Niedrig | Selten | Professionelles Schaedlingsmanagement. Fuer mich: "Pflanze hat Laeuse -> Google". |
| REQ-011 | Externe Datenanreicherung | :red_circle: Niedrig | Nie | Hintergrund-Feature. Nuetzlich, wenn es automatisch meine Pflanzen-Daten vervollstaendigt. |
| REQ-012 | CSV-Import | :red_circle: Irrelevant | Nie | Ich habe keine CSV-Dateien. |
| REQ-013 | Pflanzdurchlauf | :red_circle: Niedrig | Nie | Fuer 20 Tomaten sinnvoll, fuer 3 Einzelpflanzen nicht. |
| REQ-014 | Tankmanagement | :red_circle: Irrelevant | Nie | Keine Tanks. Giesskanne reicht. |
| REQ-015 | Kalenderansicht | :yellow_circle: Mittel | Gelegentlich | Waere nett, alle Pflege-Termine in einem Kalender zu sehen. |
| REQ-016 | InvenTree-Integration | :red_circle: Irrelevant | Nie | Brauche kein Inventarsystem. |
| REQ-017 | Vermehrungsmanagement | :red_circle: Irrelevant | Nie | Ich vermehre keine Pflanzen. |
| REQ-018 | Umgebungssteuerung | :red_circle: Irrelevant | Nie | Keine Aktoren, keine Automatisierung. |
| REQ-019 | Substratverwaltung | :red_circle: Niedrig | Nie | "Erde" reicht mir als Information. |
| REQ-020 | Onboarding-Wizard | :green_circle: Hoch | Einmalig | Kernfeature. Macht oder bricht die erste Erfahrung. |
| REQ-021 | UI-Erfahrungsstufen | :green_circle: Hoch | Dauerhaft | Absolut essenziell. Ohne das ist die App unbenutzbar fuer mich. |
| REQ-022 | Pflegeerinnerungen | :green_circle: Hoch | Taeglich | DAS Feature, wegen dem ich die App nutzen wuerde. |
| REQ-023 | Benutzerverwaltung | :yellow_circle: Mittel | Einmalig | Muss sein, nervt aber (Registrierungspflicht). |
| REQ-024 | Mandantenverwaltung | :red_circle: Niedrig | Nie | Ich habe keinen Gemeinschaftsgarten. |
| REQ-025 | Datenschutz/DSGVO | :yellow_circle: Mittel | Selten | Gesetzlich notwendig, aber nicht mein Antrieb die App zu nutzen. |

**Zusammenfassung:** Von 25 REQs sind **4 hoch relevant** (REQ-009, REQ-020, REQ-021, REQ-022), **5 mittel** (REQ-001, REQ-002, REQ-006, REQ-015, REQ-023), und **16 irrelevant oder niedrig**. Der Overkill-Faktor liegt bei **64%** -- fast zwei Drittel der Features sind fuer meine Situation unnoetig.

---

## 10. Nutzerreise: Idealer erster Tag

So sollte mein erster Tag mit Kamerplanter aussehen:

### Minute 0-1: Installation
1. Webseite oeffnen (oder PWA installieren)
2. "Weiter ohne Konto" (Gastmodus -- **fehlt aktuell!**)
3. Oder: Google-Login mit einem Klick

### Minute 1-3: Pflanzen einrichten
4. Erfahrungsstufe: "Einsteiger -- Zeig mir nur das Wichtigste" :white_check_mark: (REQ-020)
5. Starter-Kit: "Zimmerpflanzen" :white_check_mark: (REQ-020)
6. **Alternative/Ergaenzung: Foto meiner Pflanze -> automatische Erkennung** :x: (fehlt!)
7. Standort: "Meine Wohnung" :white_check_mark: (REQ-020)
8. Pflanzen bestaetigen :white_check_mark: (REQ-020)

### Minute 3-4: Erste Orientierung
9. Dashboard zeigt: "Deine 3 Pflanzen sind eingerichtet!" :white_check_mark: (REQ-020, REQ-009)
10. Erste Aufgabe: "Monstera: Erde trocken? Dann giessen!" :white_check_mark: (REQ-022)
11. [Erledigt]-Button -> Erinnerung in 7 Tagen :white_check_mark: (REQ-022)

### Tag 2-7: Erinnerungen kommen
12. Push-Notification: "Monstera giessen" :x: (Push-Strategie unklar!)
13. App oeffnen -> 1 Tap -> fertig :white_check_mark: (REQ-022)

### Monat 1: System lernt
14. Adaptives Lernen passt Intervalle an :white_check_mark: (REQ-022)
15. Oktober-Erinnerung: "Heizperiode -- Calathea braucht mehr Luftfeuchte" :white_check_mark: (REQ-022)

### Problemfall: Pflanze krank
16. "Meine Monstera hat gelbe Blaetter" -> Symptom-Checker :x: (fehlt!)
17. Einfache Vorschlaege: "Weniger giessen, hellen Standort" :x: (fehlt!)

---

## 11. Top-3-Massnahmen

### Massnahme 1: Foto-basierte Pflanzenerkennung (Prio: KRITISCH)
**Problem:** Casual User kennen den Namen ihrer Pflanzen nicht.
**Loesung:** Neue REQ-026 "Pflanzenidentifikation via Bilderkennung". Integration einer externen API (PlantNet, Google Lens) oder eines ML-Modells. Im Onboarding-Wizard (REQ-020) als alternativer Pfad: "Pflanze fotografieren" statt "Species auswaehlen".
**Aufwand:** Mittel (API-Integration, Kamera-Zugriff im Browser)
**Impact:** Reduziert Einstiegshuerde massiv. Unterschied zwischen "5 Minuten Setup" und "gib auf".

### Massnahme 2: Native Push-Benachrichtigungen (Prio: KRITISCH)
**Problem:** Ohne Push-Notifications sind die Giess-Erinnerungen (REQ-022) wertlos fuer einen User, der die App nicht taeglich oeffnet.
**Loesung:** PWA-Push gemaess UI-NFR-012 ist spezifiziert, aber die Umsetzungsstrategie fuer iOS muss geklaert werden. Web Push API + Notification Permission Flow im Onboarding. Alternativ: iCal-Feed (REQ-015) aktiv bewerben als Fallback. Langfristig: Capacitor-Wrapper fuer native Push.
**Aufwand:** Mittel (PWA-Push) bis hoch (nativer Wrapper)
**Impact:** Macht den Unterschied zwischen "App die hilft" und "App die ich vergesse".

### Massnahme 3: Vereinfachter Symptom-Checker (Prio: HOCH)
**Problem:** Wenn eine Pflanze krank aussieht, hat der Casual User keine Ahnung, was zu tun ist. REQ-010 (IPM) ist fuer Profis.
**Loesung:** Einsteiger-Ansicht im IPM-System: Entscheidungsbaum mit Fotos. "Gelbe Blaetter -> Unten oder oben? -> Unten = normal (alte Blaetter) / Oben = Ueberwaesserung oder Lichtmangel". 5-10 haeufigste Symptome mit einfachen Loesungen. Keine wissenschaftlichen Namen, keine Schaderreger-Datenbank.
**Aufwand:** Niedrig (Frontend-only, Entscheidungsbaum als statische Daten)
**Impact:** Gibt dem User Kontrolle und reduziert das Gefuehl von Hilflosigkeit.

---

## 12. Konkurrenz-Vergleich: Planta vs. Greg vs. Kamerplanter

| Feature | Planta | Greg | Kamerplanter |
|---------|:------:|:----:|:------------:|
| **Foto-Erkennung** | :white_check_mark: Ja (KI-basiert) | :white_check_mark: Ja | :x: Nein |
| **Push-Notifications** | :white_check_mark: Nativ (iOS/Android) | :white_check_mark: Nativ | :yellow_circle: Nur PWA (wenn installiert) |
| **Giess-Erinnerungen** | :white_check_mark: Ja, artbasiert | :white_check_mark: Ja, lichtbasiert | :white_check_mark: Ja, artbasiert + saisonal + adaptiv |
| **Ein-Tap-Bestaetigung** | :white_check_mark: Ja | :white_check_mark: Ja | :white_check_mark: Ja (REQ-022) |
| **Pflanzen-Doktor** | :white_check_mark: Symptom-Fotos | :x: Nein | :x: Nein |
| **Duenge-Erinnerungen** | :white_check_mark: Ja | :yellow_circle: Begrenzt | :white_check_mark: Ja, saisonal + dunge-guard |
| **Saisonale Anpassung** | :yellow_circle: Begrenzt | :white_check_mark: Lichtbasiert | :white_check_mark: Ja, hemisphaerenabhaengig |
| **Adaptives Lernen** | :x: Nein | :white_check_mark: Lichtbasiert | :white_check_mark: Ja (30% Cap) |
| **Fachbegriff-Erklaerungen** | :x: Keine Fachbegriffe | :x: Keine Fachbegriffe | :white_check_mark: 38+ Glossareintraege |
| **Onboarding** | :white_check_mark: 3 Schritte | :white_check_mark: 3 Schritte | :white_check_mark: 5 Schritte (nach Registrierung) |
| **Registrierung noetig** | :x: Nein (erst spaeter) | :x: Nein (erst spaeter) | :white_check_mark: Ja (sofort) |
| **Kostenlos** | :yellow_circle: Freemium (7 Pflanzen frei) | :yellow_circle: Freemium | :white_check_mark: Open Source, unbegrenzt |
| **Profi-Features** | :x: Kaum | :x: Kaum | :white_check_mark: Hydroponik, Sensoren, IPM, etc. |
| **Self-Hosted** | :x: Nein | :x: Nein | :white_check_mark: Ja (Kubernetes) |
| **Datenschutz** | :yellow_circle: Cloud-Only | :yellow_circle: Cloud-Only | :white_check_mark: DSGVO-konform, Self-Hosted |
| **Gamification** | :white_check_mark: Pflanzenpflege-Score | :white_check_mark: Streaks, Badges | :x: Nichts |
| **Sprache** | :white_check_mark: DE/EN/etc. | :white_check_mark: EN | :white_check_mark: DE/EN |
| **Offline-Faehigkeit** | :white_check_mark: Nativ | :white_check_mark: Nativ | :yellow_circle: PWA-basiert (spezifiziert, nicht impl.) |

### Staerken von Kamerplanter gegenueber der Konkurrenz:
1. **Open Source & Self-Hosted** -- Datenschutz-bewusste Nutzer finden hier eine Alternative
2. **Kein Abo-Modell** -- Planta kostet ab der 8. Pflanze Geld
3. **Tiefe fuer Fortgeschrittene** -- Wenn ich wachse, waechst die App mit (REQ-021 Stufenmodell)
4. **Saisonale Intelligenz** -- Winter-Multiplikator und Duenge-Guard sind besser als Planta
5. **DSGVO-Konformitaet** -- Fuer EU-Nutzer ein echtes Argument

### Schwaechen von Kamerplanter gegenueber der Konkurrenz:
1. **Fehlende Foto-Erkennung** -- Groesste Einzelhuerde fuer Einsteiger
2. **Registrierungspflicht** -- Planta und Greg starten sofort
3. **Keine native App** -- Push-Notifications eingeschraenkt
4. **Keine Gamification** -- Kein Anreiz, die App regelmaessig zu oeffnen
5. **Overkill-Wahrnehmung** -- 25 REQs, 74 Edge-Collections, Kubernetes -- wirkt wie Enterprise-Software

---

## Anhang: Bewertung der NFRs und UI-NFRs

| NFR/UI-NFR | Titel | Relevant fuer Casual User? | Kommentar |
|------------|-------|:--------------------------:|-----------|
| NFR-001 | Separation of Concerns | Egal | Architektur interessiert mich nicht |
| NFR-002 | Kubernetes | Egal | Self-Hosting ist nicht mein Thema |
| NFR-003 | Code-Standard | Egal | |
| NFR-004 | Lokale Dev-Umgebung | Egal | |
| NFR-005 | Doku | Egal | |
| NFR-006 | API-Fehlerbehandlung | Indirekt | Fehlermeldungen muessen verstaendlich sein |
| NFR-007 | Betriebsstabilitaet | Indirekt | App muss halt laufen |
| NFR-008 | Teststrategie | Egal | |
| NFR-009 | Dependencies | Egal | |
| NFR-010 | UI-Masken | Mittel | Betrifft Formulare die ich ausfuellen muss |
| NFR-011 | Retention Policy | Niedrig | Gut zu wissen, dass Daten nicht ewig gespeichert werden |
| UI-NFR-001 | Responsive Design | **Hoch** | Muss auf dem Handy funktionieren |
| UI-NFR-002 | Barrierefreiheit | Mittel | Nicht mein Thema, aber grundsaetzlich wichtig |
| UI-NFR-003 | Performance | **Hoch** | Wenn die App laed, bin ich weg |
| UI-NFR-004 | Feedback | **Hoch** | Muss wissen ob meine Aktion geklappt hat |
| UI-NFR-005 | Navigation | **Hoch** | Muss mich zurechtfinden |
| UI-NFR-006 | Design System | Mittel | Sieht halt gut aus oder nicht |
| UI-NFR-007 | i18n | **Hoch** | Deutsch als Default ist Pflicht |
| UI-NFR-008 | Formulare | Mittel | Wenige Formulare im Einsteiger-Modus |
| UI-NFR-009 | Visual Identity | Niedrig | Mir egal wie das Logo aussieht |
| UI-NFR-010 | Tabellen | Niedrig | Hab kaum Daten fuer Tabellen |
| UI-NFR-011 | Fachbegriff-Erklaerungen | **Hoch** | Ohne das verstehe ich nichts |
| UI-NFR-011 (Kiosk) | Kiosk-Modus | Irrelevant | Ich bin nicht im Gewaechshaus |
| UI-NFR-012 | PWA/Offline | Mittel | Nur relevant wegen Push-Notifications |
| UI-NFR-013 | Consent-Management | Niedrig | Muss sein, interessiert mich aber nicht |
