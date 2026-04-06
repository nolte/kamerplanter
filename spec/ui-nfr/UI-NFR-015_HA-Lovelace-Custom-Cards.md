---

ID: UI-NFR-015
Titel: Home Assistant Lovelace Custom Cards — Entwicklungsrichtlinien
Kategorie: UI-Verhalten
Unterkategorie: Home Assistant, Lovelace, Custom Cards, Web Components
Technologie: JavaScript, ha-form, Shadow DOM, Home Assistant Frontend
Status: Entwurf
Prioritaet: Hoch
Version: 2.0
Autor: Business Analyst - Agrotech
Datum: 2026-03-28
Tags: [home-assistant, lovelace, custom-card, ha-form, ha-selector, shadow-dom, schema-based, web-components]
Abhaengigkeiten: [NFR-001, REQ-005, REQ-014, REQ-018]
Betroffene Module: [HA-Integration]
Changelog:
  - v2.0 (2026-03-28): Primaeransatz auf ha-form + Schema-Muster umgestellt (analog offizielle HA-Cards). document.createElement("ha-entity-picker") auf Fallback degradiert.
  - v1.0 (2026-03-09): Erstversion mit direktem ha-entity-picker Ansatz.
---

# UI-NFR-015: Home Assistant Lovelace Custom Cards — Entwicklungsrichtlinien

## 1. Business Case

### 1.1 User Story

**Als** Grower mit Home Assistant
**moechte ich** Kamerplanter-Daten (Tankfuellstand, Duengemischungen, Phasenverlauf) als native Lovelace-Cards im HA-Dashboard sehen
**um** alle Informationen an einer zentralen Stelle zu haben, ohne zwischen zwei Anwendungen wechseln zu muessen.

**Als** Grower
**moechte ich** die Cards ueber den Standard-HA-Editor konfigurieren koennen — identisch zur Bedienung offizieller HA-Cards (Entity-Picker, Textfelder, Checkboxen)
**um** die gewohnte HA-Benutzererfahrung beizubehalten und keine YAML-Konfiguration schreiben zu muessen.

**Als** Grower mit Firefox, Safari oder Chrome
**moechte ich** dass die Cards in jedem Browser zuverlaessig funktionieren
**um** nicht auf einen bestimmten Browser angewiesen zu sein.

### 1.2 Designprinzip: Maximale Annaeherung an offizielle HA-Cards

Kamerplanter Custom Cards MUESSEN sich so verhalten wie offizielle Lovelace-Cards (z.B. `hui-light-card`, `hui-tile-card`, `hui-thermostat-card`). Das bedeutet:

| Aspekt | Offizieller HA-Standard | Kamerplanter Cards |
|--------|------------------------|--------------------|
| Editor-Aufbau | `ha-form` + deklaratives Schema | `ha-form` + deklaratives Schema (identisch) |
| Entity-Filterung | `selector: { entity: { domain: [...] } }` | `selector: { entity: {} }` mit `entityFilter` |
| hass-Propagation | An `ha-form` uebergeben, intern verteilt | Identisch |
| Events | `value-changed` auf `ha-form` | Identisch |
| config-changed | `fireEvent(this, "config-changed", { config })` | Identisch (CustomEvent) |
| Element-Erstellung | Lit `html\`\`` Templates | `document.createElement("ha-form")` (Vanilla JS) |

Da unsere Cards **Vanilla JavaScript** (kein Lit Build-Setup) sind, verwenden wir `document.createElement("ha-form")` mit programmatischer Property-Setzung — dies erzeugt denselben Render-Pfad wie offizielle Lit-basierte Editors.

---

## 2. Anforderungen

### 2.1 Primaere Implementierungsstrategie: ha-form + Schema

Der **einzig zulaessige primaere Ansatz** fuer Card-Editoren ist `ha-form` mit einem deklarativen Schema. Direkte Instanziierung von `ha-entity-picker` ohne `ha-form` ist auf Ausnahmefaelle beschraenkt (§2.7).

