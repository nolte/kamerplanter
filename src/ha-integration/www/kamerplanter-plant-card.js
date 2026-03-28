/**
 * kamerplanter-plant-card
 *
 * Custom Lovelace card for Kamerplanter plant instances and planting runs.
 * Shows phase timeline with Kami SVG illustrations, current phase hero,
 * next-phase hint, and transition history table.
 *
 * Follows: https://developers.home-assistant.io/docs/frontend/custom-ui/custom-card
 *
 * Config:
 *   device_id: string  (required — Kamerplanter plant/run device)
 *   title:     string  (optional — override device name)
 */

/* ================================================================== *
 *  Constants                                                          *
 * ================================================================== */

const KAMI_PHASE_SVG = {
  germination: "/local/kami/timeline-kami-phase-germination.svg",
  seedling:    "/local/kami/timeline-kami-phase-seedling.svg",
  vegetative:  "/local/kami/timeline-kami-phase-vegetative.svg",
  flowering:   "/local/kami/timeline-kami-phase-flowering.svg",
  ripening:    "/local/kami/timeline-kami-phase-ripening.svg",
  harvest:     "/local/kami/timeline-kami-phase-harvest.svg",
  dormancy:    "/local/kami/timeline-kami-phase-dormancy.svg",
  juvenile:    "/local/kami/timeline-kami-phase-juvenile.svg",
  climbing:    "/local/kami/timeline-kami-phase-climbing.svg",
  mature:      "/local/kami/timeline-kami-phase-mature.svg",
  senescence:  "/local/kami/timeline-kami-phase-senescence.svg",
};

const STANDARD_PHASES = [
  "germination", "seedling", "vegetative",
  "flowering", "ripening", "harvest",
];

const CHECK_SVG = '<svg viewBox="0 0 24 24"><path fill="currentColor" d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z"/></svg>';

/* ================================================================== *
 *  Helpers                                                            *
 * ================================================================== */

function escapeHtml(s) {
  const el = document.createElement("span");
  el.textContent = s || "";
  return el.innerHTML;
}

function capitalize(s) {
  return s ? s.charAt(0).toUpperCase() + s.slice(1) : "";
}

function fmtDate(iso) {
  if (!iso) return "";
  const p = iso.split("-");
  return p.length >= 3 ? `${p[2]}.${p[1]}.${p[0]}` : iso;
}

function fmtDateShort(iso) {
  if (!iso) return "";
  const p = iso.split("-");
  return p.length >= 3 ? `${p[2]}.${p[1]}.` : iso;
}

function kamiSvg(phase) {
  return KAMI_PHASE_SVG[(phase || "").toLowerCase()] || null;
}

/* ================================================================== *
 *  CSS                                                                *
 * ================================================================== */

