---

ID: UI-NFR-014
Titel: Auth-Initialisierung & Seitenreload — URL-Erhalt bei Session-Wiederherstellung
Kategorie: UI-Verhalten
Unterkategorie: Authentifizierung, Routing, Ladezustände
Technologie: React, TypeScript, Redux Toolkit, React Router, Flutter
Status: Entwurf
Prioritaet: Hoch
Version: 1.0
Autor: Business Analyst - Agrotech
Datum: 2026-02-28
Tags: [auth, reload, deep-linking, session, loading-state, race-condition, redirect, jwt]
Abhaengigkeiten: [UI-NFR-003, UI-NFR-005, REQ-023, REQ-027]
Betroffene Module: [Frontend, Mobile]
---

# UI-NFR-014: Auth-Initialisierung & Seitenreload — URL-Erhalt bei Session-Wiederherstellung

## 1. Business Case

### 1.1 User Stories

**Als** authentifizierter Endanwender
**moechte ich** jede Seite per Browser-Reload (F5), Lesezeichen oder geteiltem Link direkt aufrufen koennen
**um** nach einem Seitenneuladen auf genau der Seite weiterzuarbeiten, auf der ich war — ohne Umweg ueber Login oder Dashboard.

**Als** Endanwender mit abgelaufener Session
**moechte ich** nach einem fehlgeschlagenen Wiederherstellungsversuch auf der Login-Seite landen
**um** mich schnell erneut anmelden zu koennen — und danach idealerweise zu meiner urspruenglichen Ziel-URL weitergeleitet zu werden.

**Als** nicht authentifizierter Endanwender
**moechte ich** beim Aufruf einer geschuetzten Seite auf die Login-Seite weitergeleitet werden, ohne in einer Endlos-Ladeanzeige haengen zu bleiben
**um** immer handlungsfaehig zu bleiben.

**Als** Nutzer im Light-Modus (REQ-027)
**moechte ich** dass die App sofort nutzbar ist, ohne unnoetige Auth-Ladebildschirme
**um** die Einfachheit des lokalen Deployments nicht durch kuenstliche Wartezeiten zu verlieren.

### 1.2 Geschaeftliche Motivation

Session-Wiederherstellung beim Seitenneuladen ist eine der haeufigsten Interaktionen in SPAs. Fehlerhaftes Verhalten fuehrt zu massiver Frustration:

1. **Deep-Link-Verlust** — Wird die URL beim Reload nicht beibehalten, sind geteilte Links und Lesezeichen (UI-NFR-005 R-001) wertlos
2. **Orientierungsverlust** — Unvermitteltes Landen auf Dashboard/Login nach Reload verwirrt Nutzer
3. **Doppelte Navigation** — Nutzer muessen nach jedem Reload manuell zurueck zur gewuenschten Seite navigieren
4. **Endlos-Ladebildschirm** — Haengenbleiben im Loading-State zerstoert das Vertrauen in die Anwendungsstabilitaet
5. **Race Conditions** — Asynchrone Auth-Pruefungen, die nach dem ersten Render starten, erzeugen zeitabhaengige Fehler die schwer reproduzierbar sind

### 1.3 Fachliche Beschreibung

Praktisches Beispiel:

> **Szenario**: Ein Grower arbeitet auf der Detailseite eines Pflanzdurchlaufs (`/t/mein-garten/durchlaeufe/123`). Er drueckt F5 um die Seite neu zu laden.
> **Ohne UI-NFR-014**: Die App startet mit `isAuthenticated=false`, die Route-Guard leitet sofort auf `/login` weiter. Im Hintergrund stellt die Auth-Initialisierung die Session her, `/login` erkennt den authentifizierten Nutzer und leitet auf `/dashboard` weiter. Der Nutzer landet auf dem Dashboard statt auf seiner Durchlauf-Detailseite.
> **Mit UI-NFR-014**: Die App startet mit `isLoading=true`, die Route-Guard zeigt einen Skeleton. Die Auth-Initialisierung stellt die Session her, setzt `isAuthenticated=true` und `isLoading=false`. Der Router rendert die Durchlauf-Detailseite — die URL bleibt `/t/mein-garten/durchlaeufe/123`.

---

## 2. Anforderungen

### 2.1 Initialer Ladezustand

