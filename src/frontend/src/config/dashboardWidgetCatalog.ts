import type { ExperienceLevel, DashboardLayout, WidgetPlacement } from '@/api/types';
import type { ModuleKey } from '@/config/moduleCatalog';

/**
 * REQ-045 — declarative dashboard widget catalog.
 *
 * Canonical frontend source of truth for the widgets a user can place on their
 * dashboard. Mirrors the backend registry (``KNOWN_WIDGET_KEYS`` /
 * ``dashboard_widget_catalog``); the shared key set is asserted by the contract
 * test (``dashboard-widgets.json``). Availability (module/permission/light-mode
 * gating) is server-authoritative and layered on top at runtime — this catalog
 * only holds the static, mode-independent metadata.
 */

export type WidgetKey =
  | 'quick_actions'
  | 'active_plants_summary'
  | 'tasks_today'
  | 'care_reminders'
  | 'daily_tip'
  | 'weather_forecast'
  | 'onboarding_progress'
  | 'winter_protection'
  | 'ipm_alerts'
  | 'harvest_forecast'
  | 'next_calendar_events'
  | 'community_activity'
  | 'tank_status'
  | 'phase_timeline'
  | 'plant_grid';

export interface WidgetSize {
  w: number;
  h: number;
}

export interface DashboardWidgetDefinition {
  key: WidgetKey;
  /** i18n key for the label, e.g. 'dashboard.widgets.tasks_today.label' */
  labelKey: string;
  /** i18n key for the explanatory description in the settings tab (UI-NFR-011) */
  descriptionKey: string;
  /** Grouping in the settings tab */
  category: string;
  /** Default set membership (REQ-021) */
  defaultLevel: ExperienceLevel;
  defaultSize: WidgetSize;
  minSize: WidgetSize;
  maxSize: WidgetSize;
  /** Gated via REQ-042; null = bound to core (always visible) */
  requiredModule: ModuleKey | null;
  /**
   * Issue #587 — widget surfaces sensor/actuator data (monitoring/telemetry) and
   * is additionally gated behind the per-user `smart_home_enabled` toggle. When
   * smart home is off the widget is neither rendered nor offered in the picker.
   */
  requiresSmartHome?: boolean;
  /** true → offers a per-widget config dialog */
  hasConfig: boolean;
  /**
   * Panel-level navigation target (issue #439). When set, the whole widget panel
   * becomes a link to this route in read-only mode (gated by module visibility,
   * REQ-042). null/undefined → the panel is non-interactive (read-only overview).
   */
  navigateTo?: string;
}

/** Grid columns per breakpoint (UI-NFR-001): Desktop / Tablet / Mobile. */
export const GRID_COLS_BY_BREAKPOINT = { lg: 12, md: 8, sm: 4 } as const;
export const DASHBOARD_BREAKPOINTS = ['lg', 'md', 'sm'] as const;
export const DASHBOARD_LAYOUT_SCHEMA_VERSION = 2;

function def(
  key: WidgetKey,
  category: string,
  defaultLevel: ExperienceLevel,
  defaultSize: WidgetSize,
  minSize: WidgetSize,
  maxSize: WidgetSize,
  requiredModule: ModuleKey | null,
  hasConfig = false,
  navigateTo?: string,
  requiresSmartHome = false,
): DashboardWidgetDefinition {
  return {
    key,
    labelKey: `dashboard.widgets.${key}.label`,
    descriptionKey: `dashboard.widgets.${key}.description`,
    category,
    defaultLevel,
    defaultSize,
    minSize,
    maxSize,
    requiredModule,
    requiresSmartHome,
    hasConfig,
    navigateTo,
  };
}

const s = (w: number, h: number): WidgetSize => ({ w, h });

