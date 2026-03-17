# Review: Lustloser Zimmerpflanzen-Besitzer (Februar 2026)

```yaml
Erstellt von: Stefan, 32, Bueroangestellter, planloser Nutzer ohne gruenen Daumen
Datum: 2026-02-28
Fokus: Minimaler Aufwand, Verstaendlichkeit, Erinnerungen, Ueberlebenshilfe fuer Zimmerpflanzen
Nutzer-Profil: 3-7 Zimmerpflanzen, null Expertise, null Motivation, will nur dass nichts stirbt
Vorgaenger-Review: spec/requirements-analysis/casual-houseplant-user-review.md (2026-02-27)
Analysierte Dokumente:
  - spec/req/REQ-001 bis REQ-027 (27 funktionale Anforderungen)
  - spec/nfr/NFR-001 bis NFR-011 (11 nicht-funktionale Anforderungen)
  - spec/ui-nfr/UI-NFR-001 bis UI-NFR-014 (14 UI-Anforderungen)
  - spec/stack.md
  - Vorgaenger-Reports in spec/requirements-analysis/
```

---

## Gesamtbewertung: "Kann ICH damit meine Pflanzen am Leben halten?"

| Alltagsbereich | Bewertung | Kommentar |
|---|---|---|
| Onboarding ("Komme ich rein?") | 3/5 | Wizard ist da, Light-Modus (REQ-027) loest Login-Problem. Aber Foto-Erkennung fehlt noch. |
| Pflanze hinzufuegenr ("Wie schwer ist das?") | 4/5 | Quick-Add-Plant (REQ-021 v1.1) ist genau richtig. Suche nach Trivialname funktioniert. |
| Giess-Erinnerungen ("Sagt die App mir Bescheid?") | 4/5 | REQ-022 ist gut durchdacht. Ein-Tap-Bestaetigung, adaptiv. Push-Kanal bleibt unklar. |
| Standort-Beratung ("Wo hinstellen?") | 2/5 | Nur Location-Name, keine "Fenster nach Sueden?"-Hilfe fuer Laien. |
| Problemloesung ("Pflanze kraenkelt, was tun?") | 1/5 | IPM (REQ-010) ist Profi-Kram. Kein Symptom-Checker, kein Foto-Diagnose-Tool. |
| Sprache & Verstaendlichkeit | 4/5 | UI-NFR-011 (Glossar + Tooltips) ist exzellent spezifiziert. Wenn implementiert, loest das viel. |
| Aufwand pro Woche | 4/5 | Im Beginner-Modus 2-5 Minuten realistisch. Kommt drauf an ob Push wirklich kommt. |
| Motivation & Spassfaktor | 1/5 | Keine Gamification, keine Achievements, keine emotionale Bindung an die App. |
| Nutzen fuer 3 Pflanzen (kein Overkill?) | 2/5 | 15 von 27 REQs sind fuer mich komplett irrelevant. Zu viel Profi-Zeugs sichtbar. |
| Vergleich mit Planta/Greg | 3/5 | Technisch ueberlegen, UX noch hinter Konkurrenz. REQ-027 und REQ-021 schliessen Luecke. |

**Ehrliche Einschaetzung:** Seit dem ersten Review (2026-02-27) hat sich was getan. Der Light-Modus (REQ-027) loest den Registrierungszwang. Quick-Add-Plant (REQ-021 v1.1) loest das "ich kenn den Namen nicht"-Problem teilweise. Das Glossar (UI-NFR-011) ist so gut spezifiziert, dass ich irgendwann vielleicht sogar verstehe, was ein EC-Wert ist. Aber: Foto-Erkennung fehlt immer noch komplett, es gibt null Gamification, und die Problemdiagnose ("Blatt wird gelb, was nun?") ist fuer mich nicht vorhanden. Ich wuerde die App installieren, aber ich wuerde sie nach 3 Wochen wieder loeschen, wenn meine Monstera stirbt und mir keiner gesagt hat warum.

---

## Dealbreaker -- Ohne das loesche ich die App sofort

### N-001: Keine Foto-basierte Pflanzenerkennung

**Was ich brauche:** Ich mache ein Foto, die App sagt mir was das ist. Fertig.

**Was die App hat:** Autocomplete-Suche nach Common Name (Quick-Add-Plant, REQ-021 v1.1). Das ist besser als nichts, aber es setzt voraus, dass ich den deutschen Namen kenne. Meine dritte Pflanze heisst "irgendwas Gruenes" -- das liefert kein Suchergebnis.

**Warum Dealbreaker:** Ich kenne meine eigenen Pflanzen nicht. Wenn die App mir das nicht erklaert, bin ich nach dem ersten Schritt bereits verloren. Planta und Greg loesen das mit einem Foto in 10 Sekunden.

**Was die Konkurrenz macht:**
- Planta: Foto → KI-Erkennung → Pflanzenname + Pflegeplan in 15 Sekunden
- Greg: Identisches Feature, kostenlos
- PictureThis: Kernprodukt ist Foto-Erkennung

**Was die Spec sagt:** REQ-021 v1.1 §3.8 kennt das Problem und verlinkt auf PlantNet als externen Hinweis. Das ist kein Ersatz. Der Freitext-Fallback ("Trotzdem hinzufuegen") hilft mir nicht bei der Pflege.

**Vorschlag:** N-001 als eigenes REQ spezifizieren. Adapter-Pattern (wie REQ-011): PlantNet-API als Primaeradapter, Google Vision als Fallback. Kosten: PlantNet ist kostenlos und Open Source.

