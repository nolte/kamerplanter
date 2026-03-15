---

ID: UI-NFR-012
Titel: PWA & Offline-Faehigkeit
Kategorie: UI-Verhalten Unterkategorie: Progressive Web App, Offline, Synchronisation
Technologie: React, TypeScript, Vite (vite-plugin-pwa), Workbox, IndexedDB (Dexie), Redux Toolkit
Status: Entwurf
Prioritaet: Hoch
Version: 2.0
Autor: Business Analyst - Agrotech
Datum: 2026-03-01
Tags: [pwa, offline, service-worker, indexeddb, dexie, sync, installable, cache, connectivity, mobile-strategy]
Abhaengigkeiten: [UI-NFR-001, UI-NFR-003, UI-NFR-004, UI-NFR-006, UI-NFR-009, UI-NFR-011]
Betroffene Module: [Frontend, Backend (ETag-Support)]
---

# UI-NFR-012: PWA & Offline-Faehigkeit

## 1. Business Case

### 1.1 User Stories

**Als** Grower im Growraum (Keller)
**moechte ich** Messwerte und Beobachtungen auch ohne Internetverbindung erfassen koennen
**um** keine Daten zu verlieren, wenn der Mobilfunkempfang schlecht ist.

**Als** Grower im Gewaechshaus
**moechte ich** die Anwendung auf dem Tablet als installierte App nutzen
**um** sie wie eine native App ueber den Homescreen starten zu koennen, ohne den Browser oeffnen zu muessen.

**Als** Grower unterwegs (Balkon, Garten)
**moechte ich** jederzeit sehen, ob ich online oder offline bin
**um** zu wissen, ob meine Eingaben sofort synchronisiert werden oder spaeter.

**Als** Betreiber einer Kiosk-Station
**moechte ich** dass die Anwendung bei kurzfristigen Netzwerkausfaellen weiterlaeuft
**um** den Arbeitsfluss im Gewaechshaus nicht zu unterbrechen.

**Als** Grower
**moechte ich** dass offline erfasste Daten automatisch synchronisiert werden, sobald die Verbindung wiederhergestellt ist
**um** mich nicht manuell um die Uebertragung kuemmern zu muessen.

**Als** Casual-Nutzer mit Zimmerpflanzen
**moechte ich** die App auf meinem Handy installieren koennen
**um** schnell die Pflege-Erinnerungen zu sehen, ohne den Browser oeffnen zu muessen.

### 1.2 Geschaeftliche Motivation

Gewaechshaeuser, Growaerume und Keller haben haeufig keinen oder instabilen Mobilfunk-/WLAN-Empfang. Eine rein online-faehige Anwendung ist in diesen Umgebungen unbrauchbar:

1. **Growaerume im Keller** — Kein Mobilfunkempfang, WLAN oft nicht bis in jeden Winkel
2. **Gewaechshaeuser aus Metall/Glas** — WLAN-Signal wird durch Struktur gedaempft, Abschattung
3. **Grosse Anlagen** — WLAN-Abdeckung nicht flaechendeckend garantiert
4. **Balkon/Garten** — Mobiles Internet variabel (Edge/3G in Aussenbereichen)
5. **Kiosk-Stationen** — Router-Ausfall darf den Betrieb nicht stoppen

Ohne Offline-Faehigkeit:
- Gehen Messwerte verloren, die erst am Abend am Desktop nachgetragen werden (wenn ueberhaupt)
- Wird die Datenqualitaet massiv beeintraechtigt (fehlende Zeitstempel, vergessene Werte)
- Sinkt die Nutzerakzeptanz, da die App "nie funktioniert, wenn man sie braucht"

### 1.3 Strategische Entscheidung: PWA statt Flutter als Mobile-Strategie

<!-- Architektur-Entscheidung: PWA-First Mobile-Strategie -->

Die urspruengliche Planung sah Flutter (spec/stack.md, Abschnitt 4.2) als mobile Plattform vor. Nach Analyse des IST-Zustands und der Anforderungen wird die **PWA als primaere Mobile-Strategie** empfohlen:

| Kriterium | PWA | Flutter |
|-----------|-----|---------|
| **Codebasis** | Bestehendes React-Frontend wiederverwendet | Komplett neues Dart-Codebase |
| **Offline-Faehigkeit** | Service Worker + IndexedDB | Eigene SQLite/Hive-Implementierung |
| **Installierbar** | Ja (Add to Home Screen) | Ja (App Store) |
| **Store-Deployment** | Nicht noetig | Apple Developer Account ($99/a), App-Store-Review |
| **Apple Sign-In** | Nicht erforderlich | Pflicht fuer iOS App Store |
| **Push-Benachrichtigungen** | Web Push API (iOS seit 16.4) | FCM/APNs (voll unterstuetzt) |
| **Entwicklungsaufwand** | Gering (bestehendes Frontend erweitern) | Hoch (~150 API-Endpoints manuell anbinden) |
| **Bluetooth/NFC** | Eingeschraenkt (Web Bluetooth API) | Voll unterstuetzt |
| **Wartung** | Ein Codebase | Zwei Codebasen parallel pflegen |

**Empfehlung:** PWA als v1 Mobile-Strategie umsetzen. Flutter nur evaluieren, wenn native Sensorzugriffe (Bluetooth LE fuer IoT-Sensoren) oder App-Store-Praesenz zwingend werden. Die REST-API-Architektur (5-Layer, NFR-001) ermoeglicht jederzeit das Hinzufuegen eines nativen Clients.

---

## 2. IST-Analyse (Stand 2026-03-01)

### 2.1 Implementierungsstand: 0% — Komplett offen

| Komponente | Status | Beschreibung |
|-----------|--------|-------------|
| Web App Manifest | Nicht vorhanden | Kein `manifest.webmanifest`, kein `<link rel="manifest">` in `index.html` |
| Service Worker | Nicht vorhanden | Kein `sw.ts`, keine Registrierung in `main.tsx` |
| `vite-plugin-pwa` | Nicht installiert | Weder in `package.json` noch in `vite.config.ts` |
| IndexedDB-Integration | Nicht vorhanden | Kein `dexie`, `idb` oder sonstiger IndexedDB-Zugriff |
| Offline-Erkennung | Nicht vorhanden | Kein `navigator.onLine`-Check, kein Connectivity-Hook |
| PWA-Icons | Nicht vorhanden | Kein `public/`-Verzeichnis, keine App-Icons |
| API-Caching | Nicht vorhanden | Kein Response-Cache, kein Cache-Invalidierung |
| Sync-Mechanismus | Nicht vorhanden | Keine Offline-Queue, kein Background Sync |
| Install-Prompt | Nicht vorhanden | Kein `beforeinstallprompt`-Handling |
| Meta-Tags | Minimal | Nur `viewport`, `description`, `charset` in `index.html` |

### 2.2 Vorhandene Infrastruktur (nutzbar)