| # | Regel | Stufe |
|---|-------|-------|
| R-001 | Card-Editoren MUESSEN `ha-form` als primaeres Editor-Element verwenden. | MUSS |
| R-002 | Die Konfiguration MUSS als deklaratives Schema-Array definiert werden (analog `hui-light-card-editor`). | MUSS |
| R-003 | Das Schema MUSS als Modul-Level-Variable oder per Getter definiert werden — nicht inline im Render. | MUSS |
| R-004 | `ha-form` MUSS `.hass`, `.schema` und `.data` als JavaScript-Properties (nicht HTML-Attribute) erhalten. | MUSS |
| R-005 | Konfigurationsaenderungen MUESSEN ausschliesslich ueber das `value-changed`-Event von `ha-form` verarbeitet werden. | MUSS |

**Referenz-Implementierung (Vanilla JS):**

```javascript
// Schema auf Modul-Ebene oder als Klassen-Getter definieren
const TANK_CARD_SCHEMA = [
  {
    name: "title",
    label: "Titel (optional)",
    selector: { text: {} },
  },
  {
    name: "tank_entity",
    label: "Tank (Kamerplanter)",
    required: true,
    selector: {
      entity: {
        // Kamerplanter Tank-Info Sensoren
        // entityFilter wird per Property gesetzt (siehe R-013)
      },
    },
  },
  {
    name: "show_ph",
    label: "pH anzeigen",
    selector: { boolean: {} },
  },
];

class KamerplanterTankCardEditor extends HTMLElement {
  setConfig(config) {
    this._config = { title: "", tank_entity: "", show_ph: true, ...config };
    if (this._hass) this._scheduleRender();
  }

  set hass(hass) {
    this._hass = hass;
    this._scheduleRender();
  }

  async _scheduleRender() {
    await _haFormReady; // Warten auf ha-form (§2.2)
    this._render();
  }

  _render() {
    if (!this._config || !this._hass) return;

    if (!this._form) {
      this.innerHTML = "";
      this._form = document.createElement("ha-form");
      this._form.addEventListener("value-changed", (e) => {
        this._config = e.detail.value;
        this.dispatchEvent(
          new CustomEvent("config-changed", {
            detail: { config: this._config },
            bubbles: true,
            composed: true,
          })
        );
      });
      this.appendChild(this._form);
    }

    // Properties setzen — identisch zu Lit .property=${value} Binding
    this._form.hass = this._hass;
    this._form.schema = TANK_CARD_SCHEMA;
    this._form.data = this._config;
  }
}
```

### 2.2 ha-form Lazy Loading

`ha-form` wird von Home Assistant ebenfalls lazy geladen. Das Modul-Level-Singleton MUSS auf `ha-form` warten, nicht auf `ha-entity-picker` direkt.

| # | Regel | Stufe |
|---|-------|-------|
| R-006 | Das Lazy-Loading-Singleton MUSS auf `ha-form` warten (`customElements.whenDefined("ha-form")`). | MUSS |
| R-007 | Das Singleton MUSS als Modul-Level-Variable definiert sein (einmalig ausgefuehrt, gecacht). | MUSS |
| R-008 | `_scheduleRender()` MUSS auf das Singleton warten, bevor DOM manipuliert wird. | MUSS |

**Referenz-Implementierung:**

```javascript
/**
 * Modul-Level Singleton: wartet bis ha-form verfuegbar ist.
 * ha-form propagiert hass intern zu ha-selector-entity → ha-entity-picker.
 * Kein manuelles Laden von ha-entity-picker noetig.
 */
const _haFormReady = (async () => {
  if (customElements.get("ha-form")) return;

  // Warten bis HA-Frontend grundlegend initialisiert ist
  await customElements.whenDefined("hui-entities-card");

  // loadCardHelpers triggert den Import der Form-Komponenten
  const helpers = await window.loadCardHelpers?.();
  if (helpers) {
    const temp = await helpers.createCardElement({ type: "entities", entities: [] });
    if (temp?.constructor?.getConfigElement) {
      await temp.constructor.getConfigElement();
    }
  }

  await customElements.whenDefined("ha-form");
})();
```