---

### N-002: Registrierungszwang vor dem ersten Nutzen (TEILWEISE GELOEST)

**Status seit letztem Review:** REQ-027 (Light-Modus) loest dieses Problem fuer Self-Hosting. Fuer SaaS-Betrieb bleibt das Problem bestehen.

**Was jetzt moeglich ist:** Im Light-Modus (KAMERPLANTER_MODE=light) keine Registrierung, kein Login, sofort loslegen. Das ist genau richtig fuer jemanden mit einem Raspberry Pi oder Docker auf dem Laptop.

**Was noch fehlt:** Fuer den Cloud/SaaS-Betrieb gibt es keinen Gastmodus ohne E-Mail-Verifikation. Wenn ich die App im Browser aufrufe (ohne eigenen Server), muss ich mich noch registrieren. Das bleibt ein Problem fuer den Casual User der einfach "die App ausprobieren" will.

**Vorschlag:** Auch im Full-Modus: Gaststatus mit eingeschraenkter Nutzung (max 3 Pflanzen, keine Sync) fuer 30 Tage ohne Registrierung.

---

### N-003: Push-Benachrichtigungen -- Zustellkanal unklar

**Was ich brauche:** Mein Handy vibriert. Auf dem Display steht "Giess deine Monstera". Ich gehe hin, giesse, tippe "Erledigt". Das war's.

**Was die Spec hat:** REQ-022 generiert Celery-Tasks serverseitig. UI-NFR-012 bereitet das PWA-Manifest fuer Web Push vor. Aber: Kein REQ beschreibt einen konkreten Notification-Delivery-Kanal.

**Das Problem in der Spec:**
- REQ-022 §10 Erinnerungstypen: generiert Tasks, aber kein Zustellmechanismus definiert
- UI-NFR-012 R-006: "Anwendung SOLL Push-Benachrichtigungen unterstuetzen koennen" -- SOLL, nicht MUSS
- E-Mail-Erinnerungen: nirgendwo spezifiziert
- Native Push (iOS/Android): kein Flutter-App-REQ fuer Zimmerpflanzen-Nutzer

**Warum Dealbreaker:** Die App weiss, wann ich giessen soll. Aber sie sagt mir nichts. Das ist wie ein Wecker der nichts klingelt. Wenn mir die App keine Nachricht schickt, vergesse ich sie. Dann sterben meine Pflanzen trotzdem.

**Vorschlag:** Notification-Adapter-REQ (analog zu REQ-011 External Enrichment): ABC-Interface mit austauschbaren Backends. Mindestanforderung: E-Mail (SMTP, immer moeglich) + Web Push (PWA). Profi-Option: Apprise fuer 100+ Dienste (Telegram, Pushover, ntfy, Gotify).

---

## Frustrierend -- Funktioniert theoretisch, aber nervt mich

### F-001: Anmeldevorgang zu komplex (Full-Modus)

**Vorhandene Anforderung:** REQ-023 (Benutzerverwaltung)

**Was mich frustriert:** Auch mit "Angemeldet bleiben" (REQ-023 v1.3) muss ich einmalig durch Registrierung + E-Mail-Verifizierung. Fuer jemanden der nur Pflanzen giesst, ist das Overhead. Der erste Eindruck zaehlt -- und der ist "Formular ausfuellen".

**Wie ich es mir vorstelle:** Entweder Light-Modus (schon da) oder: Social-Login-Button als einzige Option auf dem ersten Screen. Kein E-Mail-Formular, kein Passwort. "Mit Google anmelden" → sofort los.

**Aufwand fuer Nutzer:** REQ-023 hat SSO spezifiziert (Google, GitHub, Apple). Das loest das Problem wenn der Login-Screen das als ERSTEN Button zeigt, nicht als Option unter dem Formular.

### F-002: Onboarding fragt nach Standorttyp statt mir zu helfen

**Vorhandene Anforderung:** REQ-020 (Onboarding-Wizard), Schritt 3

**Was mich frustriert:** Ich soll auswaehlen: Fensterbank / Balkon / Garten / Growzelt / Gewaechshaus / Innenraum. Das ist okay. Aber danach passiert nichts mit dieser Information. Die App sagt mir nicht "deine Monstera braucht mehr Licht als dein Nordfenster gibt". Sie speichert es nur.

**Was fehlt:** Nach Standortauswahl MUSS die App eine simple Einschaetzung geben:
- "Fensterbank Sueden: gut fuer Kaktus, zu viel fuer Calathea"
- "Ecke im Wohnzimmer: nur schattentolerante Pflanzen"

Das haette ich gebraucht bevor meine Calathea eingegangen ist.

**Aufwand fuer Nutzer:** Zu hoch fuer null Ergebnis. Daten werden gesammelt aber nicht genutzt um mir zu helfen.

### F-003: Mandantenverwaltung sichtbar fuer Einzelnutzer (TEILWEISE GELOEST)

**Vorhandene Anforderung:** REQ-024 (Mandantenverwaltung), REQ-027 (Light-Modus)

**Was mich frustriert:** Im Full-Modus gibt es immer noch einen "persoenlichen Tenant" der beim Onboarding angelegt wird. Ich weiss nicht was ein Tenant ist. Ich will das auch nicht wissen.

**Was jetzt besser ist:** REQ-027 versteckt das im Light-Modus vollstaendig. Das ist gut.