const CARD_STYLES = `
  /* ---- Host & Card ---- */
  :host {
    display: block;
    overflow: hidden;
    max-width: 100%;
    box-sizing: border-box;
    --kp-marker: 48px;
  }
  ha-card {
    overflow: hidden;
    max-width: 100%;
  }

  /* ---- Header ---- */
  .kp-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 16px 16px 0;
    gap: 12px;
  }
  .kp-header__left {
    display: flex;
    align-items: center;
    gap: 12px;
    min-width: 0;
    flex: 1;
  }
  .kp-header__kami {
    width: 48px;
    height: 48px;
    flex-shrink: 0;
    object-fit: contain;
    border-radius: 10px;
  }
  .kp-header__icon {
    font-size: 1.6em;
    flex-shrink: 0;
    line-height: 1;
  }
  .kp-header__text {
    display: flex;
    flex-direction: column;
    min-width: 0;
  }
  .kp-header__name {
    font-size: 1.15em;
    font-weight: 600;
    color: var(--primary-text-color);
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }
  .kp-header__plan {
    font-size: 0.78em;
    color: var(--secondary-text-color);
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }
  .kp-header__days {
    flex-shrink: 0;
    background: var(--primary-color, #4caf50);
    color: var(--text-primary-color, #fff);
    border-radius: 14px;
    padding: 6px 14px;
    font-size: 1.15em;
    font-weight: 700;
    line-height: 1.2;
  }
  .kp-header__days small {
    font-size: 0.6em;
    font-weight: 400;
    opacity: 0.85;
  }

  /* ---- Content ---- */
  .kp-content {
    padding: 12px 16px 16px;
    overflow: hidden;
    box-sizing: border-box;
  }

  /* ---- Hero ---- */
  .kp-hero {
    display: flex;
    align-items: baseline;
    gap: 10px;
    margin-bottom: 16px;
  }
  .kp-hero__phase {
    font-size: 1.3em;
    font-weight: 700;
    color: var(--primary-text-color);
  }
  .kp-hero__days {
    font-size: 0.85em;
    color: var(--secondary-text-color);
  }

  /* ---- Timeline ---- */
  .kp-timeline {
    display: flex;
    align-items: flex-start;
    width: 100%;
    margin-bottom: 20px;
    box-sizing: border-box;
    overflow-x: auto;
    overflow-y: hidden;
    scrollbar-width: none;       /* Firefox */
    -ms-overflow-style: none;    /* IE/Edge */
  }
  .kp-timeline::-webkit-scrollbar {
    display: none;               /* Chrome/Safari */
  }

  .kp-timeline__connector {
    flex: 1 1 0;
    min-width: 4px;
    height: 3px;
    margin-top: calc(var(--kp-marker) / 2);
    border-radius: 2px;
    background: var(--divider-color, #e0e0e0);
    transition: background 0.3s;
  }
  .kp-timeline__connector--done {
    background: var(--primary-color, #4caf50);
  }
  .kp-timeline__connector--active {
    background: linear-gradient(
      to right,
      var(--accent-color, #ff9800),
      var(--divider-color, #e0e0e0)
    );
  }

  /* ---- Step ---- */
  .kp-step {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 6px;
    flex: 1 1 0;
    min-width: 0;
  }

  .kp-step__marker {
    width: var(--kp-marker);
    height: var(--kp-marker);
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
    transition: transform 0.2s ease, box-shadow 0.2s ease;
  }
  .kp-step__marker svg {
    width: 40%;
    height: 40%;
  }
  .kp-step__marker--kami {
    background: none;
    border: none;
    border-radius: 14px;
    overflow: hidden;
  }
  .kp-step__marker--kami img {
    width: 100%;
    height: 100%;
    object-fit: contain;
    border-radius: 14px;
    display: block;
  }

  /* Step states */
  .kp-step--completed .kp-step__marker {
    background: var(--primary-color, #4caf50);
    color: var(--text-primary-color, #fff);
  }
  .kp-step--completed .kp-step__marker--kami {
    background: none;
    box-shadow: 0 0 0 3px var(--primary-color, #4caf50);
  }

  .kp-step--current .kp-step__marker {
    background: var(--accent-color, #ff9800);
    color: var(--text-primary-color, #fff);
    transform: scale(1.08);
    box-shadow: 0 0 0 4px rgba(255, 152, 0, 0.25);
  }
  .kp-step--current .kp-step__marker--kami {
    background: none;
    box-shadow:
      0 0 0 3px var(--accent-color, #ff9800),
      0 0 14px rgba(255, 152, 0, 0.3);
  }

  .kp-step--upcoming .kp-step__marker {
    background: transparent;
    border: 2px solid var(--divider-color, #ccc);
  }
  .kp-step--upcoming .kp-step__marker--kami {
    border: none;
    opacity: 0.35;
    filter: grayscale(80%);
  }

  .kp-step__pulse {
    width: 24%;
    height: 24%;
    border-radius: 50%;
    background: var(--text-primary-color, #fff);
    animation: kp-pulse 2s ease-in-out infinite;
  }
  @keyframes kp-pulse {
    0%, 100% { transform: scale(1); opacity: 1; }
    50% { transform: scale(1.3); opacity: 0.7; }
  }

  .kp-step__body {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 1px;
    width: 100%;
  }
  .kp-step__name {
    font-size: 0.72em;
    font-weight: 500;
    color: var(--secondary-text-color);
    text-align: center;
    max-width: 100%;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }
  .kp-step--current .kp-step__name {
    font-weight: 700;
    color: var(--primary-text-color);
  }
  .kp-step--upcoming .kp-step__name {
    opacity: 0.6;
  }
  .kp-step__date,
  .kp-step__duration {
    font-size: 0.62em;
    color: var(--secondary-text-color);
    opacity: 0.7;
  }
  .kp-step--current .kp-step__date {
    opacity: 1;
  }

  /* ---- Next-phase hint ---- */
  .kp-next {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 10px 14px;
    border-radius: 10px;
    background: var(--secondary-background-color, #f5f5f5);
    font-size: 0.88em;
    color: var(--primary-text-color);
    margin-bottom: 14px;
  }
  .kp-next__kami {
    width: 28px;
    height: 28px;
    object-fit: contain;
    flex-shrink: 0;
    opacity: 0.7;
  }
  .kp-next__arrow {
    color: var(--primary-color, #4caf50);
    font-weight: 700;
    font-size: 1.1em;
  }

  /* ---- Detail table ---- */
  .kp-details {
    border-top: 1px solid var(--divider-color, #e0e0e0);
    padding-top: 12px;
  }
  .kp-details__header,
  .kp-details__row {
    display: grid;
    grid-template-columns: 1fr auto auto;
    gap: 8px;
    align-items: center;
  }
  .kp-details__header {
    padding-bottom: 6px;
    font-size: 0.7em;
    font-weight: 600;
    color: var(--secondary-text-color);
    text-transform: uppercase;
    letter-spacing: 0.5px;
  }
  .kp-details__header span:nth-child(2),
  .kp-details__header span:nth-child(3) {
    text-align: right;
  }
  .kp-details__row {
    padding: 6px 0;
    font-size: 0.88em;
    border-bottom: 1px solid rgba(0, 0, 0, 0.06);
  }
  .kp-details__row:last-child {
    border-bottom: none;
  }
  .kp-details__row--current {
    font-weight: 600;
    color: var(--primary-text-color);
  }
  .kp-details__phase {
    display: flex;
    align-items: center;
    gap: 8px;
    color: var(--primary-text-color);
  }
  .kp-details__phase img {
    width: 24px;
    height: 24px;
    object-fit: contain;
    flex-shrink: 0;
    border-radius: 5px;
  }
  .kp-details__row--current .kp-details__phase::before {
    content: "";
    display: inline-block;
    width: 7px;
    height: 7px;
    border-radius: 50%;
    background: var(--accent-color, #ff9800);
    flex-shrink: 0;
  }
  .kp-details__date,
  .kp-details__days {
    color: var(--secondary-text-color);
    text-align: right;
  }
  .kp-details__date {
    min-width: 72px;
  }
  .kp-details__days {
    min-width: 36px;
  }

  /* ---- Empty / Error states ---- */
  .kp-empty {
    padding: 24px 16px;
    text-align: center;
    color: var(--secondary-text-color);
    font-size: 0.95em;
  }
  .kp-error {
    padding: 16px;
    color: var(--error-color, #db4437);
  }
`;