| # | Regel | Stufe |
|---|-------|-------|
| R-001 | Der Auth-State MUSS mit `isLoading=true` initialisiert werden, bis die Session-Pruefung abgeschlossen ist. | MUSS |
| R-002 | Route-Guards fuer geschuetzte Seiten MUESSEN bei `isLoading=true` einen Ladezustand (Skeleton/Spinner) anzeigen und DUERFEN NICHT auf Login oder eine andere Seite weiterleiten. | MUSS |
| R-003 | Route-Guards fuer oeffentliche Seiten (Login, Register) MUESSEN bei `isLoading=true` ebenfalls einen Ladezustand anzeigen und DUERFEN NICHT auf Dashboard weiterleiten. | MUSS |
| R-004 | Im Light-Modus (REQ-027, kein Auth) MUSS die App ohne Auth-Ladezustand direkt rendern. | MUSS |

### 2.2 Session-Wiederherstellung

| # | Regel | Stufe |
|---|-------|-------|
| R-005 | Beim Seitenneuladen MUSS die Anwendung versuchen, die bestehende Session wiederherzustellen (Token-Refresh oder Profil-Abfrage), BEVOR Routing-Entscheidungen getroffen werden. | MUSS |
| R-006 | Bei erfolgreicher Session-Wiederherstellung MUSS die aktuelle Browser-URL beibehalten werden — es DARF KEINE Weiterleitung auf Dashboard oder eine andere Standardseite erfolgen. | MUSS |
| R-007 | Bei fehlgeschlagener Session-Wiederherstellung (Token abgelaufen, Server nicht erreichbar) MUSS `isLoading` auf `false` gesetzt werden, sodass Route-Guards den nicht-authentifizierten Nutzer korrekt auf die Login-Seite weiterleiten. | MUSS |
| R-008 | Die Session-Wiederherstellung MUSS ein Timeout besitzen (empfohlen: 10 Sekunden). Bei Ueberschreitung MUSS `isLoading=false` gesetzt werden, um Endlos-Ladebildschirme zu verhindern. | MUSS |

### 2.3 Redirect nach Login

| # | Regel | Stufe |
|---|-------|-------|
| R-009 | Wird ein nicht-authentifizierter Nutzer von einer geschuetzten Seite auf Login umgeleitet, SOLL die urspruengliche Ziel-URL als `returnTo`-Parameter in der Login-URL erhalten bleiben (z.B. `/login?returnTo=/t/garten/durchlaeufe/123`). | SOLL |
| R-010 | Nach erfolgreichem Login SOLL die App zur `returnTo`-URL navigieren (falls vorhanden), statt zum Default-Dashboard. | SOLL |
| R-011 | `returnTo`-URLs MUESSEN validiert werden — nur relative Pfade innerhalb der Anwendung sind erlaubt (Open-Redirect-Schutz). | MUSS |

### 2.4 Zustandskonsistenz

| # | Regel | Stufe |
|---|-------|-------|
| R-012 | Jeder asynchrone Auth-Thunk (Login, Register, Profil laden, Token-Refresh, Logout) MUSS in seinem `rejected`-Handler `isLoading=false` setzen, um Zustandsverklemmungen zu verhindern. | MUSS |
| R-013 | Nach `logout` MUSS der vollstaendige Auth-State zurueckgesetzt werden (`user=null`, `accessToken=null`, `isAuthenticated=false`, `isLoading=false`). | MUSS |
| R-014 | Die Auth-Initialisierung DARF nur einmal pro App-Mount ausgefuehrt werden — wiederholte Aufrufe (z.B. durch React Strict Mode doppeltes Mount) MUESSEN idempotent sein. | MUSS |

---

## 3. Sequenzdiagramme

### 3.1 Erfolgreiche Session-Wiederherstellung (Page Reload)

```
Browser                  Redux Store           AuthProvider          Backend API
   │                         │                      │                     │
   │── Seite neuladen ──────>│                      │                     │
   │                         │ isLoading=true        │                     │
   │                         │ isAuthenticated=false  │                     │
   │                         │                      │                     │
   │  ProtectedRoute:        │                      │                     │
   │  isLoading=true         │                      │                     │
   │  → zeigt Skeleton       │                      │                     │
   │                         │                      │                     │
   │                         │       useEffect()    │                     │
   │                         │<─── initAuth() ──────│                     │
   │                         │                      │── POST /auth/refresh │
   │                         │                      │<── 200 access_token ─│
   │                         │ accessToken=xxx       │                     │
   │                         │ isAuthenticated=true   │                     │
   │                         │                      │── GET /auth/profile  │
   │                         │                      │<── 200 user profile ─│
   │                         │ user={...}            │                     │
   │                         │ isLoading=false        │                     │
   │                         │                      │                     │
   │  ProtectedRoute:        │                      │                     │
   │  isAuthenticated=true   │                      │                     │
   │  → rendert <Outlet/>    │                      │                     │
   │  → URL bleibt erhalten  │                      │                     │
   │                         │                      │                     │
```

