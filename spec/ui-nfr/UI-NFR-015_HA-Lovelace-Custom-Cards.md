---

ID: UI-NFR-015
Titel: Home Assistant Lovelace Custom Cards — Entwicklungsrichtlinien
Kategorie: UI-Verhalten
Unterkategorie: Home Assistant, Lovelace, Custom Cards, Web Components
Technologie: JavaScript, Lit, Shadow DOM, Home Assistant Frontend
Status: Entwurf
Prioritaet: Hoch
Version: 1.0
Autor: Business Analyst - Agrotech
Datum: 2026-03-09
Tags: [home-assistant, lovelace, custom-card, ha-entity-picker, ha-textfield, shadow-dom, lit, web-components, lazy-loading, firefox, safari, chrome]
Abhaengigkeiten: [NFR-001, REQ-005, REQ-014, REQ-018]
Betroffene Module: [HA-Integration]
---

# UI-NFR-015: Home Assistant Lovelace Custom Cards — Entwicklungsrichtlinien

## 1. Business Case

### 1.1 User Story

**Als** Grower mit Home Assistant
**moechte ich** Kamerplanter-Daten (Tankfuellstand, Duengemischungen, Phasenverlauf) als native Lovelace-Cards im HA-Dashboard sehen
**um** alle Informationen an einer zentralen Stelle zu haben, ohne zwischen zwei Anwendungen wechseln zu muessen.

**Als** Grower
**moechte ich** die Cards ueber den Standard-HA-Editor konfigurieren koennen (Entity-Picker, Textfelder, Checkboxen)
**um** die gewohnte HA-Benutzererfahrung beizubehalten und keine YAML-Konfiguration schreiben zu muessen.

**Als** Grower mit Firefox, Safari oder Chrome
**moechte ich** dass die Cards in jedem Browser zuverlaessig funktionieren
**um** nicht auf einen bestimmten Browser angewiesen zu sein.

### 1.2 Geschaeftliche Motivation

Home Assistant ist die zentrale Smart-Home-Plattform fuer Kamerplanter-Nutzer. Custom Lovelace Cards muessen sich nahtlos in das HA-Oekosystem einfuegen — sowohl visuell (native HA-Komponenten) als auch technisch (korrekte Lifecycle-Behandlung, Shadow DOM, Lazy Loading). Fehlerhafte Cards fuehren zu leeren Editoren, nicht funktionierenden Dropdowns und Nutzerfrustration.

Die HA-Frontend-Architektur hat spezifische Eigenheiten (Lit Web Components, Lazy Loading, Shadow DOM), die sich grundlegend von Standard-Web-Entwicklung unterscheiden und dedizierte Richtlinien erfordern.

---

## 2. Anforderungen

### 2.1 HA-Komponenten Lazy Loading (Kritisch)

Home Assistant laedt Lit-Komponenten (`ha-entity-picker`, `ha-textfield`, `ha-icon`, etc.) **lazy** — sie sind beim Laden einer Custom Card **nicht** automatisch verfuegbar. Ohne explizites Vorladen bleiben die Elemente als leere HTML-Tags ohne Funktion (kein Rendering, kein Dropdown, kein Input).

| # | Regel | Stufe |
|---|-------|-------|
| R-001 | Custom Cards MUESSEN vor dem ersten Render sicherstellen, dass alle benoetigten HA-Lit-Komponenten geladen und bei `customElements` registriert sind. | MUSS |
| R-002 | Das Laden MUSS ueber `window.loadCardHelpers()` erfolgen — dies ist die offizielle, stabile API die von HACS und der HA-Community empfohlen wird. | MUSS |
| R-003 | Das Lazy-Loading-Promise MUSS als Modul-Level-Singleton implementiert werden (einmalige Ausfuehrung, Ergebnis wird gecacht). | MUSS |
| R-004 | Nach `loadCardHelpers()` MUSS `customElements.whenDefined("ha-entity-picker")` abgewartet werden, bevor Elemente erstellt oder Properties gesetzt werden. | MUSS |
| R-005 | Das Lazy-Loading DARF den Card-Render NICHT blockieren — die Card selbst (nicht der Editor) SOLL auch ohne Editor-Komponenten rendern koennen. | SOLL |

**Referenz-Implementierung:**

