# Umsetzungsplan: Dokumentation vervollständigen & Docs-Audit abarbeiten

**Datum:** 2026-07-04
**Branch / Worktree:** `chore/docs-audit`
**Quelle:** [`docs-completeness-audience-audit-2026-07.md`](./docs-completeness-audience-audit-2026-07.md) (8 Fable-5-Audit-Bündel)
**Ziel:** Jeden Audit-Finding (3× P0, ~30× P1, ~30× P2, ~20× P3) in ein umsetzbares Arbeitspaket überführen und in reviewbare PRs bündeln, sodass das Audit nachweislich vollständig abgearbeitet ist (Tracking-Matrix in §7).

---

## 0. Prinzipien & Konventionen

**Seitenzentriert statt findingzentriert.** Wo mehrere Findings dieselbe Seite betreffen, werden sie in **einem** Arbeitspaket (WP) gebündelt — die Seite wird einmal angefasst und dabei Drift-Korrektur (P1 4a), Lückenfüllung (P1 4b), Faktenkorrektur (4c) und P2/P3-Feinschliff derselben Datei gemeinsam erledigt. Das vermeidet Mehrfach-Reviews und Merge-Konflikte.

**DE ist kanonisch, EN wird gespiegelt.** Jede inhaltliche Änderung erfolgt paarweise `docs/de/…` + `docs/en/…`. Alle Sachfehler sind aktuell in beide Sprachen gespiegelt — Korrekturen ebenso.