| Komponente | Pfad | Relevanz fuer PWA |
|-----------|------|-------------------|
| Vite 6 Build-System | `vite.config.ts` | `vite-plugin-pwa` integriert sich nativ |
| Axios API-Client | `src/api/client.ts` | Interceptor fuer Offline-Queuing erweiterbar |
| Redux Store | `src/store/store.ts` | Offline-State-Slice einhaengbar |
| notistack | `App.tsx` | Connectivity-Benachrichtigungen ueber bestehende SnackbarProvider |
| react-router-dom v7 | `src/routes/AppRoutes.tsx` | Precaching-Liste ableitbar |
| i18n (DE/EN) | `src/i18n/` | Offline-UI-Texte in bestehende Struktur integrierbar |
| AuthProvider | `src/auth/AuthProvider.tsx` | JWT-Token-Persistierung fuer Offline-Auth noetig |
| `updated_at` auf allen Entities | `base_repository.py:62,73` | Versionsstempel fuer Konflikterkennung vorhanden |
| UI-NFR-009 Visual Identity | `spec/ui-nfr/UI-NFR-009` | Branding-Richtlinien fuer PWA-Icons/Splash |

---

## 3. Anforderungen

### 3.1 PWA-Grundanforderungen

| # | Regel | Stufe |
|---|-------|-------|
| R-001 | Die Anwendung MUSS als **Progressive Web App** installierbar sein (Web App Manifest + Service Worker). | MUSS |
| R-002 | Das Web App Manifest MUSS mindestens folgende Felder definieren: `name`, `short_name`, `start_url`, `display: "standalone"`, `theme_color`, `background_color`, Icons in 192px und 512px. | MUSS |
| R-003 | Die `start_url` MUSS auf die Kiosk-Startseite (`/kiosk`) oder die Dashboard-Seite verweisen, je nach Geraetetyp. | MUSS |
| R-004 | Die Anwendung MUSS auf dem Homescreen des Geraets installiert werden koennen (Android: Add to Home Screen, iOS: Add to Home Screen via Safari). | MUSS |
| R-005 | Im `standalone`-Modus MUSS die Anwendung ohne Browser-UI-Elemente (Adressleiste, Tabs) dargestellt werden. | MUSS |
| R-006 | Die Anwendung SOLL Push-Benachrichtigungen unterstuetzen koennen (Web Push API), auch wenn die Implementierung zunaechst nicht erfolgt. Das Manifest MUSS dafuer vorbereitet sein. | SOLL |

### 3.2 Service Worker & Caching-Strategie

| # | Regel | Stufe |
|---|-------|-------|
| R-007 | Die Anwendung MUSS einen Service Worker registrieren, der das Caching statischer Assets (HTML, CSS, JS, Bilder, Fonts) uebernimmt. | MUSS |
| R-008 | Fuer statische Assets MUSS eine **Cache-First**-Strategie verwendet werden: Zuerst aus dem Cache laden, bei Cache-Miss vom Netzwerk holen und cachen. | MUSS |
| R-009 | Fuer API-Responses MUSS eine **Network-First**-Strategie verwendet werden: Zuerst vom Netzwerk laden, bei Netzwerkfehler aus dem Cache laden. | MUSS |
| R-010 | Fuer die Kiosk-Startseite und die wichtigsten Navigationsrouten MUSS eine **Precaching**-Strategie verwendet werden: Diese Seiten werden beim Service-Worker-Install vorab in den Cache gelegt. | MUSS |
| R-011 | Der Service Worker MUSS ueber `vite-plugin-pwa` (Workbox-basiert) implementiert werden, um mit dem Vite-Build-System kompatibel zu bleiben. | MUSS |
| R-012 | API-Cache-Eintraege MUESSEN eine maximale TTL (Time-To-Live) von **15 Minuten** haben — danach MUSS bei naechster Online-Verfuegbarkeit neu geladen werden. | MUSS |
| R-013 | Der Cache MUSS eine Obergrenze von **50 MB** fuer API-Responses haben. Bei Ueberschreitung werden die aeltesten Eintraege geloescht (LRU). | MUSS |
| R-014 | Service-Worker-Updates MUESSEN dem Nutzer ueber ein UI-Element angezeigt werden (z.B. Banner "Neue Version verfuegbar — Jetzt aktualisieren"). | MUSS |

### 3.3 Offline-Dateneingabe

| # | Regel | Stufe |
|---|-------|-------|
| R-015 | Die Anwendung MUSS im Offline-Zustand das Erfassen folgender Daten ermoeglichen: Messwerte (EC, pH, Temperatur, Luftfeuchtigkeit), Bewaesserungsereignisse, Problembeobachtungen (Text + optional Foto), Aufgaben-Status-Updates. | MUSS |
| R-016 | Offline erfasste Daten MUESSEN in einer lokalen **IndexedDB**-Datenbank zwischengespeichert werden. | MUSS |
| R-017 | Jeder Offline-Datensatz MUSS folgende Metadaten enthalten: Erfassungszeitpunkt (Client-Timestamp), Sync-Status (`pending`, `synced`, `conflict`, `failed`), Entitaets-Typ, Nutzer-ID. | MUSS |
| R-018 | Die lokale Speicherung MUSS auch bei App-Neustart erhalten bleiben (IndexedDB ist persistent). | MUSS |
| R-019 | Es SOLL eine Obergrenze von **500 Offline-Eintraegen** geben. Bei Erreichen der Grenze MUSS der Nutzer gewarnt werden, dass eine Synchronisation noetig ist. | SOLL |
| R-020 | Pflanzenstammdaten (Arten, Sorten, Standorte) MUESSEN offline lesbar sein — diese Daten werden beim letzten Online-Zugriff vorab gecacht. | MUSS |

### 3.4 Synchronisation

| # | Regel | Stufe |
|---|-------|-------|
| R-021 | Die Anwendung MUSS **automatische Synchronisation** durchfuehren, sobald eine Netzwerkverbindung wiederhergestellt wird. | MUSS |
| R-022 | Die Synchronisation MUSS die **Background Sync API** verwenden, wenn vom Browser unterstuetzt. Fallback: Synchronisation beim naechsten App-Start oder manuell. | MUSS |
| R-023 | Offline-Eintraege MUESSEN in chronologischer Reihenfolge synchronisiert werden (FIFO). | MUSS |
| R-024 | Waehrend der Synchronisation MUSS ein **Sync-Fortschrittsindikator** angezeigt werden (z.B. "Synchronisiere 3/12 Eintraege..."). | MUSS |
| R-025 | Nach erfolgreicher Synchronisation MUSS der Nutzer per Snackbar/Overlay informiert werden (z.B. "12 Eintraege synchronisiert"). | MUSS |
| R-026 | Fehlgeschlagene Synchronisationsversuche MUESSEN automatisch nach **exponential Backoff** wiederholt werden (1s -> 2s -> 4s -> 8s -> max. 60s). | MUSS |
| R-027 | Nach 5 fehlgeschlagenen Versuchen MUSS der Eintrag als `failed` markiert und der Nutzer informiert werden. Ein manueller "Erneut versuchen"-Button MUSS angeboten werden. | MUSS |

### 3.5 Konflikterkennung