**Was noch fehlt:** Auch im Full-Modus sollte der persoenliche Tenant fuer Einzelnutzer unsichtbar sein. "Mein Garten" als einfacher Name reicht. Das Wort "Mandant" oder "Tenant" darf ein Einsteiger niemals sehen.

### F-004: Zu viele Pflichtfelder ausserhalb des Wizards (GELOEST)

**Status:** REQ-021 v1.1 §3.8 (Quick-Add-Plant) loest das direkt. Einsteiger sehen nur: Suchfeld + optionaler Spitzname + optionaler Standort. Das sind 1-3 Felder. Genau richtig.

**Verbleibende Luecke:** Quick-Add-Plant sucht in bestehenden Stammdaten. Was wenn meine Pflanze nicht in der Datenbank ist? Der Freitext-Fallback erstellt eine Pflanze ohne Pflegeprofil. Dann bekomme ich keine sinnvollen Erinnerungen. Das sollte die App deutlich kommunizieren: "Diese Pflanze kenne ich nicht. Du kriegst allgemeine Erinnerungen bis wir sie identifizieren."

### F-005: Giessprozess ohne Mengengabe

**Vorhandene Anforderung:** REQ-022 (Pflegeerinnerungen), watering_method

**Was mich frustriert:** Die Erinnerung sagt "von oben giessen, bis Wasser unten herauslaeuft". Das ist gut. Aber wie VIEL ist das? "Bis Wasser herauslaeuft" ist fuer einen Topf von 10 Liter etwas anderes als fuer einen von 1 Liter.

**Wie ich es mir vorstelle:** Optional: "Schritt fuer Schritt: 1. Warte bis obere 2cm Erde trocken sind. 2. Giesse langsam, bis Wasser durch das Loch unten tropft. 3. Kippe ueberschuessiges Wasser aus dem Untersetzer."

**Aufwand fuer Nutzer:** Minimal. Die Anleitung ist schon in der Spec als i18n-Text vorhanden. Sie muss nur in der Benachrichtigung ankommen.

---

## Ueberfordernd -- Das ist fuer Profis, nicht fuer mich

### U-001: Phasensteuerung (REQ-003)

**Anforderung:** "State-Machine fuer phaenologische Phasenubergaenge mit phasenspezifischen PPFD, Photoperiode, NPK-Profilen"

**Warum mich das ueberfordert:** Meine Monstera hat keine "Keimungsphase". Sie steht seit 2 Jahren auf meinem Fensterbrett. Das Konzept "Phase" ist fuer Zimmerpflanzen-Dauerkulturen biologisch irrelevant. Fuer Cannabis-Grower macht das Sinn. Fuer mich nicht.

**Was ein Anfaenger stattdessen braucht:** "Aktiv" (Sommer, jetzt giessen und duengen) und "Winterruhe" (Winter, seltener giessen, nicht duengen). Das sind die einzigen zwei Zustaende die ich verstehe.

**Kommentar:** REQ-020 hat Zimmerpflanzen-spezifische Phasen (acclimatization, active_growth, maintenance, repotting_recovery) bereits definiert. Das ist besser. Aber im Beginner-Modus sollte das vollstaendig unsichtbar sein -- ich will nie das Wort "Phase" sehen mussen.

### U-002: Duenge-Logik (REQ-004) -- fuer Zimmerpflanzenbesitzer

**Anforderung:** "Praezise Mischverhaeltnisse fuer Reservoirs, EC-Budget-Management, CalMag-Korrektur aus Wasserquelle, NPK-Ratios"

**Warum mich das ueberfordert:** Ich kaufe im Supermarkt Fluessigduenger von Compo. Auf der Flasche steht "5ml pro Liter Wasser alle 2 Wochen von Maerz bis Oktober". Das ist mein Duegeplan. EC, CalMag, NPK, Mischverhaeltnisse -- das ist fuer professionelle Hydroponik-Betreiber.

**Was ein Anfaenger stattdessen braucht:** "Duengen: Alle 2 Wochen Maerz bis Oktober. Kaufe Fluessigduenger fuer Zimmer- oder Gruenpflanzen (z.B. Compo, Wuxal). Halbe Dosierung auf der Flasche." Das ist alles was ich brauche.

**Was die Spec hat:** REQ-021 §3.5 (Einsteiger-Duenge-Ansicht) zeigt genau das: "Alle 2 Wochen mit Fluessigduenger (halbe Dosierung)". Das ist perfekt. Solange das im Beginner-Modus wirklich alles ist was ich sehe, bin ich zufrieden.

### U-003: Tankmanagement (REQ-014)

**Anforderung:** "Tank als Infrastruktur-Objekt, Naehrstoffloesungs-Reservoirs, EC/pH-Sonden, Befuellungshistorie"

**Warum mich das ueberfordert:** Ich habe keinen Tank. Ich habe eine Giesskanneaus Plastik die ich mit Leitungswasser fuelle. "Tank-Typ: Naehrstofflosung" -- ich weiss nicht mal was das ist.

**Was ein Anfaenger stattdessen braucht:** Nichts. Dieses Feature sollte im Beginner-Modus vollstaendig unsichtbar sein. REQ-021 Navigations-Tiering versteckt "Tanks" erst ab Expert-Modus (Level 9). Das ist korrekt.

### U-004: Substrat-Verwaltung (REQ-019)

**Anforderung:** "Substrat-Konfiguration und Lebenszyklusverwaltung, pH/EC-Verlauf, CEC-Werte, air_porosity_percent"