### 2.3 Schema-Definition

Das Schema ist ein Array von Felddefinitionen. Jedes Feld hat `name`, optionales `label`, und einen `selector`.

| # | Regel | Stufe |
|---|-------|-------|
| R-009 | Jedes Schema-Feld MUSS `name` und `selector` enthalten. | MUSS |
| R-010 | `label` SOLL immer gesetzt sein (sonst zeigt ha-form den Feldnamen roh an). | SOLL |
| R-011 | Das Schema DARF NICHT bei jedem Render neu erstellt werden — Modul-Konstante oder memoisierten Getter verwenden. | MUSS |
| R-012 | Fuer dynamische Schemas (entitaetsabhaengige Felder) MUSS Memoisation eingesetzt werden (Funktion mit gecachtem Rueckgabewert). | MUSS |

**Verfuegbare Selector-Typen:**

| Selector | Verwendung | Beispiel |
|----------|-----------|---------|
| `entity` | Entity-Auswahl (rendert ha-entity-picker) | `{ entity: { domain: ["sensor"] } }` |
| `text` | Texteingabe (rendert ha-textfield) | `{ text: {} }` |
| `boolean` | Checkbox (rendert ha-switch) | `{ boolean: {} }` |
| `number` | Zahleneingabe mit min/max | `{ number: { min: 0, max: 100, step: 1 } }` |
| `select` | Dropdown | `{ select: { options: ["a", "b"] } }` |
| `icon` | Icon-Picker | `{ icon: {} }` |
| `color_rgb` | Farb-Picker | `{ color_rgb: {} }` |

**Dynamisches Schema-Beispiel:**

```javascript
// Memoisation: Schema nur neu berechnen wenn sich entity aendert
let _lastEntity = undefined;
let _cachedSchema = null;

function getTankCardSchema(entityId) {
  if (entityId === _lastEntity && _cachedSchema) return _cachedSchema;
  _lastEntity = entityId;
  _cachedSchema = [
    { name: "title", label: "Titel", selector: { text: {} } },
    { name: "tank_entity", label: "Tank-Entity", required: true, selector: { entity: {} } },
    // Zeige erweiterte Optionen nur wenn Entity gewaehlt
    ...(entityId
      ? [
          { name: "show_ph", label: "pH anzeigen", selector: { boolean: {} } },
          { name: "show_ec", label: "EC anzeigen", selector: { boolean: {} } },
        ]
      : []),
  ];
  return _cachedSchema;
}

// Im _render():
this._form.schema = getTankCardSchema(this._config.tank_entity);
```

### 2.4 Entity-Filterung via Selector und entityFilter

`ha-form` uebergibt den `entity`-Selector intern an `ha-selector-entity`, der wiederum `ha-entity-picker` rendert. Filterung erfolgt deklarativ im Schema oder per `entityFilter`-Function.

| # | Regel | Stufe |
|---|-------|-------|
| R-013 | Domain-Filterung SOLL deklarativ im Schema via `selector: { entity: { domain: [...] } }` erfolgen. | SOLL |
| R-014 | Kamerplanter-spezifische Filterung (z.B. `sensor.kp_*_info`) MUSS als `entityFilter`-Function via `computedSchema` oder direkt auf dem `ha-form`-Element implementiert werden. | MUSS |
| R-015 | `includeEntities`-Arrays DUERFEN NICHT hartcodiert sein — immer dynamisch aus `this._hass.states` aufbauen. | MUSS |
| R-016 | `allowCustomEntity` SOLL im Schema oder als Selector-Property gesetzt werden. | SOLL |