| # | Regel | Stufe |
|---|-------|-------|
| R-028 | Wenn ein Datensatz offline geaendert wurde und zwischenzeitlich serverseitig aktualisiert wurde, MUSS die Anwendung einen **Konflikt** erkennen. | MUSS |
| R-029 | Die Konflikterkennung MUSS auf einem **Versionsstempel** (`updated_at`-Timestamp) basieren. Das Backend liefert `updated_at` auf allen Entities (via `base_repository.py`). | MUSS |
| R-030 | Bei einem Konflikt MUSS der Nutzer informiert werden und zwischen folgenden Optionen waehlen koennen: "Meine Version uebernehmen", "Server-Version uebernehmen", "Abbrechen". | MUSS |
| R-031 | Der Konfliktdialog MUSS beide Versionen (lokal und Server) nebeneinander anzeigen, mit Hervorhebung der abweichenden Felder. | MUSS |
| R-032 | Im Kiosk-Modus SOLL der Konfliktdialog vereinfacht werden: Nur "Meine Version uebernehmen" und "Verwerfen" als Optionen, mit grossen Touch-Targets (vgl. UI-NFR-011). | SOLL |

### 3.6 Konnektivitaets-Anzeige

| # | Regel | Stufe |
|---|-------|-------|
| R-033 | Die Anwendung MUSS permanent einen **Konnektivitaets-Indikator** anzeigen, der den aktuellen Online/Offline-Status darstellt. | MUSS |
| R-034 | Der Online-Status MUSS als gruener Punkt oder gruenes Icon dargestellt werden. | MUSS |
| R-035 | Der Offline-Status MUSS als roter/orangener Punkt oder Icon mit dem Text "Offline" dargestellt werden. | MUSS |
| R-036 | Beim Wechsel von Online zu Offline MUSS eine deutliche Benachrichtigung angezeigt werden (Snackbar: "Offline — Eingaben werden lokal gespeichert"). | MUSS |
| R-037 | Beim Wechsel von Offline zu Online MUSS eine Benachrichtigung angezeigt werden (Snackbar: "Online — Synchronisation startet..."). | MUSS |
| R-038 | Der Indikator MUSS die Anzahl der noch nicht synchronisierten Eintraege als Badge anzeigen (z.B. "Offline (3)"). | MUSS |
| R-039 | Im Kiosk-Modus MUSS der Konnektivitaets-Indikator mindestens **32px** gross und in der App-Bar permanent sichtbar sein. | MUSS |

### 3.7 Offline-Einschraenkungen

| # | Regel | Stufe |
|---|-------|-------|
| R-040 | Wenn eine Aktion offline nicht moeglich ist (z.B. Anlegen einer neuen Pflanzenart, die serverseitige Validierung erfordert), MUSS die Anwendung den Nutzer **vor** der Eingabe darueber informieren: "Diese Aktion ist nur online moeglich." | MUSS |
| R-041 | Offline nicht verfuegbare Aktionen MUESSEN visuell als deaktiviert dargestellt werden (ausgegraut) mit einem Offline-Icon als Indikator. | MUSS |
| R-042 | Die Anwendung MUSS klar dokumentieren (in einer Hilfeseite oder Tooltip), welche Funktionen offline verfuegbar sind und welche nicht. | MUSS |

### 3.8 Foto-Offline-Handling

| # | Regel | Stufe |
|---|-------|-------|
| R-043 | Fotos (Pflanzendokumentation, IPM-Beobachtungen) MUESSEN offline in IndexedDB als Blob gespeichert werden koennen. | MUSS |
| R-044 | Offline gespeicherte Fotos MUESSEN auf dem Geraet komprimiert werden (max. 1920px Kantenlaenge, JPEG 80% Qualitaet), um den IndexedDB-Speicher zu schonen. | MUSS |
| R-045 | Bei der Synchronisation MUESSEN Fotos sequenziell hochgeladen werden (nicht parallel), um den Upload bei schwacher Verbindung stabil zu halten. | MUSS |
| R-046 | Ein Upload-Fortschritt MUSS pro Foto angezeigt werden (Prozentanzeige oder Progress-Bar). | MUSS |
| R-047 | Die Gesamtgroesse der offline gespeicherten Fotos SOLL auf **200 MB** begrenzt sein. Bei Ueberschreitung MUSS der Nutzer gewarnt werden. | SOLL |

### 3.9 Auth-Token-Persistierung

| # | Regel | Stufe |
|---|-------|-------|
| R-048 | JWT Access Tokens und Refresh Tokens MUESSEN so persistiert werden, dass sie bei App-Neustart (nach Offline-Phase) verfuegbar bleiben. | MUSS |
| R-049 | Wenn der Access Token waehrend einer Offline-Phase ablaeuft (15 min TTL, REQ-023), MUSS die App beim naechsten Online-Zugriff automatisch einen Token-Refresh versuchen, bevor ein Re-Login erzwungen wird. | MUSS |
| R-050 | Waehrend einer Offline-Phase MUSS die App den Nutzer **nicht** ausloggen, auch wenn der Access Token abgelaufen ist. Die lokale Authentifizierung MUSS auf dem letzten gueltigen Auth-State basieren. | MUSS |
| R-051 | Wenn der Refresh Token waehrend einer laengeren Offline-Phase ablaeuft (30 Tage TTL), MUSS die App beim naechsten Online-Zugriff den Nutzer freundlich zum Re-Login auffordern und alle nicht-synchronisierten Daten MUESSEN erhalten bleiben. | MUSS |

### 3.10 Redux-Integration fuer Offline-State

| # | Regel | Stufe |
|---|-------|-------|
| R-052 | Ein dediziertes Redux-Slice `offlineSlice` MUSS den Offline-State verwalten: Connectivity-Status, Pending-Count, Sync-Fortschritt, letzte Sync-Zeit. | MUSS |
| R-053 | Alle existierenden API-Aufrufe (via `src/api/client.ts` Axios-Interceptor) MUESSEN bei Offline-Status automatisch in die IndexedDB-Queue umgeleitet werden, anstatt einen Netzwerkfehler zu werfen. | MUSS |
| R-054 | Das `offlineSlice` MUSS per `useAppSelector` aus jeder Komponente abfragbar sein, um Offline-Gating (R-040, R-041) deklarativ zu steuern. | MUSS |

---

## 4. Backend-Voraussetzungen

Die folgenden Backend-Erweiterungen sind noetig, um die PWA-Features vollstaendig zu unterstuetzen. Diese sind **nicht** Teil der Frontend-Implementierung, muessen aber vor oder parallel zu Phase 2–3 umgesetzt werden.

### 4.1 ETag-Support fuer Konflikterkennung (R-028, R-029)

| # | Regel | Stufe |
|---|-------|-------|
| B-001 | Alle GET-Responses fuer einzelne Entities MUESSEN einen `ETag`-Header zurueckgeben, basierend auf dem `updated_at`-Feld. | MUSS |
| B-002 | Alle PUT/PATCH-Requests MUESSEN den `If-Match`-Header akzeptieren. Bei Mismatch MUSS HTTP 412 (Precondition Failed) zurueckgegeben werden, mit der aktuellen Server-Version im Response-Body. | MUSS |
| B-003 | Die `base_repository.py` MUSS ein `_rev`-Feld (ArangoDB-Revision) oder den `updated_at`-Timestamp als ETag-Quelle bereitstellen. | MUSS |

### 4.2 Bulk-Sync-Endpoint (R-021, R-023)

