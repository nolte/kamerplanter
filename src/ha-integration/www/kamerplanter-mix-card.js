/**
 * Ensure HA Lit components (ha-entity-picker, ha-textfield) are loaded.
 */
const _haComponentsReadyMix = (async () => {
  if (customElements.get("ha-entity-picker")) return;
  await customElements.whenDefined("hui-entities-card");
  const helpers = await window.loadCardHelpers?.();
  if (helpers) {
    const temp = await helpers.createCardElement({ type: "entities", entities: [] });
    if (temp && temp.constructor?.getConfigElement) await temp.constructor.getConfigElement();
  }
  await customElements.whenDefined("ha-entity-picker");
})();

/**
 * Kamerplanter Mix Card Editor
 * Uses ha-entity-picker and ha-textfield for native HA look & feel.
 */
class KamerplanterMixCardEditor extends HTMLElement {
  setConfig(config) {
    this._config = { entities: [], title: "", ...config };
    if (this._hass) this._scheduleRender();
  }

  set hass(hass) {
    this._hass = hass;
    this._scheduleRender();
  }

  async _scheduleRender() {
    await _haComponentsReadyMix;
    this._render();
  }

  _getMixEntityFilter() {
    if (!this._hass) return [];
    const selected = new Set(this._config.entities || []);
    return Object.keys(this._hass.states)
      .filter((id) => id.startsWith("sensor.kp_") && id.endsWith("_mix"))
      .filter((id) => !selected.has(id));
  }

  _render() {
    if (!this._config || !this._hass) return;

    // Clear previous content
    this.innerHTML = "";

    // Style
    const style = document.createElement("style");
    style.textContent = `
      .editor-row { margin-bottom: 16px; }
      .entity-list { display: flex; flex-direction: column; gap: 6px; margin-bottom: 12px; }
      .entity-item { display: flex; align-items: center; gap: 8px; padding: 6px 8px; background: var(--card-background-color, #fff); border: 1px solid var(--divider-color, #e0e0e0); border-radius: 8px; }
      .entity-item ha-icon { color: var(--secondary-text-color); flex-shrink: 0; --mdc-icon-size: 20px; }
      .entity-item span { flex: 1; font-size: 0.85em; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
      .entity-item button { border: none; background: none; cursor: pointer; color: var(--error-color, #db4437); font-size: 1.1em; padding: 4px 6px; border-radius: 4px; }
      .entity-item button:hover { background: rgba(219,68,55,0.08); }
      .add-row { display: flex; gap: 8px; align-items: center; }
      .add-row ha-entity-picker { flex: 1; }
      button.add-btn { padding: 8px 16px; border: 1px solid var(--primary-color, #03a9f4); background: var(--primary-color, #03a9f4); color: #fff; border-radius: 8px; cursor: pointer; font-size: 0.85em; font-weight: 500; white-space: nowrap; flex-shrink: 0; }
      button.add-btn:hover { opacity: 0.9; }
      .section-label { font-size: 0.8em; font-weight: 600; color: var(--secondary-text-color); text-transform: uppercase; letter-spacing: 0.05em; margin: 0 0 8px; }
      .hint { font-size: 0.75em; color: var(--secondary-text-color); font-style: italic; margin-top: 8px; }
      ha-textfield { display: block; width: 100%; }
      ha-entity-picker { display: block; }
    `;
    this.appendChild(style);

    // Title field
    const titleRow = document.createElement("div");
    titleRow.className = "editor-row";
    const titleEl = document.createElement("ha-textfield");
    titleEl.label = "Titel";
    titleEl.placeholder = "Mix Rezept";
    titleEl.value = this._config.title || "";
    titleRow.appendChild(titleEl);
    this.appendChild(titleRow);

    // Entity section
    const entityRow = document.createElement("div");
    entityRow.className = "editor-row";

    const sectionLabel = document.createElement("div");
    sectionLabel.className = "section-label";
    sectionLabel.textContent = "Channel Sensoren";
    entityRow.appendChild(sectionLabel);

    // Build selected entity list
    const listEl = document.createElement("div");
    listEl.className = "entity-list";
    for (const entityId of this._config.entities || []) {
      const friendly = this._hass?.states[entityId]?.attributes?.friendly_name || entityId;
      const item = document.createElement("div");
      item.className = "entity-item";
      item.innerHTML = `<ha-icon icon="mdi:flask-outline"></ha-icon><span>${friendly}</span><button data-entity="${entityId}">\u2715</button>`;
      listEl.appendChild(item);
    }
    entityRow.appendChild(listEl);

    // Add picker row
    const addRow = document.createElement("div");
    addRow.className = "add-row";
    const addPicker = document.createElement("ha-entity-picker");
    addPicker.hass = this._hass;
    addPicker.label = "Sensor hinzuf\u00fcgen";
    addPicker.allowCustomEntity = true;
    addPicker.includeEntities = this._getMixEntityFilter();
    addRow.appendChild(addPicker);
    const addBtn = document.createElement("button");
    addBtn.className = "add-btn";
    addBtn.textContent = "+";
    addRow.appendChild(addBtn);
    entityRow.appendChild(addRow);

    const hint = document.createElement("div");
    hint.className = "hint";
    hint.textContent = "Volumen wird direkt aus KA geladen (Tank/Gie\u00dfkanne). Freie Eingabe in der Card m\u00f6glich.";
    entityRow.appendChild(hint);
    this.appendChild(entityRow);

    // Bind title
    titleEl.addEventListener("input", (e) => {
      this._config = { ...this._config, title: e.target.value };
      this._fireChanged();
    });

    // Bind add button
    addBtn.addEventListener("click", () => {
      const val = addPicker.value;
      if (val && !(this._config.entities || []).includes(val)) {
        this._config = { ...this._config, entities: [...(this._config.entities || []), val] };
        this._fireChanged();
        this._render();
      }
    });

    // Bind remove buttons
    listEl.querySelectorAll("button[data-entity]").forEach((btn) => {
      btn.addEventListener("click", () => {
        this._config = { ...this._config, entities: (this._config.entities || []).filter((e) => e !== btn.dataset.entity) };
        this._fireChanged();
        this._render();
      });
    });
  }