**Entity-Filter ueber ha-form (empfohlen):**

```javascript
// ha-form unterstuetzt computedSchema fuer dynamische Selector-Properties
// Alternativ: entityFilter direkt per Property auf ha-selector-entity

// Ansatz 1: include_entities im Schema (wenn Menge klein und bekannt)
function buildSchema(hass) {
  const tankEntities = Object.keys(hass.states)
    .filter((id) => id.startsWith("sensor.kp_") && id.endsWith("_info"));

  return [
    {
      name: "tank_entity",
      label: "Tank (Kamerplanter)",
      required: true,
      selector: {
        entity: {
          include_entities: tankEntities,
          // Erlaubt manuelle Eingabe falls Filter zu restriktiv
        },
      },
    },
  ];
}

// Im _render() — Schema wird mit aktuellem hass aufgebaut:
this._form.schema = buildSchema(this._hass);
```

```javascript
// Ansatz 2: entityFilter-Function (flexibler, fuer Pattern-Matching)
// Auf das ha-form-Element wird entityFilter-context nicht direkt unterstuetzt.
// Stattdessen: computedSchema als Function mit hass-Abhaengigkeit.

// Wenn ha-form entityFilter nicht unterstuetzt: schema mit include_entities
// aus hass.states aufbauen (Ansatz 1 bevorzugen).
```

### 2.5 Event-Handling: value-changed und config-changed

| # | Regel | Stufe |
|---|-------|-------|
| R-017 | Der Editor MUSS genau einen `value-changed`-Listener auf `ha-form` registrieren. | MUSS |
| R-018 | Bei jedem `value-changed`-Event MUSS die vollstaendige Konfiguration per `config-changed` CustomEvent propagiert werden. | MUSS |
| R-019 | Das `config-changed`-Event MUSS `bubbles: true` und `composed: true` setzen. | MUSS |
| R-020 | Event-Listener DUERFEN NICHT bei jedem `_render()`-Aufruf neu registriert werden (Memory Leak). Listener einmalig im ersten Render registrieren. | MUSS |

**Korrektes Event-Handling-Pattern:**

```javascript
_render() {
  if (!this._config || !this._hass) return;

  // Einmalige Initialisierung (kein doppelter Listener)
  if (!this._form) {
    this._form = document.createElement("ha-form");

    this._form.addEventListener("value-changed", (e) => {
      this._config = e.detail.value;
      this.dispatchEvent(new CustomEvent("config-changed", {
        detail: { config: this._config },
        bubbles: true,
        composed: true,
      }));
    });

    this.appendChild(this._form);
  }

  // Properties bei jedem Render aktualisieren
  this._form.hass = this._hass;
  this._form.schema = getSchema(this._config);
  this._form.data = this._config;
}
```

### 2.6 Shadow DOM — Card vs. Editor

| # | Regel | Stufe |
|---|-------|-------|
| R-021 | Die Card-Darstellungskomponente MUSS Shadow DOM verwenden (`attachShadow({ mode: "open" })`). | MUSS |
| R-022 | Der Card-Editor DARF KEIN Shadow DOM verwenden — `ha-form` und HA-Komponenten benoetigen Zugriff auf den globalen HA-Theme-Context. | MUSS |
| R-023 | `<style>`-Bloecke im Editor MUESSEN HA-CSS-Custom-Properties verwenden (`var(--primary-color)`, `var(--secondary-text-color)`, `var(--card-background-color)`). | MUSS |
| R-024 | SVG `<clipPath>`-Elemente in Shadow DOM MUESSEN innerhalb von `<defs>` stehen — Firefox rendert sie sonst nicht. | MUSS |

### 2.7 Mehrfach-Entity-Auswahl via multiple: true

