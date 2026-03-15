/**
 * kamerplanter-phase-card
 *
 * Custom Lovelace card showing phase progress with Kami SVG illustrations.
 * Displays progress bar, week/day info, next-phase hint, and phase stepper.
 *
 * Follows: https://developers.home-assistant.io/docs/frontend/custom-ui/custom-card
 *
 * Config:
 *   entity: string  (required — phase_timeline sensor entity_id)
 *   title:  string  (optional — override card title)
 */

/* ================================================================== *
 *  Constants                                                          *
 * ================================================================== */

const KP_PHASE_KAMI = {
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

const PHASE_LABELS = {
  harvest: "Ernte",
  flush: "Sp\u00fclphase",
  ripening: "Reife",
  drying: "Trocknung",
  curing: "Curing",
  dormancy: "Ruhephase",
  germination: "Keimung",
  seedling: "S\u00e4mling",
  vegetative: "Vegetativ",
  flowering: "Bl\u00fcte",
};

/* ================================================================== *
 *  Helpers                                                            *
 * ================================================================== */

function kpEsc(s) {
  const el = document.createElement("span");
  el.textContent = s || "";
  return el.innerHTML;
}

function kpKami(phase) {
  return KP_PHASE_KAMI[(phase || "").toLowerCase()] || null;
}

function kpFmtDateShort(iso) {
  if (!iso) return "";
  const p = iso.split("-");
  return p.length >= 3 ? `${p[2]}.${p[1]}.` : iso;
}

function kpCapitalize(s) {
  return s ? s.charAt(0).toUpperCase() + s.slice(1) : "";
}

/* ================================================================== *
 *  CSS                                                                *
 * ================================================================== */

const PHASE_CARD_STYLES = `
  :host {
    display: block;
    overflow: hidden;
    max-width: 100%;
    box-sizing: border-box;
  }
  ha-card {
    overflow: hidden;
    max-width: 100%;
    padding: 0;
  }

  /* ---- Header ---- */
  .kpp-header {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 16px 16px 0;
  }
  .kpp-header__kami {
    width: 40px;
    height: 40px;
    object-fit: contain;
    border-radius: 8px;
    flex-shrink: 0;
  }
  .kpp-header__icon {
    font-size: 1.4em;
    flex-shrink: 0;
    line-height: 1;
  }
  .kpp-header__title {
    font-size: 1.1em;
    font-weight: 500;
    color: var(--primary-text-color);
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  /* ---- Content ---- */
  .kpp-content {
    padding: 12px 16px 16px;
    overflow: hidden;
    box-sizing: border-box;
  }

  /* ---- Progress ---- */
  .kpp-progress {
    margin-bottom: 16px;
  }
  .kpp-progress__header {
    display: flex;
    justify-content: space-between;
    align-items: baseline;
    margin-bottom: 8px;
  }
  .kpp-progress__phase {
    font-size: 1.05em;
    font-weight: 600;
    color: var(--primary-text-color);
  }
  .kpp-progress__info {
    font-size: 0.9em;
    font-weight: 500;
    color: var(--secondary-text-color);
  }
  .kpp-progress__track {
    width: 100%;
    height: 10px;
    background: var(--divider-color, #e0e0e0);
    border-radius: 5px;
    overflow: hidden;
  }
  .kpp-progress__fill {
    height: 100%;
    border-radius: 5px;
    background: var(--primary-color, #03a9f4);
    transition: width 0.5s ease;
  }
  .kpp-progress__footer {
    display: flex;
    justify-content: space-between;
    margin-top: 6px;
  }
  .kpp-progress__pct {
    font-size: 0.85em;
    font-weight: 600;
    color: var(--primary-color, #03a9f4);
  }
  .kpp-progress__remaining {
    font-size: 0.85em;
    color: var(--secondary-text-color);
  }
  .kpp-progress__nodata {
    font-size: 0.85em;
    color: var(--secondary-text-color);
    font-style: italic;
  }

  /* ---- Next phase hint ---- */
  .kpp-next {
    display: flex;
    align-items: center;
    gap: 10px;
    margin-top: 10px;
    padding: 8px 12px;
    border-radius: 8px;
    background: var(--secondary-background-color, #f5f5f5);
    font-size: 0.85em;
    color: var(--primary-text-color);
  }
  .kpp-next--active {
    background: rgba(3, 169, 244, 0.12);
    border-left: 3px solid var(--primary-color, #03a9f4);
  }
  .kpp-next__kami {
    width: 24px;
    height: 24px;
    object-fit: contain;
    flex-shrink: 0;
    opacity: 0.7;
  }
  .kpp-next__icon {
    font-size: 1.1em;
    flex-shrink: 0;
  }

  /* ---- Phase stepper with Kami ---- */
  .kpp-steps {
    display: flex;
    width: 100%;
    padding-top: 12px;
    border-top: 1px solid var(--divider-color, #e0e0e0);
    box-sizing: border-box;
    overflow-x: auto;
    overflow-y: hidden;
    scrollbar-width: none;
    -ms-overflow-style: none;
  }
  .kpp-steps::-webkit-scrollbar {
    display: none;
  }

  .kpp-steps__connector {
    flex: 1 1 0;
    min-width: 4px;
    height: 3px;
    margin-top: 18px;
    border-radius: 2px;
    background: var(--divider-color, #e0e0e0);
  }
  .kpp-steps__connector--done {
    background: var(--primary-color, #4caf50);
  }
  .kpp-steps__connector--active {
    background: linear-gradient(
      to right,
      var(--accent-color, #ff9800),
      var(--divider-color, #e0e0e0)
    );
  }

  .kpp-step {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 4px;
    flex: 1 1 0;
    min-width: 0;
  }

  .kpp-step__marker {
    width: 36px;
    height: 36px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
    transition: transform 0.2s ease, box-shadow 0.2s ease;
  }
  .kpp-step__marker--kami {
    background: none;
    border: none;
    border-radius: 10px;
    overflow: hidden;
  }
  .kpp-step__marker--kami img {
    width: 100%;
    height: 100%;
    object-fit: contain;
    border-radius: 10px;
    display: block;
  }

  .kpp-step--completed .kpp-step__marker {
    background: var(--primary-color, #4caf50);
  }
  .kpp-step--completed .kpp-step__marker--kami {
    background: none;
    box-shadow: 0 0 0 2px var(--primary-color, #4caf50);
  }

  .kpp-step--current .kpp-step__marker {
    background: var(--accent-color, #ff9800);
    transform: scale(1.08);
    box-shadow: 0 0 0 3px rgba(255, 152, 0, 0.25);
  }
  .kpp-step--current .kpp-step__marker--kami {
    background: none;
    box-shadow:
      0 0 0 2px var(--accent-color, #ff9800),
      0 0 10px rgba(255, 152, 0, 0.3);
  }

  .kpp-step--upcoming .kpp-step__marker {
    background: transparent;
    border: 2px solid var(--divider-color, #ccc);
  }
  .kpp-step--upcoming .kpp-step__marker--kami {
    border: none;
    opacity: 0.35;
    filter: grayscale(80%);
  }

  .kpp-step__dot {
    width: 10px;
    height: 10px;
    border-radius: 50%;
    background: var(--text-primary-color, #fff);
  }

  .kpp-step__label {
    font-size: 0.68em;
    font-weight: 500;
    color: var(--secondary-text-color);
    text-align: center;
    max-width: 100%;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }
  .kpp-step--current .kpp-step__label {
    font-weight: 700;
    color: var(--primary-text-color);
  }
  .kpp-step--upcoming .kpp-step__label {
    opacity: 0.6;
  }
  .kpp-step__date {
    font-size: 0.58em;
    color: var(--secondary-text-color);
    opacity: 0.7;
  }
  .kpp-step--current .kpp-step__date {
    opacity: 1;
  }

  /* ---- Error ---- */
  .kpp-error {
    padding: 16px;
    color: var(--error-color, #db4437);
  }
`;

const PHASE_EDITOR_STYLES = `
  .kpp-editor__row {
    margin-bottom: 16px;
  }
  .kpp-editor__label {
    display: block;
    font-weight: 500;
    margin-bottom: 4px;
    font-size: 0.9em;
    color: var(--primary-text-color);
  }
  .kpp-editor__select,
  .kpp-editor__input {
    width: 100%;
    padding: 10px 12px;
    border: 1px solid var(--divider-color, #ccc);
    border-radius: 8px;
    background: var(--card-background-color, #fff);
    color: var(--primary-text-color);
    font-size: 0.95em;
    box-sizing: border-box;
    outline: none;
    transition: border-color 0.2s;
  }
  .kpp-editor__select:focus,
  .kpp-editor__input:focus {
    border-color: var(--primary-color, #4caf50);
  }
`;

/* ================================================================== *
 *  Editor                                                             *
 * ================================================================== */

class KamerplanterPhaseCardEditor extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: "open" });
  }

  setConfig(config) {
    this._config = { entity: "", title: "", ...config };
    if (this._hass) this._render();
  }

  set hass(hass) {
    this._hass = hass;
    this._render();
  }

  _getTimelineEntities() {
    if (!this._hass) return [];
    return Object.keys(this._hass.states)
      .filter((id) => id.startsWith("sensor.kp_") && id.endsWith("_phase_timeline"))
      .map((id) => ({
        id,
        name: this._hass.states[id].attributes.friendly_name || id,
      }))
      .sort((a, b) => a.name.localeCompare(b.name));
  }

  _render() {
    if (!this._config || !this._hass) return;
    const root = this.shadowRoot;

    if (!this._built) {
      root.innerHTML = `
        <style>${PHASE_EDITOR_STYLES}</style>
        <div>
          <div class="kpp-editor__row">
            <label class="kpp-editor__label">Phase Timeline Sensor</label>
            <select class="kpp-editor__select" id="entity"></select>
          </div>
          <div class="kpp-editor__row">
            <label class="kpp-editor__label">Titel (optional)</label>
            <input class="kpp-editor__input" id="title" type="text" placeholder="Phasen-Fortschritt" />
          </div>
        </div>
      `;
      root.getElementById("entity").addEventListener("change", (e) => {
        this._config = { ...this._config, entity: e.target.value };
        this._dispatch();
      });
      root.getElementById("title").addEventListener("input", (e) => {
        this._config = { ...this._config, title: e.target.value };
        this._dispatch();
      });
      this._built = true;
    }

    const select = root.getElementById("entity");
    const entities = this._getTimelineEntities();
    select.innerHTML = "";

    const emptyOpt = document.createElement("option");
    emptyOpt.value = "";
    emptyOpt.textContent = "\u2014 Sensor ausw\u00e4hlen \u2014";
    select.appendChild(emptyOpt);

    for (const ent of entities) {
      const opt = document.createElement("option");
      opt.value = ent.id;
      opt.textContent = ent.name;
      select.appendChild(opt);
    }
    select.value = this._config.entity || "";

    const titleEl = root.getElementById("title");
    if (titleEl.value !== (this._config.title || "")) {
      titleEl.value = this._config.title || "";
    }
  }

  _dispatch() {
    const event = new Event("config-changed", { bubbles: true, composed: true });
    event.detail = { config: this._config };
    this.dispatchEvent(event);
  }
}

