/**
 * Kamerplanter Care Card — Custom Lovelace Card (REQ-030)
 *
 * Displays overdue, today, and upcoming care tasks grouped by urgency.
 * Each row shows plant name + task type + "Done" button.
 * The "Done" button calls kamerplanter.confirm_care service.
 *
 * Data sources:
 *   - sensor.kp_tasks_due_today (today + upcoming)
 *   - sensor.kp_tasks_overdue (overdue tasks)
 *
 * Configuration (in Lovelace YAML):
 *   type: custom:kamerplanter-care-card
 *   title: Pflege-Dashboard         # optional
 *   upcoming_days: 3                # optional, default 3
 */

const CARD_VERSION = "1.0.0";

class KamerplanterCareCard extends HTMLElement {
  static get properties() {
    return {
      hass: {},
      config: {},
    };
  }

  set hass(hass) {
    this._hass = hass;
    this._render();
  }

  setConfig(config) {
    this._config = {
      title: config.title || "Kamerplanter Pflege",
      upcoming_days: config.upcoming_days || 3,
      entity_due: config.entity_due || "sensor.kp_tasks_due_today",
      entity_overdue: config.entity_overdue || "sensor.kp_tasks_overdue",
    };
  }

  getCardSize() {
    return 3;
  }

  static getConfigElement() {
    return undefined;
  }

  static getStubConfig() {
    return {
      title: "Kamerplanter Pflege",
      upcoming_days: 3,
    };
  }

  connectedCallback() {
    if (!this.shadowRoot) {
      this.attachShadow({ mode: "open" });
    }
    this._render();
  }

  _getTaskIcon(category) {
    const icons = {
      watering: "mdi:watering-can",
      giessen: "mdi:watering-can",
      fertilizing: "mdi:bottle-tonic",
      duengen: "mdi:bottle-tonic",
      repotting: "mdi:flower-pollen",
      umtopfen: "mdi:flower-pollen",
      pest_check: "mdi:bug",
      schaedlingskontrolle: "mdi:bug",
      pruning: "mdi:content-cut",
      schneiden: "mdi:content-cut",
    };
    const key = (category || "").toLowerCase();
    return icons[key] || "mdi:clipboard-check-outline";
  }

  _buildTaskRows(tasks, colorClass) {
    if (!tasks || tasks.length === 0) return "";
    return tasks
      .map(
        (task) => `
      <div class="task-row ${colorClass}">
        <ha-icon icon="${this._getTaskIcon(task.category)}" class="task-icon"></ha-icon>
        <div class="task-info">
          <span class="plant-name">${this._escapeHtml(task.name || "Unknown")}</span>
          <span class="task-type">${this._escapeHtml(task.category || "Pflege")}</span>
        </div>
        <button class="done-btn ${colorClass}-btn"
                data-task-key="${this._escapeAttr(task.task_key || "")}"
                data-notification-key="${this._escapeAttr(task.notification_key || task.task_key || "")}">
          <ha-icon icon="mdi:check" class="btn-icon"></ha-icon>
        </button>
      </div>
    `
      )
      .join("");
  }

  _escapeHtml(str) {
    const div = document.createElement("div");
    div.textContent = str;
    return div.innerHTML;
  }