/**
 * ha-form ready singleton (UI-NFR-015 §2.2).
 */
const _haFormReadyPlant = (async () => {
  if (customElements.get("ha-form")) return;
  await customElements.whenDefined("hui-entities-card");
  const helpers = await window.loadCardHelpers?.();
  if (helpers) {
    const temp = await helpers.createCardElement({ type: "entities", entities: [] });
    if (temp?.constructor?.getConfigElement) await temp.constructor.getConfigElement();
  }
  await customElements.whenDefined("ha-form");
})();

/**
 * Build plant card editor schema.
 * Uses selector: { device: { integration: "kamerplanter" } } to filter
 * to Kamerplanter Plant Instance / Planting Run devices natively.
 */
const PLANT_CARD_SCHEMA = [
  { name: "device_id", label: "Pflanze / Planting Run", required: true,
    selector: { device: { integration: "kamerplanter" } } },
  { name: "title",     label: "Titel (optional)",
    selector: { text: {} } },
];

/* ================================================================== *
 *  Editor                                                             *
 * ================================================================== */

/**
 * Kamerplanter Plant Card Editor
 * Uses ha-form + schema — identical pattern to official HA card editors
 * (UI-NFR-015 §2.1). No Shadow DOM (UI-NFR-015 R-022).
 */
