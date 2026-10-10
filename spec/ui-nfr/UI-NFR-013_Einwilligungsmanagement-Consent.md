---

ID: UI-NFR-013
Titel: Einwilligungsmanagement (Consent)
Kategorie: UI-Verhalten Unterkategorie: Datenschutz, Einwilligung, TTDSG
Technologie: React, TypeScript, MUI 9
Status: Entwurf
Priorität: Hoch
Version: 1.2 (#2174/#2175: Widerruf serverseitiger Einwilligungen im Tab, Erteilung am Ort der Funktion — §5.3; 1.1 #2159: Banner eingebunden, Sentry-Gate im Browser, `useConsent`, Widerrufsschalter)
Autor: Business Analyst - Agrotech
Datum: 2026-02-27
Tags: [consent, cookie-banner, ttdsg, dsgvo, privacy, sentry, tracking, einwilligung]
Abhängigkeiten: [REQ-025, NFR-001, UI-NFR-006]
Betroffene Module: [Frontend]
---

# UI-NFR-013: Einwilligungsmanagement (Consent)

> **Referenz:** SEC-M-007 (IT-Security-Review)

## 1. Business Case

### 1.1 User Stories

**Als** Nutzer der Anwendung
**möchte ich** beim ersten Besuch transparent informiert werden, welche Daten erhoben werden und wofür
**um** eine informierte Entscheidung über optionale Datenverarbeitungen treffen zu können.

**Als** Nutzer
**möchte ich** meine Einwilligung jederzeit widerrufen können
**um** mein Recht nach Art. 7 Abs. 3 DSGVO wahrzunehmen, ohne dass mir Nachteile entstehen.

**Als** Betreiber der Anwendung
**möchte ich** dass die Einwilligungsverwaltung rechtssicher umgesetzt ist
**um** die Anforderungen des TTDSG § 25 und der DSGVO Art. 7 zu erfüllen.

### 1.2 Geschäftliche Motivation

Das Telemediengesetz (TTDSG) § 25 regelt die Speicherung von und den Zugriff auf Informationen auf Endgeräten. Die DSGVO Art. 7 stellt Anforderungen an die Einwilligung. Kamerplanter verwendet mehrere Technologien, die unter diese Regelungen fallen:

1. **Sentry Error Tracking** — überträgt Fehler-Reports an einen externen Dienst (potenziell US)
2. **Sentry Session Replay** — zeichnet Nutzerinteraktionen auf
3. **HaveIBeenPwned API** — sendet SHA-1-Prefix des Passworts an externen Dienst
4. **Externe Stammdatenanreicherung** (REQ-011) — kontaktiert GBIF, Perenual etc.

Ohne rechtskonformes Einwilligungsmanagement drohen Bußgelder nach DSGVO Art. 83 (bis 4 % des Jahresumsatzes) und Abmahnungen nach TTDSG.

---

## 2. Rechtsgrundlagen

### 2.1 Abgrenzung: Technisch notwendig vs. einwilligungspflichtig

**Technisch notwendig (keine Einwilligung erforderlich):**

| Speicherung | Zweck | Rechtsgrundlage |
|-------------|-------|----------------|
| Refresh-Token Cookie (`HttpOnly`, `Secure`, `SameSite=Lax`) | Authentifizierung (REQ-023) | TTDSG § 25 Abs. 2 Nr. 2 — unbedingt erforderlich |
| CSRF-Cookie (Double-Submit, REQ-023 v1.2) | Sicherheit | TTDSG § 25 Abs. 2 Nr. 2 |
| `localStorage`: Sprache (`i18nextLng`) | Spracheinstellung (UI-NFR-007) | TTDSG § 25 Abs. 2 Nr. 2 |
| `localStorage`: Theme (`theme-mode`) | Light/Dark-Modus | TTDSG § 25 Abs. 2 Nr. 2 |
| `localStorage`: Tenant-Auswahl (`active-tenant`) | Mandantenkontext (REQ-024) | TTDSG § 25 Abs. 2 Nr. 2 |
| `localStorage`: Kiosk-Modus-Präferenz (UI-NFR-019) | Betriebsmodus | TTDSG § 25 Abs. 2 Nr. 2 |
| Session-State (Redux, In-Memory) | Anwendungsbetrieb | Kein Endgerätzugriff |

**Einwilligung erforderlich:**

| Verarbeitung | Consent-Kategorie | Rechtsgrundlage |
|-------------|-------------------|----------------|
| Sentry Error Tracking | `error_tracking` | DSGVO Art. 6 Abs. 1 lit. a (Einwilligung) — Datenübermittlung an Drittanbieter |
| Sentry Session Replay | `error_tracking` (Sub-Option) | DSGVO Art. 6 Abs. 1 lit. a — Aufzeichnung von Nutzerverhalten |
| HaveIBeenPwned Passwortprüfung | `external_services` | DSGVO Art. 6 Abs. 1 lit. a — k-Anonymity-Hash an externen Dienst |
| Externe Stammdatenanreicherung (REQ-011) | `external_services` | DSGVO Art. 6 Abs. 1 lit. a — Server-seitige API-Aufrufe zu GBIF, Perenual etc. |

---

## 3. Anforderungen

### 3.1 Consent-Banner

| # | Regel | Stufe |
|---|-------|-------|
| CB-001 | Beim ersten Besuch eines neuen Nutzers MUSS ein Consent-Banner angezeigt werden. **Ausnahme:** Im Light-Modus (REQ-027, `KAMERPLANTER_MODE=light`) entfaellt das Consent-Banner, da die DSGVO-Haushaltsausnahme (Art. 2 Abs. 2 lit. c) greift. Die externe Stammdatenanreicherung (REQ-011) ist im Light-Modus standardmaessig deaktiviert; bei manueller Aktivierung (`ENABLE_ENRICHMENT_LIGHTMODE=true`) MUSS ein einmaliges Opt-in-Modal angezeigt werden. <!-- Quelle: Widerspruchsanalyse W-002, W-008 --> | MUSS |
| CB-002 | Das Banner MUSS **minimal-invasiv** gestaltet sein: als Bottom-Sheet oder Inline-Banner, NICHT als Fullscreen-Overlay oder Modal, das die gesamte Seite blockiert. | MUSS |
| CB-003 | Das Banner MUSS eine Schaltfläche „Alle akzeptieren" und eine Schaltfläche „Nur Notwendige" gleichwertig (gleiche visuelle Prominenz) anbieten. | MUSS |
| CB-004 | Das Banner MUSS eine Schaltfläche „Einstellungen" anbieten, die die Kategorie-Auswahl öffnet. | MUSS |
| CB-005 | Die Anwendung MUSS ohne Einwilligung in optionale Kategorien voll funktionsfähig bleiben. Kein Feature DARF von optionaler Einwilligung abhängig sein, es sei denn, es ist ein reines Analyse-/Tracking-Feature. | MUSS |
| CB-006 | Das Banner DARF NICHT erneut erscheinen, wenn der Nutzer bereits eine Auswahl getroffen hat (bis zum Widerruf oder Ablauf). | MUSS |

### 3.2 Consent-Kategorien

| # | Regel | Stufe |
|---|-------|-------|
| CK-001 | Die Kategorie **„Notwendig"** MUSS immer aktiv und NICHT abwählbar sein. Sie umfasst: Auth-Cookies, CSRF, Sprache, Theme, Tenant-Auswahl, Session-State. | MUSS |
| CK-002 | Die Kategorie **„Fehleranalyse"** (`error_tracking`) MUSS separat einwilligungsfähig sein. Sie umfasst: Sentry Error Tracking, Sentry Session Replay. | MUSS |
| CK-003 | Die Kategorie **„Externe Dienste"** (`external_services`) MUSS separat einwilligungsfähig sein. Sie umfasst: HaveIBeenPwned Passwortprüfung, Externe Stammdatenanreicherung (REQ-011). | MUSS |
| CK-004 | Jede Kategorie MUSS eine verständliche Beschreibung enthalten, die erklärt, welche Daten wohin übertragen werden. | MUSS |

### 3.3 Consent-Persistierung

| # | Regel | Stufe |
|---|-------|-------|
| CP-001 | Für **authentifizierte Nutzer** MUSS der Consent-Status über die REQ-025 ConsentEngine (`POST /api/v1/privacy/consents`) serverseitig gespeichert werden. | MUSS |
| CP-002 | Für **nicht-authentifizierte Nutzer** (vor Login/Registrierung) MUSS der Consent-Status in `localStorage` gespeichert werden. | MUSS |
| CP-003 | Bei der Registrierung/Login MUSS der localStorage-Consent mit dem serverseitigen Consent synchronisiert werden. Serverseitiger Consent hat Vorrang bei Konflikten. | MUSS |
| CP-004 | Der Consent-Status MUSS mindestens enthalten: Kategorie, Entscheidung (granted/denied), Zeitstempel, Version der Consent-Texte. | MUSS |

### 3.4 Consent-Widerruf

| # | Regel | Stufe |
|---|-------|-------|
| CW-001 | Nutzer MÜSSEN ihre Einwilligung jederzeit widerrufen können — über die Datenschutz-Einstellungen im Profil-Bereich. | MUSS |
| CW-002 | Der Widerruf MUSS genauso einfach sein wie die Erteilung (Art. 7 Abs. 3 DSGVO). | MUSS |
| CW-003 | Bei Widerruf von „Fehleranalyse" MUSS Sentry **sofort** deaktiviert werden (kein Nachladen, kein Tracking bis zur nächsten Initialisierung). | MUSS |
| CW-004 | Bei Widerruf von „Externe Dienste" MUSS die HIBP-Prüfung bei Passwortänderung/-erstellung deaktiviert werden und die automatische Stammdatenanreicherung (REQ-011) ausgesetzt werden. | MUSS |
| CW-005 | Der Widerruf MUSS über `DELETE /api/v1/privacy/consents/{purpose}` (REQ-025) an das Backend propagiert werden. | MUSS |

### 3.5 Consent-gesteuerte Initialisierung

| # | Regel | Stufe |
|---|-------|-------|
| CI-001 | Sentry (`@sentry/react`) DARF ERST initialisiert werden (`Sentry.init()`), wenn die Einwilligung für `error_tracking` vorliegt. | MUSS |
| CI-002 | Vor Einwilligung DARF KEIN Sentry-SDK-Code geladen werden, der Daten erhebt oder überträgt. | MUSS |
| CI-003 | Die Anwendung MUSS einen **ConsentProvider** (React Context) bereitstellen, der den aktuellen Consent-Status hält und als Gate für optionale Features dient. | MUSS |
| CI-004 | Hooks wie `useConsent('error_tracking')` MÜSSEN verfügbar sein, damit Komponenten consent-abhängig rendern können. | SOLL |

---

## 4. UI-Design

### 4.1 Banner-Layout

```
┌──────────────────────────────────────────────────────────────┐
│  Diese Anwendung verwendet optionale Dienste zur Fehler-     │
│  analyse und Anbindung externer Datenquellen.                │
│                                                              │
│  [Einstellungen]    [Nur Notwendige]    [Alle akzeptieren]   │
└──────────────────────────────────────────────────────────────┘
```

- Position: Bottom-Sheet, fixiert am unteren Bildschirmrand
- Design: Gemäß UI-NFR-006 Design System (MUI 7 Komponenten)
- Responsive: Auf Mobile werden die Buttons vertikal gestapelt (UI-NFR-001)
- Barrierefreiheit: `role="dialog"`, `aria-label`, Fokus-Management (UI-NFR-002)

### 4.2 Einstellungen-Dialog

```
┌──────────────────────────────────────────────────────────────┐
│  Datenschutz-Einstellungen                              [×]  │
│                                                              │
│  ☑ Notwendig (immer aktiv)                          [locked] │
│    Auth-Cookies, Spracheinstellung, Theme, Session           │
│                                                              │
│  ☐ Fehleranalyse                                    [toggle] │
│    Fehler-Reports werden an Sentry gesendet, um die          │
│    Stabilität der Anwendung zu verbessern.                   │
│    Datenempfänger: Sentry (EU/Self-Hosted)                   │
│                                                              │
│  ☐ Externe Dienste                                  [toggle] │
│    Passwortprüfung (HaveIBeenPwned) und automatische         │
│    Anreicherung botanischer Stammdaten (GBIF, Perenual).     │
│    Datenempfänger: HaveIBeenPwned (UK), GBIF (DK),          │
│    Perenual (US)                                             │
│                                                              │
│              [Auswahl speichern]                             │
└──────────────────────────────────────────────────────────────┘
```

- Realisierung: MUI `Dialog` oder `Drawer`
- Toggles: MUI `Switch` mit Label
- „Notwendig" ist ausgegraut (disabled, checked)
- i18n: Texte in DE/EN (UI-NFR-007), Schlüssel: `pages.consent.*`

---

## 5. Technische Architektur

### 5.1 ConsentProvider

```typescript
// Konzeptuelle Struktur (illustrativ)
interface ConsentState {
  necessary: true;                    // immer true
  error_tracking: boolean | null;     // null = noch nicht entschieden
  external_services: boolean | null;
  timestamp: string | null;
  version: string;                    // Version der Consent-Texte
}
```

- `null` = Banner muss angezeigt werden
- `true`/`false` = Nutzer hat entschieden
- Provider liest initialen State aus localStorage (unauthentifiziert) oder API (authentifiziert)

### 5.2 Sentry-Gate

Sentry wird nur bei `error_tracking === true` initialisiert:

```typescript
// Konzeptuelle Struktur (illustrativ)
function SentryGate({ children }: { children: React.ReactNode }) {
  const { consent } = useConsent();

  useEffect(() => {
    if (consent.error_tracking === true) {
      Sentry.init({ /* ... */ });
    } else {
      // Sentry deaktivieren falls bereits initialisiert
      Sentry.close();
    }
  }, [consent.error_tracking]);

  return <>{children}</>;
}
```

### 5.3 Umsetzungsstand (#2159, 2026-10-09)

- **CI-001/CI-002/CW-003 umgesetzt:** `src/frontend/src/observability/errorTracking.ts` lädt `@sentry/react` (ein einziger dynamischer Import je Seite) und ruft `Sentry.init()` nur, wenn `error_tracking === true` ist und nicht der Light-Modus läuft; `null` (unentschieden) und `false` gelten als nein. Das Modul abonniert den Consent-Speicher einmal: eine spätere Zustimmung startet das SDK ohne Neuladen. Ein Widerruf (auch aus einem anderen Tab, `storage`-Ereignis) setzt den Client **synchron** auf `enabled = false`, leert die Breadcrumbs von Isolation- und Current-Scope (`Scope#clear()` gibt es in SDK 11 nicht mehr) und ruft danach `Sentry.close(2000)`; `beforeSend` und `beforeBreadcrumb` prüfen die Einwilligung zuerst und verwerfen sonst (`null`). Grund (gemessen in `@sentry/core` 11.4.0, `client.js`): `close(timeout)` wartet erst `flush(timeout)` ab und setzt `enabled = false` danach, und `_isClientDoneProcessing` behandelt `0` als unbegrenzt (`while (!timeout || ticked < timeout)`); `addBreadcrumb` prüft nur, ob ein Client existiert (`breadcrumbs.js`). Ohne DSN abonniert das Modul nichts und lädt nichts.
- **CI-003 abweichend, CI-004 umgesetzt:** Statt eines React-Context hält ein React-freies Modul (`src/frontend/src/observability/consent.ts`, Schlüssel `kamerplanter:consent:v1`) den Zustand, weil das Sentry-Gate vor dem ersten Render entscheiden muss. `useConsent()` (`src/frontend/src/hooks/useConsent.ts`, `useSyncExternalStore`) liefert `{ consent, setConsent }`; `consent.error_tracking` ersetzt die Form `useConsent('error_tracking')` aus §3.5.
- **CB-001 mit DSN-Bedingung:** Das Banner ist im App-Shell eingebunden (`AppConsentBanner`, außerhalb des Routers, also auch auf Anmelde- und Registrierungsseite) und erscheint nur, wenn **eine `SENTRY_DSN` konfiguriert ist** und nicht der Light-Modus läuft. Begründung: Browser-Fehler-Tracking ist die einzige Verarbeitung, die diese Entscheidung schaltet — `external_services` liest seit REQ-025 v1.31 (#2136) kein Code mehr, und der Abgleich mit der ConsentEngine (CP-001/CP-003/CW-005) fehlt noch. Ohne DSN würde das Banner eine wirkungslose Einwilligung einholen. Kommt eine weitere Kategorie oder der Server-Abgleich, wird die Bedingung zu „eine Kategorie, die die Entscheidung schaltet, ist aktiv".
- **Light-Modus:** kein Banner (CB-001), und der Tracker startet dort auch mit einer gespeicherten Zustimmung nicht (etwa nach einem Wechsel von `full` auf `light`) — durchgesetzt in `trackingPermitted()`, nicht nur über das fehlende Banner. Der Widerrufsschalter ist im Light-Modus folgerichtig ausgeblendet.
- **CB-003/CB-004:** „Nur Notwendige" und „Alle akzeptieren" haben dieselbe Button-Variante; „Einstellungen" klappt die Kategorie-Auswahl im Banner auf (nur `error_tracking`, siehe oben).
- **Banner-Darstellung:** `zIndex` = `modal - 1` (über Seiteninhalt, unter Dialogen, Drawern und Snackbars), Abstand unten inkl. `env(safe-area-inset-bottom)`, Höhe max. `100dvh - 32px`, Touch-Ziele mind. 44 px. „Einstellungen“ bleibt beim Aufklappen fokussiert und trägt `aria-expanded`/`aria-controls`.
- **CW-001/CW-002 im Browser:** Datenschutz → Einwilligungen trägt den Schalter „Fehleranalyse erlauben", der denselben Speicher schreibt.
- **CW-001/CW-002/CW-005 für serverseitige Zwecke (#2174, #2175):** Datenschutz → Einwilligungen rendert die Zwecke aus `GET /api/v1/privacy/consents` und trägt bei jedem erteilten, nicht verpflichtenden Zweck die Schaltfläche „Widerrufen“ (`DELETE /api/v1/privacy/consents/{purpose}`, `data-testid="consent-revoke-<purpose>"`); ein neuer Zweck des Backends erscheint dort ohne Frontend-Änderung. Erteilt wird nicht im Tab, sondern am Ort der Funktion, mit dem Text, was übertragen wird: Pflanzenerkennung (`plant_identification`, Gate vor der Aufnahme), KI-Seite (`ai_knowledge_question`, Gate nach `403 CONSENT_REQUIRED`, danach wird die Frage erneut gesendet), Schalter „Als Referenzbild für die Erkennung nutzen“ (`reference_contribution`: der Schalter **ist** die Einwilligung; beim Speichern wird sie vor dem Beitrag erteilt, ein Fehlschlag bricht das Speichern sichtbar ab). Im Light-Modus gibt es keine serverseitigen Einwilligungen: Die KI-Seite fragt dort nicht, der Referenzschalter ist ausgeblendet. **Offen:** `pest_reference_contribution` (Schädlings-Erkennungsindex, REQ-044 v1.4) erscheint im Tab und ist dort widerrufbar, hat aber noch keinen Erteilungsort in der Oberfläche (naheliegend: der Bild-Beitrag auf der Schädlings-Detailseite); bis dahin nur über `POST /api/v1/privacy/consents`.
- **Speicher verweigert das Schreiben** (Quota, gesperrter Storage): Die Entscheidung dieser Seite gilt im Speicher und gewinnt über einen noch lesbaren älteren Wert, bis ein Schreiben gelingt oder ein anderer Tab eine neuere Entscheidung speichert. Ein Widerruf bleibt so ein Widerruf; eine aktiv erteilte Zustimmung gilt bis zum Neuladen, danach fragt das Banner erneut. Gewählt statt „vor dem Schreiben löschen“, weil das bei einem Fehlschlag eine nie getroffene Ablehnung erzeugt und selbst vom Gelingen von `removeItem` abhängt.
- **Offen:** CP-001/CP-003/CW-005 (Server-Abgleich über `POST/DELETE /api/v1/privacy/consents`); die Browser-Entscheidung gilt bis dahin nur in diesem Browser und ist unabhängig von der serverseitigen Einwilligung `error_tracking`, die den `user`-Block der Backend-Ereignisse steuert (NFR-001 SE-006). Session Replay (SE-003) ist nicht aktiviert.
- **Regressionszäune (kein Beleg des Gates — der Beleg sind die Verhaltenstests in `errorTracking.test.ts` und `errorTrackingChunkLoad.test.ts`):** `src/frontend/src/test/guards/trackerSdkBehindConsent.test.ts` lässt Tracker-Pakete und -Hosts (inkl. GlitchTip) in App-Quellen (`ts/tsx/js/jsx/mjs`), `index.html` und `public/` nur in `errorTracking.ts` zu; kein statischer Value-Import (auch mehrzeilig) in irgendeiner App-Quelle; genau ein `import('@sentry/…')` im Loader; `startErrorTracking(` nur hinter `if (trackingPermitted())`; Tracker-Abhängigkeiten in `dependencies`, `devDependencies`, `peerDependencies` und `optionalDependencies` nur mit Eintrag in der Liste des Zauns.

---

## 6. Abhängigkeiten

| Abhängigkeit | Typ | Begründung |
|-------------|-----|-----------|
| REQ-025 (DSGVO Betroffenenrechte) | Fachlich | ConsentEngine Backend: `POST/DELETE /api/v1/privacy/consents` |
| NFR-001 §8.3 (Sentry) | Technisch | Sentry-Initialisierung ist consent-gesteuert |
| UI-NFR-006 (Design System) | Design | MUI 9 Komponenten für Banner und Dialog |
| UI-NFR-007 (i18n) | Übersetzung | Consent-Texte in DE/EN |
| UI-NFR-002 (Barrierefreiheit) | Barrierefreiheit | Fokus-Management, ARIA-Attribute |

---

## 7. Akzeptanzkriterien

### Definition of Done

- [ ] **Banner**
    - [ ] Consent-Banner erscheint beim ersten Besuch eines neuen Nutzers
    - [ ] Banner ist minimal-invasiv (Bottom-Sheet, kein Fullscreen-Overlay)
    - [ ] „Alle akzeptieren" und „Nur Notwendige" sind gleichwertig dargestellt
    - [ ] „Einstellungen" öffnet Kategorie-Auswahl
    - [ ] Banner verschwindet nach Auswahl und erscheint nicht erneut

- [ ] **Kategorien**
    - [ ] „Notwendig" ist immer aktiv und nicht abwählbar
    - [ ] „Fehleranalyse" und „Externe Dienste" sind separat einwilligungsfähig
    - [ ] Jede Kategorie hat verständliche Beschreibung mit Datenempfänger

- [ ] **Consent-gesteuerte Initialisierung**
    - [ ] Sentry wird ERST nach Einwilligung initialisiert (`error_tracking`)
    - [ ] Ohne Einwilligung wird kein Sentry-SDK-Code geladen, der Daten erhebt
    - [ ] Consent-Widerruf deaktiviert Sentry sofort

- [ ] **Persistierung & Synchronisation**
    - [ ] Unauthentifiziert: Consent in localStorage gespeichert
    - [ ] Authentifiziert: Consent über REQ-025 API synchronisiert
    - [ ] Login synchronisiert localStorage → Server-Consent

- [ ] **Widerruf**
    - [ ] Consent-Widerruf jederzeit über Datenschutz-Einstellungen möglich
    - [ ] Widerruf ist genauso einfach wie Erteilung
    - [ ] Widerruf propagiert über API an Backend

- [ ] **Barrierefreiheit & i18n**
    - [ ] Banner hat `role="dialog"` und korrekte ARIA-Attribute
    - [ ] Texte in DE und EN verfügbar
    - [ ] Responsive Layout (Mobile: Buttons vertikal)

---

**Dokumenten-Ende**

**Version**: 1.1
**Status**: Entwurf
**Letzte Aktualisierung**: 2026-10-09
**Review**: Pending
**Genehmigung**: Pending