**Verbindliche Admonition-Konvention (behebt Muster M-1/M-2).** Bevor die Korrektur-Wellen starten, wird eine Konvention im Backend-/Doku-Style-Guide verankert und durchgängig angewandt:
- Feature vollständig fehlend/Scaffold → `!!! warning "Noch nicht implementiert (REQ-XXX)"` **am Seitenanfang** + alle Handlungsanweisungen im **Futur** („wird … bieten").
- Feature teilweise implementiert → `!!! note "Teilweise verfügbar"` + betroffene Abschnitte einzeln markiert.
- Feature nur per API/Env-Var (keine UI) → `!!! info "Nur über API / Betreiber-Konfiguration"`.

**Tabellen aus Code/Seed generieren (behebt M-3).** Care-Presets, `FAMILY_CARE_MAP`, Starter-Kits, Substrat-Typen, Workflow-Templates, Enum-Listen werden nicht mehr handgepflegt (siehe WP-P1).

**Verifikation pro WP (Definition of Done):**
1. `task docs` bzw. `mkdocs build --strict` grün (Link-/Anker-Integrität; isoliertes venv nötig).
2. DE/EN-Parität: identische Gliederung, beide Sprachen geändert.
3. Inhaltliche Gegenprobe: jede belegte Aussage per `grep`/Code-Stelle verifiziert (kein „Doku eilt voraus" mehr).
4. Bei Frontend-Bezug: Nav-Label/Button-Text = i18n-Key (nicht Modellname).
5. 3-Agent-Kette bzw. `mkdocs-documentation`-Agent-Review vor PR.

**Ausführende Rolle:** `mkdocs-documentation`-Agent (Doku-Arbeit). Code-Verifikation via `grep`/`Read`. Reine Code-Fixes (§0c) laufen **nicht** über diesen Plan.

---

## 0b. Entscheidungspunkte

> **Stand 2026-07-04:** Vom Nutzer bestätigt („passt"). Diese Entscheidungen sind für den Plan verbindlich.

| ID | Entscheidung | **Entscheidung** | Verworfene Alternative | Blockiert |
|----|--------------|-------------------------|------------------------|-----------|
| E-1 | Companion-Edges: fehlender Admin-Guard | **Guard nachrüsten** als separates Code-Issue (Edges wirken global → Security); Doku beschreibt Admin-Beschränkung | Doku auf „jeder Nutzer, global" korrigieren | WP-C8 FAQ-Wortlaut |
| E-2 | REQ-025 Privacy-UI | **Doku „API verfügbar, UI folgt"** (Doku-only jetzt); UI-Routing bleibt separates Code-Issue (§0c) | UI sofort routen → Banner ganz weg | WP-A4 Banner-Wortlaut |
| E-3 | Fakten-Tabellen | **Jetzt manuell fixen** (mit Quell-Kommentar), Generierung als Prozess-WP-P1 danach — blockiert Welle 2 nicht | Sofort Build-Step generieren | WP-P1 Umfang |
| E-4 | Entwurfs-Specs ohne Impl (z. B. REQ-039) | **Konsistent Seite-mit-Banner** (wie actuator-control); Bestand bleibt, wenig Rework | Nur Implementiertes; Banner-Seiten entfernen | WP-C1/E4, Konsistenz M-1 |
| E-5 | `troubleshooting.md` Zielort | **`docs/*/development/`** (Betriebs-/Entwickler-Fehlerbehebung) mit Slug-Redirect | `deployment/` | WP-S1 |
| E-6 | Umfang Zielgruppen-Journeys | **J1–J4** (3 Primär + CanG-Compliance ZG-005); J5/J6 (P3) später | Nur J1–J3 · oder alle J1–J6 | Welle 4 Scope |

---

## 0c. Abgrenzung — NICHT Teil dieses Doku-Plans

Diese Findings sind **keine** Doku-Arbeit und werden als separate Issues geführt (im Plan nur referenziert, damit die Matrix vollständig ist):

- **Code-Bugs:** Companion-Admin-Guard (E-1b, Security), `claude-shared/scripts/check_links.py` `_pre_slug`-Underscore-Bug (Upstream-PR).
- **Feature-Routing:** REQ-025 Privacy-UI nicht geroutet (E-2a).
- **Feature-Gaps ohne Doku-Maßnahme jetzt** (Doku korrekt abwesend, nur bei Implementierung nachziehen): REQ-037 ET-Bewässerung, REQ-026 Aquaponik, REQ-016 InvenTree, REQ-033 MCP-Server, REQ-038 CV-Diagnose, REQ-040/041 Enrichment-Quellen, REQ-035 Glossar-Feature, REQ-036 Diagnose-Assistent, sowie die reinen Produkt-Gaps der Zielgruppen UZG-002/005/006 und Yield/Kosten-Analytik (ZG-006). → Sammel-Issue „Docs-DoD bei REQ-Implementierung" (WP-P3).

---

## Welle 1 — Sofort (P0 + Faktenlügen + Freshness)

> Ziel: irreführende & faktisch falsche Inhalte stoppen; mechanische Defekte beseitigen. Zwei kleine, risikoarme PRs.

### PR-A — „docs: fix P0 drift & false banners"

| WP | Datei(en) | Änderung | Finding | Aufwand |
|----|-----------|----------|---------|---------|
| A1 | `user-guide/ai-assistant.md`, `user-guide/ai-providers.md` (+EN) | Preview-Banner (M-1 `!!! info` nur-API); Chat-/Tipp-/Provider-UI als „in Entwicklung"; Provider-Setup auf Env-Vars `LLM_PROVIDER`/`LLM_MODEL` umschreiben; Ollama-/Hardware-Teil als Betreiber-Doku behalten | P0-1 | M |
| A2 | `user-guide/planting-runs.md` (+EN) | Run-Typ „Mischkultur" + Rollen-Schritt (Primär/Begleit/Fang) + Kompatibilitätscheck streichen; Verweis auf realen Companion-Weg (WP-C8) | P0-2 | S |
| A3 | `user-guide/planting-runs.md` (+EN) | „Folgepflanzung anlegen" (Sukzession) mit Warnbanner kennzeichnen (Issue #299) | P0-3 | S |
| A4 | `user-guide/privacy.md` (+EN) | Banner korrigieren: DSGVO-**API** verfügbar (`/api/v1/privacy/`), UI folgt (Wortlaut je E-2) | 4c-Privacy | S |

### PR-B — „docs: freshness (dead refs, anchors, mkdocs config)"

| WP | Datei(en) | Änderung | Finding | Aufwand |
|----|-----------|----------|---------|---------|
| B1 | `docs/en/development/agent-catalog.md` | **Löschen** (erledigt 11 tote Cross-Refs + einzige Paritätslücke + Orphan) | Freshness Critical | S |
| B2 | `docs/en/user-guide/admin.md:395` | Anker `#enabling-pest-recognition` → `#enabling-pest-detection` | Freshness Critical | S |
| B3 | `mkdocs.yml` | `edit_uri` `main`→`develop`; `nav_translations` um „Module & Funktionen"; Leiche „Object Storage — Helm" entfernen | Freshness Info | S |
| B4 | `docs/en/adr/001-arangodb-multi-model.md`, `docs/en/guides/troubleshooting.md` | EN auf DE-Stand nachziehen (fehlende Abschnitte / 32 Zeilen aus #156) | Freshness Warning | M |
| B5 | `docs/wichtige-prompts.md`, `docs/security/nuclei-triage.md` | Entscheiden: in Nav/Sprachbaum aufnehmen oder bewusst excluden; `TBD`→`rotation.md`-Verweis auflösen | Freshness Warning/Info | S |
| B6 | *(Abgrenzung §0c)* | `check_links.py` `_pre_slug`-Bug als Upstream-Issue in `claude-shared` anlegen | Freshness Upstream | S |

---

## Welle 2 — Seiten-Korrektur & -Ausbau (P1 4a/4c + P2/P3 je Seite)

> Ziel: pro Seite ein WP, das **alle** Findings dieser Seite erledigt (Drift raus, reale Features rein, Fakten aus Code). Gruppiert in thematische PRs.

### PR-C — Kultur-Grundlagen

| WP | Seite (+EN) | Zu erledigen (Findings) | Aufwand |
|----|-------------|-------------------------|---------|
| C1 | `growth-phases.md` | Phasenmodell aktualisieren (10+ Typen, „Ernte" ist keine Phase mehr, #306); **Auto-Transitions** dokumentieren (zeit-/photoperiodisch/vernalisation); Verwaltung `/phasen/definitionen`+`/phasen/ablaeufe`; Biennial/Vernalisation; Falschaussage „erkennt nicht automatisch" streichen; Run-Membership-Guard (409) | L |
| C2 | `locations-substrates.md` | Substrat-Typen aus `SubstrateType`-Enum regenerieren; **Substrat-Chargen** (Wiederverwendung, Slot-Zuweisung); **Mix-Dialog** (Komponenten+%); Klimazone Köppen→USDA „8a"; custom Location-Typen; GPS-Nutzen (Sonnenzeiten→Auto-Blüte); EC-Ersterwähnung + Link | L |
| C3 | `planting-runs.md` | (nach A2/A3) Create-Dialog-Felder real (`id_prefix`, `spacing_cm`, Substrat-Charge, `sourcePlantKey`); **Pflanzen adoptieren**; **Aktivitätsplan-Tab**; **Pflanzentagebuch (Diary)**; Ernte-Batch-Fiktion streichen; Batch-vs-Einzel-Phasenwechsel | L |
| C8 | `guides/companion-planting.md` | **Neu schreiben** entlang realer UI: Stammdaten-Kompatibilitätspflege, `SpeciesCompanionTab`, `CropRotationPage`, Slot-Nachbarschafts-Check; Fruchtfolge eigener Abschnitt; FAQ-Guard-Wortlaut (E-1); Screenshot-Platzhalter; Familien-Fallback×0.8 (korrekt) behalten | L |
| C9 | `plant-management.md` | Artenzahlen entkonkretisieren („alle mitgelieferten Arten"); **Aktivitäten als Stammdaten** je Art; Feldnamen-Überschriften laientauglich; EN-Struktur-Parität (KI-Abschnitt) | M |

### PR-D — Bewässerung & Düngung

| WP | Seite (+EN) | Zu erledigen | Aufwand |
|----|-------------|--------------|---------|
| D1 | `fertilization.md` | Spülprotokoll auf Rechner-Ablauf umschreiben (kein Button/Task-Automatik); EC-Zieltabelle auf REQ-004-A/`EC_MAX_TABLE`; **Multi-Channel Delivery**; **Wasser-Mischer/EC-Budget-Rechner** Bedienung; **Dünger-Bestand/Inkompatibilität/clone/validate**; Erfahrungsstufen-Gating-Hinweis; mixing_priority-Konfigurierbarkeit; Gantt-Visualisierungen | L |
| D2 | `watering-log.md` | **Komplett neu schreiben** gegen reales Modell (ersetzt Events, aggregiert nicht); reale Feldliste; fiktive Spalten/Minigraph/Spülungserkennung/HA-Auto/Retention raus; Modellnamen/REQ-Nummern aus Nutzertext | L |
| D3 | `tanks.md` | Equipment-Attribute; gelöster Sauerstoff; **EC-Verdünnungsrechner**; **Tank-Verknüpfung** (`feeds-from`); Live-Sensorwerte; HA-Entity-Auswahl; Fill-Stats; Hydro-Begriffe (DWC/NFT) erklären | M |
| D4 | `guides/nutrient-mixing.md` | Spüldauer Erde 14–30 (Konsistenz mit D1); EC@25-Temperaturkorrektur; Terminologie/Nav-Pfade real; Fertigation/Drain-to-Waste erklären | M |

### PR-E — Sensorik / Aktorik / Smart-Home

| WP | Seite (+EN) | Zu erledigen | Aufwand |
|----|-------------|--------------|---------|
| E1 | `sensors.md` | Fallback-Automatik/Ausfallerkennung/Interpolation/manuelle-Pflanzen-UI mit Banner (nicht impl.); manuelle Messung real = Tank; MQTT als „Future"; Version v2.3→v2.7; Formularfelder real (kein „Datenquelle"/„Verbindung prüfen"); **HA-Autocomplete** dokumentieren; Metriken (soil_moisture/DLI/Aquaponik) angleichen; Retention-Querverweis | L |
| E2 | `guides/home-assistant-integration.md` | JSON `enabled_keys`→`entity_keys`; Bulk-Endpoint ergänzen; Frost-Entity in Standort-Tabelle (mit Status) | S |
| E3 | `locations-substrates.md` | *(Klimazone → in C2 gebündelt)* | — |
| E4 | `guides/climate-zones.md` **oder** Verzicht | Je E-4: Seite-mit-Banner für REQ-039 **oder** dokumentierter Verzicht | S/M |

### PR-F — Ernte / Kalender / Aufgaben / Pflege

| WP | Seite (+EN) | Zu erledigen | Aufwand |
|----|-------------|--------------|---------|
| F1 | `harvest.md` | Trocknung/Spülung/Dunkelphase mit „Teilweise implementiert"-Banner; Reifeprognose→**Beobachtungs-Workflow**; Ertragskennzahlen (kein Auto), reale Metriken; Qualitätsskala 0–100/Grade bis D; `CONTINUOUS`-Erntetyp; Auto-Status-Behauptung raus | L |
| F2 | `calendar.md` | 5 reale Tabs (inkl. **Phasen-Timeline**, **Saisonübersicht**); Quick-Actions streichen; 11 Ereignis-Kategorien; reale Filter; **Feed-Token-Regenerierung + Ablauf (410)**; Aussaatkalender-Ausbau (Balkentypen/Kategorien/Vorrangregeln/Jahr+Site) | L |
| F3 | `tasks.md` | Workflow-Templates 16→**4**; **erweiterte Funktionen** (Recurrence/Checkliste/Timer/Skill/Foto/dormant); Eskalation real; „Erinnerung"-Feld raus; Pflegestil-Tabelle entfernen→Link auf care-reminders; **Aktivitätspläne**; Kalender-FAQ „wiederkehrend" korrigieren | L |
| F4 | `care-reminders.md` | Care-Preset-Tabelle + `FAMILY_CARE_MAP` aus Code (WP-P1); **Überwinterung** mit Banner; Reminder-Typen 6; **Guards** (Gießplan/Nährstoffplan); Dashboard-Stufen 3; Snooze/Skip; Outdoor-Presets vollständig; Preset-Codes deutsche Klartextnamen | L |
| F5 | `guides/post-harvest.md` | Schritte 4–5 als „geplant"; QualityAssessment-Skala angleichen; Fachinhalt behalten | S |

### PR-G — KI / RAG / IPM-Text / Plattform-Rest

| WP | Seite (+EN) | Zu erledigen | Aufwand |
|----|-------------|--------------|---------|
| G1 | `guides/rag-knowledge-base.md` | Guide-Upload-UI streichen; Reindex→`/ingest`; Embedding multilingual-e5 1024-dim (ADR-006) | M |
| G2 | `architecture/ai-architecture.md` | Embedding-Angaben konsistent auf ADR-006 | S |
| G3 | `user-guide/plant-identification.md` | FAQ Krankheits-Foto → auf Schädlingserkennung verweisen; `pest-detection.md` in „Siehe auch" | S |
| G4 | `user-guide/pest-management.md` | „Nützling freigesetzt"/„Befallshistorie" entfernen/als geplant; Inspektions-/Behandlungs-Flow auf reale Wege (Foto-Erkennung/API) | M |
| G5 | `user-guide/tenants.md` | Gemeinschaftsfunktionen (Pinnwand/Rotation/Einkaufsliste) + Matrix-Zeilen mit Banner/entfernen | M |
| G6 | `user-guide/onboarding.md` | Starter-Kit-Tabelle 11 aus `starter_kits.yaml` (WP-P1) | S |
| G7 | `user-guide/privacy.md` | Consent-Tabelle: `pest_detection_cloud` (Kindwise) ergänzen + Link | S |
| G8 | `user-guide/ai-providers.md` | Default-Modell `gemma3:12b` + RAM-Hinweis (nach A1) | S |

---

## Welle 3 — Neue Seiten (Existenz-Lücken implementierter Features)

### PR-H — Neue Enduser-Seiten

| WP | Neue Seite (DE+EN) | Inhalt | REQ | Aufwand |
|----|--------------------|--------|-----|---------|
| H1 | `user-guide/notifications.md` | 4 Kanäle (HA/E-Mail/PWA/**Apprise**), Kanal-Präferenzen je Typ, Ruhezeiten, Test-Versand, Notification-Center; Env-Vars (Apprise/SMTP) in `reference/environment-variables.md` | REQ-030 | L |
| H2 | `user-guide/import.md` | CSV-Templates laden, Upload, Dry-Run/Validierungsbericht, Bestätigen, Fehlerbehandlung | REQ-012 | M |
| H3 | `user-guide/account.md` | Konto anlegen, Login inkl. OAuth/OIDC, Passwort-Reset, Profil/Sprache/Erfahrungsstufe, Sitzungen; Links aus `tenants.md`/`privacy.md` umbiegen (weg von curl-API) | REQ-023 | M |
| H4 | `guides/data-enrichment.md` | Externe Anreicherung (GBIF/Perenual): Quellen, Sync anstoßen, read-only Origin-Chip-Felder; Verweis aus `plant-identification.md` präzisieren | REQ-011 | M |

*(Multi-Channel-Delivery, Companion-UI, Aktivitätsplan, Phasen-Verwaltung, Substrat-Chargen, Diary sind Abschnitte in bestehenden Seiten → bereits in Welle 2 WP-D1/C8/F3/C1/C2/C3 verortet.)*

Nav + `user-guide/index.md` in H1–H3 gleich mitpflegen (überlappt WP-S4).

---

## Welle 4 — Zielgruppen-Konformität & Struktur

### PR-I — Struktur & Auffindbarkeit

| WP | Datei | Änderung | Finding | Aufwand |
|----|-------|----------|---------|---------|
| S1 | `guides/troubleshooting.md` → verschieben (E-5) | Betreiber-Inhalt nach `development/` bzw. `deployment/`; Redirect | ZG-P1 | S |
| S2 | `user-guide/plant-health-troubleshooting.md` (neu) | Symptom-Guide „Meiner Pflanze geht es schlecht" (gelbe Blätter/braune Spitzen/weiße Punkte → Ursache → Handlung → Link pest-detection/care-reminders) | UZG-001/ZG-003 | M |
| S3 | `reference/glossary.md` (neu) | Glossar: VPD, EC, GDD, Karenz, Hysterese, PPFD, DWC/NFT, Dormanz, CanG; aus Getting-Started verlinken (Brücke bis REQ-035) | M-6 | M |
| S4 | `user-guide/index.md` (+EN) | Alle 33 Seiten + REQ-Spalte (Druckansichten, Foto-Galerie, Gießprotokoll, Object Storage, Detail-Seiten, Foto-ID …) | 4b/P3 | S |
| S5 | `guides/index.md` (+EN) | 11 statt 6 Guides, nach Use-Case gruppiert | ZG-P2 | S |
| S6 | `docs/de/index.md` (+EN) | Docker/Skaffold-CTAs → Deployment/Development; erster CTA → Getting-Started; Projektgeschichte in About/Development | ZG-P3 | S |
| S7 | `getting-started/erste-pflanze.md` (+EN) | Foto-Einstieg-Callout „Weißt du nicht, was du hast? → per Foto"; Getting-Started-Tabs auf Journeys verdrahten | UZG-001-P1 | M |

### PR-J — Kuratierte Journeys (Use-Case-Guides)

| WP | Neue Seite (DE+EN) | Verkettet aus | Zielgruppe | Aufwand |
|----|--------------------|---------------|-----------|---------|
| J1 | `guides/journey-cannabis-cycle.md` | planting-runs→growth-phases→fertilization/nutrient-mixing→sensors/vpd→harvest→post-harvest→propagation | ZG-001 | L |
| J2 | `guides/journey-garden-year.md` | calendar/Aussaatkalender→companion/Fruchtfolge→tasks→Überwinterung; **Eisheilige/Phänologie/Forsythienblüte** einführen | ZG-002 | L |
| J3 | `guides/journey-hydroponics-setup.md` | Standort→tanks→nutrient-mixing→sensors→actuator; NFT/DWC-Setup | ZG-006 | L |
| J4 | `guides/compliance-anbauvereinigung.md` (E-6) | Chargen/Karenz/Retention/Rollen/OIDC; Reporting-Grenzen ehrlich benennen | ZG-005 | L |
| J5 | *(optional, E-6)* `guides/kamerplanter-im-unterricht.md` | Tenants/Runs/QR-Karten/Foto-Galerie; CSV-Export-Roadmap | UZG-003 | M |
| J6 | *(optional, E-6)* Abschnitt „Sammlungen verwalten" in `plant-management.md` | Fotos/Notizen/Umtopf-Historie | UZG-004 | S |

---

## Welle 5 — Prozess (Rückfall verhindern)

| WP | Maßnahme | Finding |
|----|----------|---------|
| P1 | Fakten-Tabellen aus Quelle generieren (E-3): Include/Build-Step für Care-Presets, `FAMILY_CARE_MAP`, Starter-Kits, Substrat-Typen, Workflow-Templates, Enum-Listen | M-3 |
| P2 | Admonition-Konvention (§0) in Backend-/Doku-Style-Guide aufnehmen | M-1/M-2 |
| P3 | „Doku-Sync" als Definition-of-Done in Feature-PR-Template; Sammel-Issue für §0c-Feature-Gaps (Docs bei Implementierung) | M-1, §0c |
| P4 | Upstream: `check_links.py`-`_pre_slug`-Fix | Freshness |

---

## 6. Reihenfolge, Abhängigkeiten, Aufwand

```
Welle 1 (PR-A, PR-B)  ── unabhängig, sofort ────────────────┐
                                                            │
E-1..E-6 klären ───────────────────────────────────────────┤
                                                            ▼
Welle 2 (PR-C..PR-G)  ── Seiten-Korrektur ──► Welle 3 (PR-H, neue Seiten)
   (WP-P1 vor F4/G6/C2)                            │
                                                   ▼
                            Welle 4 (PR-I Struktur ──► PR-J Journeys)
                                                   │
                                                   ▼
                                            Welle 5 (Prozess)
```

**Kritische Abhängigkeiten:**
- WP-P1 (Tabellen-Generierung, E-3) **vor** F4/G6/C2, sonst doppelte Handarbeit.
- PR-A/A2+A3 **vor** WP-C3/C8 (Companion-Neuschrieb baut auf entschlackter planting-runs auf).
- WP-S4/S5 (Indizes) **nach** Welle 3 (neue Seiten müssen gelistet werden) — oder inkrementell in H1–H3 mitpflegen.
- J1–J4 (Journeys) **nach** Welle 2 (verketten korrigierte Seiten).

**Grobaufwand** (S≈0,5 d / M≈1 d / L≈2 d, Doku-Agent): Welle 1 ≈ 3 d · Welle 2 ≈ 22 d · Welle 3 ≈ 5 d · Welle 4 ≈ 12 d · Welle 5 (P1 code-nah) ≈ 3–5 d. **Gesamt ≈ 45–48 Personentage Doku** (ohne §0c-Code-Arbeit). Parallelisierbar über mehrere `mkdocs-documentation`-Agent-Läufe (Seiten sind unabhängig).

---

## 7. Tracking-Matrix (Nachweis vollständiger Abarbeitung)

Jeder Audit-Finding → WP. Status-Spalte beim Abarbeiten pflegen (`☐/☑`).

| Audit-Finding | Severity | WP | PR | Status |
|---------------|----------|----|----|--------|
| KI-Assistent/Provider-UI fiktiv | P0 | A1 | PR-A | ☐ |
| Mischkultur-Run-Typ+Rollen | P0 | A2 | PR-A | ☐ |
| Sukzession „Folgepflanzung" | P0 | A3 | PR-A | ☐ |
| Privacy-Banner faktisch falsch | P1 | A4 | PR-A | ☐ |
| agent-catalog.md (11 tote Refs) | Crit | B1 | PR-B | ☐ |
| EN-Anker pest-recognition | Crit | B2 | PR-B | ☐ |
| edit_uri/nav_translations/Leiche | Info | B3 | PR-B | ☐ |
| EN-ADR-001 + troubleshooting hinter DE | Warn | B4 | PR-B | ☐ |
| Verwaiste Seiten + TBD/rotation.md | Warn | B5 | PR-B | ☐ |
| check_links _pre_slug (Upstream) | Info | B6/P4 | §0c | ☐ |
| growth-phases: Modell/Auto-Trans/Verwaltung/Biennial/Guard | P1 | C1 | PR-C | ☐ |
| locations-substrates: Typen/Chargen/Mix/Klimazone/Location-Typen/GPS | P1/P2 | C2 | PR-C | ☐ |
| planting-runs: Felder/adopt/Aktivitätsplan/Diary/Ernte-Batch/Batch-Guard | P1/P2 | C3 | PR-C | ☐ |
| companion-planting Neuschrieb (reale UI/Fruchtfolge/Guard/Screenshot) | P1/P2 | C8 | PR-C | ☐ |
| plant-management: Artenzahlen/Aktivitäten/Feldnamen/EN-Parität | P2/P3 | C9 | PR-C | ☐ |
| fertilization: Spülung/EC/Multi-Channel/Rechner/Bestand/Gating/mixing/Gantt | P1/P2/P3 | D1 | PR-D | ☐ |
| watering-log Neuschrieb | P1 | D2 | PR-D | ☐ |
| tanks: Equipment/DO/EC-Verdünnung/Verknüpfung/Live/HA | P2 | D3 | PR-D | ☐ |
| nutrient-mixing: Spüldauer/EC@25/Terminologie | P2/P3 | D4 | PR-D | ☐ |
| sensors: Fallback/Ausfall/MQTT/Version/Felder/Autocomplete/Metriken | P1/P3 | E1 | PR-E | ☐ |
| HA-Guide: entity_keys/Bulk/Frost-Entity | P2/P3 | E2 | PR-E | ☐ |
| REQ-039 Klimazonen-Seite (E-4) | P2 | E4 | PR-E | ☐ |
| harvest: Trocknung/Reife/Ertrag/Qualität/CONTINUOUS/Status | P1/P2 | F1 | PR-F | ☐ |
| calendar: Tabs/Quick-Actions/Kategorien/Feed-Token/Aussaat | P1/P2 | F2 | PR-F | ☐ |
| tasks: Templates/erweitert/Eskalation/Pflegestil/Aktivitätspläne | P1/P2 | F3 | PR-F | ☐ |
| care-reminders: Presets/Familie/Überwinterung/Guards/Dashboard/Outdoor | P1/P2/P3 | F4 | PR-F | ☐ |
| post-harvest: Schritte 4–5/Skala | P3 | F5 | PR-F | ☐ |
| rag-knowledge-base: Upload/Reindex/Embedding | P1 | G1 | PR-G | ☐ |
| ai-architecture Embedding | P2 | G2 | PR-G | ☐ |
| plant-identification FAQ Krankheit | P2 | G3 | PR-G | ☐ |
| pest-management: Nützlinge/Historie/Inspektion | P1 | G4 | PR-G | ☐ |
| tenants Gemeinschaftsfunktionen | P1 | G5 | PR-G | ☐ |
| onboarding Starter-Kits 11 | P2 | G6 | PR-G | ☐ |
| privacy Consent-Tabelle Kindwise | P3 | G7 | PR-G | ☐ |
| ai-providers Default-Modell/RAM | P3 | G8 | PR-G | ☐ |
| REQ-030 Benachrichtigungen (Seite) | P1 | H1 | PR-H | ☐ |
| REQ-012 Import (Seite) | P1 | H2 | PR-H | ☐ |
| REQ-023 Konto/Auth (Seite) | P1/P2 | H3 | PR-H | ☐ |
| REQ-011 Enrichment (Seite) | P1 | H4 | PR-H | ☐ |
| troubleshooting-Split (E-5) | P1 | S1 | PR-I | ☐ |
| Symptom-Diagnose-Guide | P1 | S2 | PR-I | ☐ |
| Glossar | P2 | S3 | PR-I | ☐ |
| user-guide/index vollständig | P3 | S4 | PR-I | ☐ |
| guides/index vollständig | P2 | S5 | PR-I | ☐ |
| Startseite Endnutzer-Tonalität | P3 | S6 | PR-I | ☐ |
| Getting-Started Foto-Einstieg/Journeys | P1 | S7 | PR-I | ☐ |
| Journey Cannabis-Zyklus | P1 | J1 | PR-J | ☐ |
| Journey Gartenjahr (+Phänologie) | P1/P2 | J2 | PR-J | ☐ |
| Journey Hydroponik | P1/P2 | J3 | PR-J | ☐ |
| ZG-005 Compliance-Guide | P1 | J4 | PR-J | ☐ |
| UZG-003 Unterricht (opt.) | P3 | J5 | PR-J | ☐ |
| UZG-004 Sammler (opt.) | P3 | J6 | PR-J | ☐ |
| Feature-Gaps §0c (ET/Aquaponik/InvenTree/MCP/CV-Diag/Marktg./Gewächsh./Microgreens) | P3 | P3 | §0c | ☐ |
| Companion-Admin-Guard (Code, E-1) | P2 | §0c | §0c | ☐ |
| Privacy-UI-Routing (Code, E-2) | P2 | §0c | §0c | ☐ |
| Tabellen-Generierung | Prozess | P1 | PR-P | ☐ |
| Admonition-Konvention Style-Guide | Prozess | P2 | PR-P | ☐ |
| Doku-Sync DoD | Prozess | P3 | PR-P | ☐ |

**Vollständigkeitsnachweis:** Alle im Audit ausgewiesenen Findings (3 P0, ~30 P1, ~30 P2, ~20 P3) sind einem WP zugeordnet; §0c-Zeilen sind bewusst als Nicht-Doku-Arbeit markiert, aber in der Matrix geführt, damit nichts unter den Tisch fällt.