| # | Regel | Stufe |
|---|-------|-------|
| B-004 | Ein neuer Endpoint `POST /api/v1/sync/batch` SOLL mehrere Offline-Eintraege in einem einzigen Request synchronisieren koennen, um die Anzahl der Netzwerk-Roundtrips zu minimieren. | SOLL |
| B-005 | Der Batch-Sync-Response MUSS pro Eintrag den Sync-Status zurueckgeben: `synced`, `conflict` (mit Server-Version), oder `failed` (mit Fehlerbeschreibung). | SOLL |

### 4.3 Stammdaten-Snapshot-Endpoint (R-020)

| # | Regel | Stufe |
|---|-------|-------|
| B-006 | Ein Endpoint `GET /api/v1/offline/snapshot` SOLL einen kompakten Snapshot aller offline-relevanten Stammdaten liefern (Species, Cultivars, Sites, Locations, Slots), um das initiale Caching in einem Request zu ermoeglichen. | SOLL |
| B-007 | Der Snapshot-Endpoint MUSS einen `Last-Modified`-Header zurueckgeben. Der Client SOLL per `If-Modified-Since` pruefen, ob ein neuer Snapshot noetig ist. | SOLL |

---

## 5. Implementierungsphasen

### 5.1 Phase 1 — PWA-Installierbarkeit (Abdeckung: R-001 bis R-014)

**Ziel:** Die App wird installierbar und laedt deutlich schneller. Lighthouse PWA-Score >= 90.

**Keine Abhaengigkeit zu Backend-Aenderungen.**

#### 5.1.1 Neue Dateien

| Datei | Beschreibung |
|-------|-------------|
| `src/frontend/public/manifest.webmanifest` | Web App Manifest mit name, short_name, start_url, display, theme_color, background_color, Icons |
| `src/frontend/public/icons/icon-192x192.png` | PWA-Icon 192px (gemaess UI-NFR-009 Visual Identity) |
| `src/frontend/public/icons/icon-512x512.png` | PWA-Icon 512px (gemaess UI-NFR-009 Visual Identity) |
| `src/frontend/public/icons/apple-touch-icon.png` | iOS-spezifisches Icon (180px) |
| `src/frontend/src/sw.ts` | Service Worker Source (Workbox-basiert, wenn injectManifest gewaehlt) |
| `src/frontend/src/components/common/UpdateBanner.tsx` | Banner-Komponente: "Neue Version verfuegbar — Jetzt aktualisieren" |
| `src/frontend/src/components/common/InstallPrompt.tsx` | Optionaler Install-Prompt ("App installieren") fuer Android-Geraete |
| `src/frontend/src/hooks/usePwaUpdate.ts` | Hook: Service-Worker-Update-Erkennung, controllerchange-Event |

#### 5.1.2 Zu aendernde Dateien

| Datei | Aenderung |
|-------|-----------|
| `src/frontend/package.json` | `vite-plugin-pwa` als devDependency hinzufuegen |
| `src/frontend/vite.config.ts` | `VitePWA()` Plugin konfigurieren (generateSW oder injectManifest, Precache-Liste, Workbox-Runtime-Caching-Regeln) |
| `src/frontend/index.html` | `<link rel="manifest">`, `<meta name="theme-color">`, `<meta name="apple-mobile-web-app-capable">`, `<link rel="apple-touch-icon">` |
| `src/frontend/src/main.tsx` | Service-Worker-Registrierung via `registerSW` aus `virtual:pwa-register` |
| `src/frontend/src/App.tsx` | `<UpdateBanner />` einbinden |

#### 5.1.3 Vite-Plugin-PWA Konfiguration (Referenz)

```typescript
// vite.config.ts — Zielzustand
import { VitePWA } from 'vite-plugin-pwa';

export default defineConfig({
  plugins: [
    react(),
    VitePWA({
      registerType: 'prompt', // Nutzer entscheidet ueber Update
      includeAssets: ['icons/*.png'],
      manifest: {
        name: 'Kamerplanter',
        short_name: 'Kamerplanter',
        description: 'Plant Lifecycle Management',
        start_url: '/',
        display: 'standalone',
        theme_color: '#2E7D32', // Primaerfarbe aus UI-NFR-009
        background_color: '#ffffff',
        icons: [
          { src: '/icons/icon-192x192.png', sizes: '192x192', type: 'image/png' },
          { src: '/icons/icon-512x512.png', sizes: '512x512', type: 'image/png' },
          { src: '/icons/icon-512x512.png', sizes: '512x512', type: 'image/png', purpose: 'maskable' },
        ],
      },
      workbox: {
        // Phase 1: Nur statische Assets cachen
        globPatterns: ['**/*.{js,css,html,ico,png,svg,woff2}'],
        // Phase 2 ergaenzt: Runtime-Caching fuer API-Responses
        runtimeCaching: [
          {
            urlPattern: /^\/api\/v1\//,
            handler: 'NetworkFirst',
            options: {
              cacheName: 'api-cache',
              expiration: { maxEntries: 200, maxAgeSeconds: 15 * 60 },
              networkTimeoutSeconds: 5,
            },
          },
        ],
      },
    }),
  ],
  // ... restliche Config
});
```

#### 5.1.4 Precaching-Routen

Die folgenden Routen MUESSEN vorab gecacht werden (abgeleitet aus `AppRoutes.tsx`):

| Route | Begruendung |
|-------|------------|
| `/` | Dashboard / Startseite |
| `/kiosk` | Kiosk-Startseite (UI-NFR-011) |
| `/standorte` | Standortuebersicht |
| `/aufgaben` | Aufgabenliste |
| `/pflege` | Pflege-Dashboard |
| `/duengung/fertilizers` | Duengerliste |

#### 5.1.5 Akzeptanzkriterien Phase 1

- [ ] Web App Manifest ist korrekt konfiguriert (Lighthouse Installable-Check bestanden)
- [ ] Anwendung ist auf Android installierbar (Add to Home Screen)
- [ ] Anwendung ist auf iOS installierbar (Safari: Add to Home Screen)
- [ ] Im Standalone-Modus wird keine Browser-UI angezeigt
- [ ] Statische Assets werden per Cache-First geladen (zweiter Seitenaufruf funktioniert offline fuer die App-Shell)
- [ ] Service-Worker-Update wird dem Nutzer per Banner angezeigt
- [ ] Lighthouse PWA-Score >= 90
- [ ] Keine Regressionen in bestehenden 198 Vitest-Tests

---

### 5.2 Phase 2 — Offline-Kernfunktionen (Abdeckung: R-015 bis R-020, R-048 bis R-054)

**Ziel:** Die kritischsten Offline-Szenarien werden abgedeckt: Messwerte und Bewaesserung im Growraum erfassen, Pflanzenstammdaten offline lesbar.

**Backend-Abhaengigkeit:** B-006, B-007 (Snapshot-Endpoint) — kann aber mit individuellem Caching der bestehenden List-Endpoints umgangen werden.

#### 5.2.1 Neue Dateien