export const dashboardWidgetCatalog: Record<WidgetKey, DashboardWidgetDefinition> = {
  // ── Essentials ──
  // h=4 (not 2): at 12 cols the tile Grid (xs:6/sm:4/md:2) still renders one
  // full row of 6 icon tiles + a title line; h=2 (2*44+16=104px) clipped that
  // content in both the edit grid (fixed ROW_HEIGHT) and, previously, the
  // read-only grid. h=4 matches maxSize.h, i.e. the widget can no longer be
  // grown further but starts at a height that actually fits its content.
  quick_actions: def('quick_actions', 'essentials', 'beginner', s(12, 4), s(4, 2), s(12, 4), null),
  tasks_today: def('tasks_today', 'essentials', 'beginner', s(4, 4), s(2, 3), s(8, 8), 'tasks', false, '/aufgaben/queue'),
  care_reminders: def('care_reminders', 'essentials', 'beginner', s(4, 4), s(2, 3), s(8, 8), 'tasks', false, '/aufgaben/queue'),
  active_plants_summary: def('active_plants_summary', 'essentials', 'beginner', s(4, 3), s(2, 2), s(8, 6), 'plants', false, '/pflanzen/plant-instances'),
  onboarding_progress: def('onboarding_progress', 'essentials', 'beginner', s(4, 3), s(2, 2), s(12, 4), null, false, '/onboarding'),

  // ── Insights ──
  daily_tip: def('daily_tip', 'insights', 'beginner', s(4, 4), s(2, 3), s(8, 8), 'ai'),
  weather_forecast: def('weather_forecast', 'insights', 'beginner', s(4, 3), s(2, 2), s(8, 6), null, true),
  harvest_forecast: def('harvest_forecast', 'insights', 'intermediate', s(4, 4), s(2, 3), s(8, 8), 'harvest', true, '/ernte/batches'),
  community_activity: def('community_activity', 'insights', 'intermediate', s(4, 4), s(2, 3), s(8, 8), null),

  // ── Cultivation ──
  winter_protection: def('winter_protection', 'cultivation', 'beginner', s(6, 4), s(3, 3), s(12, 8), 'overwintering', false, '/ueberwinterung/profile'),
  ipm_alerts: def('ipm_alerts', 'cultivation', 'intermediate', s(4, 4), s(2, 3), s(8, 8), 'ipm', false, '/pflanzenschutz/pests'),
  next_calendar_events: def('next_calendar_events', 'cultivation', 'intermediate', s(4, 4), s(2, 3), s(8, 8), 'calendar', false, '/kalender'),
  phase_timeline: def('phase_timeline', 'cultivation', 'expert', s(8, 4), s(3, 3), s(12, 8), 'plants', false, '/phasen/ablaeufe'),
  plant_grid: def('plant_grid', 'cultivation', 'expert', s(8, 5), s(4, 3), s(12, 10), 'plants', false, '/pflanzen/plant-instances'),

  // ── Monitoring ──
  // Issue #587: monitoring widgets surface sensor telemetry → smart-home-gated.
  tank_status: def('tank_status', 'monitoring', 'expert', s(4, 4), s(2, 3), s(8, 8), 'tanks', false, '/standorte/tanks', true),
};

/** Ordered list of categories for grouping in the settings tab. */
export const WIDGET_CATEGORIES: string[] = ['essentials', 'insights', 'cultivation', 'monitoring'];

/**
 * REQ-021 — default widget set per experience level. Higher levels are
 * additive (each includes all widgets of the levels below it).
 */
const BEGINNER_WIDGETS: WidgetKey[] = [
  'quick_actions',
  'tasks_today',
  'care_reminders',
  'active_plants_summary',
  'daily_tip',
  'winter_protection',
  'weather_forecast',
  'onboarding_progress',
];
const INTERMEDIATE_WIDGETS: WidgetKey[] = [
  ...BEGINNER_WIDGETS,
  'ipm_alerts',
  'harvest_forecast',
  'next_calendar_events',
  'community_activity',
];
const EXPERT_WIDGETS: WidgetKey[] = [
  ...INTERMEDIATE_WIDGETS,
  'tank_status',
  'phase_timeline',
  'plant_grid',
];

export const DEFAULT_WIDGETS_BY_LEVEL: Record<ExperienceLevel, WidgetKey[]> = {
  beginner: BEGINNER_WIDGETS,
  intermediate: INTERMEDIATE_WIDGETS,
  expert: EXPERT_WIDGETS,
};

let instanceCounter = 0;
/** Unique instance id for a *newly user-added* widget. NOT for the derived
 *  default layout — that must use deterministic ids (see resolveDefaultLayout)
 *  so re-deriving it across renders keeps stable React keys. */
export function newInstanceId(): string {
  instanceCounter += 1;
  return `w-${instanceCounter.toString(36)}-${Math.floor(performance.now()).toString(36)}`;
}

/**
 * Pack the given widget keys row-by-row into a 12-column ``lg`` grid using each
 * widget's ``defaultSize``. Produces a full layout (widgets + lg placements);
 * md/sm are left empty and derived client-side from lg by react-grid-layout.
 *
 * ``availableKeys`` (when provided) filters out server-unavailable widgets so a
 * fresh default never renders a gated widget.
 */
