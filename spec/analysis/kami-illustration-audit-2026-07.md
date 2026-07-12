# KAMI-Illustrations-Audit — Kamerplanter Web-App

**Datum:** 2026-07-13
**Issue:** #591 (Deliverable 1 — Audit-Dokument)
**Scope:** Vollständiger Sweep der laufenden Frontend-App (`src/frontend/src/`) auf fehlende KAMI-Figuren, -Illustrationen und -Nav-Icons, die das Design-System vorsieht.
**Methodik:** Statische Code-Analyse (Routen/Pages, Layouts, Shared-Komponenten, Asset-Barrel, `public/manifest.json`) abgeglichen gegen `spec/design/KAMI-CHARACTER-REFERENCE.md` (§4.2 Emotions-Katalog, §5 Größen-Leiter, §9 Prompt-Baukasten, §10 Emotion→Einsatzort) und alle Prompt-Docs unter `spec/design/`.
**Status:** Read-Only-Audit — **keine** Asset-Generierung, **keine** Code-/Asset-Änderung. Deliverable 2 (Prompt-Generierung) ist ausdrücklich Follow-up.
**Format-Vorlage:** `spec/analysis/frontend-ui-audit-2026-04.md`.

---

## 1. Overview

KAMI (`spec/design/KAMI-CHARACTER-REFERENCE.md` v1.0) ist das App-Maskottchen — ein anthropomorpher Keimling im Terrakotta-Topf mit verbindlichem 13-Emotionen-Katalog, Größen-Leiter (512→32px) und 7-Block-Prompt-Kit. Illustrationen werden über das Barrel `src/frontend/src/assets/brand/illustrations/index.ts` sowie die Consumer `EmptyState` (→ `DataTable`), `PhaseKamiTimeline`/`PhaseTimelineStepper` und `ErrorPage`/`RouterErrorPage` konsumiert.

### 1.1 Ist-Bestand (vorhandene Assets)

| Kategorie | Ort | Anzahl | Consumer | Status |
|---|---|---|---|---|
| Feature-Illustrationen | `assets/brand/illustrations/features/feature-kami-*.{svg,png}` | 12 (je SVG+PNG) | Listen-Empty-States via Barrel-Export | vollständig konsumiert (1 Ausnahme: `kamiDashboard` = toter Export) |
| Phasen-Illustrationen | `assets/brand/illustrations/phases/timeline-kami-phase-*.{svg,png}` | 14 (je SVG+PNG) | `PhaseKamiTimeline`, `PhaseTimelineStepper`, `PhaseDefinitionDetailPage` (via `import.meta.glob`) | vollständig |
| HTTP-Error-Illustrationen | `assets/illustrations/errors/error-{400,401,403,404,408,429,500,502,503}.svg` | 9 | `ErrorPage`, `RouterErrorPage`, `NotFoundPage` | vollständig |

**Gesamt:** 35 distinkte KAMI-Motive als Asset vorhanden (Features + Phasen als SVG **und** PNG-Fallback, Errors nur SVG).

### 1.2 Auditierte Flächen (Klassifikation has-KAMI / missing / N/A)