```javascript
/**
 * Modul-Level Singleton — wird einmal ausgefuehrt, Promise wird gecacht.
 * Alle Editoren warten auf dasselbe Promise.
 */
const _haComponentsReady = (async () => {
  // Schneller Pfad: bereits geladen (z.B. nach Navigation im Dashboard)
  if (customElements.get("ha-entity-picker")) return;

  // Warten bis das HA-Frontend grundlegend initialisiert ist
  await customElements.whenDefined("hui-entities-card");

  // Card Helpers laden — dies triggert den Import der Editor-Komponenten
  const helpers = await window.loadCardHelpers?.();
  if (helpers) {
    const temp = await helpers.createCardElement({
      type: "entities",
      entities: [],
    });
    if (temp && temp.constructor?.getConfigElement) {
      await temp.constructor.getConfigElement();
    }
  }

  // Sicherstellen dass die Komponente tatsaechlich registriert ist
  await customElements.whenDefined("ha-entity-picker");
})();
```

**Warum `loadCardHelpers()` noetig ist:**

| Ansatz | Ergebnis |
|--------|----------|
| `<ha-entity-picker>` via `innerHTML` | Element bleibt leer — Lit-Klasse nicht geladen |
| `document.createElement("ha-entity-picker")` | Element bleibt leer — Lit-Klasse nicht geladen |
| `customElements.whenDefined()` allein | Promise resolved nie, wenn kein anderer Code den Import triggert |
| `window.loadCardHelpers()` + `whenDefined()` | Zuverlaessig in Chrome, Firefox, Safari |

### 2.2 Card Editor Lifecycle (setConfig / set hass)

Home Assistant ruft `setConfig(config)` und `set hass(hass)` in **undefinierter Reihenfolge** auf dem Editor auf. Typisch ist: `setConfig()` zuerst, `set hass()` danach. `ha-entity-picker` benoetigt zwingend ein gueltiges `hass`-Objekt fuer das Entity-Dropdown.

| # | Regel | Stufe |
|---|-------|-------|
| R-006 | `setConfig()` MUSS die Konfiguration speichern, DARF aber nur rendern wenn `this._hass` bereits gesetzt ist. | MUSS |
| R-007 | `set hass()` MUSS `this._hass` speichern und einen Render ausloesen. | MUSS |
| R-008 | Die Render-Methode MUSS als Guard `if (!this._config \|\| !this._hass) return;` beginnen. | MUSS |
| R-009 | Der Render MUSS ueber eine `async _scheduleRender()` Methode erfolgen, die auf `_haComponentsReady` wartet. | MUSS |

**Referenz-Implementierung:**

```javascript
class MyCardEditor extends HTMLElement {
  setConfig(config) {
    this._config = { ...defaults, ...config };
    if (this._hass) this._scheduleRender();
  }

  set hass(hass) {
    this._hass = hass;
    this._scheduleRender();
  }

  async _scheduleRender() {
    await _haComponentsReady;   // Warten auf Lazy Loading (§2.1)
    this._render();
  }

  _render() {
    if (!this._config || !this._hass) return;
    // ... DOM aufbauen ...
  }
}
```

### 2.3 Element-Erstellung (document.createElement vs. innerHTML)

Lit Web Components (`ha-entity-picker`, `ha-textfield`) verarbeiten HTML-Attribute und JavaScript-Properties unterschiedlich. Lit-Template-Syntax (`.value="${x}"`) funktioniert **nur** innerhalb von Lit `html` Templates, **nicht** in `innerHTML`-Strings.

| # | Regel | Stufe |
|---|-------|-------|
| R-010 | HA-Lit-Komponenten MUESSEN mit `document.createElement()` erstellt werden, nicht via `innerHTML`. | MUSS |
| R-011 | Properties (`hass`, `value`, `includeEntities`, `includeDomains`, `allowCustomEntity`) MUESSEN als JavaScript-Properties auf dem Element-Objekt gesetzt werden, nicht als HTML-Attribute. | MUSS |
| R-012 | Native HTML-Elemente (div, span, input, button, label) DUERFEN weiterhin via `innerHTML` erstellt werden. | KANN |
| R-013 | Lit-Template-Syntax (`.property="${value}"`, `@event="${handler}"`) DARF NICHT in `innerHTML`-Strings verwendet werden — diese Syntax ist Lit-exklusiv und wird vom Browser-HTML-Parser ignoriert. | MUSS |

