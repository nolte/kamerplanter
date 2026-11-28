---

ID: UI-NFR-013
Titel: Einwilligungsmanagement (Consent)
Kategorie: UI-Verhalten Unterkategorie: Datenschutz, Einwilligung, TTDSG
Technologie: React, TypeScript, MUI 9
Status: Entwurf
Priorität: Hoch
Version: 1.3 (#3025 N-40: eigener Zweck `browser_error_reports` für Browser-Fehlerberichte, Gerät/Konto-Abgleich mit Fälle-Tabelle §5.4, Kategorie „Externe Dienste“ gestrichen — Betreiberentscheidungen 2026-11-27); 1.2 (#2174/#2175: Widerruf serverseitiger Einwilligungen im Tab, Erteilung am Ort der Funktion — §5.3; 1.1 #2159: Banner eingebunden, Sentry-Gate im Browser, `useConsent`, Widerrufsschalter)
Autor: Business Analyst - Agrotech
Datum: 2026-02-27
Tags: [consent, cookie-banner, ttdsg, dsgvo, privacy, sentry, tracking, einwilligung]
Abhängigkeiten: [REQ-025, NFR-001, UI-NFR-006]
Betroffene Module: [Frontend]
---

# UI-NFR-013: Einwilligungsmanagement (Consent)

> **Referenz:** SEC-M-007 (IT-Security-Review)

## 0. Änderungen

| Version | Datum | Änderung |
|---|---|---|
| 1.3 | 2026-11-28 | **#3025 N-40, Betreiberentscheidungen 2026-11-27.** (1) Browser-Fehlerberichte haben einen **eigenen** Einwilligungszweck `browser_error_reports` (REQ-025 v1.41 §3.6); der Server-Zweck `error_tracking` (Zuordnung von Backend-Ereignissen zum Konto) bleibt in Name und Text unverändert, bestehende Konto-Einwilligungen behalten ihre Bedeutung. (2) Eine nur im Browser gespeicherte Zustimmung — auch eine aus der Zeit vor dieser Version oder von vor der Anmeldung — wird **nie** als Konto-Einwilligung verbucht; nach der Umstellung fragt die App einmal neu (CP-005). (3) Eine Ablehnung ohne Anmeldung gilt für dieses Gerät und wird durch keine Zustimmung überstimmt; sie widerruft keine Konto-Einwilligung (CP-007). (4) Die Kategorie „Externe Dienste“ (`external_services`) ist gestrichen: Es gibt keine Verarbeitung dahinter (CK-003, CW-004 entfallen; §1.2, §2.1, §4.2, §5.1, DoD angepasst). Neu: Zusammenspiel Gerät/Konto als Fälle-Tabelle (§5.4), Kontowechsel, mehrere Tabs, lang offene Tabs und fehlgeschlagener Abgleich (CP-008…CP-012). Session Replay bleibt nicht aktiviert und bräuchte einen eigenen Zweck. |
| 1.2 | 2026-10-09 | #2174/#2175: Widerruf serverseitiger Einwilligungen im Tab, Erteilung am Ort der Funktion (§5.3). |
| 1.1 | 2026-10-09 | #2159: Banner eingebunden, Sentry-Gate im Browser, `useConsent`, Widerrufsschalter. |

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

1. **Fehlerberichte aus dem Browser** (Sentry-Protokoll, Referenzprofil GlitchTip) — überträgt bei einem Fehler im Browser einen Bericht an den Fehler-Tracker, den der Betreiber eingerichtet hat (gegebenenfalls ein externer Dienst, potenziell außerhalb der EU)
2. **Session Replay** — würde Nutzerinteraktionen aufzeichnen; **nicht aktiviert**, bräuchte einen eigenen Zweck

Eine HaveIBeenPwned-Prüfung gibt es nicht, und die Stammdatenanreicherung (REQ-011) ist ein Katalog-Job ohne Personenbezug (REQ-025 v1.31, #2136); beide brauchen keine Einwilligung. Die frühere Kategorie „Externe Dienste“ ist deshalb seit v1.3 gestrichen.

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
| Fehlerberichte aus dem Browser (Sentry-SDK im Browser) | `browser_error_reports` | DSGVO Art. 6 Abs. 1 lit. a (Einwilligung) und § 25 Abs. 1 TDDDG (ehemals TTDSG) — Speicher-/Zugriff des SDK im Endgerät, Übermittlung an den Fehler-Tracker des Betreibers. **Beim Umsetzen festgelegt (v1.3), rechtlich zu bestätigen (#2517):** die konservative Variante Einwilligung statt berechtigtem Interesse |
| Session Replay | — (nicht aktiviert; käme mit eigenem Zweck) | DSGVO Art. 6 Abs. 1 lit. a — Aufzeichnung von Nutzerverhalten |

Nicht hier geregelt, weil kein Browser-Speicherzugriff: Der Server-Zweck `error_tracking` entscheidet, ob ein Fehlerbericht **des Backends** Konto- und Mandanten-Pseudonym trägt (REQ-025 §3.6, NFR-001 SE-006). Er wird in der Oberfläche als eigener Zweck in der Einwilligungsliste geführt und hat mit dem Senden aus dem Browser nichts zu tun.

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
| CK-002 | Die Kategorie **„Fehlerberichte aus dem Browser"** (Zweck `browser_error_reports`) MUSS separat einwilligungsfähig sein. Sie umfasst das Senden von Fehlerberichten durch das Sentry-SDK im Browser. Session Replay gehört **nicht** dazu (nicht aktiviert; käme mit eigenem Zweck). | MUSS |
| CK-003 | *Entfallen (v1.3):* Die Kategorie „Externe Dienste“ hat keine Verarbeitung dahinter (keine HaveIBeenPwned-Prüfung; die Stammdatenanreicherung sendet nur Artnamen, REQ-025 v1.31). Sie wird weder angezeigt noch gespeichert; ein alter Wert `external_services` im Browser wird beim Lesen verworfen. | — |
| CK-004 | Jede Kategorie MUSS eine verständliche Beschreibung enthalten, die erklärt, welche Daten wohin übertragen werden. Für `browser_error_reports` nennt sie: was ein Bericht enthält (Fehlermeldung und Programmablauf, Seite ohne vertrauliche Adressparameter, Browser, Betriebssystem, App-Version, die Schritte davor), was er nicht enthält (Formulareingaben, Anfrage-Inhalte, Cookies, E-Mail-Adresse, Konto-Pseudonym), dass der Tracker beim Empfang die IP-Adresse sieht, und den Empfänger (der Fehler-Tracker des Betreibers, mit seinem Hostnamen aus der konfigurierten DSN). | MUSS |

### 3.3 Consent-Persistierung und Abgleich Gerät/Konto

Zwei Speicherorte, zwei Urheber: Die **Geräte-Entscheidung** liegt im `localStorage` dieses Browsers und stammt von einer Handlung ohne Anmeldung (oder vom Zurücksetzen in den Einstellungen). Die **Konto-Einwilligung** liegt als `ConsentRecord` im Backend (REQ-025) und stammt nur von einer Handlung der angemeldeten Person. Welche der beiden gilt, entscheidet eine einzige Funktion über die Fälle-Tabelle in §5.4.

| # | Regel | Stufe |
|---|-------|-------|
| CP-001 | Für **authentifizierte Nutzer** MUSS die Entscheidung über `POST /api/v1/privacy/consents` bzw. `DELETE /api/v1/privacy/consents/browser_error_reports` serverseitig gespeichert werden. Der Server stempelt die Version des Zwecktexts (`consent_version` = `ConsentPurpose.version`) bei Erteilung und Widerruf; der Client sendet keine Version. | MUSS |
| CP-002 | Für **nicht-authentifizierte Nutzer** (vor Login/Registrierung) MUSS die Entscheidung in `localStorage` gespeichert werden (Schlüssel `kamerplanter:consent:v1`, Feld `browser_error_reports`, mit Zeitstempel und Textversion). | MUSS |
| CP-003 | Beim Login wird **nichts** vom Browser zum Server übertragen. Eine Geräte-Zustimmung ist nie eine Konto-Einwilligung — sie kann von einer anderen Person am selben Gerät stammen und galt einem Text ohne Konto. Fehlt eine gültige Konto-Entscheidung, fragt die App die angemeldete Person (Banner in der Kontofassung). | MUSS |
| CP-004 | Der Consent-Status MUSS mindestens enthalten: Kategorie, Entscheidung (granted/denied), Zeitstempel, Version der Consent-Texte. Eine Zustimmung gilt nur zur **aktuellen** Textversion; eine Ablehnung gilt auch zu einer älteren. | MUSS |
| CP-005 | **Einmal-Neuabfrage nach der Umstellung:** Eine Zustimmung aus der Zeit vor v1.3 (Feld `error_tracking: true` im Browser) zählt als „nicht entschieden“; das Banner fragt einmal neu. Eine Ablehnung von damals (`error_tracking: false`) bleibt eine Ablehnung dieses Geräts. Server-Einwilligungen `error_tracking` werden nicht umgedeutet. | MUSS |
| CP-006 | Ist eine Person angemeldet, sendet der Browser nur mit gültiger **Konto**-Einwilligung zur aktuellen Textversion, die in diesem Seitenaufruf vom Server gelesen oder bestätigt wurde und nicht älter als 30 Minuten ist — und nur, wenn auf diesem Gerät nicht abgelehnt wurde. Eine Geräte-Zustimmung allein genügt angemeldet nie. | MUSS |
| CP-007 | **Ablehnung am Gerät:** Eine Geräte-Ablehnung schaltet die Berichte dieses Browsers für jede Person ab, die sich hier anmeldet; die Konto-Einwilligung bleibt unverändert (kein Widerruf durch eine andere Person am Gerät). Aufheben kann sie nur eine Handlung am Gerät: „Entscheidung dieses Browsers zurücksetzen“ in den Datenschutz-Einstellungen. Eine frühere Zustimmung überstimmt eine Ablehnung nie. | MUSS |
| CP-008 | **Vor Abschluss der Anmelde-Prüfung** (Auth-Bootstrap) ist unbekannt, wer angemeldet ist: Es wird nicht gesendet, das SDK wird nicht gestartet, und das Banner erscheint nicht. Erst nach dem Bootstrap gilt „abgemeldet“ oder „angemeldet als X“. Diese Meldung läuft im Initial-Chunk, nicht in einem nachgeladenen Modul. | MUSS |
| CP-009 | **Kontowechsel / Abmelden:** Beim Wechsel der Person verwirft der Tab die gelesene Konto-Entscheidung sofort und liest die der neuen Person; bis dahin wird nicht gesendet. Ein noch nicht übertragener Widerruf bleibt je Konto erhalten (`kamerplanter:consent:pending-revoke:<konto-hash>` — ein gerätelokaler Hash des Kontoschlüssels, nicht der Schlüssel selbst, weil der Eintrag das Abmelden überdauern muss, 07 PRIV-512; gelöscht, sobald der Widerruf übertragen ist) und wird beim nächsten Abgleich dieses Kontos zuerst gesendet; solange er aussteht, sendet der Browser für dieses Konto nicht. | MUSS |
| CP-010 | **Mehrere Tabs:** Eine Geräte-Entscheidung erreicht alle Tabs über das `storage`-Ereignis. Eine Konto-Entscheidung in einem Tab meldet sich bei den anderen (`kamerplanter:consent:account-signal`): Ein Widerruf stoppt dort sofort, danach lesen sie neu. Eine Serverantwort, die vor einer neueren Entscheidung (eigene, aus einem anderen Tab, Kontowechsel) angefordert wurde, wird verworfen und neu gelesen — eine veraltete Antwort überschreibt nie einen frischeren Stand. | MUSS |
| CP-011 | **Lang offene Tabs:** Ein angemeldeter Tab liest die Konto-Entscheidung neu, wenn er sichtbar wird (höchstens einmal je Minute), wenn das Netz zurückkommt (`online`) und alle 10 Minuten, solange er sichtbar ist. Eine Bestätigung älter als 30 Minuten zählt nicht mehr (CP-006), so endet ein Widerruf auf einem anderen Gerät spätestens nach dieser Zeit auch hier. | MUSS |
| CP-012 | **Fehlgeschlagener Abgleich:** Ein fehlgeschlagenes Lesen zählt als „keine gültige Einwilligung“ (kein Bericht, kein Banner) und wird beim nächsten Auslöser nach CP-011 wiederholt. Ein fehlgeschlagenes Erteilen ändert nichts und zeigt am Ort der Handlung einen Fehler mit „Erneut versuchen“. Ein fehlgeschlagener Widerruf stoppt die Berichte sofort trotzdem, bleibt als ausstehend gespeichert (CP-009) und wird angezeigt. Die Datenschutz-Einstellungen zeigen „nicht abgeglichen“ und „Widerruf ausstehend“ jeweils mit „Erneut versuchen“. Nie wirkt ein Fehlschlag als Zustimmung. | MUSS |

### 3.4 Consent-Widerruf

| # | Regel | Stufe |
|---|-------|-------|
| CW-001 | Nutzer MÜSSEN ihre Einwilligung jederzeit widerrufen können — über die Datenschutz-Einstellungen im Profil-Bereich. | MUSS |
| CW-002 | Der Widerruf MUSS genauso einfach sein wie die Erteilung (Art. 7 Abs. 3 DSGVO). | MUSS |
| CW-003 | Bei Widerruf von „Fehlerberichte aus dem Browser" MUSS Sentry **sofort** deaktiviert werden (kein Nachladen, kein Tracking bis zur nächsten Initialisierung) — auch wenn die Übertragung an den Server fehlschlägt (CP-012). | MUSS |
| CW-004 | *Entfallen (v1.3)* mit CK-003. | — |
| CW-005 | Der Widerruf einer angemeldeten Person MUSS über `DELETE /api/v1/privacy/consents/browser_error_reports` (REQ-025) an das Backend propagiert werden; schlägt das fehl, gilt CP-009/CP-012. | MUSS |

### 3.5 Consent-gesteuerte Initialisierung

| # | Regel | Stufe |
|---|-------|-------|
| CI-001 | Sentry (`@sentry/react`) DARF ERST initialisiert werden (`Sentry.init()`), wenn die Entscheidungsfunktion aus §5.4 „senden“ ergibt; das gilt auch vor dem ersten Render (CP-008). | MUSS |
| CI-002 | Vor Einwilligung DARF KEIN Sentry-SDK-Code geladen werden, der Daten erhebt oder überträgt. | MUSS |
| CI-003 | Die Anwendung MUSS einen **ConsentProvider** (React Context) bereitstellen, der den aktuellen Consent-Status hält und als Gate für optionale Features dient. | MUSS |
| CI-004 | Hooks wie `useConsent()` MÜSSEN verfügbar sein, damit Komponenten consent-abhängig rendern können. | SOLL |

---

## 4. UI-Design

### 4.1 Banner-Layout

```
┌──────────────────────────────────────────────────────────────┐
│  Fehlerberichte aus dem Browser?                             │
│  Optional sendet dieser Browser bei einem Fehler einen       │
│  Bericht an den Fehler-Tracker des Betreibers (<host>).      │
│  [abgemeldet:] gilt nur für diesen Browser                   │
│  [angemeldet:] wird in deinem Konto gespeichert              │
│                                                              │
│  [Einstellungen]    [Nur Notwendige]    [Alle akzeptieren]   │
└──────────────────────────────────────────────────────────────┘
```

- Position: Bottom-Sheet, fixiert am unteren Bildschirmrand
- Design: Gemäß UI-NFR-006 Design System (MUI 9 Komponenten)
- Responsive: Auf Mobile werden die Buttons vertikal gestapelt (UI-NFR-001)
- Barrierefreiheit: nicht-modal (`role="region"` mit `aria-label`, CB-002 — ein `dialog` würde einen Fokus-Fang verlangen, den ein Bottom-Sheet nicht haben soll), Bedienziele mindestens 48 px hoch, alle Aktionen per Tastatur; während eine Konto-Entscheidung übertragen wird, tragen die Schaltflächen `aria-disabled` und `aria-busy` (nicht `disabled`, damit der Fokus bleibt); ein Fehler erscheint als `role="alert"` mit „Erneut versuchen“ (UI-NFR-002)
- Zwei Fassungen desselben Banners: **Gerät** (abgemeldet, Entscheidung gilt nur für diesen Browser) und **Konto** (angemeldet, Entscheidung wird im Konto gespeichert und gilt in allen Browsern, in denen die Person angemeldet ist und nicht abgelehnt wurde). Welche erscheint, regelt §5.4.

### 4.2 Einstellungen im Banner und in den Datenschutz-Einstellungen

```
┌──────────────────────────────────────────────────────────────┐
│  ☑ Notwendig (immer aktiv)                          [locked] │
│    Auth-Cookies, Spracheinstellung, Theme, Session           │
│                                                              │
│  ☐ Fehlerberichte aus dem Browser                   [toggle] │
│    Was ein Bericht enthält und was nicht, Empfänger (CK-004) │
│                                                              │
│              [Auswahl speichern]                             │
└──────────────────────────────────────────────────────────────┘
```

- Realisierung: „Einstellungen“ klappt die Auswahl im Banner auf (kein eigener Dialog); Toggles: MUI `Switch` mit Label und `aria-describedby` auf die Beschreibung.
- „Externe Dienste“ erscheint nicht (CK-003 entfallen).
- **Datenschutz → Einwilligungen** (nur angemeldet erreichbar) trägt im Abschnitt „Fehlerberichte aus dem Browser“: den Schalter der **Konto**-Einwilligung (zeigt den vom Server bestätigten Stand, nicht optimistisch; während der Übertragung `aria-busy`), die Zeile „Dieser Browser sendet gerade: ja/nein“, die Geräte-Entscheidung („Ohne Anmeldung: erlaubt/abgelehnt“) mit „Entscheidung dieses Browsers zurücksetzen“, sowie die Hinweise aus CP-012 mit „Erneut versuchen“. Die allgemeine Liste der Zwecke führt `browser_error_reports` dann nicht ein zweites Mal (eine Bedienung je Zweck).
- In der allgemeinen Liste trägt eine Einwilligung, die zu einer älteren Textversion erteilt wurde (`consent_version` ≠ `purpose_version`), den Zusatz „für eine frühere Fassung erteilt“.
- i18n: Texte in DE/EN (UI-NFR-007), Schlüssel `consent.*` im nachgeladenen Namensraum `pages.json` (nicht im Initial-Chunk).

---

## 5. Technische Architektur

### 5.1 Zustand

```typescript
// Konzeptuelle Struktur (illustrativ; Umsetzung observability/consent.ts)
interface DeviceDecision {             // localStorage, CP-002
  necessary: true;
  browser_error_reports: boolean | null; // null = noch nicht entschieden
  timestamp: string | null;
  version: string;                     // Textversion, = ConsentPurpose.version im Backend
}
type Auth = 'unknown' | 'signed_out' | { signed_in: string /* user_key */ };
type Account = 'unknown' | 'failed' | 'undecided' | 'denied' | { granted: number /* bestätigt um */ };
```

- `browser_error_reports: null` = Banner in der Gerätefassung, wenn abgemeldet.
- `Account` gilt nur für das Konto, für das gelesen wurde, und nur in diesem Seitenaufruf (im Speicher, nicht im `localStorage`).
- Gerät, Anmeldezustand, Konto-Entscheidung und ausstehender Widerruf bilden **einen** Schnappschuss; Tracker, Banner und Einstellungen lesen dieselbe Entscheidungsfunktion (§5.4).

### 5.2 Sentry-Gate

Sentry wird nur initialisiert, wenn die Entscheidungsfunktion aus §5.4 „senden“ ergibt (illustrativ, vor v1.3 hieß das Feld `error_tracking`):

```typescript
// Konzeptuelle Struktur (illustrativ)
function SentryGate({ children }: { children: React.ReactNode }) {
  const { snapshot } = useConsent();

  useEffect(() => {
    if (browserReportsPermitted(snapshot)) {
      Sentry.init({ /* ... */ });
    } else {
      // Sentry deaktivieren falls bereits initialisiert
      Sentry.close();
    }
  }, [snapshot]);

  return <>{children}</>;
}
```

### 5.3 Umsetzungsstand (#2159 2026-10-09, #3025 N-40 2026-11-28)

- **CI-001/CI-002/CW-003 umgesetzt:** `src/frontend/src/observability/errorTracking.ts` lädt `@sentry/react` (ein einziger dynamischer Import je Seite) und ruft `Sentry.init()` nur, wenn `browserReportsPermitted()` (§5.4) wahr ist und nicht der Light-Modus läuft. Das Modul abonniert den Consent-Speicher einmal: eine spätere Zustimmung startet das SDK ohne Neuladen. Ein Widerruf (auch aus einem anderen Tab, `storage`-Ereignis) setzt den Client **synchron** auf `enabled = false`, leert die Breadcrumbs von Isolation- und Current-Scope (`Scope#clear()` gibt es in SDK 11 nicht mehr) und ruft danach `Sentry.close(2000)`; `beforeSend` und `beforeBreadcrumb` prüfen die Entscheidungsfunktion zuerst (mit der aktuellen Uhrzeit, so greift auch das 30-Minuten-Alter aus CP-006) und verwerfen sonst (`null`). Grund (gemessen in `@sentry/core` 11.4.0, `client.js`): `close(timeout)` wartet erst `flush(timeout)` ab und setzt `enabled = false` danach, und `_isClientDoneProcessing` behandelt `0` als unbegrenzt (`while (!timeout || ticked < timeout)`); `addBreadcrumb` prüft nur, ob ein Client existiert (`breadcrumbs.js`). Ohne DSN abonniert das Modul nichts und lädt nichts.
- **CI-003 abweichend, CI-004 umgesetzt:** Statt eines React-Context hält ein React-freies Modul (`src/frontend/src/observability/consent.ts`) Geräte-Entscheidung, Anmeldezustand, Konto-Entscheidung und ausstehenden Widerruf, weil das Sentry-Gate vor dem ersten Render entscheiden muss. `useConsent()` (`src/frontend/src/hooks/useConsent.ts`, `useSyncExternalStore`) liefert den Schnappschuss.
- **CP-008:** `src/frontend/src/observability/consentAuthBridge.ts` meldet den Redux-Anmeldezustand an den Consent-Speicher (`store.subscribe`, aufgerufen in `main.tsx`, Initial-Chunk). Vor `auth.initialized` gilt „unbekannt“.
- **CP-001/CP-003/CP-009…CP-012:** `src/frontend/src/observability/consentSync.ts` (eigener Chunk, geladen bei der ersten Anmeldung im Seitenaufruf) liest `GET /api/v1/privacy/consents`, schreibt `POST`/`DELETE` und hält den Abgleich (Epoche je Entscheidung gegen veraltete Antworten, Signal an andere Tabs, Auslöser nach CP-011). Lädt der Chunk nicht, bleibt die Konto-Entscheidung „unbekannt“: kein Bericht, kein Banner; die Einstellungsseite lädt das Modul selbst und zeigt den Zustand.
- **CB-001 mit DSN-Bedingung:** Das Banner ist im App-Shell eingebunden (`AppConsentBanner`, außerhalb des Routers, also auch auf Anmelde- und Registrierungsseite) und erscheint nur, wenn **eine `SENTRY_DSN` konfiguriert ist** und nicht der Light-Modus läuft: Browser-Fehlerberichte sind die einzige Verarbeitung, die diese Entscheidung schaltet. Ohne DSN führt die Einwilligungsliste `browser_error_reports` als gewöhnlichen, widerrufbaren Zweck.
- **Light-Modus:** kein Banner (CB-001), kein Abgleich, und der Tracker startet dort auch mit einer gespeicherten Zustimmung nicht (etwa nach einem Wechsel von `full` auf `light`) — durchgesetzt in `trackingPermitted()`, nicht nur über das fehlende Banner. Der Abschnitt in den Einstellungen ist im Light-Modus ausgeblendet.
- **CB-003/CB-004:** „Nur Notwendige“ und „Alle akzeptieren“ haben dieselbe Button-Variante; „Einstellungen“ klappt die Kategorie-Auswahl im Banner auf (nur `browser_error_reports`).
- **Banner-Darstellung:** `zIndex` = `modal - 1` (über Seiteninhalt, unter Dialogen, Drawern und Snackbars), Abstand unten inkl. `env(safe-area-inset-bottom)` bzw. Bottom-Navigation, Höhe max. `100dvh - 32px`, Bedienziele mind. 48 px. „Einstellungen“ bleibt beim Aufklappen fokussiert und trägt `aria-expanded`/`aria-controls`.
- **CW-001/CW-002/CW-005 für serverseitige Zwecke (#2174, #2175):** Datenschutz → Einwilligungen rendert die Zwecke aus `GET /api/v1/privacy/consents` und trägt bei jedem erteilten, nicht verpflichtenden Zweck die Schaltfläche „Widerrufen“ (`DELETE /api/v1/privacy/consents/{purpose}`, `data-testid="consent-revoke-<purpose>"`); ein neuer Zweck des Backends erscheint dort ohne Frontend-Änderung. Erteilt wird nicht im Tab, sondern am Ort der Funktion, mit dem Text, was übertragen wird: Pflanzenerkennung (`plant_identification`, Gate vor der Aufnahme), KI-Seite (`ai_knowledge_question`, Gate nach `403 CONSENT_REQUIRED`, danach wird die Frage erneut gesendet), Schalter „Als Referenzbild für die Erkennung nutzen“ (`reference_contribution`: der Schalter **ist** die Einwilligung; beim Speichern wird sie vor dem Beitrag erteilt, ein Fehlschlag bricht das Speichern sichtbar ab), Banner bzw. Schalter „Fehlerberichte aus dem Browser“ (`browser_error_reports`). Im Light-Modus gibt es keine serverseitigen Einwilligungen. **Offen:** `pest_reference_contribution` (Schädlings-Erkennungsindex, REQ-044 v1.4) erscheint im Tab und ist dort widerrufbar, hat aber noch keinen Erteilungsort in der Oberfläche; bis dahin nur über `POST /api/v1/privacy/consents`.
- **Speicher verweigert das Schreiben** (Quota, gesperrter Storage): Die Geräte-Entscheidung dieser Seite gilt im Speicher und gewinnt über einen noch lesbaren älteren Wert, bis ein Schreiben gelingt oder ein anderer Tab eine neuere Entscheidung speichert. Ein Widerruf bleibt so ein Widerruf; eine aktiv erteilte Zustimmung gilt bis zum Neuladen, danach fragt das Banner erneut. Gilt ebenso für den ausstehenden Konto-Widerruf (CP-009): Er wirkt dann bis zum Neuladen aus dem Speicher.
- Session Replay (NFR-001 SE-003) ist nicht aktiviert.
- **Regressionszäune (kein Beleg des Gates — der Beleg sind die Verhaltenstests in `errorTracking.test.ts`, `errorTrackingChunkLoad.test.ts`, `consentDecision.test.ts` und `consentSync.test.ts`):** `src/frontend/src/test/guards/trackerSdkBehindConsent.test.ts` lässt Tracker-Pakete und -Hosts (inkl. GlitchTip) in App-Quellen (`ts/tsx/js/jsx/mjs`), `index.html` und `public/` nur in `errorTracking.ts` zu; kein statischer Value-Import (auch mehrzeilig) in irgendeiner App-Quelle; genau ein `import('@sentry/…')` im Loader; `startErrorTracking(` nur hinter `if (trackingPermitted())`; Tracker-Abhängigkeiten in `dependencies`, `devDependencies`, `peerDependencies` und `optionalDependencies` nur mit Eintrag in der Liste des Zauns. Backend: `tests/unit/guards/test_consent_purposes_are_read.py` verlangt für einen Zweck, den nur der Browser liest, die Nennung in einer Frontend-Quelle und die gleiche Textversion in `consent_engine.py` und `observability/consent.ts`.

### 5.4 Fälle-Tabelle: sendet dieser Browser Berichte?

Voraussetzung in jeder Zeile: `SENTRY_DSN` gesetzt, Full-Modus. Sonst: nie senden, kein Banner. „Konto gültig erteilt“ heißt: Erteilung zur aktuellen Textversion, in diesem Seitenaufruf gelesen oder bestätigt, höchstens 30 Minuten alt, kein ausstehender Widerruf für dieses Konto.

| Gerät (abgemeldet entschieden) | Anmeldung | Konto | Sendet? | Banner | Was wird wo gespeichert |
|---|---|---|---|---|---|
| beliebig | unbekannt (Bootstrap läuft) | — | **nein** | nein | nichts |
| zugestimmt | abgemeldet | — | **ja** | nein | Gerät |
| abgelehnt | abgemeldet | — | nein | nein | Gerät |
| unentschieden | abgemeldet | — | nein | **ja, Gerätefassung** | Klick → Gerät |
| zugestimmt | angemeldet | gültig erteilt | **ja** | nein | — |
| zugestimmt | angemeldet | abgelehnt/widerrufen | nein | nein | — |
| zugestimmt | angemeldet | keine Angabe bzw. ältere Fassung | nein | **ja, Kontofassung** | Klick → Konto (Server, mit Textversion, IP, User-Agent); Gerät bleibt |
| abgelehnt | angemeldet | gültig erteilt | **nein** (CP-007) | nein | Konto bleibt unverändert |
| abgelehnt | angemeldet | abgelehnt | nein | nein | — |
| abgelehnt | angemeldet | keine Angabe | nein | nein (eine Ablehnung wird nicht erneut angefragt) | — |
| unentschieden | angemeldet | gültig erteilt | **ja** | nein | — (Konto gilt in jedem Browser ohne Ablehnung) |
| unentschieden | angemeldet | abgelehnt | nein | nein | — |
| unentschieden | angemeldet | keine Angabe | nein | **ja, Kontofassung** | Klick → Konto |
| beliebig | angemeldet | noch nicht gelesen / Lesen fehlgeschlagen | nein | nein; Einstellungen zeigen „nicht abgeglichen“ | — |
| beliebig | angemeldet | Widerruf ausstehend (CP-009) | nein | nein; Einstellungen zeigen „ausstehend“ | `pending-revoke:<konto-hash>` im Gerät bis zur Übertragung |

Eine alte Browser-Zustimmung aus der Zeit vor v1.3 ist „unentschieden“ (CP-005), eine alte Ablehnung „abgelehnt“.

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
    - [ ] „Fehlerberichte aus dem Browser" ist separat einwilligungsfähig; „Externe Dienste" erscheint nicht (v1.3)
    - [ ] Jede Kategorie hat verständliche Beschreibung mit Datenempfänger

- [ ] **Consent-gesteuerte Initialisierung**
    - [ ] Sentry wird ERST nach Einwilligung initialisiert (`browser_error_reports`, §5.4), nie vor Abschluss des Auth-Bootstraps
    - [ ] Ohne Einwilligung wird kein Sentry-SDK-Code geladen, der Daten erhebt
    - [ ] Consent-Widerruf deaktiviert Sentry sofort

- [ ] **Persistierung & Synchronisation**
    - [ ] Unauthentifiziert: Consent in localStorage gespeichert
    - [ ] Authentifiziert: Consent über REQ-025 API gespeichert und gelesen
    - [ ] Login überträgt **keine** Browser-Zustimmung zum Server (CP-003); fehlt eine Konto-Entscheidung, fragt die Kontofassung des Banners
    - [ ] Ablehnung am Gerät hält trotz Konto-Einwilligung (CP-007); Kontowechsel, mehrere Tabs, lang offene Tabs und Fehlschläge nach CP-009…CP-012

- [ ] **Widerruf**
    - [ ] Consent-Widerruf jederzeit über Datenschutz-Einstellungen möglich
    - [ ] Widerruf ist genauso einfach wie Erteilung
    - [ ] Widerruf propagiert über API an Backend

- [ ] **Barrierefreiheit & i18n**
    - [ ] Banner hat `role="region"` mit `aria-label`, 48-px-Ziele, Fehler als `role="alert"`
    - [ ] Texte in DE und EN verfügbar
    - [ ] Responsive Layout (Mobile: Buttons vertikal)

---

**Dokumenten-Ende**

**Version**: 1.3
**Status**: Entwurf
**Letzte Aktualisierung**: 2026-11-28
**Review**: Pending
**Genehmigung**: Pending