Fuer Use-Cases wo der Nutzer eine beliebig lange Liste von Entities konfigurieren soll (z.B. Mix-Channels, Sensor-Gruppen), MUSS `selector: { entity: { multiple: true } }` verwendet werden. Dies rendert intern `ha-entities-picker` mit nativem Add/Remove — **kein Fallback auf direktes `ha-entity-picker` noetig**.

| # | Regel | Stufe |
|---|-------|-------|
| R-025 | Fuer dynamische Entity-Listen MUSS `selector: { entity: { multiple: true } }` verwendet werden — nicht `document.createElement("ha-entity-picker")` mit manueller Listenverwaltung. | MUSS |
| R-026 | `multiple: true` im Selector rendert `ha-entities-picker` (HA-nativ) mit Add/Remove-Buttons, Drag-to-Reorder und Suche. | INFO |
| R-027 | Direktes `document.createElement("ha-entity-picker")` DARF NUR verwendet werden wenn weder Single- noch Multi-Selector den Use-Case abdecken koennen — mit Pflicht-Kommentar im Code. | KANN |

**Mix-Card: dynamische Entity-Liste via multiple (korrekt):**

```javascript
function buildMixCardSchema(hass) {
  const mixEntities = hass
    ? Object.keys(hass.states).filter(
        (id) => id.startsWith("sensor.kp_") && id.endsWith("_mix")
      )
    : [];

  return [
    {
      name: "title",
      label: "Titel",
      selector: { text: {} },
    },
    {
      name: "entities",
      label: "Mix-Kanaele",
      required: true,
      selector: {
        entity: {
          multiple: true,              // rendert ha-entities-picker
          include_entities: mixEntities,
        },
      },
    },
  ];
}

// Im Editor: identisch zum Single-Entity-Ansatz
this._form.hass = this._hass;
this._form.schema = buildMixCardSchema(this._hass);
this._form.data = this._config;  // this._config.entities = ["sensor.kp_...", ...]
```

**Was `multiple: true` liefert (nativ, ohne eigenen Code):**
- Chip-Liste der gewaelten Entities mit einzelnem Remove-Button
- Suchfeld fuer neue Entities (gefiltert via `include_entities`)
- Reihenfolge per Drag-and-Drop aenderbar

### 2.8 Card-Registrierung

| # | Regel | Stufe |
|---|-------|-------|
| R-030 | Jede Card MUSS sich via `customElements.define()` mit `kamerplanter-{name}-card` registrieren. | MUSS |
| R-031 | Der Editor MUSS sich als `kamerplanter-{name}-card-editor` registrieren. | MUSS |
| R-032 | Die Card-Klasse MUSS `static getConfigElement()` implementieren (gibt Editor-Element zurueck). | MUSS |
| R-033 | Die Card-Klasse MUSS `static getStubConfig()` implementieren (gibt Default-Konfiguration zurueck). | MUSS |
| R-034 | Die Card MUSS sich in `window.customCards` registrieren. | MUSS |

**Referenz:**

```javascript
customElements.define("kamerplanter-tank-card", KamerplanterTankCard);
customElements.define("kamerplanter-tank-card-editor", KamerplanterTankCardEditor);

class KamerplanterTankCard extends HTMLElement {
  static getConfigElement() {
    return document.createElement("kamerplanter-tank-card-editor");
  }
  static getStubConfig() {
    return { tank_entity: "", title: "", show_ph: true, show_ec: true, show_temp: true };
  }
}

window.customCards = window.customCards || [];
window.customCards.push({
  type: "kamerplanter-tank-card",
  name: "Kamerplanter Tank",
  description: "Tankfuellstand mit SVG-Visualisierung",
  preview: true,
});
```

### 2.9 Deployment & Caching