customElements.define("kamerplanter-phase-card-editor", KamerplanterPhaseCardEditor);

/* ================================================================== *
 *  Card                                                               *
 * ================================================================== */

class KamerplanterPhaseCard extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: "open" });
    this._built = false;
  }

  setConfig(config) {
    if (!config.entity) {
      throw new Error("Bitte einen Phase-Timeline-Sensor ausw\u00e4hlen");
    }
    this._config = { title: "", ...config };
  }

  set hass(hass) {
    this._hass = hass;
    this._update();
  }

  getCardSize() {
    return 4;
  }

  getGridOptions() {
    return { columns: 6, min_columns: 3, rows: 4, min_rows: 3 };
  }

  static getConfigElement() {
    return document.createElement("kamerplanter-phase-card-editor");
  }

  static getStubConfig(hass) {
    if (!hass) return { entity: "", title: "" };
    const match = Object.keys(hass.states).find(
      (id) => id.startsWith("sensor.kp_") && id.endsWith("_phase_timeline")
    );
    return { entity: match || "", title: "" };
  }

  /* ---- DOM ---- */

  _ensureDom() {
    if (this._built) return;
    this.shadowRoot.innerHTML = `
      <style>${PHASE_CARD_STYLES}</style>
      <ha-card>
        <div class="kpp-header" id="header"></div>
        <div class="kpp-content">
          <div class="kpp-progress" id="progress"></div>
          <div class="kpp-steps" id="steps"></div>
        </div>
      </ha-card>
    `;
    this._built = true;
  }

  _update() {
    if (!this._hass || !this._config) return;

    const stateObj = this._hass.states[this._config.entity];
    if (!stateObj) {
      this.shadowRoot.innerHTML = `
        <style>${PHASE_CARD_STYLES}</style>
        <ha-card><div class="kpp-error">Entity ${kpEsc(this._config.entity)} nicht gefunden</div></ha-card>
      `;
      this._built = false;
      return;
    }

    this._ensureDom();
    const $ = (id) => this.shadowRoot.getElementById(id);

    const attrs = stateObj.attributes;
    const title = this._config.title || attrs.friendly_name || "Phasen-Fortschritt";
    const currentPhase = attrs.current_phase_name || stateObj.state || "\u2014";
    const kamiUrl = kpKami(currentPhase);

    /* Header with Kami */
    $("header").innerHTML = kamiUrl
      ? `<img class="kpp-header__kami" src="${kamiUrl}" alt="${kpEsc(currentPhase)}" />
         <span class="kpp-header__title">${kpEsc(title)}</span>`
      : `<span class="kpp-header__icon">\uD83C\uDF31</span>
         <span class="kpp-header__title">${kpEsc(title)}</span>`;

    /* Progress section */
    $("progress").innerHTML = this._renderProgress(attrs, currentPhase);

    /* Phase stepper with Kami */
    const phases = [];
    for (const [key, val] of Object.entries(attrs)) {
      if (val && typeof val === "object" && "status" in val) {
        phases.push({ name: key, ...val });
      }
    }
    $("steps").innerHTML = this._renderSteps(phases);
  }

  _renderProgress(attrs, currentPhase) {
    const phaseWeek = attrs.phase_week;
    const plannedWeeks = attrs.phase_planned_weeks;
    const remainingWeeks = attrs.phase_remaining_weeks;
    const progressPct = attrs.phase_progress_pct;
    const daysInPhase = attrs.days_in_phase;
    const typicalDays = attrs.typical_duration_days;
    const remainingDays = attrs.remaining_days;

    let progressHtml = "";

    if (phaseWeek != null && plannedWeeks != null && plannedWeeks > 0) {
      const pct = Math.min(100, progressPct || 0);
      const infoText = daysInPhase != null
        ? `Tag ${daysInPhase} / ${typicalDays || "?"}`
        : `Woche ${phaseWeek} / ${plannedWeeks}`;
      const remainText = remainingDays != null
        ? `${remainingDays} ${remainingDays === 1 ? "Tag" : "Tage"} verbleibend`
        : `${remainingWeeks} ${remainingWeeks === 1 ? "Woche" : "Wochen"} verbleibend`;

      progressHtml = `
        <div class="kpp-progress__header">
          <span class="kpp-progress__phase">${kpEsc(kpCapitalize(currentPhase))}</span>
          <span class="kpp-progress__info">${infoText}</span>
        </div>
        <div class="kpp-progress__track">
          <div class="kpp-progress__fill" style="width:${pct}%"></div>
        </div>
        <div class="kpp-progress__footer">
          <span class="kpp-progress__pct">${pct}%</span>
          <span class="kpp-progress__remaining">${remainText}</span>
        </div>
      `;

      /* Next phase hint */
      const nextPlanPhase = attrs.next_plan_phase;
      const nextPhaseWeeks = attrs.next_plan_phase_weeks;
      const weeksUntilNext = attrs.weeks_until_next_phase;

      if (nextPlanPhase != null && weeksUntilNext != null) {
        const label = PHASE_LABELS[nextPlanPhase] || kpCapitalize(nextPlanPhase);
        const nKami = kpKami(nextPlanPhase);
        const kamiImg = nKami
          ? `<img class="kpp-next__kami" src="${nKami}" alt="" />`
          : `<span class="kpp-next__icon">\u27A1</span>`;

        if (weeksUntilNext === 0) {
          progressHtml += `
            <div class="kpp-next kpp-next--active">
              ${kamiImg}
              <span><strong>${kpEsc(label)}</strong> hat begonnen (${nextPhaseWeeks} ${nextPhaseWeeks === 1 ? "Woche" : "Wochen"})</span>
            </div>`;
        } else {
          progressHtml += `
            <div class="kpp-next">
              ${kamiImg}
              <span><strong>${kpEsc(label)}</strong> in ${weeksUntilNext} ${weeksUntilNext === 1 ? "Woche" : "Wochen"}</span>
            </div>`;
        }
      }
    } else {
      progressHtml = `
        <div class="kpp-progress__header">
          <span class="kpp-progress__phase">${kpEsc(kpCapitalize(currentPhase))}</span>
        </div>
        <div class="kpp-progress__nodata">Keine Phasendaten verf\u00fcgbar</div>
      `;
    }

    return progressHtml;
  }

  _renderSteps(phases) {
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
        const cls = prev === "completed" ? "kpp-steps__connector--done"
          : prev === "current" ? "kpp-steps__connector--active"
          : "";
        html += `<div class="kpp-steps__connector ${cls}"></div>`;
      }

      /* Marker */
      const svg = kpKami(p.name);
      let marker = "";
      if (svg) {
        marker = `<img src="${svg}" alt="${kpEsc(p.name)}" />`;
      } else {
        marker = `<div class="kpp-step__dot"></div>`;
      }

      const dateStr = p.started || p.date || "";

      html += `
        <div class="kpp-step kpp-step--${state}">
          <div class="kpp-step__marker${svg ? " kpp-step__marker--kami" : ""}">
            ${marker}
          </div>
          <span class="kpp-step__label">${kpEsc(kpCapitalize(p.name))}</span>
          ${dateStr ? `<span class="kpp-step__date">${kpFmtDateShort(dateStr)}</span>` : ""}
        </div>
      `;
    }
    return html;
  }
}

customElements.define("kamerplanter-phase-card", KamerplanterPhaseCard);

/* ================================================================== *
 *  Registration                                                       *
 * ================================================================== */

window.customCards = window.customCards || [];
window.customCards.push({
  type: "kamerplanter-phase-card",
  name: "Kamerplanter Phasen-Fortschritt",
  description: "Zeigt den Fortschritt der aktuellen Wachstumsphase mit Kami-Illustrationen",
  preview: false,
  documentationURL: "https://kamerplanter.readthedocs.io/de/latest/guides/home-assistant-integration/",
});