**Warum mich das ueberfordert:** Meine Pflanzen stehen in Erde. Das war's. "CEC", "air_porosity", "ec_base_ms", "bulk_density_g_per_l" -- ich verstehe kein einziges dieser Felder.

**Was ein Anfaenger stattdessen braucht:** "Welche Erde?" mit Antwortoptionen: "Normale Blumenerde", "Kakteenerde", "Orchideenrinde", "Ich weiss nicht". Die App macht dann alles weitere automatisch. Substrat als Dropdown mit 5 Optionen, nicht als technische Konfigurationsmaske.

**Kommentar:** Fuer Experten ist REQ-019 grossartig. Fuer mich ist es erschlagend. Beginner-Modus MUSS das vollstaendig verbergen.

### U-005: IPM-System (REQ-010)

**Anforderung:** "Mehrstufiger IPM-Ansatz, Schaedlingsbefall, Karenzzeiten, Resistenzmanagement, beneficial_organisms"

**Warum mich das ueberfordert:** Ich weiss nicht was eine Trauermücke ist bis ich sie sehe. Ich weiss nicht was Spinnmilben sind. Ich weiss dass gelbe Blatter schlecht sind.

**Was ein Anfaenger stattdessen braucht:** Einen Symptom-Checker. Ich waehle: Blattfarbe (gelb/braun/schwarz/fleckig), betroffener Teil (Blatt/Stiel/Wurzel), und bekomme "Das koennte X sein. Loesung: Y." Keine Fachbegriffe, keine Karenzzeiten, keine chemische Formel.

**Was die Spec hat:** IPM ist vollstaendig auf professionelle Nutzung zugeschnitten. Fuer Zimmerpflanzen fehlt ein einfacher Diagnose-Assistent.

### U-006: Ernte, Post-Harvest, Pflanzdurchlaeuf (REQ-007, REQ-008, REQ-013)

**Warum mich das ueberfordert:** Ich ernte nichts. Meine Monstera liefert keine Fruechte die ich nach Trichom-Mikroskopie beurteile. Post-Harvest-Protokolle fuer Jar-Curing sind nicht mein Anwendungsfall.

**Was ein Anfaenger stattdessen braucht:** Diese Features komplett unsichtbar. REQ-021 Navigations-Tiering loest das fuer "Ernte & Post-Harvest" (nur im Expert-Modus sichtbar). Gut.

### U-007: Aquaponik (REQ-026)

**Anforderung:** "Fisch-Pflanzen-Kreislaufsysteme, Stickstoffkreislauf, Biofilter-Cycling"

**Warum mich das ueberfordert:** Ich habe keine Fische. Ich verstehe nicht warum das in derselben App ist wie meine Monstera.

**Was ein Anfaenger stattdessen braucht:** Dieses Feature muss im Beginner-Modus so verborgen sein, dass ich keine Ahnung habe dass es existiert.

---

## Gut geloest -- Das hat mir geholfen

### G-001: Quick-Add-Plant (REQ-021 v1.1 §3.8)

Endlich. Ich tippe "Monstera", sehe ein Bild, klicke drauf, bin fertig. Kein Botanik-Studium erforderlich. Die Autocomplete-Suche ueber common_names ist genau der richtige Ansatz. Freitext-Fallback fuer unbekannte Pflanzen ist eine ehrliche Loesung.

**Warum gut:** Erster sinnvoller Schritt auf dem Weg zur normalen Benutzbarkeit. Genau das was ein Laie braucht.

### G-002: Pflegeerinnerungen mit Ein-Tap-Bestaetigung (REQ-022)

Die care_style-Presets (tropical, succulent, cactus, etc.) erleichtern die Konfiguration enorm. Saisonale Anpassung, adaptives Lernen, Duenge-Guard fuer Winter -- das ist durchdacht. Ein-Tap-Bestaetigung ohne Formular ist pflicht.

**Warum gut:** Das ist der Kern-Use-Case fuer mich. Wenn das funktioniert, ueberleben meine Pflanzen.

### G-003: Glossar und Tooltips (UI-NFR-011)

38 Fachbegriffe mit Einsteiger-Tipp -- das ist das richtigste Feature in der ganzen Spec. Wenn ich irgendwo "EC" sehe und auf ein Info-Icon tippen kann und dann lese "wie viel Duenger im Wasser ist -- fuer Anfaenger: halte dich an die Flaschendosierung" -- dann ist das genau das was ich brauche.

**Warum gut:** Fachbegriffe sind okay wenn sie erklaert werden. Dieses Feature macht das gesamte System zugaenglicher ohne es zu vereinfachen.

### G-004: Einsteiger-Modus mit Navigation-Tiering (REQ-021)

5 Menupunkte fuer Einsteiger: Dashboard, Meine Pflanzen, Aufgaben, Kalender, Einstellungen. Das ist genau richtig. Ich brauche kein Menu mit 15 Eintraegen.

**Warum gut:** Weniger ist mehr. 15 Eintraege erschlagen mich. 5 Eintraege kommen ich zurecht.

### G-005: Starter-Kits fuer Zimmerpflanzen (REQ-020)

"Zimmerpflanzen" und "Zimmerpflanzen (haustierfreundlich)" als vorkonfigurierte Kits mit Monstera, Ficus, Pothos, Sansevieria -- genau die Pflanzen die ich habe. Und der Haustier-Toxizitaetshinweis ist naetzlich (mein Vermieter hat eine Katze).

**Warum gut:** Das nimmt mir die Entscheidungsarbeit ab. "Klicke Zimmerpflanzen" -> fertig.

### G-006: Light-Modus (REQ-027)