| # | Regel | Stufe |
|---|-------|-------|
| R-035 | Card-JS-Dateien MUESSEN unter `/config/www/` im HA-Pod abgelegt werden. | MUSS |
| R-036 | Lovelace-Ressourcen MUESSEN als `type: module` registriert werden. | MUSS |
| R-037 | Bei jedem Deployment MUSS der Cache-Buster in `/config/.storage/lovelace_resources` aktualisiert werden (`?v={timestamp}`). | MUSS |
| R-038 | Nach Deployment MUSS der HA-Prozess neu gestartet werden (Pod-Restart). | MUSS |
| R-039 | Nutzer MUESSEN nach einem Update einen Hard-Reload (Ctrl+F5) durchfuehren. | SOLL |

---

## 3. Vollstaendige Referenz-Implementierung

### 3.1 Card Editor (ha-form Primaeransatz)

```javascript
// ============================================================
// Modul-Level: Lazy Loading fuer ha-form
// ============================================================
const _haFormReady = (async () => {
  if (customElements.get("ha-form")) return;
  await customElements.whenDefined("hui-entities-card");
  const helpers = await window.loadCardHelpers?.();
  if (helpers) {
    const temp = await helpers.createCardElement({ type: "entities", entities: [] });
    if (temp?.constructor?.getConfigElement) await temp.constructor.getConfigElement();
  }
  await customElements.whenDefined("ha-form");
})();

// ============================================================
// Schema (Modul-Level — nicht pro Render neu erstellen)
// ============================================================
function buildTankCardSchema(hass) {
  const tankEntities = hass
    ? Object.keys(hass.states).filter(
        (id) => id.startsWith("sensor.kp_") && id.endsWith("_info")
      )
    : [];

  return [
    {
      name: "title",
      label: "Titel (optional)",
      selector: { text: {} },
    },
    {
      name: "tank_entity",
      label: "Tank (Kamerplanter)",
      required: true,
      selector: {
        entity: {
          include_entities: tankEntities,
        },
      },
    },
    {
      name: "show_ph",
      label: "pH anzeigen",
      selector: { boolean: {} },
    },
    {
      name: "show_ec",
      label: "EC anzeigen",
      selector: { boolean: {} },
    },
    {
      name: "show_temp",
      label: "Temperatur anzeigen",
      selector: { boolean: {} },
    },
  ];
}

// ============================================================
// Editor-Klasse
// ============================================================
class KamerplanterTankCardEditor extends HTMLElement {
  constructor() {
    super();
    this._config = null;
    this._hass = null;
    this._form = null;
  }

  setConfig(config) {
    this._config = {
      title: "",
      tank_entity: "",
      show_ph: true,
      show_ec: true,
      show_temp: true,
      ...config,
    };
    if (this._hass) this._scheduleRender();
  }

  set hass(hass) {
    this._hass = hass;
    this._scheduleRender();
  }

  async _scheduleRender() {
    await _haFormReady;
    this._render();
  }

  _render() {
    if (!this._config || !this._hass) return;

    // ha-form einmalig erstellen
    if (!this._form) {
      this._form = document.createElement("ha-form");

      this._form.addEventListener("value-changed", (e) => {
        this._config = e.detail.value;
        this.dispatchEvent(
          new CustomEvent("config-changed", {
            detail: { config: this._config },
            bubbles: true,
            composed: true,
          })
        );
      });

      this.appendChild(this._form);
    }

    // Properties bei jedem Render aktuell halten
    this._form.hass = this._hass;
    this._form.schema = buildTankCardSchema(this._hass);
    this._form.data = this._config;
  }
}

// ============================================================
// Card-Klasse (Darstellung mit Shadow DOM)
// ============================================================
class KamerplanterTankCard extends HTMLElement {
  static getConfigElement() {
    return document.createElement("kamerplanter-tank-card-editor");
  }

  static getStubConfig() {
    return { tank_entity: "", title: "", show_ph: true, show_ec: true, show_temp: true };
  }

  constructor() {
    super();
    this.attachShadow({ mode: "open" });
  }

  setConfig(config) {
    this._config = config;
    if (this._hass) this._render();
  }

  set hass(hass) {
    this._hass = hass;
    this._render();
  }

  _render() {
    if (!this._config || !this._hass) return;
    // ... Darstellungslogik mit this.shadowRoot ...
  }
}

// ============================================================
// Registrierung
// ============================================================
customElements.define("kamerplanter-tank-card-editor", KamerplanterTankCardEditor);
customElements.define("kamerplanter-tank-card", KamerplanterTankCard);

window.customCards = window.customCards || [];
window.customCards.push({
  type: "kamerplanter-tank-card",
  name: "Kamerplanter Tank",
  description: "Tankfuellstand und Naehrstoffwerte",
  preview: true,
});
```

