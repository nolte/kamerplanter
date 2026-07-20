# KAMI-Design-Register (`spec/design/`)

> **Zweck:** Zentrales Register aller KAMI-Grafik-Prompt-Dokumente unter `spec/design/`.
> Bildet **Prompt-Doc ↔ Motiv ↔ Ziel-Asset-Pfad ↔ Status ↔ Audit-Gap-ID** ab und ist gegen
> `src/frontend/src/assets/brand/illustrations/index.ts` (Asset-Barrel) sowie `public/manifest.json`
> abgleichbar.
> **Erstellt:** 2026-07-13 (Issue #593, Deliverable 2 — Prompt-Ableitung aus dem KAMI-Audit)
> **Norm:** `KAMI-CHARACTER-REFERENCE.md` (§3 Palette/Outline, §4.2 Emotionen, §5 Groessen, §6 Komposition, §9 Prompt-Kit)
> **Audit-Quelle:** `spec/analysis/kami-illustration-audit-2026-07.md` (17 priorisierte Gaps G-01…G-17)

---

## Status-Legende

| Status | Bedeutung |
|---|---|
| `Prompt ✅ / Asset ✅` | Prompt-Doc **und** gerendertes Asset vorhanden (im Barrel/Ordner) |
| `Prompt ✅ / Asset ❌` | Prompt-Doc vorhanden, Asset-Generierung offen (Downstream-Follow-on, out of DoD #593) |
| `Asset ✅ / Prompt ✅ (Housekeeping)` | Asset existiert, aber unkonsumiert (Code-Housekeeping, kein Illustrations-Gap) |

**Wichtig:** Issue #593 liefert ausschliesslich **Prompt-Dokumente**. Alle mit
`Prompt ✅ / Asset ❌` markierten Eintraege erfordern noch Downstream-Rendering + PNG→SVG-
Vektorisierung + Barrel-/Manifest-Verdrahtung (siehe „Follow-on" unten).

---

## 1. Register — alle Prompt-Dokumente

| Prompt-Doc | Typ | Motive | Ziel-Asset-Pfad | Gap-ID(s) | Status |
|---|---|---:|---|---|---|
| `app-icons-kami-pwa.md` | app-icon + logo | 3 | `public/icons/icon-512.png`, `public/icons/icon-192.png`, `assets/brand/logo/logo-kami.svg` | G-01, G-02 | Prompt ✅ / Asset ❌ |
| `illustration-kami-onboarding-willkommen.md` | illustration (hero) | 1 (×2 Themes) | `assets/brand/illustrations/onboarding/illustration-kami-willkommen.svg` | G-03 | Prompt ✅ / Asset ❌ |
| `nav-icons-kami-sidebar.md` | nav-icon (Serie) | 27 (×2 Themes) | `assets/icons/nav/nav-kami-{slug}.svg` | G-04 | Prompt ✅ / Asset ❌ |
| `illustration-kami-tank-fuellstaende.md` | illustration (Serie) | 6 (×2 Themes) | `assets/illustrations/tank/kami-tank-fill-{000…100}.svg` | G-05 | Prompt ✅ / Asset ❌ |
| `feature-kami-fachmodule.md` | feature-illustration (Serie) | 10 | `assets/brand/illustrations/features/feature-kami-{modul}.svg` | G-06 | Prompt ✅ / Asset ❌ |
| `banner-kami-hauptapplikation.md` | banner/hero | mehrere Groessen | In-App-Header / OG-Image (kein Barrel) | G-07 | Prompt ✅ / Asset ❌ |
| `illustration-kami-tankmanagement.md` | illustration (hero/empty) | 1 | `assets/brand/illustrations/…` (Tankmanagement) | G-08 | Prompt ✅ / Asset ❌ |
| `illustration-kami-dashboard-willkommen.md` | illustration (hero + empty) | 2 (×2 Themes) | `assets/brand/illustrations/states/state-kami-dashboard-*.svg` | G-09, (G-16) | Prompt ✅ / Asset ❌ |
| `illustration-kami-erfolg-celebration.md` | illustration (feedback) | 1 (×2 Themes) | `assets/brand/illustrations/states/state-kami-celebration.svg` | G-10 | Prompt ✅ / Asset ❌ |
| `timeline-kami-phase-post-harvest.md` | timeline-phase (Serie) | 2 | `assets/brand/illustrations/phases/timeline-kami-phase-{drying,curing}.svg` | G-11 | Prompt ✅ / Asset ❌ |
| `illustration-kami-empty-state.md` | illustration (empty-state) | 1 (×2 Themes) | `assets/brand/illustrations/states/state-kami-empty.svg` | G-12 | Prompt ✅ / Asset ❌ |
| `social-preview-github-kamerplanter.md` | hero (social) | 1 (×2 Themes) | GitHub Repo Social-Preview (kein Barrel) | G-13 | Prompt ✅ / Asset ❌ |
| `banner-kami-ha-integration.md` | banner/hero | mehrere Groessen | HA-README / HACS (ausserhalb `src/frontend/`) | G-14 | Prompt ✅ / Asset ❌ |
| `ha-integration-icon-kami.md` | app-icon | 1 (neutral) | HA `custom_components/…` (ausserhalb `src/frontend/`) | G-15 | Prompt ✅ / Asset ❌ |
| `illustration-kami-loading.md` | illustration (loading) | 1 (×2 Themes) | `assets/brand/illustrations/states/state-kami-loading.svg` | G-17 | Prompt ✅ / Asset ❌ |
| `feature-kami-kernfunktionen.md` | feature-illustration (Serie) | 12 | `assets/brand/illustrations/features/feature-kami-*.svg` | (Bestand) | Prompt ✅ / Asset ✅ |
| `timeline-kami-phasen.md` | timeline-phase (Serie) | 5 | `assets/brand/illustrations/phases/…` (Basis-5) | (Bestand) | Prompt ✅ / Asset ✅ |
| `timeline-kami-phasen-erweitert.md` | timeline-phase (Serie) | 6 | `assets/brand/illustrations/phases/…` (erweitert) | (Bestand) | Prompt ✅ / Asset ✅ |
| `timeline-kami-phase-flushing.md` | timeline-phase | 1 | `assets/brand/illustrations/phases/…flushing` | (Bestand) | Prompt ✅ / Asset ✅ |
| `timeline-kami-phase-leaf-phase.md` | timeline-phase | 1 | `assets/brand/illustrations/phases/…leaf-phase` | (Bestand) | Prompt ✅ / Asset ✅ |
| `timeline-kami-phase-short-day-induction.md` | timeline-phase | 1 | `assets/brand/illustrations/phases/…short-day-induction` | (Bestand) | Prompt ✅ / Asset ✅ |
| `illustration-kami-http-errors.md` | illustration (errors) | 9 | `assets/illustrations/errors/error-*.svg` | (Bestand) | Prompt ✅ / Asset ✅ |

**Neu in #593 authored:** `app-icons-kami-pwa.md`, `illustration-kami-onboarding-willkommen.md`,
`feature-kami-fachmodule.md`, `illustration-kami-dashboard-willkommen.md`,
`illustration-kami-erfolg-celebration.md`, `timeline-kami-phase-post-harvest.md`,
`illustration-kami-empty-state.md`, `illustration-kami-loading.md` (**8 neue Docs**).
**Ergaenzt (Dark-Variante nachdokumentiert):** `illustration-kami-tank-fuellstaende.md` (G-05),
`nav-icons-kami-sidebar.md` (G-04) — **2 Docs**. Uebrige 5 prompt-only-Bestandsdocs
(G-07/08/13/14/15) sind bereits Light+Dark-vollstaendig → nur referenziert, nicht dupliziert.

---

## 2. Audit-Gap-Abdeckung (alle 17 Gaps)

| Gap-ID | Prio | Kurzbeschreibung | Prompt-Doc | Abgedeckt |
|---|---|---|---|---|
| G-01 | Critical | PWA App-Icon 512 (maskable) | `app-icons-kami-pwa.md` (Prompt 1) | ✅ |
| G-02 | Critical | PWA App-Icon 192 (maskable) | `app-icons-kami-pwa.md` (Prompt 2) | ✅ |
| G-03 | Critical | Onboarding/Login Willkommens-Hero | `illustration-kami-onboarding-willkommen.md` | ✅ |
| G-04 | High | 27 Sidebar-Nav-Icons | `nav-icons-kami-sidebar.md` (+ Dark ergaenzt) | ✅ |
| G-05 | High | Tank-Fuellstand-Serie (6) | `illustration-kami-tank-fuellstaende.md` (+ Dark ergaenzt) | ✅ |
| G-06 | High | 10 Fachmodul-Feature-Illos | `feature-kami-fachmodule.md` | ✅ |
| G-07 | High | Banner Hauptapplikation | `banner-kami-hauptapplikation.md` (Bestand) | ✅ |
| G-08 | Medium | Tankmanagement-Illustration | `illustration-kami-tankmanagement.md` (Bestand) | ✅ |
| G-09 | Medium | Dashboard Willkommens-/Leer-Hero | `illustration-kami-dashboard-willkommen.md` | ✅ |
| G-10 | Medium | Erfolg-/Celebration-KAMI | `illustration-kami-erfolg-celebration.md` | ✅ |
| G-11 | Medium | Post-Harvest-Phasen drying/curing | `timeline-kami-phase-post-harvest.md` | ✅ |
| G-12 | Medium | Generischer Empty-/Such-KAMI | `illustration-kami-empty-state.md` | ✅ |
| G-13 | Medium | GitHub-Social-Preview | `social-preview-github-kamerplanter.md` (Bestand) | ✅ |
| G-14 | Medium | HA-Integrations-Banner | `banner-kami-ha-integration.md` (Bestand) | ✅ |
| G-15 | Medium | HA-Integrations-Icon | `ha-integration-icon-kami.md` (Bestand) | ✅ |
| G-16 | Low | Toter Export `kamiDashboard` (Housekeeping) | referenziert in `illustration-kami-dashboard-willkommen.md` | ✅ (referenziell) |
| G-17 | Low | Loading-State-KAMI | `illustration-kami-loading.md` | ✅ |

**Abdeckung: 17/17 Gaps.** Keine Orphan-Prompts, keine offene Gap-Position.

**Zu G-16:** Kein neues Motiv — das Asset `feature-kami-dashboard.svg` existiert bereits im
Barrel (`kamiDashboard`), wird aber von keiner Komponente importiert. Empfehlung im Dashboard-Doc:
als Dashboard-Hero konsumieren statt loeschen. Reine Code-Konsistenz, kein Illustrations-Gap.

---

## 3. Barrel-Abgleich (`assets/brand/illustrations/index.ts`)

**Aktuell exportiert (Ist):** 12 Feature-Motive (`kamiDashboard`…`kamiTanks`) + 14 Phasen-Motive.
`kamiDashboard` ist exportiert, aber unkonsumiert (G-16).

**Durch #593 vorbereitet (Soll, Downstream zu ergaenzen nach Rendering):**

| Neuer Export | Prompt-Doc | Gap |
|---|---|---|
| `kamiWelcome` | `illustration-kami-onboarding-willkommen.md` | G-03 |
| `kamiAquaponik`, `kamiEnvironment`, `kamiKiAssistent`, `kamiKiDiagnose`, `kamiKiRecognition`, `kamiPostHarvest`, `kamiPropagation`, `kamiUeberwinterung`, `kamiInventree`, `kamiGlossar` | `feature-kami-fachmodule.md` | G-06 |
| `kamiDashboardWelcome`, `kamiDashboardEmpty` | `illustration-kami-dashboard-willkommen.md` | G-09 |
| `kamiCelebration` | `illustration-kami-erfolg-celebration.md` | G-10 |
| `kamiPhaseDrying`, `kamiPhaseCuring` | `timeline-kami-phase-post-harvest.md` | G-11 |
| `kamiEmpty` | `illustration-kami-empty-state.md` | G-12 |
| `kamiLoading` | `illustration-kami-loading.md` | G-17 |

PWA-Icons (G-01/02) liegen unter `public/icons/` (kein Barrel-Export, per `manifest.json`
referenziert). Tank-Serie (G-05) unter `assets/illustrations/tank/` (eigener Ordner, per
`import.meta.glob`/direktem Import). Nav-Icons (G-04) unter `assets/icons/nav/`.

---

## 4. Follow-on (Downstream, out of DoD #593)

Priorisiert gemaess Audit §4 (Critical → High → Medium → Low):

1. **G-01/G-02 (Critical):** `public/icons/` anlegen + maskable App-Icons rendern → behebt die
   gebrochene `manifest.json`-Referenz (404 beim PWA-Install).
2. **G-03 (Critical):** Willkommens-Hero rendern + in Login/Register/Onboarding einbinden.
3. **G-04/G-05/G-06/G-07 (High):** Nav-Icon-Serie, Tank-Serie, Fachmodul-Illos, Banner rendern
   + vektorisieren + Barrel-/Sidebar-Verdrahtung.
4. **G-08…G-15 (Medium):** restliche Illustrationen/Banner/Icons.
5. **G-16/G-17 (Low):** `kamiDashboard` konsumieren bzw. Export entfernen; Loading-KAMI.

Jeder Schritt: PNG rendern → Hintergrund transparent pruefen → PNG→SVG (vtracer) →
Barrel-Export/`manifest.json`/Consumer verdrahten → Light+Dark verifizieren.

---

## 5. Automatisierte Render-/Review-Pipeline (`scripts/kami/`)

Der „PNG rendern"-Schritt aus §4 ist automatisiert und mit einem **automatischen
Claude-Vision-Konformitaets-Check** gegen `KAMI-CHARACTER-REFERENCE.md` versehen. Details:
`scripts/kami/README.md`.

- **`spec/design/_generation-manifest.yaml`** — maschinelle SSOT: pro Motiv/Variante ein
  Render-Job (`id`, `gap`, `variant`, `emotion`, `pose`, `size`, `out`) mit FLUX-Prompt
  (inline oder als `doc:`+`motif_heading:`-Referenz in das jeweilige Prompt-Doc dieses Registers).
  Deckt Batch 1 (20 Jobs, die 8 neuen #593-Docs, inline) + Batch 2 (59 Jobs: Features G-06,
  Tank G-05, Nav G-04 via `doc:`-Referenz) ab.
- **`scripts/kami/render.py`** — treibt die nolte-media `image-generate` (FLUX.1-schnell via
  Cloudflare, kostenlos) ueber den Manifest; verwaltet Job-Zustaende; regeneriert abgelehnte
  Bilder mit frischem Seed. `task kami:status` / `task kami:generate` / `task kami:worklist`.
- **`.claude/agents/kami-image-reviewer.md`** — prueft je EIN generiertes PNG visuell gegen
  §3/§3.2/§4.2/§5/§6/§8 und schreibt ein `approved`/`rejected`-Verdikt zurueck (Regen-Loop).

**Modell-Hinweis (nolte-media):** Provider `cloudflare`=FLUX.1-schnell (Default, frei, ignoriert
width/height → immer ~1024² quadratisch), `gemini`=gemini-2.5-flash-image (kostenpflichtig +
SynthID-Wasserzeichen), `pollinations`=FLUX (frei, Lizenz ungeklaert). FLUX kennt **keine**
Negativ-Prompts → `render.py` normalisiert `doc:`-Bloecke FLUX-tauglich (streicht `Avoid:`,
tauscht Dark-Outline).
