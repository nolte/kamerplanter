---

ID: UI-NFR-012
Titel: PWA & Offline-Fähigkeit
Kategorie: UI-Verhalten Unterkategorie: Progressive Web App, Offline, Synchronisation
Technologie: React, TypeScript, Vite (vite-plugin-pwa), Workbox, IndexedDB
Status: Entwurf
Priorität: Hoch
Version: 1.0
Autor: Business Analyst - Agrotech
Datum: 2026-02-27
Tags: [pwa, offline, service-worker, indexeddb, sync, installable, cache, connectivity]
Abhängigkeiten: [UI-NFR-001, UI-NFR-003, UI-NFR-004, UI-NFR-006, UI-NFR-011]
Betroffene Module: [Frontend]
---

# UI-NFR-012: PWA & Offline-Fähigkeit

## 1. Business Case

### 1.1 User Story

**Als** Grower im Growraum (Keller)
**möchte ich** Messwerte und Beobachtungen auch ohne Internetverbindung erfassen können
**um** keine Daten zu verlieren, wenn der Mobilfunkempfang schlecht ist.

**Als** Grower im Gewächshaus
**möchte ich** die Anwendung auf dem Tablet als installierte App nutzen
**um** sie wie eine native App über den Homescreen starten zu können, ohne den Browser öffnen zu müssen.

**Als** Grower unterwegs (Balkon, Garten)
**möchte ich** jederzeit sehen, ob ich online oder offline bin
**um** zu wissen, ob meine Eingaben sofort synchronisiert werden oder später.

**Als** Betreiber einer Kiosk-Station
**möchte ich** dass die Anwendung bei kurzfristigen Netzwerkausfällen weiterläuft
**um** den Arbeitsfluss im Gewächshaus nicht zu unterbrechen.

**Als** Grower
**möchte ich** dass offline erfasste Daten automatisch synchronisiert werden, sobald die Verbindung wiederhergestellt ist
**um** mich nicht manuell um die Übertragung kümmern zu müssen.

### 1.2 Geschäftliche Motivation

Gewächshäuser, Growräume und Keller haben häufig keinen oder instabilen Mobilfunk-/WLAN-Empfang. Eine rein online-fähige Anwendung ist in diesen Umgebungen unbrauchbar:

1. **Growräume im Keller** — Kein Mobilfunkempfang, WLAN oft nicht bis in jeden Winkel
2. **Gewächshäuser aus Metall/Glas** — WLAN-Signal wird durch Struktur gedämpft, Abschattung
3. **Große Anlagen** — WLAN-Abdeckung nicht flächendeckend garantiert
4. **Balkon/Garten** — Mobiles Internet variabel (Edge/3G in Außenbereichen)
5. **Kiosk-Stationen** — Router-Ausfall darf den Betrieb nicht stoppen

Ohne Offline-Fähigkeit:
- Gehen Messwerte verloren, die erst am Abend am Desktop nachgetragen werden (wenn überhaupt)
- Wird die Datenqualität massiv beeinträchtigt (fehlende Zeitstempel, vergessene Werte)
- Sinkt die Nutzerakzeptanz, da die App „nie funktioniert, wenn man sie braucht"

---

## 2. Anforderungen

### 2.1 PWA-Grundanforderungen

| # | Regel | Stufe |
|---|-------|-------|
| R-001 | Die Anwendung MUSS als **Progressive Web App** installierbar sein (Web App Manifest + Service Worker). | MUSS |
| R-002 | Das Web App Manifest MUSS mindestens folgende Felder definieren: `name`, `short_name`, `start_url`, `display: "standalone"`, `theme_color`, `background_color`, Icons in 192px und 512px. | MUSS |
| R-003 | Die `start_url` MUSS auf die Kiosk-Startseite (`/kiosk`) oder die Dashboard-Seite verweisen, je nach Gerätetyp. | MUSS |
| R-004 | Die Anwendung MUSS auf dem Homescreen des Geräts installiert werden können (Android: Add to Home Screen, iOS: Add to Home Screen via Safari). | MUSS |
| R-005 | Im `standalone`-Modus MUSS die Anwendung ohne Browser-UI-Elemente (Adressleiste, Tabs) dargestellt werden. | MUSS |
| R-006 | Die Anwendung SOLL Push-Benachrichtigungen unterstützen können (Web Push API), auch wenn die Implementierung zunächst nicht erfolgt. Das Manifest MUSS dafür vorbereitet sein. | SOLL |

