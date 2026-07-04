# Docs-Audit: Vollständigkeit & Zielgruppen-Konformität (Juli 2026)

**Datum:** 2026-07-04
**Branch / Worktree:** `chore/docs-audit` (`/home/nolte/repos/.worktrees/kamerplanter/docs-audit`)
**Basis:** `develop` @ `740dad66`
**Methodik:** 8 parallele Fable-5-Audit-Agenten (read-only), je thematisches Bündel bzw. Querschnitt. Jede Enduser-Doc-Seite (`docs/de/`, `docs/en/`) wurde gegen die Spezifikation (`spec/req/`) **und** den tatsächlich implementierten Code (`src/frontend/src/pages/`, `src/backend/app/`, `src/knowledge-service/`) geprüft, sowie gegen die 12 Zielgruppen-Personas (`spec/target-audiences/`).

---

## 1. Gesamtbewertung

Die Enduser-Dokumentation ist **strukturell reif und sprachlich überwiegend zielgruppengerecht**: DE/EN-Parität ist mit *einer* Ausnahme durchgängig, die konzeptionellen Guides (VPD, GDD, EC-Budget, Alkalinität/pH-Reserve, Curing, Companion-Grundlagen) sind fachlich stark und codetreu, und die Computer-Vision-Strecke (Pflanzenidentifikation, Schädlingserkennung, Referenzbild-Kuration, IPM-Detailseiten) ist vorbildlich.

Das **zentrale, systematische Problem ist Doku-Code-Drift** — und zwar in **beide Richtungen gleichzeitig**:

1. **Doku eilt dem Code voraus** (irreführend, gefährlicher): Zahlreiche Seiten beschreiben UI-Workflows und Features als fertig nutzbar, die im Code nicht existieren oder nicht einmal geroutet sind. Ein Nutzer folgt Klickstrecken zu Menüpunkten, die es nicht gibt.
2. **Doku hinkt dem Code hinterher** (Lücke): Groß ausgebaute, live erreichbare Features haben **keine** Enduser-Seite.
3. **Faktendrift in Tabellen**: Preset-Zahlen, Enum-Listen, Starter-Kits, EC-Zielwerte weichen systematisch vom Code ab, weil sie manuell gepflegt statt generiert werden.

Dazu kommen strukturelle Zielgruppen-Lücken (keine kuratierten Journeys, Laien landen in `kubectl`/`curl`-Doku) und ein paar mechanische Freshness-Defekte.

**Findings gesamt:** 3 × P0, ~30 × P1, ~30 × P2, ~20 × P3.

---

## 2. Die sechs übergreifenden Muster

Diese Muster wiederholen sich über alle Bündel — sie zu adressieren wirkt stärker als das Abarbeiten einzelner Findings.

### M-1 — Uneinheitliche Kennzeichnung unimplementierter Features
Manche Seiten weisen ihren „geplant/Scaffold"-Status **korrekt** per `!!! warning "Noch nicht implementiert"` aus (`propagation.md`, `actuator-control.md`, `guides/post-harvest.md`, `dashboard.md`, `guides/data-retention.md`), andere beschreiben spezifizierte-aber-nicht-gebaute Features als **fertig** (`sensors.md` Fallback/Ausfall/MQTT, `tenants.md` Gemeinschaftsfunktionen, `harvest.md` Trocknung/Spülung, `care-reminders.md` Überwinterung, `ai-assistant.md`/`ai-providers.md`, `calendar.md` Quick-Actions). **→ Verbindliche Admonition-Konvention einführen und flächendeckend anwenden.**