### 3.2 Lazy-Loading Sequenzdiagramm

```
Browser                    HA Frontend              Kamerplanter Card JS
  |                            |                          |
  |--- Dashboard laden ------->|                          |
  |                            |--- <script> laden ------>|
  |                            |                          |
  |                            |                  _haFormReady startet:
  |                            |                    1. customElements.get("ha-form")?
  |                            |                       → nein (lazy)
  |                            |                    2. whenDefined("hui-entities-card")
  |                            |<--- HA laed Cards -------|
  |                            |                    3. loadCardHelpers()
  |                            |--- Helpers geladen ----->|
  |                            |                    4. createCardElement({type:"entities"})
  |                            |                       → HA importiert ha-form + ha-selector-entity
  |                            |                          → ha-selector-entity importiert ha-entity-picker
  |                            |                    5. whenDefined("ha-form") → resolved ✓
  |                            |                          |
  |                            |--- setConfig(config) --->|
  |                            |                    _config gespeichert
  |                            |                    _scheduleRender() → wartet auf Promise
  |                            |                          |
  |                            |--- set hass(hass) ------>|
  |                            |                    _hass gespeichert
  |                            |                    _scheduleRender() → Promise resolved
  |                            |                    _render():
  |                            |                      createElement("ha-form")
  |                            |                      form.hass = hass
  |                            |                      form.schema = [...]
  |                            |                      form.data = config
  |                            |                          |
  |<-- Editor mit ha-form -----|<--- DOM komplett --------|
  |    (Entity-Picker, Toggle, |
  |     Textfelder nativ)      |
```

### 3.3 Vergleich: Vorher (v1.0) vs. Nachher (v2.0)

```
v1.0 (direktes ha-entity-picker):          v2.0 (ha-form + Schema):
---------------------------------------    ---------------------------------------
const picker = createElement("ha-entity-   const form = createElement("ha-form");
  picker");                                form.hass = this._hass;
picker.hass = this._hass;                  form.schema = SCHEMA;
picker.label = "Tank";                     form.data = this._config;
picker.includeEntities = [...];            form.addEventListener("value-changed",
picker.addEventListener("value-changed",     (e) => fireConfigChanged(e.detail.value)
  (e) => { ... update field ... });        );
picker.addEventListener("value-changed",
  (e) => { ... update other field ... });

// Jedes Feld manuell verwaltet           // ha-form verwaltet alle Felder zentral
// Listener-Proliferation                 // Ein einziger value-changed Listener
// DOM-Aufbau manuell                     // Schema deklarativ, DOM automatisch
```

---

## 4. Wireframe-Beispiele

### 4.1 Tank Card Editor (ha-form rendert nativ)

```
+------------------------------------------+
|  Titel (optional)                        |
|  [ha-textfield ─────────────────────── ] |  ← von ha-form via selector: { text: {} }
+------------------------------------------+
|  Tank (Kamerplanter) *                   |
|  [ha-entity-picker ▼                  ]  |  ← von ha-form via selector: { entity: {} }
|    ┌──────────────────────────────────┐  |
|    │ sensor.kp_90639_info             │  |     (include_entities aus hass.states)
|    │   Bewaesserungsfass Info         │  |
|    └──────────────────────────────────┘  |
+------------------------------------------+
|  pH anzeigen      [ha-switch          ]  |  ← von ha-form via selector: { boolean: {} }
|  EC anzeigen      [ha-switch          ]  |
|  Temp. anzeigen   [ha-switch          ]  |
+------------------------------------------+
     ↑ Kompletter Editor = ein ha-form Element mit Schema-Array
```