### 2.2 Service Worker & Caching-Strategie

| # | Regel | Stufe |
|---|-------|-------|
| R-007 | Die Anwendung MUSS einen Service Worker registrieren, der das Caching statischer Assets (HTML, CSS, JS, Bilder, Fonts) übernimmt. | MUSS |
| R-008 | Für statische Assets MUSS eine **Cache-First**-Strategie verwendet werden: Zuerst aus dem Cache laden, bei Cache-Miss vom Netzwerk holen und cachen. | MUSS |
| R-009 | Für API-Responses MUSS eine **Network-First**-Strategie verwendet werden: Zuerst vom Netzwerk laden, bei Netzwerkfehler aus dem Cache laden. | MUSS |
| R-010 | Für die Kiosk-Startseite und die wichtigsten Navigationsrouten MUSS eine **Precaching**-Strategie verwendet werden: Diese Seiten werden beim Service-Worker-Install vorab in den Cache gelegt. | MUSS |
| R-011 | Der Service Worker MUSS über `vite-plugin-pwa` (Workbox-basiert) implementiert werden, um mit dem Vite-Build-System kompatibel zu bleiben. | MUSS |
| R-012 | API-Cache-Einträge MÜSSEN eine maximale TTL (Time-To-Live) von **15 Minuten** haben — danach MUSS bei nächster Online-Verfügbarkeit neu geladen werden. | MUSS |
| R-013 | Der Cache MUSS eine Obergrenze von **50 MB** für API-Responses haben. Bei Überschreitung werden die ältesten Einträge gelöscht (LRU). | MUSS |
| R-014 | Service-Worker-Updates MÜSSEN dem Nutzer über ein UI-Element angezeigt werden (z.B. Banner „Neue Version verfügbar — Jetzt aktualisieren"). | MUSS |

### 2.3 Offline-Dateneingabe

| # | Regel | Stufe |
|---|-------|-------|
| R-015 | Die Anwendung MUSS im Offline-Zustand das Erfassen folgender Daten ermöglichen: Messwerte (EC, pH, Temperatur, Luftfeuchtigkeit), Bewässerungsereignisse, Problembeobachtungen (Text + optional Foto), Aufgaben-Status-Updates. | MUSS |
| R-016 | Offline erfasste Daten MÜSSEN in einer lokalen **IndexedDB**-Datenbank zwischengespeichert werden. | MUSS |
| R-017 | Jeder Offline-Datensatz MUSS folgende Metadaten enthalten: Erfassungszeitpunkt (Client-Timestamp), Sync-Status (`pending`, `synced`, `conflict`, `failed`), Entitäts-Typ, Nutzer-ID. | MUSS |
| R-018 | Die lokale Speicherung MUSS auch bei App-Neustart erhalten bleiben (IndexedDB ist persistent). | MUSS |
| R-019 | Es SOLL eine Obergrenze von **500 Offline-Einträgen** geben. Bei Erreichen der Grenze MUSS der Nutzer gewarnt werden, dass eine Synchronisation nötig ist. | SOLL |
| R-020 | Pflanzenstammdaten (Arten, Sorten, Standorte) MÜSSEN offline lesbar sein — diese Daten werden beim letzten Online-Zugriff vorab gecacht. | MUSS |

### 2.4 Synchronisation

| # | Regel | Stufe |
|---|-------|-------|
| R-021 | Die Anwendung MUSS **automatische Synchronisation** durchführen, sobald eine Netzwerkverbindung wiederhergestellt wird. | MUSS |
| R-022 | Die Synchronisation MUSS die **Background Sync API** verwenden, wenn vom Browser unterstützt. Fallback: Synchronisation beim nächsten App-Start oder manuell. | MUSS |
| R-023 | Offline-Einträge MÜSSEN in chronologischer Reihenfolge synchronisiert werden (FIFO). | MUSS |
| R-024 | Während der Synchronisation MUSS ein **Sync-Fortschrittsindikator** angezeigt werden (z.B. „Synchronisiere 3/12 Einträge..."). | MUSS |
| R-025 | Nach erfolgreicher Synchronisation MUSS der Nutzer per Snackbar/Overlay informiert werden (z.B. „12 Einträge synchronisiert"). | MUSS |
| R-026 | Fehlgeschlagene Synchronisationsversuche MÜSSEN automatisch nach **exponential Backoff** wiederholt werden (1s → 2s → 4s → 8s → max. 60s). | MUSS |
| R-027 | Nach 5 fehlgeschlagenen Versuchen MUSS der Eintrag als `failed` markiert und der Nutzer informiert werden. Ein manueller „Erneut versuchen"-Button MUSS angeboten werden. | MUSS |

### 2.5 Konflikterkennung

| # | Regel | Stufe |
|---|-------|-------|
| R-028 | Wenn ein Datensatz offline geändert wurde und zwischenzeitlich serverseitig aktualisiert wurde, MUSS die Anwendung einen **Konflikt** erkennen. | MUSS |
| R-029 | Die Konflikterkennung MUSS auf einem **Versionsstempel** (ETag oder `updated_at`-Timestamp) basieren. | MUSS |
| R-030 | Bei einem Konflikt MUSS der Nutzer informiert werden und zwischen folgenden Optionen wählen können: „Meine Version übernehmen", „Server-Version übernehmen", „Abbrechen". | MUSS |
| R-031 | Der Konfliktdialog MUSS beide Versionen (lokal und Server) nebeneinander anzeigen, mit Hervorhebung der abweichenden Felder. | MUSS |
| R-032 | Im Kiosk-Modus SOLL der Konfliktdialog vereinfacht werden: Nur „Meine Version übernehmen" und „Verwerfen" als Optionen, mit großen Touch-Targets (vgl. UI-NFR-011). | SOLL |

### 2.6 Konnektivitäts-Anzeige

| # | Regel | Stufe |
|---|-------|-------|
| R-033 | Die Anwendung MUSS permanent einen **Konnektivitäts-Indikator** anzeigen, der den aktuellen Online/Offline-Status darstellt. | MUSS |
| R-034 | Der Online-Status MUSS als grüner Punkt oder grünes Icon dargestellt werden. | MUSS |
| R-035 | Der Offline-Status MUSS als roter/orangener Punkt oder Icon mit dem Text „Offline" dargestellt werden. | MUSS |
| R-036 | Beim Wechsel von Online zu Offline MUSS eine deutliche Benachrichtigung angezeigt werden (Snackbar: „Offline — Eingaben werden lokal gespeichert"). | MUSS |
| R-037 | Beim Wechsel von Offline zu Online MUSS eine Benachrichtigung angezeigt werden (Snackbar: „Online — Synchronisation startet..."). | MUSS |
| R-038 | Der Indikator MUSS die Anzahl der noch nicht synchronisierten Einträge als Badge anzeigen (z.B. „Offline (3)"). | MUSS |
| R-039 | Im Kiosk-Modus MUSS der Konnektivitäts-Indikator mindestens **32px** groß und in der App-Bar permanent sichtbar sein. | MUSS |

### 2.7 Offline-Einschränkungen

| # | Regel | Stufe |
|---|-------|-------|
| R-040 | Wenn eine Aktion offline nicht möglich ist (z.B. Anlegen einer neuen Pflanzenart, die serverseitige Validierung erfordert), MUSS die Anwendung den Nutzer **vor** der Eingabe darüber informieren: „Diese Aktion ist nur online möglich." | MUSS |
| R-041 | Offline nicht verfügbare Aktionen MÜSSEN visuell als deaktiviert dargestellt werden (ausgegraut) mit einem Offline-Icon als Indikator. | MUSS |
| R-042 | Die Anwendung MUSS klar dokumentieren (in einer Hilfeseite oder Tooltip), welche Funktionen offline verfügbar sind und welche nicht. | MUSS |

### 2.8 Foto-Offline-Handling

| # | Regel | Stufe |
|---|-------|-------|
| R-043 | Fotos (Pflanzendokumentation, IPM-Beobachtungen) MÜSSEN offline in IndexedDB als Blob gespeichert werden können. | MUSS |
| R-044 | Offline gespeicherte Fotos MÜSSEN auf dem Gerät komprimiert werden (max. 1920px Kantenlänge, JPEG 80% Qualität), um den IndexedDB-Speicher zu schonen. | MUSS |
| R-045 | Bei der Synchronisation MÜSSEN Fotos sequenziell hochgeladen werden (nicht parallel), um den Upload bei schwacher Verbindung stabil zu halten. | MUSS |
| R-046 | Ein Upload-Fortschritt MUSS pro Foto angezeigt werden (Prozentanzeige oder Progress-Bar). | MUSS |
| R-047 | Die Gesamtgröße der offline gespeicherten Fotos SOLL auf **200 MB** begrenzt sein. Bei Überschreitung MUSS der Nutzer gewarnt werden. | SOLL |

---

## 3. Wireframe-Beispiele

### 3.1 Konnektivitäts-Indikator (Online)

```
┌────────────────────────────────────────────────────────┐
│  🌿 Kamerplanter           🟢 Online            👤    │
├────────────────────────────────────────────────────────┤
│                                                        │
│  [Seiteninhalt]                                        │
│                                                        │
└────────────────────────────────────────────────────────┘
```

### 3.2 Konnektivitäts-Indikator (Offline mit Pending-Einträgen)

```
┌────────────────────────────────────────────────────────┐
│  🌿 Kamerplanter        🔴 Offline (3)          👤    │
├────────────────────────────────────────────────────────┤
│  ┌──────────────────────────────────────────────────┐  │
│  │ ⚠️ Offline — Eingaben werden lokal gespeichert.  │  │
│  │                                          [✕]     │  │
│  └──────────────────────────────────────────────────┘  │
│                                                        │
│  [Seiteninhalt — Eingabe weiterhin möglich]            │
│                                                        │
└────────────────────────────────────────────────────────┘
```

### 3.3 Synchronisations-Fortschritt

```
┌────────────────────────────────────────────────────────┐
│  🌿 Kamerplanter        🟢 Synchronisiere...    👤    │
├────────────────────────────────────────────────────────┤
│  ┌──────────────────────────────────────────────────┐  │
│  │ 🔄 Synchronisiere 7/12 Einträge...              │  │
│  │ ████████████░░░░░░░░░░░░░░  58%                  │  │
│  └──────────────────────────────────────────────────┘  │
│                                                        │
│  [Seiteninhalt]                                        │
│                                                        │
└────────────────────────────────────────────────────────┘
```

### 3.4 Konfliktdialog

```
┌────────────────────────────────────────────────────────┐
│                                                        │
│  ┌──────────────────────────────────────────────────┐  │
│  │                                                  │  │
│  │  ⚠️ Konflikt bei Bewässerungseintrag             │  │
│  │                                                  │  │
│  │  ┌─────────────────┐  ┌─────────────────┐       │  │
│  │  │ Meine Version   │  │ Server-Version  │       │  │
│  │  ├─────────────────┤  ├─────────────────┤       │  │
│  │  │ EC: 2.1         │  │ EC: 1.8         │       │  │
│  │  │ pH: 6.2         │  │ pH: 6.2         │       │  │
│  │  │ Menge: 12.5 L   │  │ Menge: 10.0 L   │       │  │
│  │  │ 14:32 (lokal)   │  │ 14:28 (Server)  │       │  │
│  │  └─────────────────┘  └─────────────────┘       │  │
│  │                                                  │  │
│  │  Hervorgehobene Unterschiede: EC, Menge          │  │
│  │                                                  │  │
│  │  [Meine Version]  [Server-Version]  [Abbrechen]  │  │
│  │                                                  │  │
│  └──────────────────────────────────────────────────┘  │
│                                                        │
└────────────────────────────────────────────────────────┘
```

### 3.5 Offline nicht verfügbare Aktion

```
┌────────────────────────────────────────────────────────┐
│  🌿 Kamerplanter        🔴 Offline (3)          👤    │
├────────────────────────────────────────────────────────┤
│                                                        │
│  Stammdaten > Pflanzenarten                            │
│                                                        │
│  ┌──────────────────────────────────────────────────┐  │
│  │  [ + Neue Art anlegen ]  ← ausgegraut, 📵-Icon   │  │
│  │  "Diese Aktion ist nur online möglich."          │  │
│  └──────────────────────────────────────────────────┘  │
│                                                        │
│  ┌──────────────────────────────────────────────────┐  │
│  │  Solanum lycopersicum (Tomate)              [→]  │  │  ← lesbar (gecacht)
│  │  Capsicum annuum (Paprika)                  [→]  │  │  ← lesbar (gecacht)
│  │  Ocimum basilicum (Basilikum)               [→]  │  │  ← lesbar (gecacht)
│  └──────────────────────────────────────────────────┘  │
│                                                        │
└────────────────────────────────────────────────────────┘
```

### 3.6 Service-Worker-Update-Banner

```
┌────────────────────────────────────────────────────────┐
│  ┌──────────────────────────────────────────────────┐  │
│  │ 🔄 Neue Version verfügbar.                       │  │
│  │              [Jetzt aktualisieren]  [Später]      │  │
│  └──────────────────────────────────────────────────┘  │
│  🌿 Kamerplanter           🟢 Online            👤    │
├────────────────────────────────────────────────────────┤
│                                                        │
│  [Seiteninhalt]                                        │
│                                                        │
└────────────────────────────────────────────────────────┘
```

---

## 4. Akzeptanzkriterien

### Definition of Done

- [ ] **PWA-Installation**
    - [ ] Web App Manifest ist korrekt konfiguriert (name, icons, display, start_url)
    - [ ] Anwendung ist auf Android installierbar (Add to Home Screen)
    - [ ] Anwendung ist auf iOS installierbar (Safari: Add to Home Screen)
    - [ ] Im Standalone-Modus wird keine Browser-UI angezeigt
    - [ ] Lighthouse PWA-Score ≥90
- [ ] **Service Worker & Caching**
    - [ ] Service Worker wird beim ersten Besuch registriert
    - [ ] Statische Assets werden per Cache-First geladen
    - [ ] API-Responses werden per Network-First geladen
    - [ ] Kiosk-Startseite und Navigationsrouten sind vorab gecacht
    - [ ] Cache-TTL für API-Responses ist auf 15 Minuten gesetzt
    - [ ] Cache-Obergrenze (50 MB) wird eingehalten
    - [ ] Service-Worker-Update wird dem Nutzer angezeigt
- [ ] **Offline-Dateneingabe**
    - [ ] Messwerte können offline erfasst werden (EC, pH, Temperatur, Luftfeuchtigkeit)
    - [ ] Bewässerungsereignisse können offline erfasst werden
    - [ ] Problembeobachtungen können offline erfasst werden (inkl. Foto)
    - [ ] Aufgaben-Status kann offline aktualisiert werden
    - [ ] Offline-Einträge werden in IndexedDB gespeichert
    - [ ] Offline-Einträge überleben App-Neustart
    - [ ] Pflanzenstammdaten sind offline lesbar
- [ ] **Synchronisation**
    - [ ] Automatische Synchronisation bei Verbindungswiederherstellung
    - [ ] Sync-Fortschrittsindikator wird angezeigt
    - [ ] Erfolgsmeldung nach abgeschlossener Synchronisation
    - [ ] Exponential Backoff bei fehlgeschlagenen Versuchen
    - [ ] „Erneut versuchen"-Button nach 5 Fehlversuchen
- [ ] **Konflikterkennung**
    - [ ] Konflikte werden erkannt (Versionsstempel-Vergleich)
    - [ ] Konfliktdialog zeigt beide Versionen nebeneinander
    - [ ] Nutzer kann zwischen lokaler und Server-Version wählen
- [ ] **Konnektivitäts-Anzeige**
    - [ ] Online/Offline-Status ist permanent sichtbar
    - [ ] Badge zeigt Anzahl ausstehender Einträge
    - [ ] Statuswechsel-Benachrichtigungen erscheinen
- [ ] **Offline-Einschränkungen**
    - [ ] Nicht-offline-fähige Aktionen sind ausgegraut
    - [ ] Erklärungstext/Tooltip für deaktivierte Aktionen vorhanden
- [ ] **Foto-Handling**
    - [ ] Fotos werden offline in IndexedDB gespeichert
    - [ ] Fotos werden komprimiert (max. 1920px, JPEG 80%)
    - [ ] Fotos werden bei Sync sequenziell hochgeladen
    - [ ] Upload-Fortschritt wird pro Foto angezeigt
- [ ] **Testing**
    - [ ] End-to-End-Test: Offline-Eingabe → Flugmodus → Online → Sync → Daten auf Server vorhanden
    - [ ] Konflikt-Test: Offline-Änderung + Server-Änderung → Konfliktdialog → korrekte Auflösung
    - [ ] Stresstest: 100+ Offline-Einträge → Sync → alle korrekt übertragen
    - [ ] Foto-Test: 10 Fotos offline → Sync → alle Fotos auf Server
    - [ ] Lighthouse PWA-Audit bestanden
    - [ ] Service-Worker-Update-Flow manuell getestet
    - [ ] Test auf echten Geräten mit simuliertem Netzwerkverlust (Chrome DevTools Throttling + Flugmodus)

---

## 5. Risiken bei Nicht-Einhaltung

| Risiko | Auswirkung | Wahrscheinlichkeit | Mitigation |
|---|---|---|---|
| **App im Growraum unbrauchbar** | Kein Mobilfunkempfang im Keller, keine Dateneingabe möglich | Sehr hoch | Service Worker + IndexedDB für Offline-Kernfunktionen |
| **Datenverlust bei Verbindungsabbruch** | Eingaben gehen verloren, wenn die Verbindung mitten in einer Aktion abbricht | Hoch | Lokale Zwischenspeicherung vor API-Call, Retry-Mechanismus |
| **Veraltete Daten angezeigt** | Cache zeigt alte Werte, obwohl zwischenzeitlich aktualisiert wurde | Mittel | 15-Minuten-TTL, Network-First für API-Calls, Refresh-Button |
| **Sync-Konflikte** | Mehrere Nutzer ändern denselben Datensatz offline | Mittel | Versionsstempel-basierte Konflikterkennung, explizite Nutzerentscheidung |
| **IndexedDB-Speicher voll** | Zu viele Offline-Einträge oder zu viele Fotos | Niedrig | Obergrenzen (500 Einträge, 200 MB Fotos), Warnungen |
| **Service-Worker-Cache veraltet** | Nutzer sieht alte Version der App trotz neuem Deployment | Mittel | Update-Banner, Skip-Waiting-Strategie |
| **iOS-PWA-Einschränkungen** | Safari unterstützt Background Sync nicht, Push nur eingeschränkt | Hoch | Fallback: Manueller Sync-Button, Sync bei App-Start |

---

## 6. Technische Umsetzungshinweise

### 6.1 Empfohlene Bibliotheken

| Bibliothek | Zweck | Begründung |
|---|---|---|
| `vite-plugin-pwa` | Service Worker + Manifest | Native Vite-Integration, Workbox-basiert |
| `workbox` | Caching-Strategien | Google-Standard für PWA-Caching, gut dokumentiert |
| `idb` | IndexedDB-Wrapper | Promise-basierte API, TypeScript-Support, <1 KB |
| `dexie` | IndexedDB-ORM (Alternative) | Mächtiger als `idb`, Query-Builder, Versionierung |

### 6.2 Offline-fähige vs. Online-only Funktionen

| Offline-fähig (MUSS) | Online-only (initial) |
|---|---|
| Messwerte erfassen (EC, pH, Temperatur, rH) | Neue Pflanzenart anlegen |
| Bewässerungsereignis erstellen | Companion Planting bearbeiten |
| Problem/Beobachtung melden | Crop Rotation validieren |
| Aufgabe als erledigt markieren | Stammdaten bearbeiten (Name, Taxonomie) |
| Pflanzenstammdaten lesen | Enrichment-Service aufrufen |
| Standort-/Slot-Daten lesen | Reports generieren |
| Kiosk-Startseite & Quick-Actions | Benutzerverwaltung |
| Letzte Messwerte anzeigen (gecacht) | Echtzeit-Sensorwerte |

### 6.3 IndexedDB-Schema (Empfehlung)

```
kamerplanter-offline
├── pending-entries       // Offline-Einträge, Sync-Status, Zeitstempel
├── cached-species        // Gecachte Pflanzenarten
├── cached-cultivars      // Gecachte Sorten
├── cached-sites          // Gecachte Standorte
├── cached-locations      // Gecachte Standort-Räume
├── cached-slots          // Gecachte Slots
├── photo-queue           // Offline-Fotos als Blob
└── sync-metadata         // Letzte Sync-Zeit, Konflikte, Fehlzähler
```

---

**Dokumenten-Ende**

**Version**: 1.0
**Status**: Entwurf
**Letzte Aktualisierung**: 2026-02-27
**Review**: Pending
**Genehmigung**: Pending