| Datei | Beschreibung |
|-------|-------------|
| `src/frontend/src/offline/db.ts` | Dexie-Instanz mit Schema-Definition und Migrationslogik |
| `src/frontend/src/offline/types.ts` | TypeScript-Interfaces fuer Offline-Eintraege, Sync-Metadaten |
| `src/frontend/src/offline/offlineQueue.ts` | Enqueue/Dequeue-Logik fuer Offline-Eintraege, FIFO-Sortierung |
| `src/frontend/src/offline/stampedCache.ts` | Stammdaten-Cache-Manager (Species, Cultivars, Sites prefetch + TTL) |
| `src/frontend/src/hooks/useConnectivity.ts` | Hook: `navigator.onLine` + `online`/`offline`-Events, Connectivity-State |
| `src/frontend/src/hooks/useOfflineCapable.ts` | Hook: Prueft ob die aktuelle Aktion offline-faehig ist |
| `src/frontend/src/store/slices/offlineSlice.ts` | Redux-Slice: `isOnline`, `pendingCount`, `syncProgress`, `lastSyncAt` |
| `src/frontend/src/components/common/ConnectivityIndicator.tsx` | AppBar-Komponente: gruener/roter Punkt + Badge mit Pending-Count |
| `src/frontend/src/components/common/OfflineGate.tsx` | Wrapper-Komponente: disabled + Tooltip wenn offline und nicht offline-faehig |

#### 5.2.2 Zu aendernde Dateien

| Datei | Aenderung |
|-------|-----------|
| `src/frontend/package.json` | `dexie` als Dependency hinzufuegen |
| `src/frontend/src/api/client.ts` | Axios Request-Interceptor: Bei Offline-Status und schreibendem Request (POST/PUT/PATCH/DELETE) in IndexedDB-Queue umleiten, statt Netzwerkfehler. Response-Interceptor: Bei GET und Offline-Status aus API-Cache laden. |
| `src/frontend/src/store/store.ts` | `offlineSlice` Reducer registrieren |
| `src/frontend/src/App.tsx` | `<ConnectivityIndicator />` in AppBar einbinden, Connectivity-Listener initialisieren |
| `src/frontend/src/auth/AuthProvider.tsx` | Token-Persistierung ueberarbeiten: localStorage statt nur Memory, Offline-Graceful-Degradation (R-050) |
| `src/frontend/src/main.tsx` | IndexedDB-Initialisierung beim App-Start, Stammdaten-Prefetch triggern |

#### 5.2.3 IndexedDB-Schema (Dexie)

```typescript
// src/offline/db.ts — Zielzustand
import Dexie, { type Table } from 'dexie';

export interface PendingEntry {
  id?: number;               // Auto-increment
  entity_type: string;       // z.B. 'feeding_event', 'task_status', 'measurement'
  method: 'POST' | 'PUT' | 'PATCH' | 'DELETE';
  url: string;               // Original-API-URL
  payload: unknown;           // Request-Body
  created_at: string;         // ISO-Timestamp (Client-Zeit)
  sync_status: 'pending' | 'synced' | 'conflict' | 'failed';
  user_id: string;
  retry_count: number;
  last_error?: string;
  server_version?: unknown;   // Bei Konflikt: Server-Daten fuer Vergleich
}

export interface CachedEntity {
  key: string;               // Entity-Key (z.B. Species._key)
  entity_type: string;       // z.B. 'species', 'cultivar', 'site'
  data: unknown;              // Vollstaendiges Entity-JSON
  cached_at: string;         // ISO-Timestamp
}

export interface PhotoQueueEntry {
  id?: number;
  blob: Blob;
  entity_type: string;
  entity_key: string;
  filename: string;
  created_at: string;
  sync_status: 'pending' | 'synced' | 'failed';
  size_bytes: number;
}

export interface SyncMetadata {
  key: string;               // z.B. 'last_sync', 'last_snapshot'
  value: string;
  updated_at: string;
}

class KamerplanterOfflineDB extends Dexie {
  pendingEntries!: Table<PendingEntry>;
  cachedEntities!: Table<CachedEntity>;
  photoQueue!: Table<PhotoQueueEntry>;
  syncMetadata!: Table<SyncMetadata>;

  constructor() {
    super('kamerplanter-offline');
    this.version(1).stores({
      pendingEntries: '++id, entity_type, sync_status, created_at',
      cachedEntities: '[key+entity_type], entity_type, cached_at',
      photoQueue: '++id, entity_type, sync_status',
      syncMetadata: 'key',
    });
  }
}

export const db = new KamerplanterOfflineDB();
```

#### 5.2.4 Offline-faehige vs. Online-only Funktionen

| Offline-faehig (MUSS) | Online-only (initial) |
|---|---|
| Messwerte erfassen (EC, pH, Temperatur, rH) | Neue Pflanzenart anlegen |
| Bewaesserungsereignis erstellen | Companion Planting bearbeiten |
| Problem/Beobachtung melden | Crop Rotation validieren |
| Aufgabe als erledigt markieren | Stammdaten bearbeiten (Name, Taxonomie) |
| Pflanzenstammdaten lesen | Enrichment-Service aufrufen |
| Standort-/Slot-Daten lesen | Reports generieren |
| Kiosk-Startseite & Quick-Actions | Benutzerverwaltung |
| Letzte Messwerte anzeigen (gecacht) | Echtzeit-Sensorwerte |
| Pflege-Erinnerungen lesen (gecacht) | Onboarding-Wizard |
| Tank-Status lesen (gecacht) | Import (CSV-Upload) |

#### 5.2.5 Akzeptanzkriterien Phase 2

- [ ] Dexie-Datenbank wird beim App-Start korrekt initialisiert
- [ ] Messwerte (EC, pH, T, rH) koennen offline erfasst werden
- [ ] Bewaesserungsereignisse koennen offline erstellt werden
- [ ] Aufgaben-Status kann offline aktualisiert werden
- [ ] Offline-Eintraege ueberleben App-Neustart
- [ ] Pflanzenstammdaten (Arten, Sorten) sind offline lesbar
- [ ] Standort-/Slot-Daten sind offline lesbar
- [ ] Connectivity-Indikator zeigt Online/Offline-Status korrekt an
- [ ] Pending-Count im Badge ist aktuell
- [ ] Offline-only-Aktionen sind ausgegraut mit Erklaerungstext
- [ ] JWT-Token bleibt bei kurzem Offline-Intervall erhalten (kein Re-Login noetig)
- [ ] Keine Regressionen in bestehenden Tests

---

### 5.3 Phase 3 — Synchronisation & Benachrichtigungen (Abdeckung: R-021 bis R-027, R-033 bis R-039)

**Ziel:** Offline erfasste Daten werden automatisch synchronisiert. Nutzer hat vollstaendige Transparenz ueber den Sync-Status.

**Backend-Abhaengigkeit:** B-004, B-005 (Bulk-Sync-Endpoint) — optional, funktioniert auch mit sequenziellen Einzel-Requests.

#### 5.3.1 Neue Dateien

| Datei | Beschreibung |
|-------|-------------|
| `src/frontend/src/offline/syncEngine.ts` | Sync-Orchestrator: FIFO-Dequeue, Retry-Logik, Exponential-Backoff, Batch-Support |
| `src/frontend/src/offline/conflictResolver.ts` | Konflikt-Erkennung anhand `updated_at`-Vergleich, Merge-Strategien |
| `src/frontend/src/components/common/SyncProgress.tsx` | Overlay/Snackbar: "Synchronisiere 3/12 Eintraege...", Fortschrittsbalken |
| `src/frontend/src/components/common/ConflictDialog.tsx` | Side-by-Side-Dialog: lokale vs. Server-Version, abweichende Felder markiert |
| `src/frontend/src/components/common/SyncFailedBanner.tsx` | Banner mit "X Eintraege konnten nicht synchronisiert werden — Erneut versuchen" |