Kein Login, kein Tenant, keine DSGVO-Banner, sofort loslegen. Fuer Self-Hosting auf einem Raspberry Pi ist das perfekt.

**Warum gut:** Loest den Registrierungszwang fuer technisch versierte Einsteiger die selbst hosten wollen. Ein echter Fortschritt gegenueber dem ersten Review.

### G-007: PWA-Installation (UI-NFR-012)

Als installierbare App auf dem Homescreen ist die Web-App praktisch wie eine native App. Das ist ausreichend fuer meine Beduerfnisse solange Push-Benachrichtigungen funktionieren.

**Warum gut:** Kein App-Store-Download, kein Update-Zwang, einfach "Zu Homescreen hinzufuegen".

### G-008: Zimmerpflanzen-spezifische Pflegeanleitung in REQ-022

Die Giessmethode pro Preset (top_water, soak, drench_and_drain) mit deutschen Anleitungen -- "Tauchbad: Topf 10-15 Minuten ins Wasser stellen" -- ist genau das was mir meine Orchidee gerettet haette. Und der Wasserqualitaets-Hinweis ("Calathea: Kalkempfindlich! Regenwasser oder abgestandenes Leitungswasser") erklaert warum meine Calathea braune Blattspitzen hatte.

**Warum gut:** Praxisnahes, spezifisches Wissen in Alltagssprache. Kein Fachjargon.

---

## Nice-to-Have -- Das wuerde mich bei der Stange halten

### NH-001: Pflanzenfoto und Pflanzenpersoenlichkeit

Wenn ich meiner Monstera ein Foto machen kann und sie "Berta" nenne, und die App dann "Berta braucht heute Wasser" schreibt -- dann wuerde ich die App nicht loeschen. Emotionale Bindung durch Personalisierung.

**Aufwand:** Minimaler Backend-Aufwand (Foto-Upload-Feld auf PlantInstance, nickname-Feld ist schon da in Quick-Add-Plant). Frontend-Aufwand fuer Foto-Anzeige.

### NH-002: Streak-System und kleine Erfolge

"Du pflegst Berta seit 30 Tagen! Rekord!" -- das waere ein Grund die App weiter zu nutzen. Planta macht das. Greg macht das. Kamerplanter hat nichts davon.

**Was fehlt in der Spec:** Kein REQ fuer Gamification, Achievements, Streaks oder Wachstumsfortschritt-Anzeige. Das ist eine bewusste Entscheidung in Richtung professionelles Tool, aber fuer Casual User ein echter Motivations-Killer.

**Vorschlag:** Minimale Gamification als eigenes REQ: "Pflege-Streak" (Tage ohne vergessenes Giessen), "Pflanze am Leben seit X Tagen", einfache Badges fuer Meilensteine.

### NH-003: Gesundheitsampel pro Pflanze

Eine einfache Ampel: Gruen (alles gut), Gelb (bald Aufmerksamkeit noetig), Rot (dringend etwas tun) -- das waere auf dem Dashboard sofort verstaendlich. Kein Fachwissen noetig, sofortiger Ueberblick.

**Was die Spec hat:** REQ-009 (Dashboard) erwaehnt "Health Scores: Aggregierte Bewertung pro Pflanze". Aber im Beginner-Modus wird das Dashboard-Widget wohl versteckt. Schade -- das waere genau das richtige Feature fuer Laien.

**Vorschlag:** Die 3-Farb-Ampel als einziges sichtbares Gesundheits-Widget im Beginner-Modus. Einfach. Verstaendlich. Nuetzlich.

### NH-004: "Was ist das fuer eine Pflanze?" -- Bildbasierter Hilfetext

Wenn die Foto-Erkennung (N-001) noch nicht implementiert ist: Zumindest eine Galerie haeufiger Zimmerpflanzen mit Bildern die ich durchscrollen kann. "Sieht meine Pflanze so aus? Dann ist das eine Monstera." Als Fallback bis KI-Erkennung kommt.

### NH-005: Erinnerungen per E-Mail als sofortiger Fallback

Bevor Web Push implementiert ist: E-Mail-Erinnerung aktivierbar in den Einstellungen. "Kamerplanter Wochenueberblick: Diese Pflanzen brauchen Aufmerksamkeit." Einmal pro Woche, uebersichtlich. Das ist besser als nichts.

---

## Aufwand-Analyse: Minuten pro Woche

| Taetigkeit | Geschaetzter Aufwand | Meine Schmerzgrenze | Bewertung |
|---|---|---|---|
| Onboarding einmalig (Light-Modus) | 2-3 Min | 5 Min | OK |
| Onboarding einmalig (Full-Modus mit Registrierung) | 5-8 Min | 5 Min | Zu viel |
| Pflanze hinzufuegen (Quick-Add-Plant) | 30-60 Sek | 1 Min | Gut |
| Giess-Bestaetigung (1 Tap) | 5 Sek | 5 Sek | Perfekt |
| Duenge-Erinnerung bestaetigen | 5 Sek | 30 Sek | Gut |
| Problem melden (ohne Foto-Diagnose) | 3-5 Min | 2 Min | Zu viel |
| Gesamtaufwand/Woche (Giessen + Duengen) | 1-2 Min | 5 Min | Gut |
| Gesamtaufwand/Woche (mit Problem) | 5-10 Min | 5 Min | Problematisch |

**Fazit Aufwand:** Im Normalbetrieb (alles laeuft gut) bin ich weit unter 5 Minuten. Das ist gut. Sobald eine Pflanze krank wird, bricht das System fuer mich zusammen weil ich nicht weiss was zu tun ist.

