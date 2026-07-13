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
  | 'calendar'
  | 'watering'
  | 'tasks'
  | 'nutrition'
  | 'tanks'
  | 'aquaponics'
  | 'substrates'
  | 'calculators'
  | 'ipm'
  | 'harvest'
  | 'post_harvest'
  | 'runs'
  | 'propagation'
  | 'overwintering'
  | 'phases'
  | 'inventory'
  | 'master_data'
  | 'companion'
  | 'automation'
  | 'ai'
  | 'ai_assistant'
  | 'glossary';

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
  /**
   * Issue #587 — module surfaces sensor/actuator UI and is therefore additionally
   * gated behind the per-user `smart_home_enabled` toggle (UserPreference). When
   * smart home is disabled the module is force-hidden regardless of the experience
   * level or a personal REQ-042 override. Presentation-only: the backend keeps
   * serving all data.
   */
  requiresSmartHome?: boolean;
}

function def(
  key: ModuleKey,
  category: string,
  defaultLevel: ExperienceLevel,
  core: boolean,
  navPaths: string[],
  requiresSmartHome = false,
): ModuleDefinition {
  return {
    key,
    labelKey: `modules.${key}.label`,
    descriptionKey: `modules.${key}.description`,
    category,
    defaultLevel,
    core,
    navPaths,
    requiresSmartHome,
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
  aquaponics: def('aquaponics', 'nutrition_water', 'expert', false, ['/aquaponik']),
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
  // Owns the more specific /ernte/nachernte sidebar entry; the longest-path rule
  // in findModuleByPath lets it govern that item independently of `harvest`
  // (which owns the /ernte prefix and thus the batches entry).
  post_harvest: def('post_harvest', 'harvest', 'expert', false, ['/ernte/nachernte']),

  // ── Cultivation ──
  runs: def('runs', 'cultivation', 'expert', false, ['/durchlaeufe']),
  propagation: def('propagation', 'cultivation', 'expert', false, ['/vermehrung']),
  overwintering: def('overwintering', 'cultivation', 'intermediate', false, [
    '/ueberwinterung',
  ]),
  phases: def('phases', 'cultivation', 'expert', false, ['/phasen']),

  // ── Inventory & equipment ──
  inventory: def('inventory', 'inventory', 'beginner', false, ['/inventree']),

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
  // Owns the real /umgebungssteuerung sidebar entry (REQ-018). The section is
  // ungated in navItemConfig, so the default level is `beginner` to keep the
  // sidebar and the ModuleGuard/settings visibility in agreement. Issue #587:
  // actuator control is a smart-home surface, so it is additionally gated behind
  // the `smart_home_enabled` toggle (hidden until the user opts in).
  automation: def('automation', 'automation', 'beginner', false, ['/umgebungssteuerung'], true),

  // ── AI ──
  ai: def('ai', 'ai', 'intermediate', false, [
    '/pflanzen/identifikation',
    '/pflanzenschutz/erkennung',
  ]),
  ai_assistant: def('ai_assistant', 'ai', 'beginner', false, ['/ki-assistent']),

  // ── Knowledge & reference ──
  glossary: def('glossary', 'knowledge', 'beginner', false, ['/glossar']),
};

/** Ordered list of non-core categories for grouping in the settings dialog. */
export const MODULE_CATEGORIES: string[] = [
  'care_planning',
  'nutrition_water',
  'plant_protection',
  'harvest',
  'cultivation',
  'inventory',
  'master_data',
  'automation',
  'ai',
  'knowledge',
];

/**
 * Resolve which module owns a given navigation path. A path is owned when it
 * equals one of a module's navPaths or is a sub-path thereof.
 *
 * When several navPaths match (e.g. `/pflanzenschutz` owned by `ipm` and the
 * more specific `/pflanzenschutz/erkennung` owned by `ai`), the longest — i.e.
 * most specific — navPath wins, so a nested path can belong to a different
 * module than its parent prefix.
 */
export function findModuleByPath(path: string): ModuleDefinition | undefined {
  let best: ModuleDefinition | undefined;
  let bestLength = -1;
  for (const m of Object.values(moduleCatalog)) {
    for (const p of m.navPaths) {
      if ((path === p || path.startsWith(p + '/')) && p.length > bestLength) {
        best = m;
        bestLength = p.length;
      }
    }
  }
  return best;
}