### 3.2 Fehlgeschlagene Session-Wiederherstellung

```
Browser                  Redux Store           AuthProvider          Backend API
   │                         │                      │                     │
   │── Seite neuladen ──────>│                      │                     │
   │                         │ isLoading=true        │                     │
   │                         │                      │                     │
   │  ProtectedRoute:        │                      │                     │
   │  isLoading=true         │                      │                     │
   │  → zeigt Skeleton       │                      │                     │
   │                         │                      │                     │
   │                         │       useEffect()    │                     │
   │                         │<─── initAuth() ──────│                     │
   │                         │                      │── POST /auth/refresh │
   │                         │                      │<── 401 Unauthorized ─│
   │                         │ isLoading=false !!    │                     │
   │                         │ isAuthenticated=false  │                     │
   │                         │                      │                     │
   │  ProtectedRoute:        │                      │                     │
   │  isAuthenticated=false  │                      │                     │
   │  → Navigate to /login   │                      │                     │
   │                         │                      │                     │
```

### 3.3 Light-Modus (kein Auth)

```
Browser                  Redux Store           AuthProvider
   │                         │                      │
   │── Seite laden ─────────>│                      │
   │                         │                      │
   │                         │       useEffect()    │
   │                         │<─── initAuth() ──────│
   │                         │  mode === 'light'     │
   │                         │  → fetchProfile()     │
   │                         │ isLoading=false        │
   │                         │ isAuthenticated=true   │
   │                         │                      │
   │  → App sofort nutzbar   │                      │
   │                         │                      │
```

---

## 4. Implementierungshinweise

### 4.1 Redux Auth-Slice (State-Design)

Der initiale State MUSS `isLoading: true` setzen, damit Route-Guards vor Abschluss der Auth-Pruefung im Ladezustand verbleiben:

```typescript
const initialState: AuthState = {
  user: null,
  accessToken: null,
  isAuthenticated: false,
  isLoading: true,   // KRITISCH: nicht false!
  error: null,
};
```

Jeder `rejected`-Handler MUSS `isLoading: false` setzen:

```typescript
builder.addCase(refreshAccessToken.rejected, (state) => {
  state.isLoading = false;  // Verhindert Endlos-Skeleton
  state.user = null;
  state.accessToken = null;
  state.isAuthenticated = false;
});
```

### 4.2 Route-Guard (ProtectedRoute)

```typescript
function ProtectedRoute() {
  const { isAuthenticated, isLoading } = useAppSelector((s) => s.auth);
  if (isLoading) return <LoadingSkeleton />;        // R-002: Kein Redirect!
  if (!isAuthenticated) return <Navigate to="/login" replace />;
  return <Outlet />;
}
```

### 4.3 Public-Route-Guard (PublicOnlyRoute)

```typescript
function PublicOnlyRoute() {
  const { isAuthenticated, isLoading } = useAppSelector((s) => s.auth);
  if (isLoading) return <LoadingSkeleton />;        // R-003: Kein Redirect!
  if (isAuthenticated) return <Navigate to="/dashboard" replace />;
  return <Outlet />;
}
```

### 4.4 Anti-Pattern (Race Condition)

Folgendes Muster erzeugt die beschriebene Race Condition und DARF NICHT verwendet werden:

```typescript
// FALSCH: Route-Guard leitet sofort auf /login weiter
const initialState = { isLoading: false, isAuthenticated: false };

// FALSCH: Auth-Check startet erst nach erstem Render
useEffect(() => { initAuth(); }, []);   // zu spaet!
```

**Warum**: React rendert synchron den Komponentenbaum mit dem initialen State. `useEffect` laeuft erst NACH dem ersten Render. Wenn `isLoading=false` und `isAuthenticated=false`, leitet `ProtectedRoute` sofort auf `/login` weiter — noch bevor `initAuth()` aufgerufen wird. Die URL geht dabei verloren.

### 4.5 Flutter (Mobile)

Fuer die Flutter-App gelten dieselben Prinzipien:

- `SplashScreen` waehrend Auth-Pruefung anzeigen
- Routing erst nach Abschluss der Session-Wiederherstellung entscheiden
- Deep-Link-URL im State zwischenspeichern und nach Auth-Pruefung ansteuern