  _fireChanged() {
    this.dispatchEvent(new CustomEvent("config-changed", { detail: { config: this._config }, bubbles: true, composed: true }));
  }
}
customElements.define("kamerplanter-mix-card-editor", KamerplanterMixCardEditor);

/**
 * Kamerplanter Mix Card
 *
 * Three display modes:
 *   "perL"   — ml per Liter (default)
 *   "ka"     — total ml using KA volume (tank / watering can)
 *   "custom" — total ml using user-entered custom volume
 */
class KamerplanterMixCard extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: "open" });
    this._mode = "perL";
    this._customVols = {};
  }

  set hass(hass) {
    this._hass = hass;
    if (this._config) this._render();
  }

  setConfig(config) {
    if (!config.entities || !config.entities.length) throw new Error("Please define at least one entity");
    this._config = config;
  }

  getCardSize() { return 3; }
  getGridOptions() { return { columns: 6, min_columns: 3, rows: 3, min_rows: 2 }; }
  static getConfigElement() { return document.createElement("kamerplanter-mix-card-editor"); }
  static getStubConfig() { return { entities: [], title: "Mix Rezept" }; }

  _updateDosages(entityId, vol) {
    const stateObj = this._hass.states[entityId];
    if (!stateObj) return;
    const attrs = stateObj.attributes;
    const input = this.shadowRoot.querySelector(`.vol-input[data-entity="${entityId}"]`);
    if (!input) return;
    const channelDiv = input.closest(".channel");
    if (!channelDiv) return;
    const rows = channelDiv.querySelectorAll(".dosage-row");
    const dosages = [];
    for (const [key, val] of Object.entries(attrs)) {
      if (key.endsWith("(ml/L)") && val != null) dosages.push({ name: key.replace(" (ml/L)", ""), mlPerL: val });
    }
    dosages.sort((a, b) => b.mlPerL - a.mlPerL);
    let i = 0;
    for (const d of dosages) {
      if (rows[i]) { const mlEl = rows[i].querySelector(".ml-value"); if (mlEl) mlEl.textContent = `${(d.mlPerL * vol).toFixed(1)} ml`; }
      i++;
    }
  }

  _channelVol(entityId) {
    if (!entityId || !this._hass) return null;
    const s = this._hass.states[entityId];
    if (!s) return null;
    const v = s.attributes.volume_liters;
    return v && v > 0 ? v : null;
  }

  _render() {
    if (!this._hass || !this._config) return;
    const title = this._config.title || "Mix Rezept";
    const mode = this._mode;

    let anyKaVol = false;
    for (const eid of this._config.entities) { if (this._channelVol(eid)) { anyKaVol = true; break; } }
    for (const eid of this._config.entities) { if (!(eid in this._customVols)) this._customVols[eid] = this._channelVol(eid) || 10; }

    let channelsHtml = "";
    for (const entityId of this._config.entities) {
      const stateObj = this._hass.states[entityId];
      if (!stateObj) { channelsHtml += `<div class="channel missing">Entity ${entityId} nicht gefunden</div>`; continue; }
      const attrs = stateObj.attributes;
      const channelName = attrs.friendly_name || entityId;
      const currentWeek = attrs.current_week;
      const kaVol = this._channelVol(entityId);
      const customVol = this._customVols[entityId] || 10;
      let effVol = null;
      if (mode === "ka" && kaVol) effVol = kaVol;
      else if (mode === "custom" && customVol > 0) effVol = customVol;

      const dosages = [];
      for (const [key, val] of Object.entries(attrs)) {
        if (key.endsWith("(ml/L)") && val != null) dosages.push({ name: key.replace(" (ml/L)", ""), mlPerL: val });
      }
      dosages.sort((a, b) => b.mlPerL - a.mlPerL);

      channelsHtml += `<div class="channel"><div class="channel-header">`;
      channelsHtml += `<span class="channel-name">${channelName}</span><span class="channel-badges">`;
      if (currentWeek) channelsHtml += `<span class="badge week">W${currentWeek}</span>`;
      if (mode === "custom") {
        channelsHtml += `<span class="vol-input-wrap"><input type="number" class="vol-input" data-entity="${entityId}" value="${customVol}" min="0.1" step="0.5" /><span class="vol-unit">L</span></span>`;
      } else if (effVol) {
        channelsHtml += `<span class="badge vol">${effVol} L</span>`;
      }
      channelsHtml += `</span></div>`;

      if (!dosages.length) {
        channelsHtml += `<div class="empty">Keine Dosierungen</div>`;
      } else {
        channelsHtml += `<div class="dosage-list">`;
        for (const d of dosages) {
          const valHtml = effVol
            ? `<span class="ml-value">${(d.mlPerL * effVol).toFixed(1)} ml</span><span class="ml-sub">${d.mlPerL} ml/L</span>`
            : `<span class="ml-value">${d.mlPerL} ml/L</span>`;
          channelsHtml += `<div class="dosage-row"><span class="product-name">${d.name}</span><span class="dosage-values">${valHtml}</span></div>`;
        }
        channelsHtml += `</div>`;
      }
      channelsHtml += `</div>`;
    }

    const seg = (id, label, active) => `<button class="seg-btn ${active ? "active" : ""}" data-mode="${id}">${label}</button>`;
    let modeBarHtml = `<div class="mode-bar">`;
    modeBarHtml += seg("perL", "ml/L", mode === "perL");
    if (anyKaVol) modeBarHtml += seg("ka", "Tank/Kanne", mode === "ka");
    modeBarHtml += seg("custom", "Frei", mode === "custom");
    modeBarHtml += `</div>`;

    this.shadowRoot.innerHTML = `
      <style>
        :host { display: block; overflow: hidden; box-sizing: border-box; }
        ha-card { padding: 0; overflow: hidden; }
        .card-header { padding: 12px 16px 0; display: flex; align-items: center; justify-content: space-between; }
        .card-title { font-size: 1.1em; font-weight: 500; }
        .card-content { padding: 8px 16px 16px; }
        .mode-bar { display: flex; border: 1px solid #bdbdbd; border-radius: 8px; overflow: hidden; margin-bottom: 12px; }
        .seg-btn { flex: 1; padding: 6px 0; border: none; background: transparent; font-size: 0.8em; font-weight: 500; color: #757575; cursor: pointer; transition: all 0.15s; border-right: 1px solid #bdbdbd; }
        .seg-btn:last-child { border-right: none; }
        .seg-btn.active { background: #1976d2; color: #fff; font-weight: 600; }
        .seg-btn:not(.active):hover { background: #f5f5f5; }
        .vol-input-wrap { display: inline-flex; align-items: center; gap: 2px; background: #f5f5f5; border: 1px solid #bdbdbd; border-radius: 6px; padding: 1px 6px 1px 2px; }
        .vol-input { width: 52px; padding: 2px 4px; border: none; background: transparent; font-size: 0.82em; font-weight: 600; text-align: right; outline: none; -moz-appearance: textfield; }
        .vol-input::-webkit-outer-spin-button, .vol-input::-webkit-inner-spin-button { -webkit-appearance: none; margin: 0; }
        .vol-unit { font-size: 0.75em; color: #757575; font-weight: 500; }
        .channel { margin-bottom: 16px; }
        .channel:last-child { margin-bottom: 0; }
        .channel-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 8px; padding-bottom: 4px; border-bottom: 1px solid #e0e0e0; }
        .channel-name { font-weight: 500; font-size: 0.95em; }
        .channel-badges { display: flex; gap: 4px; }
        .badge { font-size: 0.72em; padding: 2px 8px; border-radius: 10px; font-weight: 600; }
        .badge.week { background: #03a9f4; color: #fff; }
        .badge.vol { background: #e8f5e9; color: #2e7d32; }
        .dosage-list { display: flex; flex-direction: column; gap: 4px; }
        .dosage-row { display: flex; align-items: center; justify-content: space-between; padding: 4px 0; border-bottom: 1px solid #f0f0f0; }
        .dosage-row:last-child { border-bottom: none; }
        .product-name { font-size: 0.9em; }
        .dosage-values { display: flex; align-items: baseline; gap: 6px; white-space: nowrap; }
        .ml-value { font-size: 0.9em; font-weight: 600; }
        .ml-sub { font-size: 0.72em; color: #9e9e9e; }
        .empty { font-size: 0.85em; color: #9e9e9e; font-style: italic; }
        .missing { color: #db4437; font-size: 0.85em; }
      </style>
      <ha-card>
        <div class="card-header"><span class="card-title">${title}</span></div>
        <div class="card-content">
          ${modeBarHtml}
          ${channelsHtml}
        </div>
      </ha-card>`;

    this.shadowRoot.querySelectorAll(".seg-btn").forEach((btn) => {
      btn.addEventListener("click", () => { this._mode = btn.dataset.mode; this._render(); });
    });
    this.shadowRoot.querySelectorAll(".vol-input").forEach((input) => {
      input.addEventListener("input", (e) => {
        const v = parseFloat(e.target.value);
        const eid = e.target.dataset.entity;
        if (v > 0 && eid) { this._customVols[eid] = v; this._updateDosages(eid, v); }
      });
    });
  }
}

customElements.define("kamerplanter-mix-card", KamerplanterMixCard);
window.customCards = window.customCards || [];
window.customCards.push({ type: "kamerplanter-mix-card", name: "Kamerplanter Mix Rezept", description: "D\u00fcnger-Dosierungen mit ml/L, Tank/Kanne oder freier Menge" });