  _escapeAttr(str) {
    return String(str).replace(/"/g, "&quot;").replace(/'/g, "&#39;");
  }

  _render() {
    if (!this.shadowRoot || !this._hass || !this._config) return;

    const dueTodayState = this._hass.states[this._config.entity_due];
    const overdueState = this._hass.states[this._config.entity_overdue];

    const overdueTasks =
      overdueState && overdueState.attributes
        ? overdueState.attributes.plants || []
        : [];
    const dueTodayTasks =
      dueTodayState && dueTodayState.attributes
        ? dueTodayState.attributes.plants || []
        : [];
    const urgencyCounts =
      dueTodayState && dueTodayState.attributes
        ? dueTodayState.attributes.urgency_counts || {}
        : {};

    const totalCount = overdueTasks.length + dueTodayTasks.length;
    const overdueCount = overdueTasks.length;
    const dueCount = dueTodayTasks.length;

    const hasData = totalCount > 0;

    this.shadowRoot.innerHTML = `
      <style>
        :host {
          display: block;
        }
        ha-card {
          padding: 16px;
        }
        .header {
          display: flex;
          align-items: center;
          justify-content: space-between;
          margin-bottom: 12px;
        }
        .header-title {
          font-size: 1.1rem;
          font-weight: 500;
          color: var(--primary-text-color);
        }
        .badge {
          display: inline-flex;
          align-items: center;
          justify-content: center;
          min-width: 24px;
          height: 24px;
          border-radius: 12px;
          padding: 0 6px;
          font-size: 0.8rem;
          font-weight: 600;
          color: #fff;
        }
        .badge-overdue {
          background-color: var(--error-color, #f44336);
        }
        .badge-due {
          background-color: var(--warning-color, #ff9800);
        }
        .badge-ok {
          background-color: var(--success-color, #4caf50);
        }
        .section-label {
          font-size: 0.75rem;
          font-weight: 600;
          text-transform: uppercase;
          letter-spacing: 0.08em;
          margin: 12px 0 6px 0;
          padding: 0;
        }
        .section-overdue .section-label {
          color: var(--error-color, #f44336);
        }
        .section-today .section-label {
          color: var(--warning-color, #ff9800);
        }
        .task-row {
          display: flex;
          align-items: center;
          padding: 8px 0;
          border-bottom: 1px solid var(--divider-color, rgba(0,0,0,0.12));
          gap: 12px;
        }
        .task-row:last-child {
          border-bottom: none;
        }
        .task-icon {
          --mdc-icon-size: 20px;
          color: var(--secondary-text-color);
          flex-shrink: 0;
        }
        .overdue .task-icon {
          color: var(--error-color, #f44336);
        }
        .today .task-icon {
          color: var(--warning-color, #ff9800);
        }
        .task-info {
          flex: 1;
          display: flex;
          flex-direction: column;
          min-width: 0;
        }
        .plant-name {
          font-size: 0.9rem;
          font-weight: 500;
          color: var(--primary-text-color);
          overflow: hidden;
          text-overflow: ellipsis;
          white-space: nowrap;
        }
        .task-type {
          font-size: 0.75rem;
          color: var(--secondary-text-color);
          text-transform: capitalize;
        }
        .done-btn {
          display: inline-flex;
          align-items: center;
          justify-content: center;
          width: 36px;
          height: 36px;
          min-width: 36px;
          border-radius: 50%;
          border: none;
          cursor: pointer;
          transition: background-color 0.2s, opacity 0.2s;
          flex-shrink: 0;
          background-color: var(--success-color, #4caf50);
          color: #fff;
        }
        .done-btn:hover {
          opacity: 0.85;
        }
        .done-btn:active {
          opacity: 0.7;
        }
        .done-btn:disabled {
          opacity: 0.4;
          cursor: not-allowed;
        }
        .btn-icon {
          --mdc-icon-size: 18px;
          color: #fff;
        }
        .empty-state {
          display: flex;
          flex-direction: column;
          align-items: center;
          padding: 24px 16px;
          color: var(--secondary-text-color);
          text-align: center;
        }
        .empty-state ha-icon {
          --mdc-icon-size: 48px;
          color: var(--success-color, #4caf50);
          margin-bottom: 12px;
        }
        .empty-state .title {
          font-size: 1rem;
          font-weight: 500;
          margin-bottom: 4px;
        }
        .empty-state .subtitle {
          font-size: 0.85rem;
        }
      </style>
      <ha-card>
        <div class="header">
          <span class="header-title">${this._escapeHtml(this._config.title)}</span>
          ${
            overdueCount > 0
              ? `<span class="badge badge-overdue">${overdueCount}</span>`
              : dueCount > 0
                ? `<span class="badge badge-due">${dueCount}</span>`
                : `<span class="badge badge-ok">0</span>`
          }
        </div>
        ${
          !hasData
            ? `
          <div class="empty-state">
            <ha-icon icon="mdi:check-circle-outline"></ha-icon>
            <div class="title">Alles erledigt!</div>
            <div class="subtitle">Keine Pflegeaufgaben ausstehend.</div>
          </div>
        `
            : `
          ${
            overdueTasks.length > 0
              ? `
            <div class="section-overdue">
              <div class="section-label">Ueberfaellig (${overdueTasks.length})</div>
              ${this._buildTaskRows(overdueTasks, "overdue")}
            </div>
          `
              : ""
          }
          ${
            dueTodayTasks.length > 0
              ? `
            <div class="section-today">
              <div class="section-label">Heute faellig (${dueTodayTasks.length})</div>
              ${this._buildTaskRows(dueTodayTasks, "today")}
            </div>
          `
              : ""
          }
        `
        }
      </ha-card>
    `;

    // Attach click handlers to done buttons
    this.shadowRoot.querySelectorAll(".done-btn").forEach((btn) => {
      btn.addEventListener("click", (e) => this._handleDoneClick(e));
    });
  }

  _handleDoneClick(event) {
    const btn = event.currentTarget;
    const notificationKey = btn.dataset.notificationKey;
    if (!notificationKey || !this._hass) return;

    // Disable button immediately to prevent double-clicks
    btn.disabled = true;

    this._hass.callService("kamerplanter", "confirm_care", {
      notification_key: notificationKey,
      action: "confirmed",
    });

    // Visual feedback: replace icon with checkmark
    btn.innerHTML = '<ha-icon icon="mdi:check-all" class="btn-icon"></ha-icon>';
    btn.style.backgroundColor = "var(--secondary-text-color, #9e9e9e)";
  }
}

customElements.define("kamerplanter-care-card", KamerplanterCareCard);

window.customCards = window.customCards || [];
window.customCards.push({
  type: "kamerplanter-care-card",
  name: "Kamerplanter Care Card",
  description:
    "Displays overdue and upcoming plant care tasks with actionable buttons.",
  preview: true,
});

console.info(
  `%c KAMERPLANTER-CARE-CARD %c v${CARD_VERSION} `,
  "color: white; background: #4CAF50; font-weight: bold;",
  "color: #4CAF50; background: white; font-weight: bold;"
);