---

## 5. Akzeptanzkriterien

### Definition of Done

- [ ] **Initialer Ladezustand**
    - [ ] Auth-State startet mit `isLoading=true`
    - [ ] ProtectedRoute zeigt Skeleton bei `isLoading=true`
    - [ ] PublicOnlyRoute zeigt Skeleton bei `isLoading=true`
    - [ ] Light-Modus rendert ohne unnoetige Verzoegerung
- [ ] **Session-Wiederherstellung**
    - [ ] Page-Reload auf geschuetzter Seite → URL bleibt erhalten nach erfolgreicher Wiederherstellung
    - [ ] Page-Reload bei abgelaufener Session → Weiterleitung auf Login (kein Endlos-Skeleton)
    - [ ] Page-Reload bei nicht erreichbarem Backend → Timeout → Weiterleitung auf Login
- [ ] **Zustandskonsistenz**
    - [ ] Jeder async Auth-Thunk setzt `isLoading=false` im rejected-Handler
    - [ ] Logout setzt den vollstaendigen Auth-State zurueck
    - [ ] Doppeltes Mount (Strict Mode) fuehrt nicht zu Fehlverhalten
- [ ] **Redirect nach Login** (SOLL)
    - [ ] returnTo-Parameter wird bei Redirect auf Login gesetzt
    - [ ] Nach Login wird zur returnTo-URL navigiert
    - [ ] returnTo akzeptiert nur relative Pfade
- [ ] **Testing**
    - [ ] Unit-Test: Auth-Slice Initialzustand ist `isLoading=true`
    - [ ] Unit-Test: `refreshAccessToken.rejected` setzt `isLoading=false`
    - [ ] Integration-Test: ProtectedRoute zeigt Skeleton bei `isLoading=true`
    - [ ] Integration-Test: ProtectedRoute leitet bei `isLoading=false, isAuthenticated=false` auf `/login` weiter
    - [ ] E2E-Test: Page-Reload auf geschuetzter Seite behaelt URL

---

## 6. Risiken bei Nicht-Einhaltung

| Risiko | Auswirkung | Wahrscheinlichkeit | Mitigation |
|---|---|---|---|
| **Race Condition beim Reload** | Nutzer verliert aktuelle Seite, landet auf Dashboard statt Zielseite | Hoch (bei jedem F5) | `isLoading=true` als Initialzustand, Route-Guards pruefen Loading-State |
| **Endlos-Ladebildschirm** | App haengt nach fehlgeschlagenem Token-Refresh, Nutzer kann nichts tun | Mittel | Jeder `rejected`-Handler setzt `isLoading=false`, Timeout fuer Auth-Init |
| **Deep-Link-Verlust** | Geteilte Links und Lesezeichen fuehren nie zur Zielseite | Hoch | URL-Erhalt ist Kern dieser Anforderung, Tests sichern ab |
| **Open Redirect** | Boesartige `returnTo`-URLs leiten auf externe Seiten weiter | Niedrig | Validierung: nur relative Pfade erlaubt |
| **Strict Mode Doppel-Init** | Doppelter Token-Refresh erzeugt Race Condition zwischen zwei Antworten | Mittel (nur Dev) | Idempotente Auth-Initialisierung mit Abort-Signal oder Guard-Flag |

---

## 7. Abgrenzung zu bestehenden Anforderungen

| Dokument | Fokus | Zusammenspiel mit UI-NFR-014 |
|---|---|---|
| UI-NFR-003 (Performance) | Ladezustaende, Skeletons | UI-NFR-014 nutzt Skeletons gemaess UI-NFR-003 R-006/R-007 waehrend Auth-Init |
| UI-NFR-005 (Navigation) | Deep-Linking, URL-Design | UI-NFR-014 stellt sicher, dass Deep-Links (R-001) beim Reload nicht verloren gehen |
| REQ-023 (Auth) | JWT-Tokens, Refresh, Login-Flow | UI-NFR-014 definiert das Frontend-Verhalten rund um REQ-023 Token-Refresh beim Reload |
| REQ-027 (Light-Modus) | Deployment ohne Auth | UI-NFR-014 R-004 stellt sicher, dass Light-Modus kein unnuetzes Auth-Loading zeigt |

---

**Dokumenten-Ende**

**Version**: 1.0
**Status**: Entwurf
**Letzte Aktualisierung**: 2026-02-28
**Review**: Pending
**Genehmigung**: Pending