### M-2 — „Handlungsanweisung im Indikativ" trotz Warnbanner
Selbst Seiten *mit* korrektem Banner (z. B. `propagation.md`) beschreiben danach ~170 Zeilen präzise Menüpfade im Präsens, als existierten sie. Das Banner geht im Fließtext unter. **→ Bei geplanten Features Handlungsanweisungen ins Futur setzen („wird … bieten") oder auf eine kompakte Konzeptseite eindampfen.**

### M-3 — Manuell gepflegte Tabellen driften vom Code
Care-Style-Presets (6 von 9 Zeilen falsch), `FAMILY_CARE_MAP`, Starter-Kits (9 dokumentiert vs. 11 real), Substrat-Typen, Ereignis-Kategorien, Workflow-Templates (4 real vs. 16 dokumentiert), EC-Zieltabellen, Artenzahlen. **→ Diese Tabellen aus den Seed-YAMLs/Enums generieren (Include-Mechanismus oder Build-Step) statt handzupflegen.**

### M-4 — Feature-Referenz statt zielgruppen-kuratierter Journeys
33 Feature-Seiten, aber niemand führt eine Persona durch ihren realen End-to-End-Ablauf (Grow-Zyklus Keimung→Cure, Freiland-Gartenjahr, Hydroponik-Setup). Alle drei Getting-Started-Persona-Tabs münden in **dieselbe** Seite. **→ Kuratierte Use-Case-Guides aus vorhandenen Inhalten verketten (höchster Hebel, geringster Aufwand — Inhalte existieren bereits).**

### M-5 — Betreiber-/Entwickler- und Endnutzer-Doku vermischt
Laien, die „Guides" oder „Fehlerbehebung" öffnen, landen bei `kubectl`, `VAPID`-Schlüsseln oder Claude-Code-Agent-Workflows; Auth-/Konto-Themen werden Endnutzern nur als `curl`-API-Doku angeboten. **→ Betreiber-Guides klar labeln/verschieben; niedrigschwellige Endnutzer-Pendants ergänzen.**

### M-6 — Kein zentrales Glossar
VPD, EC, GDD, Karenz, Hysterese, PPFD, DWC/NFT, CanG werden (wenn überhaupt) verstreut erklärt. Für die Laien-Zielgruppen (UZG-001, ZG-003) fehlt ein Anker. **→ Statische Glossar-Seite als Brücke bis REQ-035.**

---

## 3. P0 — Sofort (irreführend, Feature grob falsch dargestellt)

| # | REQ | Seite(n) | Befund | Maßnahme |
|---|-----|----------|--------|----------|
| P0-1 | REQ-031 | `user-guide/ai-assistant.md`, `user-guide/ai-providers.md` (+EN) | Dokumentieren komplettes KI-Chat-Panel, Tipp-Karten, Diagnose-Modus **und** die UI „Einstellungen → KI-Provider" (Provider hinzufügen/testen/Priorität) als fertig. Real: `KIAssistentPage.tsx` ist ein Scaffold und **nicht geroutet**; Provider-Konfig läuft ausschließlich per Env-Var am Knowledge-Service. | Beide Seiten als „Preview/in Entwicklung" kennzeichnen oder auf Ist-Stand umschreiben (KI nur via API/Knowledge-Service; Provider-Setup = Betreiber-Env-Vars `LLM_PROVIDER`/`LLM_MODEL`). Ollama-/Hardware-Anleitungen als Betreiber-Doku erhalten. |
| P0-2 | REQ-013 / REQ-028 | `user-guide/planting-runs.md`, `guides/companion-planting.md` (+EN) | Erfundener Run-Typ **„Mischkultur"** mit Rollen-Workflow (Primär-/Begleit-/Fangpflanze), Begleiter-Vorschlägen im Dialog und Grün/Gelb/Rot-Kompatibilitätscheck. Real: `PlantingRunType` kennt nur `MONOCULTURE`/`CLONE`, kein `role`-Feld; die Spec modelliert Mischkultur bewusst über separate Runs + Standort-Graph. | „Mischkultur"-Zeile + Rollen-Schritt streichen; Companion-Abschnitt auf die real existierenden Oberflächen umschreiben (siehe P1-Companion). |
| P0-3 | REQ-013 | `user-guide/planting-runs.md` (+EN) | Button **„Folgepflanzung anlegen"** (Sukzessions-Aussaat mit Intervall-Kopie) als vorhandenes Feature beschrieben. Real: kein Succession-Code (offener Drift, Issue #299), kein Warnbanner. | Abschnitt entfernen oder mit „Noch nicht implementiert"-Banner kennzeichnen. |

---

## 4. P1 — Wesentliche Lücken & Widersprüche

### 4a. Doku eilt Code voraus (nicht existierende Features als fertig beschrieben)

| REQ | Seite | Befund | Maßnahme |
|-----|-------|--------|----------|
| REQ-005 | `sensors.md` | Fallback-Automatik, Sensor-Ausfallerkennung (6 h), Interpolation, manuelle Mess-UI an Pflanze/Standort als vorhanden. Real: nur Sensor-CRUD + HA-Live-Read + Observations-API; manuelle Messung nur am **Tank**. | Betroffene Abschnitte mit Warnbanner (wie Wetter-Abschnitt); manuelle Eingabe auf realen Stand (Tank) umschreiben. |
| REQ-005 | `sensors.md`, `actuator-control.md` | MQTT als funktionierende Quelle 1. Real: keine MQTT-Ingestion, Feld ist `# Future`. | MQTT als „geplant/Future" kennzeichnen. |
| REQ-024 | `tenants.md` | Pinnwand, Gießrotation, Einkaufsliste mit Schritt-für-Schritt-Anleitungen + in Rollen-Matrix. Real: **kein** Backend/Frontend/i18n dafür. | Abschnitt + Matrix-Zeilen entfernen oder Warnbanner. |
| REQ-007/008 | `harvest.md` | Buttons „Trocknungsphase starten", „Spülprotokoll starten", „Dunkelphase planen". Real: REQ-008 ist Scaffold; widerspricht `guides/post-harvest.md`. | Abschnitte auf „Teilweise implementiert" reduzieren; Trockengewicht auf reale Felder `*_dry_weight_g` beschränken. |
| REQ-006 | `tasks.md` | 16 System-Workflow-Templates gelistet. Real: `workflows.yaml` hat **4** (Cannabis SOG, Tomato Standard, General Maintenance, Tank Anmischen). | Liste auf 4 kürzen; „Eigene Templates" beibehalten. |
| REQ-022 | `care-reminders.md` | Überwinterungsmanagement (Winterhärte-Ampel, Frostprognose-Trigger, Knollen-Zyklus) als fertiges System. Real: kein `OverwinteringProfile`, Reminder-Typen nur im Enum ohne Logik (Issue #299). | Warnbanner; Erinnerungstyp-Tabelle auf die 6 real generierten Typen reduzieren. |
| REQ-015 | `calendar.md` | Ansichtsmodi „Monat/Woche/Tag/Liste" + Quick-Actions (Aufgabe direkt erledigen, aus leerem Tag erstellen). Real: 5 andere Tabs (Monat, Liste, Phasen-Timeline, Aussaatkalender, Saisonübersicht); Klick navigiert nur zur Detailseite. | Tab-Tabelle ersetzen; fiktive Interaktionen streichen. |
| REQ-004 | `fertilization.md` | „Spülprotokoll starten"-Button an Pflanze + automatische Gieß-Aufgaben. Real: reine Rechner-Karte (`/nutrient-calculations/flushing`), keine Task-Erzeugung; Spüldauer-Werte widersprüchlich (21–42 vs. Code 14–30). | Auf realen Rechner-Ablauf umschreiben; Werte angleichen. |
| REQ-014 | `watering-log.md` | Falsches Konzeptmodell (aggregiert vs. real: ersetzt Event-Modelle), fiktive Spalten „Typ/Quelle", EC-Minigraph, Spülungserkennung, HA-Auto-Eintrag, 90-Tage-Retention. Real: keines davon im Code. | Seite gegen reale Implementierung neu schreiben. |
| REQ-010 | `pest-management.md` | „Nützling freigesetzt", „Befallshistorie", manueller Inspektions-/Behandlungs-Flow. Real: Beneficials nur Stammdaten; Inspektionen entstehen nur über Foto-Erkennungs-Dialog; APIs ohne dokumentierte UI. | Nicht existente Menüs entfernen/als geplant; auf reale Wege umschreiben. |

### 4b. Implementierte Features ohne Doku (Existenz-Lücken)

| REQ | Feature (implementiert, live) | Maßnahme |
|-----|-------------------------------|----------|
| REQ-030 | **Benachrichtigungssystem** — 4-Kanal (HA/E-Mail/PWA/**Apprise**), Kanal-Präferenzen, Ruhezeiten, Test-Versand, Notification-Center. Apprise nirgends erwähnt. | Neue Seite `user-guide/notifications.md` (DE+EN) + Env-Vars in Referenz. |
| REQ-012 | **Stammdaten-Import** — `ImportPage.tsx` (geroutet), CSV-Templates, Dry-Run→Confirm. Keine einzige Doc-Seite. | Neue Seite `user-guide/import.md`. |
| REQ-004 | **Multi-Channel Delivery (Ausbringungskanäle)** — Fertigation/Drench/Foliar/Top-Dress je Phase, komplettes Frontend. | Abschnitt in `fertilization.md`. |
| REQ-004-A | **Wasser-Mischer + EC-Budget-Rechner** (Osmose-Rückwärtsberechnung, EC-Budget-Vorschau) — nur theoretisch in `nutrient-mixing.md`. | Bedien-Abschnitte je Rechner-Karte. |
| REQ-028 | **Companion-/Fruchtfolge-UI** — Stammdaten-Kompatibilitätspflege, `SpeciesCompanionTab`, `CropRotationPage`, Slot-Nachbarschafts-Check. | Companion-Guide neu schreiben (ersetzt P0-2-Fiktion). |
| REQ-001/006 | **Aktivitäten & Aktivitätsplan** — Stammdaten-Sektion + Aktivitätsplan-Tab im Run („auf Run/Pflanze anwenden"). | Abschnitte in `plant-management.md` + `planting-runs.md`/`tasks.md`. |
| REQ-003 | **Phasendefinitionen & -abläufe** (`/phasen/definitionen`, `/phasen/ablaeufe`), Auto-Transitions, 11 Sequenz-Muster, Biennial/Vernalisation. `growth-phases.md` verneint Auto-Übergänge fälschlich und zeigt veraltetes 6-Phasen-Modell inkl. entfernter „Ernte"-Phase. | Phasenmodell aktualisieren; Verwaltungs-Abschnitt + Auto-Transitions ergänzen. |
| REQ-019 | **Substrat-Chargen** (Wiederverwendung, Slot-Zuweisung), **Mix-Dialog** (Komponenten + %). Doku beschreibt Flows auf Substrat- statt Charge-Ebene; FAQ „Mix im Notizfeld" veraltet. | Typ-Tabelle aus Enum regenerieren; Chargen- + Mix-Abschnitt. |
| REQ-011 | **Externe Stammdatenanreicherung** (GBIF/Perenual, Sync, Origin-Chip). Keine eigene Seite. | Neue Seite. |
| REQ-013 | **Pflanzentagebuch (Diary)** pro Run/Pflanze. Undokumentiert. | Abschnitt in `planting-runs.md`. |
| REQ-023 | **Auth/Konto-Flows** (Register/Login/OIDC/Reset/Sessions) nur als `curl`-API-Doku. | Enduser-Seite `user-guide/account.md`; Links aus tenants/privacy umbiegen. |

### 4c. Faktendrift & Konsistenz

| REQ | Seite | Befund | Maßnahme |
|-----|-------|--------|----------|
| REQ-022 | `care-reminders.md` | Care-Style-Preset-Tabelle in **6 von 9** Zeilen falsch (succulent 2,5 vs. 3,0; orchid 1,5 vs. 2,0; cactus 3,0 vs. 4,0; …); `FAMILY_CARE_MAP` weicht ab. | Tabellen aus `care_reminder_engine.py` generieren. |
| REQ-020 | `onboarding.md` | „Neun Starter-Kits" inkl. nicht existierender; real **11** in `starter_kits.yaml`, teils andere Namen. | Tabelle aus YAML regenerieren. |
| REQ-004/004-A | `fertilization.md` vs. `nutrient-mixing.md` | Widersprüchliche EC-Zieltabellen; nur nutrient-mixing entspricht dem validierenden `EC_MAX_TABLE`. | fertilization-Tabelle auf REQ-004-A/Code angleichen. |
| REQ-025 | `privacy.md` | Banner „nicht implementiert" ist **faktisch falsch** — Self-Service-API (`/api/v1/privacy/`) ist komplett da; nur die UI ist nicht geroutet. | Banner präzisieren („API verfügbar, UI folgt"). |
| REQ-005/039 | `locations-substrates.md` | Klimazonen-Beispiel „Cfb" (Köppen) kollidiert mit USDA-Schema, auf dem REQ-039/022 aufbauen. | Beispiel auf „8a" ändern + erklären. |
| HA | `home-assistant-integration.md` | JSON-Beispiel-Feld `enabled_keys` statt real `entity_keys` — Copy-Paste für HA-Entwickler bricht. | Feldname korrigieren (DE+EN). |

---

## 5. P2 — Verbesserungen (Auswahl, thematisch)

- **REQ-007 `harvest.md`**: Reifeprognose falsch (basiert real auf manuellen Reife-**Beobachtungen**, nicht „Tage+GDD"); Ertragskennzahlen nicht automatisch berechnet; Qualitätsskala (0–100, Grade bis D) falsch; kontinuierliche Ernte fehlt.
- **REQ-015 `calendar.md`**: 11 reale Ereignis-Kategorien vs. 6 dokumentierte; Feed-Token-Regenerierung + Ablauf (HTTP 410) undokumentiert (sicherheitsrelevant für geteilte Links); Aussaatkalender-Abschnitt zu dünn (Blüte-Balken, Kategorien, Vorrangregeln fehlen).
- **REQ-006 `tasks.md`**: Wiederholungsregeln, Checklisten, Timer, Skill-Level, Foto-Pflicht, `dormant`-Status undokumentiert; Eskalations- und Pflegestil-Aussagen widersprechen `care-reminders.md` (zwei Seiten dokumentieren dasselbe unterschiedlich falsch → konsolidieren).
- **REQ-022 `care-reminders.md`**: Undokumentierte Guards (Gießplan-Guard, Nährstoffplan-Voraussetzung für Dünge-Erinnerungen) — häufigste Ursache fehlender Erinnerungen.
- **REQ-004-A / REQ-021**: Rechner sind UI-Erfahrungsstufen-gated (intermediate/expert) — Doku erwähnt das nicht, Casual-Nutzer findet die beschriebenen Karten nicht.
- **REQ-014 `tanks.md`**: Equipment-Attribute, gelöster Sauerstoff, EC-Verdünnungsrechner, Tank-Verknüpfung, Live-Sensorwerte fehlen.
- **REQ-004 `fertilization.md`**: Dünger-Bestandsverwaltung, Inkompatibilitäts-Pflege, Plan clone/validate, Gantt-Visualisierungen undokumentiert.
- **Terminologie-Drift**: Doku-Navigationspfade („Düngung → Dünger", „Stammdaten → Dünger") stimmen nicht mit App-Labels („Düngemittel", „Düngeereignisse", „Gießprotokoll") überein.
- **REQ-023**: Enduser-Konto-Kapitel fehlt (siehe P1-4b); Consent-Tabelle in `privacy.md` unvollständig (`pest_detection_cloud`/Kindwise fehlt).
- **RAG/KI**: `rag-knowledge-base.md` + `architecture/ai-architecture.md` nennen falsches Embedding-Modell (MiniLM 384-dim statt multilingual-e5 1024-dim, ADR-006) und nicht existierenden Reindex-Task (real: `/ingest`); Guide-Upload-UI existiert nicht.
- **REQ-029/043**: `plant-identification.md`-FAQ verneint Krankheits-Foto-Erkennung, obwohl `pest-detection.md`/Kindwise sie liefern (Widerspruch + fehlender „Siehe auch").

---

## 6. Zielgruppen-Konformität

**Abdeckungs-Ranking (12 Personas):**

| Grad | Zielgruppen | Kern |
|------|-------------|------|
| **Gut** | ZG-003 Zimmerpflanzen, ZG-001 Cannabis-Indoor, ZG-004 Gemeinschaftsgarten | Ton/Fachtiefe passt; einzelne Bündel-Lücken |
| **Mittel** | ZG-006 Hydroponik, ZG-002 Freiland, UZG-001 Casual, ZG-005 Social Club | Bausteine da, aber fragmentiert / Einstieg nicht verdrahtet / Compliance-Klammer fehlt |
| **Schlecht** | UZG-002 Marktgärtner, UZG-003 Bildung, UZG-004 Sammler, UZG-005 Gewächshaus, UZG-006 Microgreens | Überwiegend Produkt-Gaps (keine Doku-Maßnahme vor Feature-Entscheidung) |

**Die drei größten Zielgruppen-Lücken (Doku-seitig adressierbar):**

1. **[P1] Keine kuratierten Journeys** für die 3 Primär-Zielgruppen + Hydroponik. Getting-Started-Tabs münden alle in dieselbe Seite; danach 33 Einzelseiten. → Drei verkettete Guides: „Cannabis-Grow-Zyklus Keimung→Cure", „Das Freiland-Gartenjahr", „Hydroponik-Setup NFT/DWC". Inhalte existieren bereits — nur verketten. **Höchster Hebel.**
2. **[P1] UZG-001-Foto-Einstieg nicht zu Ende gebaut**: `plant-identification.md` ist gut, aber vom Getting-Started entkoppelt und fehlt im user-guide-Index; „Fehlerbehebung" führt Laien zu `kubectl`; pflanzenbezogene Problem-Diagnose („gelbe Blätter?") und eine Endnutzer-Benachrichtigungs-Anleitung fehlen. → Foto-Einstieg in `erste-pflanze.md` verdrahten; `troubleshooting.md` in Betriebs-Doku umbenennen + Enduser-Symptom-Guide „Meiner Pflanze geht es schlecht" anlegen.
3. **[P1] ZG-005 Compliance-Klammer fehlt**: Einzelfeatures (Chargen, Karenz, Retention, Rollen) da, aber kein Guide „CanG-konforme Dokumentation für Anbauvereinigungen" — der Kaufgrund dieser Zielgruppe.

**Weitere:** `guides/index.md` listet nur 6 von 11 Guides (u. a. Nachernte & Mischkultur unsichtbar); Freiland-Begriffe „Eisheilige/Phänologie/Forsythienblüte" kommen in der gesamten Doku nicht vor; `docs/de/index.md` konfrontiert Endnutzer mit `docker compose`/Vibe-Coding-Projektgeschichte statt Getting-Started.

---

## 7. Struktur & Freshness (mechanisch, schnell behebbar)

- **[Critical] `docs/en/development/agent-catalog.md` löschen** — veraltete, EN-only, verwaiste, generierte Seite; erledigt in einem Zug **11 tote Cross-Refs**, die einzige DE/EN-Paritätslücke und einen Orphan.
- **[Critical] EN-Anker** `docs/en/user-guide/admin.md:395`: `#enabling-pest-recognition` → `#enabling-pest-detection`.
- **[Warning] EN hinter DE**: `adr/001-arangodb-multi-model.md` (fehlende Abschnitte Alternativen/Risiken/Referenzen) und `guides/troubleshooting.md` (32 DE-only-Zeilen aus #156) nachziehen.
- **[Warning] `user-guide/index.md` unvollständig**: listet 21 von 33 Seiten (fehlen u. a. Druckansichten, Foto-Galerie, Gießprotokoll, Object Storage, Detail-Seiten, Foto-Identifikation).
- **[Info] `mkdocs.yml`**: `edit_uri` zeigt auf `main` statt `develop`; `nav_translations` fehlt „Module & Funktionen" (EN-Nav zeigt DE-Label); Leiche „Object Storage — Helm".
- **[Info] Verwaiste Seiten** außerhalb der Sprachbäume: `docs/wichtige-prompts.md`, `docs/security/nuclei-triage.md` (Letztere mit `TBD`-Verweis auf nicht existierendes `rotation.md`).
- **[Upstream] Bug** in `claude-shared/scripts/check_links.py` (`_pre_slug` entfernt Underscores pauschal → systematische Anker-False-Positives) — eigener Fix im claude-shared-Repo.

---

## 8. Empfohlene Maßnahmen-Roadmap (nach Hebel/Aufwand)

**Welle 1 — Sofort, kleiner Aufwand, hoher Schaden bei Nichtstun (P0 + Quick Freshness):**
1. P0-1/2/3 entschärfen (KI-Assistent/Provider, Mischkultur-Run, Sukzession) — Banner/Umschreiben.
2. `agent-catalog.md` löschen; EN-Anker-Fix; `edit_uri` → `develop`.
3. `privacy.md`-Banner korrigieren (verneint fälschlich vorhandene DSGVO-API).

**Welle 2 — Drift-Korrektur (P1 4a + 4c):** Alle „Doku eilt voraus"-Abschnitte per einheitlicher Admonition (M-1/M-2) markieren oder umschreiben; Faktentabellen aus Code/Seed regenerieren (M-3). Priorität: `sensors.md`, `tenants.md`, `harvest.md`, `care-reminders.md`, `tasks.md`, `calendar.md`, `watering-log.md`, `fertilization.md`.

**Welle 3 — Existenz-Lücken schließen (P1 4b):** Neue Seiten für live-erreichbare, aber undokumentierte Features: `notifications.md`, `import.md`, `account.md`, Enrichment; Abschnitte für Multi-Channel-Delivery, Companion-UI, Aktivitätsplan, Phasendefinitionen, Substrat-Chargen, Diary.

**Welle 4 — Zielgruppen-Ausbau (M-4/M-5/M-6):** Drei kuratierte Journeys; `troubleshooting`-Split + Symptom-Guide; Glossar-Seite; `guides/index.md` + `user-guide/index.md` vervollständigen; Getting-Started-Tabs auf Journeys verdrahten; ZG-005-Compliance-Guide.

**Prozess-Empfehlung (verhindert Rückfall):** Faktentabellen generieren statt handpflegen (M-3); „Doku-Sync" als Definition-of-Done in Feature-PRs; Admonition-Konvention in den Doku-Style-Guide aufnehmen.

---

## Anhang: Findings pro Bündel (Agenten-Quellen)

| Bündel | P0 | Kernbefund |
|--------|----|-----------|
| Kultur-Grundlagen (REQ-001/002/019/003/013/017/028) | 2 | Mischkultur-Run + Sukzession erfunden; Companion-UI/Aktivitätsplan/Phasen-Verwaltung/Substrat-Chargen/Diary undokumentiert |
| Bewässerung/Düngung (REQ-004/004-A/014/037) | 0 | Multi-Channel + Wasser-Mischer undokumentiert; watering-log.md konzeptionell falsch; REQ-037 korrekt ohne Doku |
| Sensorik/Aktorik/HA (REQ-005/018/039) | 0 | sensors.md beschreibt nicht implementierte Automatiken; REQ-039 ohne Seite; HA-API-Feldname falsch |
| Ernte/Kalender/Aufgaben/Pflege (REQ-007/008/015/006/022) | 0 | ~Dutzend fiktive Workflows; Care-Presets 6/9 falsch; reale Highlights (Timeline, Saisonübersicht, Recurrence) fehlen |
| IPM/CV/KI (REQ-010/038/043/044/029/031/035/036/011/040/041/033) | 1 | KI-Assistent/Provider-UI existiert nicht; CV-Strecke exzellent; REQ-011 einzige echte Existenz-Lücke |
| Plattform/Datenschutz (REQ-009/012/016/020/021/023/024/025/026/027/030/032/034/042) | 0 | tenants Gemeinschaftsfunktionen fiktiv; REQ-030/012 ohne Seite; Privacy-Banner falsch; Starter-Kits drift |
| Freshness/Parität | — | agent-catalog.md löschen (11 tote Refs); EN-Anker; EN-ADR/troubleshooting hinter DE |
| Zielgruppen-Konformität | — | Keine kuratierten Journeys; Laien→kubectl/curl; kein Glossar; ZG-005-Compliance fehlt |