### 4.2 Mix Card Editor (ha-form mit multiple: true)

```
+------------------------------------------+
|  Titel                                   |
|  [ha-textfield ─────────────────────── ] |  ← selector: { text: {} }
+------------------------------------------+
|  Mix-Kanaele *                           |
|  ┌─────────────────────────────────────┐ |
|  │ [x] sensor.kp_90639_NPK_A_mix       │ |  ← ha-entities-picker (nativ)
|  │ [x] sensor.kp_90639_CalMag_mix      │ |     via selector: { entity: {
|  │ [+ Entity hinzufuegen       ▼     ] │ |       multiple: true,
|  └─────────────────────────────────────┘ |       include_entities: [...]
+------------------------------------------+     } }
     ↑ Kompletter Editor = ein ha-form Element
       multiple: true → HA rendert ha-entities-picker
       Add/Remove/Suche nativ, kein eigener Code
```

---

## 5. Akzeptanzkriterien

### Definition of Done

- [ ] Card-Editor verwendet `ha-form` als primaeres Element
- [ ] Schema ist als Modul-Konstante oder memoisierten Getter definiert (kein inline-Schema im Render)
- [ ] Entity-Filterung erfolgt via `include_entities` im Schema-Selector (dynamisch aus `hass.states`)
- [ ] Genau ein `value-changed`-Listener auf `ha-form` (kein Listener-Proliferation)
- [ ] `config-changed`-Event mit `bubbles: true, composed: true`
- [ ] `ha-form` Lazy Loading via `_haFormReady` Singleton
- [ ] Card-Editor hat kein Shadow DOM; Card-Darstellung hat Shadow DOM
- [ ] Editor rendert in **Firefox**, **Chrome** und **Safari** nativ (ha-entity-picker Dropdown funktioniert)
- [ ] Konfigurationsaenderungen werden sofort in der Card-Vorschau reflektiert
- [ ] Keine JavaScript-Fehler in der Browser-Konsole beim Oeffnen des Editors
- [ ] Direktes `document.createElement("ha-entity-picker")` nur mit Kommentar-Begruendung (§2.7)

---

## 6. Risiken bei Nicht-Einhaltung

| Risiko | Auswirkung | Eintrittswahrscheinlichkeit | Mitigation |
|--------|-----------|---------------------------|------------|
| Schema inline im Render erstellt | Neues Objekt bei jedem Render → ha-form diffed unnoetig, Flackern | **Hoch** | R-011: Modul-Konstante |
| Listener bei jedem Render registriert | Memory Leak, mehrfache config-changed Events | **Hoch** | R-020: Einmalige Initialisierung |
| ha-form ohne hass | Entity-Picker zeigt kein Dropdown | **Hoch** | R-004: hass immer setzen |
| Kein Lazy Loading | ha-form nicht definiert, Editor leer | **Hoch** | R-006: _haFormReady Singleton |
| Shadow DOM im Editor | HA-Theme-Variables nicht verfuegbar, Styling bricht | **Mittel** | R-022: Kein Shadow DOM im Editor |
| include_entities hartcodiert | Filter veraltet nach HA-Neustart | **Mittel** | R-015: Dynamisch aus hass.states |

---

**Dokumenten-Ende**

| Feld | Wert |
|------|------|
| Version | 2.0 |
| Status | Entwurf |
| Letzte Aenderung | 2026-03-28 |
| Naechstes Review | 2026-04-28 |
| Freigabe | ausstehend |