**Korrekt:**

```javascript
const picker = document.createElement("ha-entity-picker");
picker.hass = this._hass;
picker.label = "Tank (Kamerplanter)";
picker.allowCustomEntity = true;
picker.value = config.tank_entity || "";
picker.includeEntities = ["sensor.kp_90639_info"];
container.appendChild(picker);
```

**Falsch (funktioniert nicht):**

```javascript
// innerHTML mit Lit-Syntax — Properties werden NICHT gesetzt
container.innerHTML = `
  <ha-entity-picker
    .hass="${this._hass}"
    .value="${config.tank_entity}"
    .includeEntities="${entities}"
  ></ha-entity-picker>
`;

// innerHTML ohne Lit-Syntax — Attribute statt Properties, unzuverlaessig
container.innerHTML = `
  <ha-entity-picker
    label="Tank"
    allow-custom-entity
  ></ha-entity-picker>
`;
// Properties nachtraeglich setzen funktioniert NICHT zuverlaessig,
// da das Element beim Lit-Upgrade seine internen Properties
// aus den Attributen initialisiert und spaetere Aenderungen ignoriert.
```

### 2.4 ha-entity-picker — Konfiguration

| # | Regel | Stufe |
|---|-------|-------|
| R-014 | Entity-Picker MUESSEN immer `picker.hass = this._hass` gesetzt bekommen — ohne `hass` zeigt der Picker kein Dropdown. | MUSS |
| R-015 | Zur Filterung auf Kamerplanter-Entities SOLL `includeEntities` mit einem Array von Entity-IDs verwendet werden (z.B. `sensor.kp_*_info`). | SOLL |
| R-016 | Zur Filterung auf eine Domain SOLL `includeDomains` verwendet werden (z.B. `["sensor"]`). | SOLL |
| R-017 | `allowCustomEntity = true` SOLL gesetzt werden, damit Nutzer auch Entity-IDs manuell eingeben koennen. | SOLL |
| R-018 | Value-Aenderungen MUESSEN ueber das `value-changed` Event abgefangen werden: `picker.addEventListener("value-changed", (e) => { ... e.detail.value ... })`. | MUSS |
| R-019 | Die Filter-Liste (`includeEntities`) MUSS dynamisch aus `this._hass.states` aufgebaut werden, nicht hartcodiert. | MUSS |

**Entity-Filter Muster:**

```javascript
// Tank-Info Sensoren (sensor.kp_XXXXX_info)
const tankEntities = Object.keys(this._hass.states)
  .filter((id) => id.startsWith("sensor.kp_") && id.endsWith("_info"));

// Mix-Channel Sensoren (sensor.kp_XXXXX_LABEL_mix)
const mixEntities = Object.keys(this._hass.states)
  .filter((id) => id.startsWith("sensor.kp_") && id.endsWith("_mix"));
```

### 2.5 ha-textfield — Konfiguration

| # | Regel | Stufe |
|---|-------|-------|
| R-020 | `ha-textfield` MUSS mit `document.createElement("ha-textfield")` erstellt werden. | MUSS |
| R-021 | `label`, `placeholder` und `value` MUESSEN als JavaScript-Properties gesetzt werden. | MUSS |
| R-022 | Wertaenderungen MUESSEN ueber das `input` Event abgefangen werden. | MUSS |

### 2.6 Shadow DOM — Card vs. Editor

| # | Regel | Stufe |
|---|-------|-------|
| R-023 | Die Card selbst (Darstellungskomponente) MUSS Shadow DOM verwenden (`this.attachShadow({ mode: "open" })`) — dies verhindert CSS-Konflikte mit dem HA-Dashboard. | MUSS |
| R-024 | Der Card-Editor DARF KEIN Shadow DOM verwenden — HA-Lit-Komponenten im Editor benoetigen Zugriff auf den globalen HA-Theme-Context (CSS Custom Properties). | MUSS |
| R-025 | `<style>`-Bloecke im Editor MUESSEN HA-CSS-Custom-Properties verwenden (`var(--primary-color)`, `var(--secondary-text-color)`, `var(--card-background-color)`, etc.) fuer konsistentes Theming. | MUSS |
| R-026 | SVG `<clipPath>`-Elemente in Shadow DOM MUESSEN innerhalb von `<defs>` stehen — ohne `<defs>` rendert Firefox die Clip-Pfade nicht. | MUSS |