class KamerplanterPlantCardEditor extends HTMLElement {
  setConfig(config) {
    this._config = { device_id: "", title: "", ...config };
    if (this._hass) this._scheduleRender();
  }

  set hass(hass) {
    this._hass = hass;
    this._scheduleRender();
  }

  async _scheduleRender() {
    await _haFormReadyPlant;
    this._render();
  }

  _render() {
    if (!this._config || !this._hass) return;

    // Create ha-form once; reuse on subsequent renders (UI-NFR-015 R-020)
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

    this._form.hass = this._hass;
    this._form.schema = PLANT_CARD_SCHEMA;
    this._form.data = this._config;
  }
}

customElements.define("kamerplanter-plant-card-editor", KamerplanterPlantCardEditor);

/* ================================================================== *
 *  Card                                                               *
 * ================================================================== */

class KamerplanterPlantCard extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: "open" });
    this._built = false;
  }

  /* ---- Lifecycle (HA spec) ---------------------------------------- */

  /**
   * Called by HA with card configuration. Must throw on invalid config.
   * @param {object} config
   */
  setConfig(config) {
    if (!config.device_id) {
      throw new Error("Bitte ein Device ausw\u00e4hlen");
    }
    this._config = { title: "", ...config };
  }

  /**
   * Called by HA on every state change.
   * @param {object} hass
   */
  set hass(hass) {
    this._hass = hass;
    this._update();
  }

  /** Card height in 50px units (masonry view). */
  getCardSize() {
    return 8;
  }

  /** Grid options for HA sections view (56px per row). */
  getGridOptions() {
    return { columns: 6, min_columns: 3, rows: 8, min_rows: 4 };
  }

  /** Returns editor custom element. */
  static getConfigElement() {
    return document.createElement("kamerplanter-plant-card-editor");
  }

  /** Stub config for card picker — tries to pre-select first active plant device. */
  static getStubConfig(hass) {
    if (!hass) return { device_id: "", title: "" };
    const entities = hass.entities || {};
    const states = hass.states || {};
    const devices = hass.devices || {};
    for (const ent of Object.values(entities)) {
      const eid = ent.entity_id || "";
      if (!eid.match(/^sensor\.kp_\w+_phase_timeline$/)) continue;
      const st = states[eid];
      if (!st || st.state === "unavailable" || st.state === "unknown") continue;
      const dev = devices[ent.device_id];
      if (!dev) continue;
      const model = (dev.model || "").toLowerCase();
      if (model.includes("plant instance") || model.includes("planting run")) {
        return { device_id: ent.device_id, title: "" };
      }
    }
    return { device_id: "", title: "" };
  }

  /* ---- Data ---------------------------------------------------- */

  /** Collect sensor states keyed by suffix (e.g. "phase", "phase_timeline"). */
  _getEntityMap() {
    const id = this._config.device_id;
    if (!id || !this._hass) return {};
    const map = {};
    for (const ent of Object.values(this._hass.entities || {})) {
      if (ent.device_id !== id) continue;
      const st = this._hass.states[ent.entity_id];
      if (!st) continue;
      const m = ent.entity_id.match(/^(?:sensor|binary_sensor)\.kp_\w+?_(.+)$/);
      if (m) map[m[1]] = st;
    }
    return map;
  }

  /** Resolve device display name. */
  _getDeviceName() {
    const id = this._config.device_id;
    if (!id || !this._hass) return null;
    const dev = Object.values(this._hass.devices || {}).find((d) => d.id === id);
    return dev ? dev.name_by_user || dev.name : null;
  }

  /** Build ordered phase list from timeline attributes + standard backfill. */
  _buildPhases(tAttrs, currentPhase) {
    const phases = [];
    for (const [key, val] of Object.entries(tAttrs)) {
      if (val && typeof val === "object" && "status" in val) {
        phases.push({ name: key, ...val });
      }
    }

    /* Append upcoming standard phases after the current one */
    const known = new Set(phases.map((p) => p.name.toLowerCase()));
    const cur = (currentPhase || "").toLowerCase();
    let past = false;
    for (const sp of STANDARD_PHASES) {
      if (sp === cur) { past = true; continue; }
      if (past && !known.has(sp)) {
        phases.push({ name: sp, status: "upcoming", started: null, date: null, days: null });
      }
    }
    return phases;
  }

  /* ---- DOM build & update --------------------------------------- */

  /** Ensure static DOM skeleton exists. */
  _ensureDom() {
    if (this._built) return;

    this.shadowRoot.innerHTML = `
      <style>${CARD_STYLES}</style>
      <ha-card>
        <div class="kp-header">
          <div class="kp-header__left">
            <span id="headerVisual"></span>
            <div class="kp-header__text">
              <span class="kp-header__name" id="plantName"></span>
              <span class="kp-header__plan" id="planBadge"></span>
            </div>
          </div>
          <div class="kp-header__days" id="daysBadge" hidden></div>
        </div>
        <div class="kp-content">
          <div class="kp-hero">
            <span class="kp-hero__phase" id="heroPhase"></span>
            <span class="kp-hero__days" id="heroDays"></span>
          </div>
          <div class="kp-timeline" id="timeline"></div>
          <div class="kp-next" id="nextHint" hidden></div>
          <div class="kp-details" id="details" hidden></div>
        </div>
      </ha-card>
    `;
    this._built = true;
  }

  /** Main update — reads sensors and patches DOM. */
  _update() {
    if (!this._hass || !this._config) return;

    const ents = this._getEntityMap();

    if (Object.keys(ents).length === 0) {
      this.shadowRoot.innerHTML = `
        <style>${CARD_STYLES}</style>
        <ha-card><div class="kp-error">Device nicht gefunden oder keine Entities</div></ha-card>
      `;
      this._built = false;
      return;
    }

    this._ensureDom();
    const $ = (id) => this.shadowRoot.getElementById(id);

    /* Read sensors */
    const timelineObj  = ents["phase_timeline"];
    const phaseObj     = ents["phase"] || ents["status"];
    const nextPhaseObj = ents["next_phase"];
    const nutrientObj  = ents["nutrient_plan"];
    const daysObj      = ents["days_in_phase"];
    const tAttrs       = timelineObj ? timelineObj.attributes : {};

    const currentPhase = phaseObj?.state
      || tAttrs.current_phase_name
      || (timelineObj ? timelineObj.state : null)
      || "\u2014";
    const nextPhase    = nextPhaseObj?.state;
    const daysInPhase  = tAttrs.days_in_phase ?? daysObj?.state;
    const nutrientPlan = nutrientObj?.state;
    const plantName    = this._config.title || this._getDeviceName() || "Pflanze";

    /* Header */
    const headerSvg = kamiSvg(currentPhase);
    $("headerVisual").innerHTML = headerSvg
      ? `<img class="kp-header__kami" src="${headerSvg}" alt="${escapeHtml(currentPhase)}" />`
      : `<span class="kp-header__icon">\uD83C\uDF31</span>`;

    $("plantName").textContent = plantName;

    const planEl = $("planBadge");
    if (nutrientPlan && nutrientPlan !== "None" && nutrientPlan !== "unknown") {
      planEl.textContent = nutrientPlan;
      planEl.hidden = false;
    } else {
      planEl.hidden = true;
    }

    const daysEl = $("daysBadge");
    if (daysInPhase != null && daysInPhase !== "unknown") {
      daysEl.innerHTML = `${escapeHtml(String(daysInPhase))}<small>d</small>`;
      daysEl.hidden = false;
    } else {
      daysEl.hidden = true;
    }

    /* Hero */
    $("heroPhase").textContent = capitalize(currentPhase);
    $("heroDays").textContent = (daysInPhase != null && daysInPhase !== "unknown")
      ? `seit ${daysInPhase} ${Number(daysInPhase) === 1 ? "Tag" : "Tage"}`
      : "";

    /* Timeline */
    const phases = this._buildPhases(tAttrs, currentPhase);
    $("timeline").innerHTML = this._renderTimeline(phases);

    /* Next phase hint */
    const nextEl = $("nextHint");
    if (nextPhase && nextPhase !== "None" && nextPhase !== "unknown") {
      const nSvg = kamiSvg(nextPhase);
      nextEl.innerHTML = nSvg
        ? `<img class="kp-next__kami" src="${nSvg}" alt="" />`
        : `<span class="kp-next__arrow">\u2192</span>`;
      nextEl.innerHTML += `<span>N\u00e4chste Phase: <strong>${escapeHtml(capitalize(nextPhase))}</strong></span>`;
      nextEl.hidden = false;
    } else {
      nextEl.hidden = true;
    }

    /* Detail table */
    const recorded = phases.filter((p) => p.status === "completed" || p.status === "current");
    const detailEl = $("details");
    if (recorded.length > 0) {
      detailEl.innerHTML = this._renderDetails(recorded);
      detailEl.hidden = false;
    } else {
      detailEl.hidden = true;
    }
  }

  /* ---- Partial renderers ---------------------------------------- */

  _renderTimeline(phases) {
    if (phases.length === 0) return "";
    let html = "";
    for (let i = 0; i < phases.length; i++) {
      const p = phases[i];
      const state = p.status === "completed" ? "completed"
        : p.status === "current" ? "current"
        : "upcoming";

      /* Connector */
      if (i > 0) {
        const prev = phases[i - 1].status;
        const cls = prev === "completed" ? "kp-timeline__connector--done"
          : prev === "current" ? "kp-timeline__connector--active"
          : "";
        html += `<div class="kp-timeline__connector ${cls}"></div>`;
      }

      /* Marker content */
      const svg = kamiSvg(p.name);
      let marker = "";
      if (svg) {
        marker = `<img src="${svg}" alt="${escapeHtml(p.name)}" />`;
      } else if (state === "completed") {
        marker = CHECK_SVG;
      } else if (state === "current") {
        marker = `<div class="kp-step__pulse"></div>`;
      }

      const dateStr = p.started || p.date || "";

      html += `
        <div class="kp-step kp-step--${state}">
          <div class="kp-step__marker${svg ? " kp-step__marker--kami" : ""}">
            ${marker}
          </div>
          <div class="kp-step__body">
            <span class="kp-step__name">${escapeHtml(capitalize(p.name))}</span>
            ${dateStr ? `<span class="kp-step__date">${fmtDateShort(dateStr)}</span>` : ""}
            ${p.days != null ? `<span class="kp-step__duration">${p.days}d</span>` : ""}
          </div>
        </div>
      `;
    }
    return html;
  }

  _renderDetails(recorded) {
    let rows = "";
    for (const p of recorded) {
      const isCur = p.status === "current";
      const svg = kamiSvg(p.name);
      rows += `
        <div class="kp-details__row${isCur ? " kp-details__row--current" : ""}">
          <span class="kp-details__phase">
            ${svg ? `<img src="${svg}" alt="" />` : ""}
            ${escapeHtml(capitalize(p.name))}
          </span>
          <span class="kp-details__date">${fmtDate(p.started || p.date || "")}</span>
          <span class="kp-details__days">${p.days != null ? `${p.days}d` : "\u2014"}</span>
        </div>
      `;
    }
    return `
      <div class="kp-details__header">
        <span>Phase</span><span>Start</span><span>Dauer</span>
      </div>
      ${rows}
    `;
  }
}

customElements.define("kamerplanter-plant-card", KamerplanterPlantCard);

/* ================================================================== *
 *  Card Registration                                                  *
 * ================================================================== */

window.customCards = window.customCards || [];
window.customCards.push({
  type: "kamerplanter-plant-card",
  name: "Kamerplanter Pflanzen-Phasen",
  description: "Zeigt Phasen\u00fcberg\u00e4nge mit Kami-Illustrationen f\u00fcr Pflanzeninstanzen und Planting Runs",
  preview: false,
  documentationURL: "https://kamerplanter.readthedocs.io/de/latest/guides/home-assistant-integration/",
});
