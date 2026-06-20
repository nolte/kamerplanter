import type { ExperienceLevel } from '@/api/types';

/**
 * REQ-042 — declarative module catalog.
 *
 * Canonical source of truth for the feature modules the user can show/hide.
 * Each module owns one or more navigation paths; visibility of those paths is
 * derived from the experience level (REQ-021) plus the personal overrides.
 *
 * navPaths reference the real application routes (see routes/AppRoutes.tsx and
 * layouts/Sidebar.tsx) and may be prefixes — `findModuleByPath` matches a
 * concrete path against `p` itself or any sub-path `p + '/...'`.
 */

export type ModuleKey =
  | 'dashboard'
  | 'plants'
  | 'locations'
  | 'settings'
  | 'onboarding'
  | 'care'
  | 'calendar'
  | 'watering'
  | 'tasks'
  | 'nutrition'
  | 'tanks'
  | 'substrates'
  | 'calculators'
  | 'ipm'
  | 'harvest'
  | 'post_harvest'
  | 'runs'
  | 'propagation'
  | 'master_data'
  | 'companion'
  | 'sensors'
  | 'automation'
  | 'smart_home'
  | 'ai';

export interface ModuleDefinition {
  key: ModuleKey;
  /** i18n key for the label, e.g. 'modules.tanks.label' */
  labelKey: string;
  /** i18n key for the explanatory description in the settings dialog */
  descriptionKey: string;
  /** Grouping in the settings dialog, e.g. 'nutrition_water' */
  category: string;
  /** Default visibility without an override (follows REQ-021) */
  defaultLevel: ExperienceLevel;
  /** Core module: never hideable */
  core: boolean;
  /** Navigation paths shown/hidden together with this module */
  navPaths: string[];
}

function def(
  key: ModuleKey,
  category: string,
  defaultLevel: ExperienceLevel,
  core: boolean,
  navPaths: string[],
): ModuleDefinition {
  return {
    key,
    labelKey: `modules.${key}.label`,
    descriptionKey: `modules.${key}.description`,
    category,
    defaultLevel,
    core,
    navPaths,
  };
}

export const moduleCatalog: Record<ModuleKey, ModuleDefinition> = {
  // ── Core (never hideable) ──
  dashboard: def('dashboard', 'core', 'beginner', true, ['/dashboard']),
  plants: def('plants', 'core', 'beginner', true, ['/pflanzen/plant-instances']),
  locations: def('locations', 'core', 'beginner', true, [
    '/standorte/sites',
    '/standorte/locations',
    '/standorte/slots',
  ]),
  settings: def('settings', 'core', 'beginner', true, ['/settings']),
  onboarding: def('onboarding', 'core', 'beginner', true, ['/onboarding']),

  // ── Care & planning ──
  care: def('care', 'care_planning', 'beginner', false, ['/pflege']),
  calendar: def('calendar', 'care_planning', 'beginner', false, ['/kalender']),
  watering: def('watering', 'care_planning', 'beginner', false, ['/giessprotokoll']),
  tasks: def('tasks', 'care_planning', 'beginner', false, [
    '/aufgaben/queue',
    '/aufgaben/workflows',
    '/aufgaben/tasks',
  ]),

  // ── Nutrition & water ──
  nutrition: def('nutrition', 'nutrition_water', 'intermediate', false, [
    '/duengung/fertilizers',
    '/duengung/plans',
    '/duengung/feeding-events',
  ]),
  tanks: def('tanks', 'nutrition_water', 'expert', false, ['/standorte/tanks']),
  substrates: def('substrates', 'nutrition_water', 'expert', false, [
    '/standorte/substrates',
  ]),
  calculators: def('calculators', 'nutrition_water', 'expert', false, [
    '/pflanzen/calculations',
    '/duengung/calculations',
  ]),

  // ── Plant protection ──
  ipm: def('ipm', 'plant_protection', 'expert', false, ['/pflanzenschutz']),

  // ── Harvest ──
  harvest: def('harvest', 'harvest', 'expert', false, ['/ernte']),
  post_harvest: def('post_harvest', 'harvest', 'expert', false, ['/post-harvest']),

  // ── Cultivation ──
  runs: def('runs', 'cultivation', 'expert', false, ['/durchlaeufe']),
  propagation: def('propagation', 'cultivation', 'expert', false, ['/vermehrung']),

  // ── Master data ──
  master_data: def('master_data', 'master_data', 'intermediate', false, [
    '/stammdaten/botanical-families',
    '/stammdaten/species',
    '/stammdaten/activities',
    '/stammdaten/import',
  ]),
  companion: def('companion', 'master_data', 'expert', false, [
    '/stammdaten/companion-planting',
    '/stammdaten/crop-rotation',
  ]),

  // ── Automation ──
  sensors: def('sensors', 'automation', 'expert', false, ['/sensorik']),
  automation: def('automation', 'automation', 'expert', false, ['/umgebung']),
  smart_home: def('smart_home', 'automation', 'expert', false, ['/smart-home']),

  // ── AI ──
  ai: def('ai', 'ai', 'intermediate', false, ['/pflanzen/identifikation']),
};

/** Ordered list of non-core categories for grouping in the settings dialog. */
export const MODULE_CATEGORIES: string[] = [
  'care_planning',
  'nutrition_water',
  'plant_protection',
  'harvest',
  'cultivation',
  'master_data',
  'automation',
  'ai',
];

/**
 * Resolve which module owns a given navigation path. A path is owned when it
 * equals one of a module's navPaths or is a sub-path thereof.
 */
export function findModuleByPath(path: string): ModuleDefinition | undefined {
  return Object.values(moduleCatalog).find((m) =>
    m.navPaths.some((p) => path === p || path.startsWith(p + '/')),
  );
}