### 2.7 Card-Registrierung

| # | Regel | Stufe |
|---|-------|-------|
| R-027 | Jede Card MUSS sich ueber `customElements.define()` mit einem eindeutigen Tag-Namen registrieren (Konvention: `kamerplanter-{name}-card`). | MUSS |
| R-028 | Der Editor MUSS sich separat registrieren (Konvention: `kamerplanter-{name}-card-editor`). | MUSS |
| R-029 | Die Card-Klasse MUSS `static getConfigElement()` implementieren, das den Editor-Tag-Namen zurueckgibt. | MUSS |
| R-030 | Die Card-Klasse MUSS `static getStubConfig()` implementieren, das eine Default-Konfiguration zurueckgibt. | MUSS |
| R-031 | Die Card MUSS sich in `window.customCards` registrieren fuer die HA-Card-Picker-Anzeige. | MUSS |

**Referenz:**

```javascript
customElements.define("kamerplanter-tank-card", KamerplanterTankCard);
customElements.define("kamerplanter-tank-card-editor", KamerplanterTankCardEditor);

class KamerplanterTankCard extends HTMLElement {
  static getConfigElement() {
    return document.createElement("kamerplanter-tank-card-editor");
  }
  static getStubConfig() {
    return { tank_entity: "", title: "Tank" };
  }
  // ...
}

window.customCards = window.customCards || [];
window.customCards.push({
  type: "kamerplanter-tank-card",
  name: "Kamerplanter Tank",
  description: "Tankfuellstand mit SVG-Visualisierung",
});
```

### 2.8 Event-Propagation (config-changed)

| # | Regel | Stufe |
|---|-------|-------|
| R-032 | Konfigurationsaenderungen im Editor MUESSEN ueber ein `config-changed` CustomEvent an HA propagiert werden. | MUSS |
| R-033 | Das Event MUSS `bubbles: true` und `composed: true` setzen, damit es Shadow-DOM-Grenzen ueberquert. | MUSS |
| R-034 | Das Event-Detail MUSS die vollstaendige Konfiguration enthalten: `{ detail: { config: this._config } }`. | MUSS |

### 2.9 Deployment & Caching

| # | Regel | Stufe |
|---|-------|-------|
| R-035 | Card-JS-Dateien MUESSEN unter `/config/www/` im HA-Pod abgelegt werden. | MUSS |
| R-036 | Lovelace-Ressourcen MUESSEN als `type: module` registriert werden. | MUSS |
| R-037 | Bei jedem Deployment MUSS der Cache-Buster in `/config/.storage/lovelace_resources` aktualisiert werden (`?v={timestamp}`). | MUSS |
| R-038 | Nach Deployment MUSS der HA-Prozess neu gestartet werden (PID 1 Signal oder Pod-Restart). | MUSS |
| R-039 | Nutzer MUESSEN nach einem Update einen Hard-Reload (Ctrl+F5) durchfuehren — die Card-Dokumentation SOLL darauf hinweisen. | SOLL |

---

## 3. Wireframe-Beispiele

### 3.1 Card Editor mit ha-entity-picker

```
+------------------------------------------+
|  Titel (optional)                        |
|  [ha-textfield: "Bewaesserungsfass"   ]  |
+------------------------------------------+
|  Tank (Kamerplanter)                     |
|  [ha-entity-picker ▼                  ]  |
|    ┌──────────────────────────────────┐  |
|    │ sensor.kp_90639_info             │  |
|    │   Bewaesserungsfass Info         │  |
|    └──────────────────────────────────┘  |
+------------------------------------------+
|  ANZEIGE DER MESSWERTE                   |
|  pH    [x] im Fass    [x] Badge         |
|  EC    [x] im Fass    [x] Badge         |
|  Temp  [x] im Fass    [x] Badge         |
+------------------------------------------+
|  Sensoren automatisch aus KA.            |
|  Ueberschreiben optional:               |
|  HA-SENSOREN (OPTIONAL)                  |
|  [ha-entity-picker: pH Sensor     ▼  ]  |
|  [ha-entity-picker: EC Sensor     ▼  ]  |
|  [ha-entity-picker: Temp Sensor   ▼  ]  |
+------------------------------------------+
```