---

## Fachbegriff-Audit: Was ich NICHT verstehe

| Begriff in Anforderung | Wo verwendet | Verstehe ich? | Muss fuer Anfaenger ersetzt werden? |
|---|---|---|---|
| Substrat | REQ-019, REQ-002, REQ-004 | Nein | Ja → "Erde" / "Pflanzerde" / "Wachstumsmedium" |
| EC-Wert (mS/cm) | REQ-004, REQ-014, REQ-019 | Nein | Ja → "Naehrstoffgehalt im Wasser" (Einsteiger-Tooltip) |
| VPD (kPa) | REQ-003, REQ-005, REQ-018 | Nein | Ja → UI-NFR-011 hat Erklaerung. Im Beginner-Modus verbergen. |
| PPFD | REQ-005, REQ-003 | Nein | Ja → "Lichtstaerke fuer Pflanzen" oder einfach ausblenden |
| NPK | REQ-004, REQ-021 | Bedingt | Beginner-Tooltip aus UI-NFR-011 reicht: "3 Hauptnaehrstoffe auf jeder Duegenerflasche" |
| pH-Wert | REQ-004, REQ-014, REQ-019 | Bedingt | Beginner-Tooltip aus UI-NFR-011: "Saeuregrad -- Blumenerde hat meistens den richtigen Wert" |
| Phasensteuerung | REQ-003 | Nein | Ja → Im Beginner-Modus komplett unsichtbar |
| Pflanzdurchlauf | REQ-013 | Nein | Ja → UI-NFR-011 hat Erklaerung. Trotzdem verbergen im Beginner-Modus. |
| Cultivar | REQ-001 | Nein | Ja → "Sorte" (Quick-Add zeigt deutschen Namen, kein Problem) |
| Mandant / Tenant | REQ-024 | Nein | Ja → REQ-027 loest das. "Mein Garten" reicht. |
| CalMag | REQ-004 | Nein | Im Beginner-Modus nie sichtbar. Gut so. |
| Karenzzeit | REQ-010 | Nein | Im Beginner-Modus nie sichtbar. Gut so. |
| GDD | REQ-003, UI-NFR-011 | Nein | UI-NFR-011 hat Erklaerung. Im Beginner-Modus trotzdem verbergen. |
| DLI | REQ-005, UI-NFR-011 | Nein | Wie GDD. |
| care_style | REQ-022 | Nein (intern) | Internes Feld, nie dem Nutzer zeigen. Nur das Ergebnis zeigen. |
| Photoperiodismus | REQ-003, UI-NFR-011 | Nein | UI-NFR-011 hat Erklaerung. Im Beginner-Modus unwichtig. |
| Hardiness Zones | REQ-001, UI-NFR-011 | Nein | Nur fuer Outdoor relevant. Im Zimmer-Modus unwichtig. |
| Vermehrungsmanagement | REQ-017 | Nein | Im Beginner-Modus unsichtbar. Gut. |
| IPM | REQ-010, UI-NFR-011 | Nein | UI-NFR-011 hat Erklaerung aber Feature ist trotzdem zu komplex. |
| Fertigation | REQ-004 | Nein | Kein Beginner-Feature. Unsichtbar halten. |
| Fruchtfolge | REQ-002, UI-NFR-011 | Bedingt | Nur Outdoor relevant. Tooltip reicht fuer Freiland-Einsteiger. |

**Fazit Fachbegriffe:** UI-NFR-011 loest das Problem fuer viele Begriffe durch Tooltips und Glossar. Der Beginner-Modus (REQ-021) verbirgt die meisten kritischen Felder. Das Zusammenspiel dieser zwei Features ist die wichtigste Verbesserung seit dem ersten Review. Wenn BEIDE korrekt implementiert sind, ist die Fachbegriff-Huerden weitgehend geloest.

---

## Feature-Relevanz fuer Zimmerpflanzen-Laien