export function resolveDefaultLayout(level: ExperienceLevel, availableKeys?: ReadonlySet<string>): DashboardLayout {
  const cols = GRID_COLS_BY_BREAKPOINT.lg;
  const keys = DEFAULT_WIDGETS_BY_LEVEL[level].filter((k) => !availableKeys || availableKeys.has(k));

  // Deterministic ids: re-deriving the default across renders yields identical
  // React keys, so widgets reconcile instead of remounting (no dispatch loop).
  const widgets = keys.map((key) => ({ instance_id: `d-${key}`, widget_key: key, config: {} }));
  const placements: WidgetPlacement[] = [];
  let x = 0;
  let y = 0;
  let rowHeight = 0;
  for (let i = 0; i < widgets.length; i += 1) {
    const size = dashboardWidgetCatalog[keys[i]].defaultSize;
    const w = Math.min(size.w, cols);
    if (x + w > cols) {
      x = 0;
      y += rowHeight;
      rowHeight = 0;
    }
    placements.push({ instance_id: widgets[i].instance_id, x, y, w, h: size.h });
    x += w;
    rowHeight = Math.max(rowHeight, size.h);
  }

  return { schema_version: DASHBOARD_LAYOUT_SCHEMA_VERSION, widgets, placements: { lg: placements } };
}

/**
 * Migrate a possibly-v1 layout (schema_version 1 with widgets[].x/y/w/h and a
 * top-level ``columns``) to the v2 shape. Tolerant: unknown shapes fall back to
 * an empty layout. Idempotent for already-v2 layouts.
 */
export function migrateLayout(raw: unknown): DashboardLayout | null {
  if (!raw || typeof raw !== 'object') return null;
  const layout = raw as Record<string, unknown>;
  const widgets = Array.isArray(layout.widgets) ? (layout.widgets as Record<string, unknown>[]) : [];

  // Already v2: has a placements map.
  if (layout.placements && typeof layout.placements === 'object' && !Array.isArray(layout.placements)) {
    return {
      schema_version: DASHBOARD_LAYOUT_SCHEMA_VERSION,
      widgets: widgets.map((w, i) => ({
        instance_id: String(w.instance_id ?? `m-${w.widget_key}-${i}`),
        widget_key: String(w.widget_key),
        config: (w.config as Record<string, unknown>) ?? {},
      })),
      placements: layout.placements as DashboardLayout['placements'],
    };
  }

  // v1: positions live on the widgets themselves → read them as lg placements.
  const lg: WidgetPlacement[] = [];
  const migratedWidgets = widgets.map((w, i) => {
    // Deterministic fallback id (stable React keys across renders).
    const instanceId = String(w.instance_id ?? `m-${w.widget_key}-${i}`);
    if (typeof w.x === 'number' && typeof w.y === 'number') {
      lg.push({
        instance_id: instanceId,
        x: w.x as number,
        y: w.y as number,
        w: (w.w as number) ?? 4,
        h: (w.h as number) ?? 4,
      });
    }
    return {
      instance_id: instanceId,
      widget_key: String(w.widget_key),
      config: (w.config as Record<string, unknown>) ?? {},
    };
  });

  return {
    schema_version: DASHBOARD_LAYOUT_SCHEMA_VERSION,
    widgets: migratedWidgets,
    placements: lg.length ? { lg } : {},
  };
}

/**
 * Derive placements for a breakpoint. A breakpoint with its own placements
 * wins; otherwise fall back to lg (react-grid-layout auto-stacks narrower
 * breakpoints from lg). Widgets present in ``widgets`` but missing a placement
 * are appended in a single stacked column so nothing is ever dropped.
 */
export function placementsForBreakpoint(
  layout: DashboardLayout,
  breakpoint: 'lg' | 'md' | 'sm',
): WidgetPlacement[] {
  const own = layout.placements[breakpoint];
  const base = own && own.length ? own : (layout.placements.lg ?? []);
  const placed = new Set(base.map((p) => p.instance_id));
  const maxY = base.reduce((m, p) => Math.max(m, p.y + p.h), 0);
  const appended: WidgetPlacement[] = [];
  let y = maxY;
  for (const w of layout.widgets) {
    if (!placed.has(w.instance_id)) {
      appended.push({ instance_id: w.instance_id, x: 0, y, w: 4, h: 4 });
      y += 4;
    }
  }
  return [...base, ...appended];
}