### 3.2 Lazy-Loading Sequenzdiagramm

```
Browser                    HA Frontend              Custom Card JS
  |                            |                          |
  |--- Dashboard laden ------->|                          |
  |                            |--- <script> laden ------>|
  |                            |                          |
  |                            |                  _haComponentsReady startet:
  |                            |                    1. customElements.get("ha-entity-picker")?
  |                            |                       → nein (lazy, nicht geladen)
  |                            |                    2. whenDefined("hui-entities-card")
  |                            |<--- HA laed Cards -------|
  |                            |                    3. loadCardHelpers()
  |                            |--- Helpers geladen ----->|
  |                            |                    4. createCardElement({type:"entities"})
  |                            |                       → HA importiert ha-entity-picker
  |                            |                    5. whenDefined("ha-entity-picker")
  |                            |                       → resolved ✓
  |                            |                          |
  |                            |--- setConfig(config) --->|
  |                            |                    _config gespeichert
  |                            |                    _scheduleRender() → wartet auf Promise
  |                            |                          |
  |                            |--- set hass(hass) ------>|
  |                            |                    _hass gespeichert
  |                            |                    _scheduleRender() → Promise resolved
  |                            |                    _render() ausfuehren
  |                            |                          |
  |<-- Editor mit Dropdowns ---|<--- DOM komplett --------|
```

---

## 4. Akzeptanzkriterien

### Definition of Done

- [ ] `ha-entity-picker` rendert im Card-Editor in **Firefox**, **Chrome** und **Safari** als nativer HA-Dropdown mit Autovervollstaendigung
- [ ] `ha-textfield` rendert im Card-Editor als nativer HA-Textfeld mit Label und Placeholder
- [ ] Entity-Filter (`includeEntities`, `includeDomains`) schraenkt die Auswahl korrekt ein
- [ ] Konfigurationsaenderungen im Editor werden sofort in der Card-Vorschau reflektiert
- [ ] Die Card funktioniert auch wenn der Editor nie geoeffnet wird (reines YAML)
- [ ] Keine JavaScript-Fehler in der Browser-Konsole beim Oeffnen des Editors
- [ ] Kein Flackern oder Doppel-Render beim Oeffnen des Editors
- [ ] Nach Deployment + Cache-Buster-Update + HA-Restart + Ctrl+F5 zeigt der Editor die aktualisierten Komponenten

---

## 5. Risiken bei Nicht-Einhaltung

| Risiko | Auswirkung | Eintrittswahrscheinlichkeit | Mitigation |
|--------|-----------|---------------------------|------------|
| Lazy Loading nicht implementiert | Entity-Picker bleibt leer, kein Dropdown — Editor unbenutzbar | **Hoch** (100% in Firefox, variabel in Chrome) | R-001 bis R-005: `loadCardHelpers()` Pattern |
| innerHTML statt createElement | Properties gehen beim Lit-Upgrade verloren, Element rendert nicht | **Hoch** | R-010, R-011: Programmatische Erstellung |
| setConfig vor set hass | Erster Render ohne hass-Objekt, Picker zeigt kein Dropdown | **Hoch** (Standard-HA-Verhalten) | R-006 bis R-009: Deferred Render Pattern |
| Lit-Template-Syntax in innerHTML | `.value`, `.hass` werden als Text-Attribute geparst, nicht als Properties | **Hoch** | R-013: Nur JS-Properties verwenden |
| Cache-Buster fehlt | Nutzer sehen alte Version trotz Deployment | **Mittel** | R-037: Automatischer Timestamp |
| Shadow DOM im Editor | HA-Theme-Variables nicht verfuegbar, Styling bricht | **Mittel** | R-024: Kein Shadow DOM im Editor |

---

**Dokumenten-Ende**

| Feld | Wert |
|------|------|
| Version | 1.0 |
| Status | Entwurf |
| Letzte Aenderung | 2026-03-09 |
| Naechstes Review | 2026-04-09 |
| Freigabe | ausstehend |