| REQ | Titel | Relevant fuer mich? | Kommentar |
|---|---|---|---|
| REQ-001 | Stammdatenverwaltung | Bedingt | Brauche nur Pflanzenname + Trivialname. Quick-Add loest das. |
| REQ-002 | Standortverwaltung | Bedingt | Nur "Wohnzimmer Fenster" ohne technische Details. |
| REQ-003 | Phasensteuerung | Nein | Zimmerpflanzen-Phasen (REQ-020) reichen. Beginner-Modus verbergen. |
| REQ-004 | Duenge-Logik | Nein | Einsteiger-Ansicht (REQ-021 §3.5) reicht komplett. |
| REQ-005 | Hybrid-Sensorik | Nein | Ich habe keine Sensoren. Manuelle Eingabe wenn noetig. |
| REQ-006 | Aufgabenplanung | Bedingt | Nur einfache Pflegeerinnerungen. Templates fuer Zimmerpflanzen gut. |
| REQ-007 | Erntemanagement | Nein | Ich ernte nichts. Komplett unsichtbar. |
| REQ-008 | Post-Harvest | Nein | Irrelevant. Komplett unsichtbar. |
| REQ-009 | Dashboard | Bedingt | Einfache Gesundheitsampel ja. 6 komplexe Dashboards nein. |
| REQ-010 | IPM-System | Nein | Brauche Symptom-Checker, nicht Karenzzeit-Kalkulator. |
| REQ-011 | Externe Stammdatenanreicherung | Ja (Hintergrund) | Laeuft automatisch, ich merke nichts davon. Gut so. |
| REQ-012 | Stammdaten-Import | Nein | Was soll ich importieren? |
| REQ-013 | Pflanzdurchlauf | Nein | Ich hab keine Gruppe. Unsichtbar halten. |
| REQ-014 | Tankmanagement | Nein | Ich habe keinen Tank. Komplett unsichtbar. |
| REQ-015 | Kalenderansicht | Ja | "Wann muss ich was tun" -- genau richtig. iCal-Export fuer Google Calendar? Perfekt. |
| REQ-016 | InvenTree-Integration | Nein | Was ist InvenTree? |
| REQ-017 | Vermehrungsmanagement | Nein | Ich vermehre nichts. |
| REQ-018 | Umgebungssteuerung | Nein | Ich habe keine Aktoren. Kein Smart Home. |
| REQ-019 | Substratverwaltung | Nein | Ich kaufe Blumenerde. Fertig. |
| REQ-020 | Onboarding-Wizard | Ja | DAS ist mein Einstieg. Gut spezifiziert. |
| REQ-021 | UI-Erfahrungsstufen | Ja | KRITISCH. Ohne den loescht ein Laie die App nach 2 Minuten. |
| REQ-022 | Pflegeerinnerungen | Ja | DER Grund warum ich die App nutze. |
| REQ-023 | Authentifizierung | Bedingt | Notwendig aber so unsichtbar wie moeglich halten. |
| REQ-024 | Mandantenverwaltung | Nein | Ich bin allein. REQ-027 loest das. |
| REQ-025 | Datenschutz (DSGVO) | Bedingt | Erwarte ich, muss aber nichts tun dafuer. |
| REQ-026 | Aquaponik | Nein | Ich habe keine Fische. |
| REQ-027 | Light-Modus | Ja | Loest das Login-Problem fuer Self-Hosters. |

**Zusammenfassung:** 5 REQs sind fuer mich direkt relevant (020, 021, 022, 015, 027). 6 sind im Hintergrund nuetzlich (001, 002, 006, 011, 023, 025). 16 sind komplett irrelevant. Das bedeutet: 59% der Anforderungen sind fuer mein Szenario nicht nuetzlich. Das ist okay wenn ich sie nie sehe.

---

## Nutzerreise: Mein idealer erster Tag mit der App

**Szenario: Light-Modus auf Raspberry Pi oder Docker Compose lokal**

1. Browser oeffnen, URL eingeben → sofort App, kein Login
2. Onboarding-Wizard startet automatisch
3. Schritt 1: "Einsteiger" auswaehlen -- ein Tap
4. Schritt 2: "Zimmerpflanzen" auswaehlen -- ein Tap
5. Schritt 3: "Mein Wohnzimmer" eingeben, Fensterbank auswaehlen
6. Schritt 4: Monstera, Kaktus anwaehlen, Menge 2 (fuer das "gruene Ding" tippe ich Freitext)
7. Schritt 5: "Setup abschliessen" → Konfetti
8. Dashboard: "Deine 3 Pflanzen sind eingerichtet. Naechstes Giessen: Monstera in 3 Tagen."
9. App als PWA installieren ("Zu Homescreen hinzufuegen")
10. 3 Tage spaeter: Push-Benachrichtigung (Web Push) "Giess deine Monstera"
11. Ich gehe hin, giesse, oeffne App, tippe "Erledigt". Fertig.

**Gesamtdauer Einrichtung:** 3-4 Minuten. Das ist akzeptabel.

**Was mich noch stoert:** Schritt 6 -- fuer das "gruene Ding" muss ich einen Freitext eingeben und kriege dann kein Pflegeprofil. Das ist ehrlich, aber unbefriedigend.

**Szenario: Full-Modus (Cloud/SaaS)**

1. Browser oeffnen → Login-Screen mit Google-Button prominent
2. "Mit Google anmelden" → direkt zum Onboarding-Wizard
3. Schritte 1-7 wie oben
4. E-Mail-Verifizierung: Muss ich das wirklich? Bei Google-Login kein Verifizierungs-Mail noetig.
5. Gesamtdauer: 4-5 Minuten mit Google-Login. Akzeptabel wenn kein Formular ausgefuellt werden muss.

---

## Vergleich mit Konkurrenz

| Feature | Planta | Greg | Kamerplanter |
|---|---|---|---|
| Foto-Erkennung | Ja | Ja | NEIN (N-001) |
| Push-Giessererinnerung | Ja (nativ) | Ja (nativ) | Web Push (geplant) |
| Anfaenger-freundlich | Ja | Ja | Teilweise (REQ-021) |
| Kostenlos nutzbar | Freemium | Freemium | Self-Host kostenlos |
| Kein Login-Zwang | Nein | Nein | Ja (REQ-027 Light-Modus) |
| 1-Tap Giess-Bestaetigung | Ja | Ja | Ja (REQ-022) |
| Symptom-Checker | Einfach | Nein | NEIN (REQ-010 zu komplex) |
| Zimmerpflanzen-Presets | Ja | Ja | Ja (REQ-022 care_styles) |
| Fachbegriff-Erklaerungen | Nein | Nein | Ja (UI-NFR-011) |
| Offline-Faehigkeit | Begrenzt | Nein | Ja (UI-NFR-012) |
| Pro-Features | Nein | Nein | Ja (Hydro, IPM, etc.) |
| Datenschutz/Self-Host | Nein | Nein | Ja (REQ-027) |