#### 5.3.2 Zu aendernde Dateien

| Datei | Aenderung |
|-------|-----------|
| `src/frontend/src/offline/db.ts` | Index auf `retry_count` fuer Failed-Entries-Abfrage |
| `src/frontend/src/store/slices/offlineSlice.ts` | Actions: `syncStarted`, `syncProgress`, `syncCompleted`, `syncFailed`, `conflictDetected` |
| `src/frontend/src/App.tsx` | `<SyncProgress />` und `<SyncFailedBanner />` einbinden, Sync-Trigger bei Online-Wechsel |
| `src/frontend/src/hooks/useConnectivity.ts` | Sync-Engine bei `online`-Event triggern |

#### 5.3.3 Sync-Engine Verhalten

```
Offline-Eintrag erstellt
  └─> IndexedDB: sync_status = 'pending'
       └─> Online-Event empfangen
            └─> SyncEngine.processQueue()
                 ├─> Eintrag 1: POST /api/v1/... → 200 OK → sync_status = 'synced' → Eintrag loeschen
                 ├─> Eintrag 2: PUT /api/v1/... → 412 Precondition Failed → sync_status = 'conflict'
                 │    └─> ConflictDialog oeffnen (lokal vs. Server)
                 │         ├─> "Meine Version" → PUT mit If-Match: * → sync_status = 'synced'
                 │         └─> "Server-Version" → sync_status = 'synced' (verwerfen)
                 └─> Eintrag 3: POST /api/v1/... → 500 → retry_count++ → Exponential Backoff
                      └─> Nach 5 Versuchen: sync_status = 'failed' → SyncFailedBanner
```

#### 5.3.4 Akzeptanzkriterien Phase 3

- [ ] Automatische Synchronisation startet bei Verbindungswiederherstellung
- [ ] Sync-Fortschrittsindikator zeigt korrekten Stand (X/Y Eintraege)
- [ ] Erfolgsmeldung per Snackbar nach abgeschlossener Synchronisation
- [ ] Exponential Backoff bei fehlgeschlagenen Versuchen (1s, 2s, 4s, 8s, max 60s)
- [ ] Nach 5 Fehlversuchen: "failed"-Status + "Erneut versuchen"-Button
- [ ] Statuswechsel-Snackbars (Online <-> Offline) erscheinen zuverlaessig
- [ ] FIFO-Reihenfolge wird eingehalten
- [ ] End-to-End-Test: Offline-Eingabe -> Flugmodus -> Online -> Sync -> Daten auf Server vorhanden

---

### 5.4 Phase 4 — Konflikte & Fotos (Abdeckung: R-028 bis R-032, R-040 bis R-047)

**Ziel:** Fortgeschrittene Szenarien fuer Mehrbenutzer-Betrieb und Foto-Dokumentation. Erst relevant wenn Basis-Sync stabil laeuft.

**Backend-Abhaengigkeit:** B-001, B-002, B-003 (ETag-Support) — zwingend fuer Konflikterkennung.

#### 5.4.1 Neue Dateien

| Datei | Beschreibung |
|-------|-------------|
| `src/frontend/src/offline/photoCompressor.ts` | Canvas-basierte Bildkomprimierung (max 1920px, JPEG 80%) |
| `src/frontend/src/offline/photoSyncer.ts` | Sequenzieller Foto-Upload mit Fortschrittsanzeige |
| `src/frontend/src/components/common/PhotoUploadProgress.tsx` | Pro-Foto-Fortschrittsbalken waehrend Sync |
| `src/frontend/src/components/common/StorageWarning.tsx` | Warnung bei Erreichen der Speicher-Obergrenzen (500 Eintraege, 200 MB Fotos) |

#### 5.4.2 Zu aendernde Dateien

| Datei | Aenderung |
|-------|-----------|
| `src/frontend/src/offline/syncEngine.ts` | ETag/If-Match-Header-Support, 412-Response-Handling mit Konflikt-Erkennung |
| `src/frontend/src/offline/db.ts` | `photoQueue`-Tabelle aktiv nutzen, Gesamtgroesse-Berechnung |
| `src/frontend/src/components/common/PhotoUpload.tsx` | Offline-Fallback: in IndexedDB statt direkter Upload, Komprimierung |
| `src/frontend/src/api/client.ts` | ETag aus GET-Responses extrahieren und mit Entity in IndexedDB speichern |

#### 5.4.3 Akzeptanzkriterien Phase 4

- [ ] Konflikte werden erkannt (412-Response oder updated_at-Vergleich)
- [ ] Konfliktdialog zeigt beide Versionen nebeneinander mit Diff-Hervorhebung
- [ ] Nutzer kann zwischen lokaler und Server-Version waehlen
- [ ] Im Kiosk-Modus: vereinfachter Konfliktdialog (2 Optionen, grosse Touch-Targets)
- [ ] Fotos werden offline in IndexedDB gespeichert
- [ ] Fotos werden komprimiert (max. 1920px, JPEG 80%)
- [ ] Fotos werden bei Sync sequenziell hochgeladen
- [ ] Upload-Fortschritt wird pro Foto angezeigt
- [ ] Warnung bei 500 Offline-Eintraegen
- [ ] Warnung bei 200 MB Foto-Speicher
- [ ] Konflikt-Test: Offline-Aenderung + Server-Aenderung -> Konfliktdialog -> korrekte Aufloesung
- [ ] Foto-Test: 10 Fotos offline -> Sync -> alle Fotos auf Server

---

## 6. Wireframe-Beispiele

### 6.1 Konnektivitaets-Indikator (Online)

```
+--------------------------------------------------------+
|  Kamerplanter              [*] Online             [U]  |
+--------------------------------------------------------+
|                                                        |
|  [Seiteninhalt]                                        |
|                                                        |
+--------------------------------------------------------+
```

### 6.2 Konnektivitaets-Indikator (Offline mit Pending-Eintraegen)

```
+--------------------------------------------------------+
|  Kamerplanter           [!] Offline (3)           [U]  |
+--------------------------------------------------------+
|  +--------------------------------------------------+  |
|  | Offline -- Eingaben werden lokal gespeichert.     |  |
|  |                                          [X]      |  |
|  +--------------------------------------------------+  |
|                                                        |
|  [Seiteninhalt -- Eingabe weiterhin moeglich]          |
|                                                        |
+--------------------------------------------------------+
```

### 6.3 Synchronisations-Fortschritt

```
+--------------------------------------------------------+
|  Kamerplanter           [~] Synchronisiere...     [U]  |
+--------------------------------------------------------+
|  +--------------------------------------------------+  |
|  | Synchronisiere 7/12 Eintraege...                  |  |
|  | ============----------  58%                       |  |
|  +--------------------------------------------------+  |
|                                                        |
|  [Seiteninhalt]                                        |
|                                                        |
+--------------------------------------------------------+
```