| Fläche | Datei/Bereich | Klassifikation | Notiz |
|---|---|---|---|
| Listen-Empty-States (mit Illustration) | `SiteListPage`, `PlantInstanceListPage`, `TaskQueuePage`, `CalendarPage`, `PflegeDashboardPage`, `CompanionPlantingPage`, `CropRotationPage`, Species-Detail-Tabs u.a. (13 Übergaben von `illustration=`) | **has-KAMI** | nutzen Feature-Illustration passend zur Domäne |
| Phasen-Timeline / -Badges | `PhaseKamiTimeline.tsx`, `PhaseTimelineStepper.tsx`, `PhaseDefinitionDetailPage.tsx` | **has-KAMI** | 14 Phasen + Alias-Mapping (fruiting→ripening, rest*→dormancy usw.) |
| Fehlerseiten | `ErrorPage.tsx`, `RouterErrorPage.tsx`, `NotFoundPage.tsx` | **has-KAMI** | 9 Status-Codes gemappt, Fallback → 500 |
| Sidebar-Navigation | `layouts/Sidebar.tsx` | **missing** | ~30 generische MUI-Icons, **kein** KAMI-Nav-Icon (Prompt-Doc `nav-icons-kami-sidebar.md` existiert) |
| PWA App-Icons / Logo | `public/manifest.json` → `/icons/icon-192.png`, `/icons/icon-512.png` | **missing** | `public/icons/` existiert **nicht** → gebrochene Manifest-Referenz; kein Prompt-Doc |
| Onboarding / Login / Register | `pages/onboarding/OnboardingWizard.tsx`, `pages/auth/LoginPage.tsx`, `RegisterPage.tsx` | **missing** | 0 KAMI-Referenzen; Emotion „Einladend/Willkommen" (§10) unrealisiert |
| Dashboard (Hauptseite) | `pages/DashboardPage.tsx` + `components/dashboard/widgets/*` | **missing** | 0 KAMI, kein Willkommens-/Leerzustand-Motiv |
| Empty-States ohne Illustration | `EmptyState` in ~25 Dateien ohne `illustration=` (→ Fallback `InboxIcon`) | **missing** | generischer Such-/Leer-/Kein-Ergebnis-KAMI (Emotion „Neugierig/Suchend") fehlt |
| Neuere Fachmodule ohne Feature-Illustration | `aquaponik`, `environment`, `ki-assistent`, `ki-diagnose`, `ki-recognition`, `post-harvest`, `propagation`, `ueberwinterung`, `inventree`, `glossar` | **missing** | 0 KAMI-Referenzen je Modul; keine Feature-Illustration, kein Prompt-Doc |
| Post-Harvest-Phasen `drying`/`curing` | `PhaseKamiTimeline.tsx` (PHASE_COLORS gesetzt, kein KAMI-Image) | **missing** | 2 Phasen-Keys ohne dedizierte Illustration |
| Erfolg-/Celebration-Momente | Ernte abgeschlossen, Aufgabe erledigt, Phasenwechsel, Tank aufgefüllt | **missing** | kein Triumphierend-/Feiernd-KAMI im Feedback-Pfad |
| Banner / Hero (In-App, OG) | Prompt-Doc `banner-kami-hauptapplikation.md` | **missing** | kein Asset |
| Social-Preview / HA-Banner / HA-Icon | Prompt-Docs vorhanden | **missing** | keine Assets (HA-Icon liegt außerhalb `src/frontend/`) |
| Tank-Füllstände / Tankmanagement | Prompt-Docs `illustration-kami-tank-fuellstaende.md`, `illustration-kami-tankmanagement.md`; `TankListPage`/`TankDetailPage` nutzen MUI-Icons (`OpacityIcon` u.a.) | **missing** | Ziel-Dir `assets/illustrations/tank/` fehlt |
| Detail-Seiten-Formulare | ~17 Detail-Pages | **N/A** | Formular-Layouts, kein Illustrations-Slot im Design-System |
| Dialoge (Create/Edit) | ~30 Dialoge | **N/A** | KAMI im Design-System nicht für Dialoge vorgesehen |

**Auditierte Flächen gesamt: 16 Bereiche** — davon **3 has-KAMI**, **11 mit Gaps (missing)**, **2 N/A**.

---

## 2. Soll/Ist-Reconciliation-Matrix (Prompt-Docs ↔ Assets)

Abgleich aller Prompt-Docs unter `spec/design/` (ohne die Charakter-Referenz) gegen `index.ts`/Asset-Ordner.

### 2.1 both-present (Prompt-Doc **und** Asset vorhanden) — 7 Docs / 35 Assets

| Prompt-Doc | Assets | Anzahl |
|---|---|---|
| `feature-kami-kernfunktionen.md` | `features/feature-kami-*.svg` | 12 |
| `illustration-kami-http-errors.md` | `errors/error-*.svg` | 9 |
| `timeline-kami-phasen.md` (Basis-5) | `phases/…germination/seedling/vegetative/flowering/harvest` | 5 |
| `timeline-kami-phasen-erweitert.md` (6) | `phases/…ripening/juvenile/climbing/mature/dormancy/senescence` | 6 |
| `timeline-kami-phase-flushing.md` | `phases/…flushing` | 1 |
| `timeline-kami-phase-leaf-phase.md` | `phases/…leaf-phase` | 1 |
| `timeline-kami-phase-short-day-induction.md` | `phases/…short-day-induction` | 1 |

### 2.2 prompt-exists-but-asset-missing — 7 Docs

| Prompt-Doc | Erwartetes Asset / Ziel | Gap-ID |
|---|---|---|
| `nav-icons-kami-sidebar.md` (Serie 27) | 27 quadratische Nav-Icons — kein Asset, Sidebar nutzt MUI | G-04 |
| `illustration-kami-tank-fuellstaende.md` (6) | `assets/illustrations/tank/` fehlt komplett | G-05 |
| `illustration-kami-tankmanagement.md` | Tank-Empty/Hero-Illustration — kein Asset | G-08 |
| `banner-kami-hauptapplikation.md` | In-App-Header/OG-Banner — kein Asset | G-07 |
| `banner-kami-ha-integration.md` | HA-README/HACS-Banner — kein Asset | G-14 |
| `social-preview-github-kamerplanter.md` | 1280×640 GitHub-Social-Preview — kein Asset | G-13 |
| `ha-integration-icon-kami.md` | HA-Integrations-Icon (liegt außerhalb `src/frontend/`) | G-15 |

### 2.3 asset-exists-but-no-prompt — 0

Kein Asset ohne zugehöriges Prompt-Doc. **Sonderfall (Orphan-in-Code):** `kamiDashboard` (`feature-kami-dashboard.svg`) ist im Barrel exportiert und durch `feature-kami-kernfunktionen.md` gedeckt, wird aber von **keiner** Komponente importiert → siehe G-16.

### 2.4 both-missing (UI-Bedarf, weder Prompt-Doc noch Asset)

| Bereich | Gap-ID |
|---|---|
| PWA App-Icons 192/512 (maskable) + Logo | G-01, G-02 |
| Onboarding/Login/Register Willkommens-Hero | G-03 |
| Feature-Illustrationen für 10 neuere Fachmodule | G-06 |
| Dashboard Willkommens-/Leerzustand-Hero | G-09 |
| Erfolg-/Celebration-KAMI (Ernte/Aufgabe/Phasenwechsel) | G-10 |
| Post-Harvest-Phasen `drying`/`curing` | G-11 |
| Generischer Empty-/Such-/Kein-Ergebnis-KAMI (InboxIcon-Fallback) | G-12 |
| Loading-State-KAMI | G-17 |

**Matrix-Kennzahlen:** prompt-only = **7**, asset-only = **0**, both-present = **7 Docs (35 Assets)**, both-missing = **8 Gap-Cluster**.

---

## 3. Priorisierte Gap-Liste

Jeder Eintrag trägt alle Pflichtfelder (Motiv, UI-Position, Größe, **Pose**, **Emotion** aus §4.2, **Zweck**, Format, Prompt-Doc?, Asset?, Priorität), sodass ein Prompt in Deliverable 2 1:1 ableitbar ist. Emotion-Namen entsprechen dem Katalog `KAMI-CHARACTER-REFERENCE.md §4.2`; das dortige englische „Prompt-Fragment" wird in Deliverable 2 verbatim übernommen.

### CRITICAL

#### G-01 — PWA App-Icon 512×512 (maskable)

| Feld | Wert |
|---|---|
| Motiv/Beschreibung | KAMI-Kopf-/Ganzfigur zentriert als App-Icon, formatfüllend mit Safe-Zone für maskable-Beschnitt (rund/squircle), solider Markenhintergrund `#f5f5f5` bzw. theme `#2e7d32`-tauglich |
| UI-Position/Einsatzort | `public/manifest.json` → `icons[].src = /icons/icon-512.png` (`purpose: "any maskable"`); Homescreen-/Installations-Icon der PWA |
| Benötigte Größe(n) | app-icon **512×512** (maskable Safe-Zone ~40px), zusätzlich als Ableitungsquelle |
| **Pose** | Frontal, aufrecht zentriert, Blätter gerade nach oben, Arme entfallen (Icon-Reduktion), Topf im unteren Drittel |
| **Emotion** | **Happy (Standard)** — freundlich, wiedererkennbar als Default-Markenzeichen |
| **Zweck** | Marken-Wiedererkennung auf Homescreen/Task-Switcher; behebt aktuell **gebrochene** Manifest-Referenz (Ordner `public/icons/` fehlt → 404 beim Installieren) |
| Format | PNG (opak/maskable, kein Transparenz-Rand im Safe-Bereich) |
| Prompt-Doc vorhanden? | ❌ (kein Doc in `spec/design/`) |
| Asset vorhanden? | ❌ (`public/icons/` existiert nicht) |
| Priorität | **Critical** |

#### G-02 — PWA App-Icon 192×192 (maskable)

| Feld | Wert |
|---|---|
| Motiv/Beschreibung | Reduzierte Variante von G-01 für kleinere Renders (Größen-Leiter §5: 128px-Stufe als Vorlage) |
| UI-Position/Einsatzort | `public/manifest.json` → `/icons/icon-192.png` (`any maskable`) |
| Benötigte Größe(n) | app-icon **192×192** (Reduktion gemäß §5: einfarbige Blätter/Topf, Augen als Punkte, kein Mund-Detail) |
| **Pose** | Wie G-01, frontal aufrecht, keine Arme, vereinfachte Silhouette |
| **Emotion** | **Happy (Standard)** |
| **Zweck** | Scharfes Icon in kleineren PWA-Kontexten (Android-Adaptive, Notification-Badge); Teil derselben gebrochenen Manifest-Referenz |
| Format | PNG (opak/maskable) |
| Prompt-Doc vorhanden? | ❌ |
| Asset vorhanden? | ❌ |
| Priorität | **Critical** |

#### G-03 — Onboarding / Login / Willkommens-Hero

| Feld | Wert |
|---|---|
| Motiv/Beschreibung | Winkender KAMI, der neue Nutzer begrüßt — als Hero neben Login-Formular / im ersten Onboarding-Schritt |
| UI-Position/Einsatzort | `pages/auth/LoginPage.tsx`, `pages/auth/RegisterPage.tsx`, `pages/onboarding/OnboardingWizard.tsx` (Steps) — aktuell **0** KAMI-Referenzen |
| Benötigte Größe(n) | feature **320×240** (Querformat neben Formular) bzw. skalierbar 640×480 für großen Login-Split |
| **Pose** | Ein Arm angehoben und winkend, Hand offen; anderer Arm locker; Blätter aufrecht und lebendig; offene, einladende Körpersprache |
| **Emotion** | **Einladend/Willkommen (Welcoming/Inviting)** — §10 explizit für „Onboarding, Login, Willkommen, erste Nutzung", bislang unrealisiert |
| **Zweck** | Warmer erster Eindruck, senkt Einstiegshürde, etabliert das Maskottchen sofort bei Erstkontakt |
| Format | SVG-primär + PNG-Fallback |
| Prompt-Doc vorhanden? | ❌ |
| Asset vorhanden? | ❌ |
| Priorität | **Critical** |

### HIGH

#### G-04 — 27 Sidebar-Nav-Icons

| Feld | Wert |
|---|---|
| Motiv/Beschreibung | Serie eigenständiger 1:1-KAMI-Nav-Icons je Sidebar-Eintrag, jeweils mit thematischem Mini-Requisit (Gießkanne, Kalender, Lupe, Schere …) |
| UI-Position/Einsatzort | `layouts/Sidebar.tsx` — nutzt aktuell ~30 generische MUI-Icons (`DashboardIcon`, `ScienceIcon`, `WaterDropIcon`, `PestControlIcon`, `AgricultureIcon` …) |
| Benötigte Größe(n) | nav-icon **128×128 primär**, lesbar bei 32×32 (§5-Leiter: 32px = nur Grundform, keine Arme/Gesichtszüge) |
| **Pose** | Frontal zentriert, aufrecht; je Eintrag kleines Kontext-Requisit an Kamis Seite; Arme bei 32px weglassen |
| **Emotion** | **Happy (Standard)** pro Icon als Grundton; kontextnahe Varianten optional (z.B. Konzentriert für Dünge-Rechner) |
| **Zweck** | Konsistente, markentypische Navigation statt generischer Material-Icons; stärkt Wiedererkennung entlang der Hauptnavigation |
| Format | SVG-tauglich (PNG-Zwischenschritt), transparent |
| Prompt-Doc vorhanden? | ✅ `spec/design/nav-icons-kami-sidebar.md` (Serie 27) |
| Asset vorhanden? | ❌ |
| Priorität | **High** |

#### G-05 — Tank-Füllstand-Serie (6 Stufen)

| Feld | Wert |
|---|---|
| Motiv/Beschreibung | 6 Illustrationen KAMI neben Tank mit Füllstand 0/20/40/60/80/100 %, Emotion je Füllstand gestaffelt |
| UI-Position/Einsatzort | `pages/standorte/TankListPage.tsx`, `TankDetailPage.tsx` — nutzen MUI-Icons (`OpacityIcon`); Ziel-Dir `assets/illustrations/tank/` **fehlt** |
| Benötigte Größe(n) | illustration/feature **320×240** (Querformat), später SVG via vtracer |
| **Pose** | Kami steht neben/an einem Tank-Requisit (150–250 % Kami-Höhe, §6.2), Blick auf Füllstand; Gestik je Stufe |
| **Emotion** | gestaffelt nach §10: 0 %=**Panisch/Erschrocken**, 20 %=**Besorgt/Unsicher**, 40 %=**Skeptisch/Nachdenklich**, 60 %=**Stolz/Zufrieden**, 80 %=**Glücklich/Begeistert**, 100 %=**Triumphierend/Feiernd** |
| **Zweck** | Sofort ablesbarer Tank-Status mit emotionaler Dringlichkeit; ersetzt neutrale MUI-Icons durch handlungsleitende Illustration |
| Format | PNG-transparent → SVG |
| Prompt-Doc vorhanden? | ✅ `spec/design/illustration-kami-tank-fuellstaende.md` (6 Prompts) |
| Asset vorhanden? | ❌ |
| Priorität | **High** |

#### G-06 — Feature-Illustrationen für 10 neuere Fachmodule

| Feld | Wert |
|---|---|
| Motiv/Beschreibung | Je Modul eine Feature-Illustration analog der 12 bestehenden (KAMI + modul­typisches Requisit), für Header/Empty-State |
| UI-Position/Einsatzort | Module ohne jede KAMI-Referenz: `aquaponik`, `environment`, `ki-assistent`, `ki-diagnose`, `ki-recognition`, `post-harvest`, `propagation`, `ueberwinterung`, `inventree`, `glossar` — deren `EmptyState`-Aufrufe fallen auf `InboxIcon` zurück |
| Benötigte Größe(n) | feature **320×240** (primär), skalierbar 160×120 / 640×480 |
| **Pose** | Kami mit passendem Requisit je Modul (z.B. Aquaponik: Fisch/Wasserkreislauf; Überwinterung: Schneeflocke/Vlies; KI-Diagnose: Lupe; Propagation: Steckling; Glossar: Buch) |
| **Emotion** | modulabhängig: `ki-diagnose`/`ki-recognition`=**Neugierig/Suchend**, `environment`=**Konzentriert/Fokussiert**, `ueberwinterung`=**Friedlich/Genießerisch**, `aquaponik`/`propagation`=**Energisch/Kraftvoll**, `glossar`/`inventree`=**Happy** |
| **Zweck** | Visuelle Gleichbehandlung neuer Module mit den etablierten 12; konsistente Empty-States statt generischem Posteingangs-Icon |
| Format | SVG-primär + PNG-Fallback |
| Prompt-Doc vorhanden? | ❌ (Referenzmuster: `feature-kami-kernfunktionen.md`) |
| Asset vorhanden? | ❌ |
| Priorität | **High** |

#### G-07 — Banner Hauptapplikation (In-App-Header / OG-Image)

| Feld | Wert |
|---|---|
| Motiv/Beschreibung | Panorama-Hero mit winkendem KAMI, Marken-Header |
| UI-Position/Einsatzort | In-App-Header, Social/OG-Image (`<meta og:image>`), Landing — aktuell kein Asset referenziert |
| Benötigte Größe(n) | banner/hero **1920×480** (4:1), 1200×630 (OG), 800×200 (In-App-Header); Light- und Dark-Variante |
| **Pose** | Kami links, zwei Tropfen-Blätter aufrecht, ein Arm winkend; großzügiger freier Raum rechts für Text-Overlay |
| **Emotion** | **Einladend/Willkommen** (Header-Ton) bzw. **Happy** als reduzierte Variante |
| **Zweck** | Einheitlicher Marken-Auftritt in App-Header und Link-Vorschauen |
| Format | PNG (opak, fester Hintergrund) |
| Prompt-Doc vorhanden? | ✅ `spec/design/banner-kami-hauptapplikation.md` |
| Asset vorhanden? | ❌ |
| Priorität | **High** |

### MEDIUM

#### G-08 — Tankmanagement-Illustration (Empty/Hero)

| Feld | Wert |
|---|---|
| Motiv/Beschreibung | KAMI mit Tank + Ventil/Mischkanne als Modul-Hero/Empty-State für Tank-Verwaltung |
| UI-Position/Einsatzort | `pages/standorte/TankListPage.tsx` Empty-State / Header; `WateringEventListPage` nutzt `kamiTanks` (Feature-Illo), aber dediziertes Tankmanagement-Motiv fehlt |
| Benötigte Größe(n) | illustration **320×240** (primär), skalierbar 640×480 / 160×120 |
| **Pose** | Kami neben großem Tank-Requisit (150–250 % Kami-Höhe), eine Hand am Ventil |
| **Emotion** | **Konzentriert/Fokussiert** (Mischvorgang/präzise Arbeit, §10) |
| **Zweck** | Fachlich präziseres Tank-Motiv als die generische `kamiTanks`-Feature-Illo; führt in leeres Tankmanagement ein |
| Format | PNG-transparent → SVG |
| Prompt-Doc vorhanden? | ✅ `spec/design/illustration-kami-tankmanagement.md` |
| Asset vorhanden? | ❌ |
| Priorität | **Medium** |

#### G-09 — Dashboard Willkommens-/Leerzustand-Hero

| Feld | Wert |
|---|---|
| Motiv/Beschreibung | Freundlicher KAMI als Willkommens-Element bzw. Leerzustand („noch keine Pflanzen/Widgets") auf dem Dashboard |
| UI-Position/Einsatzort | `pages/DashboardPage.tsx` + `components/dashboard/widgets/*` — aktuell 0 KAMI |
| Benötigte Größe(n) | feature **320×240** bzw. ≤180px Empty-State im Widget |
| **Pose** | Aufrecht, Arme leicht ausgebreitet präsentierend; optional auf leeres Widget zeigend |
| **Emotion** | **Glücklich/Begeistert** (positiver Start) bzw. **Neugierig/Suchend** im Leerzustand |
| **Zweck** | Persönlicher Einstieg auf der Startseite; führt Erstnutzer ohne Daten freundlich weiter |
| Format | SVG-primär + PNG-Fallback |
| Prompt-Doc vorhanden? | ❌ |
| Asset vorhanden? | ❌ |
| Priorität | **Medium** |

#### G-10 — Erfolg-/Celebration-KAMI

| Feld | Wert |
|---|---|
| Motiv/Beschreibung | Feiernder KAMI (Siegerfaust, Glitzer-Sterne) für Erfolgs-Momente |
| UI-Position/Einsatzort | Feedback-Pfad bei „Ernte abgeschlossen" (`PlantingRunDetailPage`/`HarvestBatchDetailPage`), „Aufgabe erledigt" (`TaskQueuePage`), Phasenwechsel-Erfolg, „Tank aufgefüllt" — kein dedizierter Success-KAMI vorhanden |
| Benötigte Größe(n) | illustration **320×240** bzw. ≤180px in Success-Dialog/Snackbar |
| **Pose** | Ein Arm Siegerfaust nach oben, anderer an der Hüfte (Power-Pose), 2–3 Glitzer-Sterne `#fff9c4` |
| **Emotion** | **Triumphierend/Feiernd (Triumphant/Celebrating)** — §10 „großer Erfolg, Ernte, Phasenwechsel" |
| **Zweck** | Positive Verstärkung erreichter Meilensteine; erhöht Bindung/Motivation |
| Format | SVG-primär + PNG-Fallback |
| Prompt-Doc vorhanden? | ❌ |
| Asset vorhanden? | ❌ |
| Priorität | **Medium** |

#### G-11 — Post-Harvest-Phasen `drying` / `curing`

| Feld | Wert |
|---|---|
| Motiv/Beschreibung | 2 Timeline-Illustrationen für die Nachernte-Phasen Trocknen und Curing, analog der bestehenden 14 Phasen |
| UI-Position/Einsatzort | `pages/durchlaeufe/PhaseKamiTimeline.tsx` — `PHASE_COLORS` definiert `drying`/`curing` (Zeilen 75–76), aber `KAMI_PHASE_IMAGES` hat **kein** Bild → kein Timeline-Motiv |
| Benötigte Größe(n) | phase **256×256** (primär), skalierbar 64×64 / 512×512 |
| **Pose** | `drying`: Kami neben hängender/trocknender Ernte, geduldig wartend; `curing`: Kami an Vorratsglas |
| **Emotion** | **Friedlich/Genießerisch (Peaceful/Serene)** — ruhiger Reife-/Ruhemoment |
| **Zweck** | Lückenlose Phasen-Abdeckung bis in die Nacherntebehandlung (REQ-008) |
| Format | PNG-transparent → SVG |
| Prompt-Doc vorhanden? | ❌ (Referenzmuster: `timeline-kami-phasen-erweitert.md`) |
| Asset vorhanden? | ❌ |
| Priorität | **Medium** |

#### G-12 — Generischer Empty-/Such-/Kein-Ergebnis-KAMI

| Feld | Wert |
|---|---|
| Motiv/Beschreibung | Neutraler KAMI mit Lupe/Fragezeichen als Default-Empty-State statt `InboxIcon` |
| UI-Position/Einsatzort | `components/common/EmptyState.tsx` (Fallback-Zweig `InboxIcon`) → wirkt in ~25 Aufrufen ohne `illustration=` (z.B. `GlossaryPage`, `EnvironmentControlPage`, `PlantIdentificationPage`, diverse Detail-Sektionen) |
| Benötigte Größe(n) | empty-state **≤180px** (max-height im Consumer bereits 180) |
| **Pose** | Blätter leicht nach vorn geneigt, ein Arm am Kinn oder Lupe haltend; optional Fragezeichen über einem Blatt |
| **Emotion** | **Neugierig/Suchend (Curious/Searching)** — §10 „Leere Listen, Suchergebnisse, Empty State, Laden" |
| **Zweck** | Markentypischer, freundlicher Default-Leerzustand statt generischem Material-Icon; deckt alle Listen ohne domänenspezifische Feature-Illo ab |
| Format | SVG-primär + PNG-Fallback |
| Prompt-Doc vorhanden? | ❌ |
| Asset vorhanden? | ❌ |
| Priorität | **Medium** |

#### G-13 — GitHub-Social-Preview

| Feld | Wert |
|---|---|
| Motiv/Beschreibung | Repo-Social-Card mit KAMI als Fokus, Marken-Hintergrund |
| UI-Position/Einsatzort | GitHub-Repo-Einstellung „Social preview" (außerhalb App-Runtime, aber Marken-Fläche) |
| Benötigte Größe(n) | hero **1280×640** (2:1), Light- und Dark-Variante, 40px Safe-Zone |
| **Pose** | Kami zentral als klarer Fokus, aufrecht, freundlich; minimale Stützelemente |
| **Emotion** | **Happy** / **Stolz-Zufrieden** |
| **Zweck** | Professionelle Link-Vorschau des Repos in sozialen Netzen/Chats |
| Format | PNG (opak) |
| Prompt-Doc vorhanden? | ✅ `spec/design/social-preview-github-kamerplanter.md` |
| Asset vorhanden? | ❌ |
| Priorität | **Medium** |

#### G-14 — HA-Integrations-Banner

| Feld | Wert |
|---|---|
| Motiv/Beschreibung | Panorama-Banner „Pflanzen treffen Smart Home", KAMI im stilisierten Hausumriss |
| UI-Position/Einsatzort | HA-Integration README / HACS-Store (außerhalb `src/frontend/`) |
| Benötigte Größe(n) | banner/hero **1920×480** (4:1), 1200×630 (HACS-Social), 800×200; Light+Dark |
| **Pose** | Kami wächst „im Haus" (Topf auf Bodenlinie), Blick auf schwebendes Mini-Dashboard-Panel |
| **Emotion** | **Neugierig/Suchend** bzw. **Happy** (aufmerksam auf Datenpanel) |
| **Zweck** | Marken-Header der HA-Integration; kommuniziert bidirektionale Smart-Home-Anbindung |
| Format | PNG (opak) |
| Prompt-Doc vorhanden? | ✅ `spec/design/banner-kami-ha-integration.md` |
| Asset vorhanden? | ❌ |
| Priorität | **Medium** |

#### G-15 — HA-Integrations-Icon

| Feld | Wert |
|---|---|
| Motiv/Beschreibung | KAMI-Icon für das HA-Integrations-Menü/HACS, neutral für Light+Dark HA-Theme |
| UI-Position/Einsatzort | Home-Assistant Custom Integration (Asset-Ziel außerhalb `src/frontend/`, z.B. `custom_components/…`) |
| Benötigte Größe(n) | app-icon **512×512** (`icon@2x`), 256×256 (`icon`), lesbar bei 32×32 |
| **Pose** | Frontal aufrecht, markante Keimling-im-Topf-Silhouette; 32px-Variante ohne Gesicht/Arme |
| **Emotion** | **Happy (Standard)** |
| **Zweck** | Wiedererkennbares Integrations-Icon in HA/HACS; HA-Dark-Theme-Outline weiß (§3.2) |
| Format | PNG (transparent) |
| Prompt-Doc vorhanden? | ✅ `spec/design/ha-integration-icon-kami.md` |
| Asset vorhanden? | ❌ (nicht in `src/frontend/`; ggf. bereits in HA-Repo prüfen) |
| Priorität | **Medium** |

### LOW

#### G-16 — Toter Export `kamiDashboard` (Housekeeping)

| Feld | Wert |
|---|---|
| Motiv/Beschreibung | Bestehendes Asset `feature-kami-dashboard.svg` ist im Barrel exportiert, aber unkonsumiert |
| UI-Position/Einsatzort | `assets/brand/illustrations/index.ts` (`export … kamiDashboard`) — **keine** importierende Komponente (Dashboard nutzt keine Feature-Illo) |
| Benötigte Größe(n) | n/a (Asset existiert, feature 320×240) |
| **Pose** | (Asset vorhanden) — Wiederverwendung als Dashboard-Hero (siehe G-09) statt Löschung erwägen |
| **Emotion** | (Asset vorhanden) — Happy |
| **Zweck** | Entweder in Dashboard-Hero (G-09) konsumieren oder Export entfernen; kein Illustrations-Gap, sondern Konsistenz-Housekeeping |
| Format | SVG (vorhanden) |
| Prompt-Doc vorhanden? | ✅ `feature-kami-kernfunktionen.md` |
| Asset vorhanden? | ✅ `features/feature-kami-dashboard.svg` |
| Priorität | **Low** |

#### G-17 — Loading-State-KAMI

| Feld | Wert |
|---|---|
| Motiv/Beschreibung | KAMI-Motiv für längere Ladevorgänge (statt reinem Spinner) |
| UI-Position/Einsatzort | globale Lade-/Suspense-Fallbacks (kein dediziertes KAMI-Loading vorhanden) |
| Benötigte Größe(n) | empty-state **≤180px** |
| **Pose** | Blätter leicht nach vorn, ein Arm am Kinn (wartend/beobachtend) |
| **Emotion** | **Neugierig/Suchend** bzw. **Konzentriert/Fokussiert** (§10 „Laden") |
| **Zweck** | Freundliche Überbrückung von Wartezeit, markenkonform |
| Format | SVG-primär + PNG-Fallback |
| Prompt-Doc vorhanden? | ❌ |
| Asset vorhanden? | ❌ |
| Priorität | **Low** |

### 3.1 Gap-Zählung nach Priorität

| Priorität | Gaps | IDs |
|---|---|---|
| Critical | 3 | G-01, G-02, G-03 |
| High | 4 | G-04, G-05, G-06, G-07 |
| Medium | 8 | G-08, G-09, G-10, G-11, G-12, G-13, G-14, G-15 |
| Low | 2 | G-16, G-17 |
| **Summe** | **17** | |

**Mengengerüst hinter den Gaps:** G-04 = 27 Icons, G-05 = 6 Illustrationen, G-06 = 10 Feature-Illos, G-11 = 2 Phasen → einzelne Prompt-Motive in Deliverable 2 deutlich > 17.

Alle 17 Gaps tragen die Pflichtfelder **Pose + Emotion (aus §4.2) + Zweck** (G-16 dokumentiert sie referenziell, da Asset bereits existiert).

---

## 4. Process / Handoff auf Deliverable 2

Dieses Dokument ist die alleinige DoD von Issue #591 (Deliverable 1). Es erzeugt **keine** Assets und **keinen** Code.

**Übergabe an Deliverable 2 (separater Follow-up):**

1. Jeder Gap-Eintrag ist so strukturiert, dass er 1:1 in das 7-Block-Prompt-Kit (`KAMI-CHARACTER-REFERENCE.md §9`) überführbar ist: `[2] SZENE + EMOTION` speist sich aus **Pose** + **Emotion** (englisches Prompt-Fragment aus §4.2 verbatim), `[1] FORMAT + TYP` aus **Benötigte Größe(n)** + **Format**, `[4]/[5]/[6]/[7]` sind konstante Blöcke.
2. Für Gaps mit **vorhandenem Prompt-Doc** (prompt-only, Abschnitt 2.2) ist der Prompt bereits geschrieben — Deliverable 2 muss dort nur **rendern + vektorisieren + einbinden**, keinen neuen Prompt verfassen.
3. Für **both-missing**-Gaps (Abschnitt 2.4) muss Deliverable 2 zuerst ein Prompt-Doc unter `spec/design/` erzeugen (Agent `gemini-graphic-prompt-generator`), dann rendern.
4. Empfohlene Reihenfolge: Critical (G-01/02 zuerst — behebt gebrochene Manifest-Referenz) → High → Medium → Low.
5. Ziel-Asset-Orte: Feature/Empty-State/Phasen → `src/frontend/src/assets/brand/illustrations/…` + Barrel-Export in `index.ts`; Tank-Serie → neues `assets/illustrations/tank/`; PWA-Icons → neues `public/icons/`; HA-Assets → HA-Integration-Repo (außerhalb `src/frontend/`).

---

## 5. Nicht geprüft / Einschränkungen

- **Visuelle Qualität** vorhandener Assets (Stil-Konformität zur Charakter-Referenz) wurde **nicht** bewertet — nur Präsenz/Konsumption.
- **HA-Integration-Assets** (G-14, G-15) liegen außerhalb `src/frontend/`; ein evtl. Bestand im HA-Custom-Component-Repo wurde nicht geprüft.
- **Kiosk-Modus** (`pages/kiosk/`) nur oberflächlich; keine dedizierte KAMI-Fläche identifiziert.
- **Mobile/Flutter** (nicht implementiert) außerhalb Scope.
- Zählung „~25 Empty-States ohne Illustration" ist qualitativ (viele sind Sektions-Leerzustände innerhalb von Detail-Seiten); G-12 adressiert den gemeinsamen Fallback-Pfad zentral.