**Wo Kamerplanter gewinnt:**
- Self-Hosting / Datenschutz: Einzigartiges Feature gegenueber allen Konkurrenten
- Fachbegriff-Erklaerungen (UI-NFR-011): Niemand macht das so gut
- Zimmerpflanzen-Pflegewissen (REQ-022 biologische Begruendungen): Deutlich tiefer als Planta
- Offline-Faehigkeit: Besser als Konkurrenz

**Wo Kamerplanter verliert:**
- Foto-Erkennung: Kompletter Fehlstelle, Dealbreaker fuer viele
- Native Push-Notifications: Web Push ist kein Ersatz fuer native iOS/Android-Notifications
- Gamification: Null. Planta macht das gut.
- Symptom-Checker: Fehlt komplett fuer Laien

---

## Empfehlung: Top-5-Massnahmen damit ICH die App nutze

### Massnahme 1: Foto-Erkennung als REQ spezifizieren (N-001)

**Beschreibung:** Adapter-Muster analog zu REQ-011. PlantNet-API (kostenlos, Open Source) als Primaer-Adapter. Einstiegspunkt: "Ich kenne den Namen nicht"-Button in Quick-Add-Plant oeffnet Kamera, sendet Foto an PlantNet, zeigt Top-3-Ergebnisse zur Bestaetigung.

**Aufwand:** Mittel. API-Integration + UI-Komponente. PlantNet-API ist gut dokumentiert.

**Auswirkung fuer Casual User:** Sehr hoch. Loest das erste und wichtigste Problem.

### Massnahme 2: Push-Notification-Adapter spezifizieren (N-003)

**Beschreibung:** REQ-022 muss einen konkreten Zustellkanal definieren. Minimum: E-Mail via vorhandenem EmailService (schon implementiert). Erweiterung: Web Push (UI-NFR-012 ist vorbereitet). Bonus: Apprise-Adapter fuer Pro-Nutzer.

**Aufwand:** Gering fuer E-Mail (EmailService vorhanden). Mittel fuer Web Push.

**Auswirkung fuer Casual User:** Sehr hoch. Ohne Notification ist die App fuer Vergessliche nutzlos.

### Massnahme 3: Symptom-Checker als separates, einfaches Feature

**Beschreibung:** Kein IPM-Kalkulator. Ein einfacher Entscheidungsbaum: "Was siehst du?" → Gelbe Blatter / Braune Spitzen / Weiche Stellen / Kleine Insekten / Weisser Belag → "Das koennte X sein" → "Was du tun kannst: Y" in 3 Schritten.

**Aufwand:** Mittel. Entscheidungsbaum als JSON, einfache Frontend-Komponente.

**Auswirkung fuer Casual User:** Hoch. "Was ist mit meiner Pflanze?" ist die zweithaeufigste Frage nach "Wann giessen?".

### Massnahme 4: Minimale Gamification spezifizieren

**Beschreibung:** Pflege-Streak (Tage ohne vergessenes Giessen). Meilenstein-Badges ("Pflanze seit 30 Tagen am Leben!"). Wachstumsfortschritt pro Pflanze ("Deine Monstera wächst seit 6 Monaten!"). Ein eigenes REQ (analog zu REQ-022) mit 5 einfachen Achievements.

**Aufwand:** Gering. Hauptsaechlich Frontend-Feature auf Basis vorhandener Daten.

**Auswirkung fuer Casual User:** Mittel. Kein Dealbreaker, aber hoehere Retention-Rate.

### Massnahme 5: Standort-Lichtberatung fuer Laien

**Beschreibung:** Nach Standort-Eingabe im Wizard: Einfache Einschaetzung welche Pflanzentypen fuer diesen Standort geeignet sind. "Nordfenster: nur Schattenpflanzen (Einblatt, Farn). Suedfenster: sonnenhungrige Pflanzen (Kaktus, Chili). Keine direkte Sonne: Monstera, Pothos." Kein PPFD, keine Messung. Nur qualitative Aussagen.

**Aufwand:** Gering. Regelbasierte Logik auf Basis von REQ-001 Lichtbedarf-Kategorien.

**Auswirkung fuer Casual User:** Mittel-hoch. Verhindert dass Pflanzen am falschen Standort sterben.

---

## Vergleich mit Vorgaenger-Review (2026-02-27)

| Finding | Status im Vorgaenger | Status jetzt | Veraenderung |
|---|---|---|---|
| N-001 Foto-Erkennung | Dealbreaker, kein REQ | Dealbreaker, kein REQ | Unveraendert |
| N-002 Registrierungszwang | Dealbreaker | Teilweise geloest (REQ-027) | Verbessert |
| N-003 Push-Benachrichtigungen | Dealbreaker | Bleibt Dealbreaker | Unveraendert |
| F-003 Mandantenverwaltung sichtbar | Frustrierend | Teilweise geloest (REQ-027) | Verbessert |
| F-004 Zu viele Pflichtfelder | Frustrierend | Geloest (REQ-021 v1.1 Quick-Add) | Geloest |
| U-004 Fachbegriffe | Ueberfordernd | Teilweise geloest (UI-NFR-011) | Verbessert |

**Gesamttendenz:** Seit dem Vorgaenger-Review wurden mehrere wichtige Probleme behoben. Die App ist messbara einsteigerfreundlicher geworden. Die zwei verbliebenen Dealbreaker (Foto-Erkennung, Push-Delivery) sind die letzten grossen Huerden.

---

*Ende des Reviews. Datum: 2026-02-28.*