### 6.4 Konfliktdialog

```
+--------------------------------------------------------+
|                                                        |
|  +--------------------------------------------------+  |
|  |                                                  |  |
|  |  Konflikt bei Bewaesserungseintrag               |  |
|  |                                                  |  |
|  |  +-----------------+  +-----------------+        |  |
|  |  | Meine Version   |  | Server-Version  |        |  |
|  |  +-----------------+  +-----------------+        |  |
|  |  | EC: *2.1*       |  | EC: *1.8*       |        |  |
|  |  | pH: 6.2         |  | pH: 6.2         |        |  |
|  |  | Menge: *12.5 L* |  | Menge: *10.0 L* |        |  |
|  |  | 14:32 (lokal)   |  | 14:28 (Server)  |        |  |
|  |  +-----------------+  +-----------------+        |  |
|  |                                                  |  |
|  |  Unterschiede: EC, Menge                         |  |
|  |                                                  |  |
|  |  [Meine Version]  [Server-Version]  [Abbrechen]  |  |
|  |                                                  |  |
|  +--------------------------------------------------+  |
|                                                        |
+--------------------------------------------------------+
```

### 6.5 Offline nicht verfuegbare Aktion

```
+--------------------------------------------------------+
|  Kamerplanter           [!] Offline (3)           [U]  |
+--------------------------------------------------------+
|                                                        |
|  Stammdaten > Pflanzenarten                            |
|                                                        |
|  +--------------------------------------------------+  |
|  |  [ + Neue Art anlegen ]  <- ausgegraut            |  |
|  |  "Diese Aktion ist nur online moeglich."          |  |
|  +--------------------------------------------------+  |
|                                                        |
|  +--------------------------------------------------+  |
|  |  Solanum lycopersicum (Tomate)              [>]   |  |  <- lesbar (gecacht)
|  |  Capsicum annuum (Paprika)                  [>]   |  |  <- lesbar (gecacht)
|  |  Ocimum basilicum (Basilikum)               [>]   |  |  <- lesbar (gecacht)
|  +--------------------------------------------------+  |
|                                                        |
+--------------------------------------------------------+
```

### 6.6 Service-Worker-Update-Banner

```
+--------------------------------------------------------+
|  +--------------------------------------------------+  |
|  | Neue Version verfuegbar.                          |  |
|  |            [Jetzt aktualisieren]  [Spaeter]       |  |
|  +--------------------------------------------------+  |
|  Kamerplanter              [*] Online             [U]  |
+--------------------------------------------------------+
|                                                        |
|  [Seiteninhalt]                                        |
|                                                        |
+--------------------------------------------------------+
```

---

## 7. Technologieentscheidungen

### 7.1 IndexedDB-Bibliothek: Dexie

| Kriterium | Dexie | idb |
|-----------|-------|-----|
| API-Komfort | Query-Builder, Live-Queries | Promise-Wrapper, manuell |
| Schema-Versionierung | Eingebaut (`.version().stores()`) | Manuell |
| TypeScript-Support | Exzellent (generische Tabellen) | Gut |
| Bundle-Groesse | ~30 KB gzipped | ~1 KB gzipped |
| Komplexe Abfragen | `.where().between().and()` | Manuelles Cursor-Iterieren |
| Community/Wartung | Aktiv gepflegt, grosse Community | Von Jake Archibald (Google), minimal |

**Entscheidung:** Dexie. Der Query-Builder und die eingebaute Schema-Versionierung sparen erheblich Boilerplate. Die 30 KB Mehraufwand sind im Kontext eines React/MUI-Bundles vernachlaessigbar.

### 7.2 Service Worker Modus: generateSW vs. injectManifest

| Kriterium | generateSW | injectManifest |
|-----------|------------|----------------|
| Konfiguration | Deklarativ in `vite.config.ts` | Eigene `sw.ts`-Datei |
| Flexibilitaet | Standard-Workbox-Strategien | Volle Kontrolle |
| Background Sync | Workbox-Plugin | Manuell implementierbar |
| Custom Logic | Eingeschraenkt | Beliebig |

**Entscheidung Phase 1:** `generateSW` — schnellster Weg zur funktionierenden PWA. Ausschliesslich deklarative Konfiguration in `vite.config.ts`.

**Entscheidung Phase 3:** Migration zu `injectManifest`, wenn Background Sync oder Custom-Sync-Logik im Service Worker noetig wird.

### 7.3 Offline-Queue vs. Axios-Interceptor

Die Offline-Queue wird als **Axios-Request-Interceptor** in `src/api/client.ts` implementiert:

1. Request-Interceptor prueft `navigator.onLine`
2. Bei schreibendem Request (POST/PUT/PATCH/DELETE) und Offline-Status:
   - Request wird **nicht** an das Netzwerk gesendet
   - Stattdessen wird ein `PendingEntry` in IndexedDB erstellt
   - Der Interceptor returned eine synthetische Success-Response (optimistisches UI)
3. Bei lesendem Request (GET) und Offline-Status:
   - Zuerst im API-Cache (Service Worker) suchen
   - Dann in IndexedDB-Cache (Stammdaten) suchen
   - Wenn nichts gefunden: Offline-Fehlermeldung

**Vorteil:** Alle bestehenden API-Aufrufe (~150 Endpoints) profitieren automatisch, ohne Aenderung an den einzelnen Seiten/Slices.

---

## 8. Abhaengigkeitsmatrix

```
Phase 1 (PWA-Install)
  |
  v
Phase 2 (Offline-Kern) -----> Backend: B-006, B-007 (optional)
  |
  v
Phase 3 (Sync) -----> Backend: B-004, B-005 (optional)
  |
  v
Phase 4 (Konflikte & Fotos) -----> Backend: B-001, B-002, B-003 (zwingend)
```

| Phase | Abhaengig von | Blockiert | Backend noetig |
|-------|--------------|-----------|----------------|
| Phase 1 | Nichts | Phase 2, 3, 4 | Nein |
| Phase 2 | Phase 1 | Phase 3 | Optional (Snapshot-Endpoint) |
| Phase 3 | Phase 2 | Phase 4 | Optional (Bulk-Sync) |
| Phase 4 | Phase 3 | Nichts | Zwingend (ETag-Support) |

---

## 9. Risiken

| Risiko | Auswirkung | Wahrscheinlichkeit | Mitigation |
|---|---|---|---|
| **App im Growraum unbrauchbar** | Kein Mobilfunkempfang im Keller, keine Dateneingabe moeglich | Sehr hoch | Service Worker + IndexedDB fuer Offline-Kernfunktionen |
| **Datenverlust bei Verbindungsabbruch** | Eingaben gehen verloren, wenn die Verbindung mitten in einer Aktion abbricht | Hoch | Lokale Zwischenspeicherung vor API-Call, Retry-Mechanismus |
| **Veraltete Daten angezeigt** | Cache zeigt alte Werte, obwohl zwischenzeitlich aktualisiert wurde | Mittel | 15-Minuten-TTL, Network-First fuer API-Calls, Refresh-Button |
| **Sync-Konflikte** | Mehrere Nutzer aendern denselben Datensatz offline | Mittel | Versionsstempel-basierte Konflikterkennung, explizite Nutzerentscheidung |
| **IndexedDB-Speicher voll** | Zu viele Offline-Eintraege oder zu viele Fotos | Niedrig | Obergrenzen (500 Eintraege, 200 MB Fotos), Warnungen |
| **Service-Worker-Cache veraltet** | Nutzer sieht alte Version der App trotz neuem Deployment | Mittel | Update-Banner, Skip-Waiting-Strategie |
| **iOS-PWA-Einschraenkungen** | Safari unterstuetzt Background Sync nicht, Push nur eingeschraenkt | Hoch | Fallback: Manueller Sync-Button, Sync bei App-Start |
| **JWT-Ablauf waehrend Offline** | Access Token (15 min) laeuft im Growraum ab | Hoch | Token-Persistierung, automatischer Refresh bei Reconnect (R-049) |
| **IndexedDB in Inkognito-Modus** | Manche Browser loeschen IndexedDB-Daten beim Schliessen des Inkognito-Fensters | Niedrig | Warnung anzeigen wenn Inkognito erkannt wird |
| **Optimistisches UI bei spaeterem Server-Fehler** | Nutzer denkt Aktion war erfolgreich, Server lehnt spaeter ab | Mittel | Sync-Ergebnis immer anzeigen, bei Fehler deutliche Benachrichtigung |

---

## 10. Neue NPM-Abhaengigkeiten

| Paket | Typ | Version | Groesse (gzipped) | Begruendung |
|-------|-----|---------|-------------------|-------------|
| `vite-plugin-pwa` | devDependency | >= 0.21 | Build-only | PWA-Integration in Vite, Workbox-Konfiguration |
| `dexie` | dependency | >= 4.0 | ~30 KB | IndexedDB-ORM mit Query-Builder und Schema-Versionierung |

---

## 11. i18n-Keys (Neue Uebersetzungen)

Alle neuen UI-Texte MUESSEN in `src/i18n/locales/de/translation.json` und `src/i18n/locales/en/translation.json` unter dem Namespace `pwa.*` hinzugefuegt werden:

```
pwa.online                    → "Online" / "Online"
pwa.offline                   → "Offline" / "Offline"
pwa.offlineBanner             → "Offline -- Eingaben werden lokal gespeichert." / "Offline -- entries saved locally."
pwa.onlineBanner              → "Online -- Synchronisation startet..." / "Online -- synchronization starting..."
pwa.syncProgress              → "Synchronisiere {{current}}/{{total}} Eintraege..." / "Syncing {{current}}/{{total}} entries..."
pwa.syncComplete              → "{{count}} Eintraege synchronisiert." / "{{count}} entries synced."
pwa.syncFailed                → "{{count}} Eintraege konnten nicht synchronisiert werden." / "{{count}} entries failed to sync."
pwa.retrySync                 → "Erneut versuchen" / "Retry"
pwa.updateAvailable           → "Neue Version verfuegbar." / "New version available."
pwa.updateNow                 → "Jetzt aktualisieren" / "Update now"
pwa.updateLater               → "Spaeter" / "Later"
pwa.installApp                → "App installieren" / "Install app"
pwa.onlineOnly                → "Diese Aktion ist nur online moeglich." / "This action requires an internet connection."
pwa.conflictTitle             → "Konflikt erkannt" / "Conflict detected"
pwa.conflictMyVersion         → "Meine Version" / "My version"
pwa.conflictServerVersion     → "Server-Version" / "Server version"
pwa.conflictCancel            → "Abbrechen" / "Cancel"
pwa.conflictDifferences       → "Unterschiede: {{fields}}" / "Differences: {{fields}}"
pwa.storageWarningEntries     → "{{count}}/500 Offline-Eintraege. Bitte synchronisieren." / "{{count}}/500 offline entries. Please sync."
pwa.storageWarningPhotos      → "Foto-Speicher: {{mb}}/200 MB. Bitte synchronisieren." / "Photo storage: {{mb}}/200 MB. Please sync."
pwa.pendingCount              → "{{count}} ausstehend" / "{{count}} pending"
```

---

## 12. Testing-Strategie

### 12.1 Unit-Tests (Vitest)

| Modul | Testfokus |
|-------|-----------|
| `offline/db.ts` | Schema-Erstellung, Migration, CRUD-Operationen |
| `offline/offlineQueue.ts` | Enqueue/Dequeue, FIFO-Reihenfolge, Status-Transitions |
| `offline/syncEngine.ts` | Retry-Logik, Exponential-Backoff-Berechnung, Konflikt-Erkennung |
| `offline/photoCompressor.ts` | Komprimierung, Max-Dimensionen, JPEG-Qualitaet |
| `hooks/useConnectivity.ts` | Online/Offline-Events, Debouncing |
| `store/slices/offlineSlice.ts` | Reducer-Tests: pendingCount, syncProgress |
| `api/client.ts` (Interceptor) | Offline-Queuing, Cache-Fallback |

### 12.2 Integrations-Tests

| Szenario | Beschreibung |
|----------|-------------|
| Offline-Roundtrip | Offline-Eintrag erstellen -> IndexedDB pruefen -> Online simulieren -> API-Mock antwortet 200 -> Eintrag geloescht |
| Conflict-Roundtrip | Offline-Eintrag erstellen -> Online simulieren -> API-Mock antwortet 412 -> Konflikt-State pruefen |
| Token-Expiry | Token ablaufen lassen -> Offline simulieren -> Online simulieren -> Refresh-Request pruefen |

### 12.3 End-to-End-Tests (Manuell + Lighthouse)

| Test | Beschreibung |
|------|-------------|
| E2E-Offline-Sync | Offline-Eingabe -> Flugmodus -> Online -> Sync -> Daten auf Server vorhanden |
| E2E-Konflikt | Offline-Aenderung + Server-Aenderung -> Konfliktdialog -> korrekte Aufloesung |
| E2E-Stress | 100+ Offline-Eintraege -> Sync -> alle korrekt uebertragen |
| E2E-Foto | 10 Fotos offline -> Sync -> alle Fotos auf Server |
| Lighthouse PWA-Audit | Score >= 90, alle PWA-Checks bestanden |
| Device-Test | Chrome DevTools Throttling + Flugmodus auf echten Android/iOS-Geraeten |

---

**Dokumenten-Ende**

**Version**: 2.0
**Status**: Entwurf
**Letzte Aktualisierung**: 2026-03-01
**Review**: Pending
**Genehmigung**: Pending
**Aenderungshistorie**:
- v1.0 (2026-02-28): Initiale Anforderungen (47 Regeln, 4 Phasen)
- v1.1 (2026-02-28): Implementierungsprioritaet & MVP-Scope ergaenzt (Frontend-Design-Review K-003)
- v2.0 (2026-03-01): Major-Update — IST-Analyse, Strategische PWA-vs-Flutter-Entscheidung, Backend-Voraussetzungen (ETag, Bulk-Sync, Snapshot), Auth-Token-Persistierung (R-048 bis R-051), Redux-Integration (R-052 bis R-054), Datei-fuer-Datei-Implementierungsplan, IndexedDB-Schema (Dexie), Technologieentscheidungen, Abhaengigkeitsmatrix, i18n-Keys, Testing-Strategie
