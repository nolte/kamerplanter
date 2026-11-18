/**
 * Domain colour tokens — the single source for growth-phase, sensor-metric and calendar-category colours
 * (#3021, UI-NFR-006 / UI-NFR-016 R-006/R-008).
 *
 * Every view that paints a phase, a metric or a calendar category reads its colour from here, through
 * `theme.palette.phase` / `.metric` / `.eventCategory` (light and dark variants) and the lookup functions below.
 * Before this module the phase map was declared seven times with four conflicting palettes; the guard
 * `test/guards/domainColorsSingleSource.test.ts` fails when a colour map is declared again outside `src/theme/`.
 *
 * Phase colours are graphics (bars, dots, swatches), never the only cue: each view also prints the phase label.
 * Text drawn on top of one of these colours takes {@link readableTextOn}, which picks the black or white that
 * reaches the higher contrast on the painted surface.
 */
import { getContrastRatio, type Theme } from '@mui/material/styles';
import type { CalendarEventCategory } from '@/api/types';

type ModeColor = { readonly light: string; readonly dark: string };
type ThemeMode = 'light' | 'dark';

// ── Growth phases ───────────────────────────────────────────────────

/** Phases with a colour of their own. Every other phase name maps onto one of these via {@link PHASE_ALIASES}. */
export const PHASE_COLOR_KEYS = [
  'germination',
  'seedling',
  'vegetative',
  'flowering',
  'harvest',
  'drying',
  'curing',
  'flushing',
  'ripening',
  'cloning',
  'dormancy',
  'juvenile',
  'climbing',
  'mature',
  'senescence',
  'short_day_induction',
  'indoor_sowing',
  'outdoor_planting',
] as const;

export type PhaseColorKey = (typeof PHASE_COLOR_KEYS)[number];

/**
 * Light values: the first ten are the garden-plan palette, pinned bit for bit by the cross-language
 * `phase_color` vectors (backend `domain/engines/phase_colors.py`, REQ-053 GP-FR-067) — do not move them.
 * Dark values: the next-lighter tone of the same Material hue, so the fill keeps its hue and reads on the
 * `#121212` / `#1e1e1e` dark surfaces.
 */
const PHASE_COLORS: Readonly<Record<PhaseColorKey, ModeColor>> = {
  germination: { light: '#81C784', dark: '#A5D6A7' },
  seedling: { light: '#66BB6A', dark: '#81C784' },
  vegetative: { light: '#43A047', dark: '#66BB6A' },
  flowering: { light: '#AB47BC', dark: '#BA68C8' },
  harvest: { light: '#EF5350', dark: '#E57373' },
  drying: { light: '#FF7043', dark: '#FF8A65' },
  curing: { light: '#FFA726', dark: '#FFB74D' },
  flushing: { light: '#42A5F5', dark: '#64B5F6' },
  ripening: { light: '#FF8A65', dark: '#FFAB91' },
  cloning: { light: '#26A69A', dark: '#4DB6AC' },
  dormancy: { light: '#78909C', dark: '#90A4AE' },
  juvenile: { light: '#9CCC65', dark: '#AED581' },
  climbing: { light: '#C0CA33', dark: '#D4E157' },
  mature: { light: '#2E7D32', dark: '#43A047' },
  senescence: { light: '#8D6E63', dark: '#A1887F' },
  short_day_induction: { light: '#7E57C2', dark: '#9575CD' },
  indoor_sowing: { light: '#FDD835', dark: '#FFEE58' },
  outdoor_planting: { light: '#7CB342', dark: '#9CCC65' },
};

/** Species-specific phase names and sowing-calendar phases, mapped onto the phase whose colour they share. */
const PHASE_ALIASES: Readonly<Record<string, PhaseColorKey>> = {
  growth: 'vegetative',
  leaf_phase: 'vegetative',
  active_growth: 'vegetative',
  spring_growth: 'mature',
  fruiting: 'ripening',
  corm_ripening: 'ripening',
  tuber_formation: 'ripening',
  autumn_ripening: 'ripening',
  establishment: 'germination',
  pup_establishment: 'germination',
  bulbil_establishment: 'germination',
  rooting: 'germination',
  sprouting: 'juvenile',
  sprout_formation: 'juvenile',
  young_palm: 'juvenile',
  hardening_off: 'seedling',
  recovery: 'cloning',
  pre_bloom: 'flowering',
  budding: 'flowering',
  bud_formation: 'flowering',
  bract_coloring: 'flowering',
  growth_bloom: 'flowering',
  autumn_growth_bloom: 'flowering',
  rest: 'dormancy',
  cool_rest: 'dormancy',
  rest_phase: 'dormancy',
  rest_after_bloom: 'dormancy',
  summer_rest: 'dormancy',
  summer_dormancy: 'dormancy',
  winter_rest: 'dormancy',
  winter_dormancy: 'dormancy',
  dry_storage: 'drying',
  winter_hull_change: 'senescence',
};

/** Colours for phases without a token, picked by a hash of the name (distinct, stable per name). */
export const PHASE_FALLBACK_PALETTE = [
  '#7E57C2',
  '#5C6BC0',
  '#29B6F6',
  '#26C6DA',
  '#66BB6A',
  '#D4E157',
  '#FFCA28',
  '#FFA726',
  '#EC407A',
  '#78909C',
] as const;

function modeOf(theme: Theme): ThemeMode {
  return theme.palette.mode === 'dark' ? 'dark' : 'light';
}

/** Lower-case and drop everything outside `a`…`z`: `"Short Day-Induction"` and `short_day_induction` agree. */
function normalise(name: string): string {
  return name.toLowerCase().replace(/[^a-z]/g, '');
}

const PHASE_INDEX: ReadonlyMap<string, PhaseColorKey> = new Map<string, PhaseColorKey>([
  ...PHASE_COLOR_KEYS.map((key): [string, PhaseColorKey] => [normalise(key), key]),
  ...Object.entries(PHASE_ALIASES).map(([alias, key]): [string, PhaseColorKey] => [normalise(alias), key]),
]);

/** The colour token a phase key (`phase_name` / `SowingPhase` / growth-phase name) resolves to, if any. */
export function phaseColorKey(phase: string | null | undefined): PhaseColorKey | undefined {
  if (!phase) return undefined;
  return PHASE_INDEX.get(normalise(phase));
}

function nameHash(name: string): number {
  let hash = 0;
  for (let index = 0; index < name.length; index += 1) {
    hash = (hash * 31 + name.charCodeAt(index)) | 0;
  }
  return Math.abs(hash);
}

/** The phase palette for one mode — what `theme.palette.phase` carries. */
export function phasePalette(mode: ThemeMode): Readonly<Record<PhaseColorKey, string>> {
  return Object.fromEntries(PHASE_COLOR_KEYS.map((key) => [key, PHASE_COLORS[key][mode]])) as Record<
    PhaseColorKey,
    string
  >;
}

export interface PhaseColorOptions {
  /**
   * What an unknown phase gets: `neutral` (default) is the theme's grey, `distinct` a stable colour from
   * {@link PHASE_FALLBACK_PALETTE} so several unknown phases stay apart in one legend.
   */
  unknown?: 'neutral' | 'distinct';
}

/** Colour of a phase in the active theme, resolved by phase key. */
export function getPhaseColor(
  theme: Theme,
  phase: string | null | undefined,
  { unknown = 'neutral' }: PhaseColorOptions = {},
): string {
  const key = phaseColorKey(phase);
  // A theme built outside `@/theme/theme` (a bare `createTheme()` in a test) carries no domain tokens: read the
  // static token for its mode instead of crashing.
  if (key) return theme.palette.phase?.[key] ?? PHASE_COLORS[key][modeOf(theme)];
  if (unknown === 'distinct' && phase) return PHASE_FALLBACK_PALETTE[nameHash(phase) % PHASE_FALLBACK_PALETTE.length];
  return theme.palette.grey[theme.palette.mode === 'dark' ? 600 : 500];
}

/** The ten phases the garden-plan colour contract knows (backend `phase_colors.PHASE_COLORS`). */
const PLAN_PHASE_KEYS: ReadonlySet<PhaseColorKey> = new Set<PhaseColorKey>([
  'germination',
  'seedling',
  'vegetative',
  'flowering',
  'harvest',
  'drying',
  'curing',
  'flushing',
  'ripening',
  'cloning',
]);

/**
 * Garden-plan marker colour (REQ-053 GP-FR-067): a fixed paint shared with the server-rendered SVG/PDF, so it
 * is mode-independent and follows the `phase_color` vectors exactly — only the ten plan phases are named,
 * aliases do not apply, every other name takes the hash colour of the unnormalised name.
 */
export function planPhaseColor(phaseName: string): string {
  const key = normalise(phaseName);
  if (PLAN_PHASE_KEYS.has(key as PhaseColorKey)) return PHASE_COLORS[key as PhaseColorKey].light;
  return PHASE_FALLBACK_PALETTE[nameHash(phaseName) % PHASE_FALLBACK_PALETTE.length];
}

// ── Sensor metrics ──────────────────────────────────────────────────

export const METRIC_COLOR_KEYS = [
  'ph',
  'ec_ms',
  'water_temp_celsius',
  'temperature_celsius',
  'humidity_percent',
  'fill_level_percent',
  'co2_ppm',
  'vpd_kpa',
  'ppfd',
  'tds_ppm',
  'dissolved_oxygen_mgl',
  'orp_mv',
  'other',
] as const;

export type MetricColorKey = (typeof METRIC_COLOR_KEYS)[number];

const METRIC_COLORS: Readonly<Record<MetricColorKey, ModeColor>> = {
  ph: { light: '#4caf50', dark: '#81c784' },
  ec_ms: { light: '#ff9800', dark: '#ffb74d' },
  water_temp_celsius: { light: '#2196f3', dark: '#64b5f6' },
  temperature_celsius: { light: '#f44336', dark: '#e57373' },
  humidity_percent: { light: '#9c27b0', dark: '#ba68c8' },
  fill_level_percent: { light: '#00bcd4', dark: '#4dd0e1' },
  co2_ppm: { light: '#795548', dark: '#a1887f' },
  vpd_kpa: { light: '#607d8b', dark: '#90a4ae' },
  ppfd: { light: '#ffc107', dark: '#ffd54f' },
  tds_ppm: { light: '#ff5722', dark: '#ff8a65' },
  dissolved_oxygen_mgl: { light: '#03a9f4', dark: '#4fc3f7' },
  orp_mv: { light: '#8bc34a', dark: '#aed581' },
  other: { light: '#1976d2', dark: '#90caf9' },
};

export function metricPalette(mode: ThemeMode): Readonly<Record<MetricColorKey, string>> {
  return Object.fromEntries(METRIC_COLOR_KEYS.map((key) => [key, METRIC_COLORS[key][mode]])) as Record<
    MetricColorKey,
    string
  >;
}

/** Line colour of a sensor metric; a metric without a token takes `metric.other`. */
export function getMetricColor(theme: Theme, metric: string | null | undefined): string {
  const palette = theme.palette.metric ?? metricPalette(modeOf(theme));
  return metric && Object.prototype.hasOwnProperty.call(palette, metric) ? palette[metric as MetricColorKey] : palette.other;
}

// ── Calendar event categories ───────────────────────────────────────

const EVENT_CATEGORY_COLORS: Readonly<Record<CalendarEventCategory, ModeColor>> = {
  training: { light: '#4CAF50', dark: '#81C784' },
  pruning: { light: '#8BC34A', dark: '#AED581' },
  transplanting: { light: '#795548', dark: '#A1887F' },
  feeding: { light: '#2196F3', dark: '#64B5F6' },
  ipm: { light: '#FF9800', dark: '#FFB74D' },
  harvest: { light: '#F44336', dark: '#E57373' },
  maintenance: { light: '#9E9E9E', dark: '#BDBDBD' },
  phase_transition: { light: '#9C27B0', dark: '#BA68C8' },
  tank_maintenance: { light: '#00BCD4', dark: '#4DD0E1' },
  watering_forecast: { light: '#42A5F5', dark: '#90CAF9' },
  custom: { light: '#607D8B', dark: '#90A4AE' },
};

export function eventCategoryPalette(mode: ThemeMode): Readonly<Record<CalendarEventCategory, string>> {
  return Object.fromEntries(
    Object.entries(EVENT_CATEGORY_COLORS).map(([key, value]) => [key, value[mode]]),
  ) as Record<CalendarEventCategory, string>;
}

/** Colour of a calendar category; an unknown category takes the theme's grey. */
export function getEventCategoryColor(theme: Theme, category: string | null | undefined): string {
  const palette = theme.palette.eventCategory ?? eventCategoryPalette(modeOf(theme));
  return category && Object.prototype.hasOwnProperty.call(palette, category)
    ? palette[category as CalendarEventCategory]
    : theme.palette.grey[500];
}

// ── Text on a domain colour ─────────────────────────────────────────

function rgb(color: string): [number, number, number] {
  const hex = color.trim().match(/^#([0-9a-f]{3}|[0-9a-f]{6})$/i);
  if (hex) {
    const digits = hex[1].length === 3 ? [...hex[1]].map((d) => d + d).join('') : hex[1];
    const n = parseInt(digits, 16);
    return [(n >> 16) & 255, (n >> 8) & 255, n & 255];
  }
  const fn = color.trim().match(/^rgba?\(([^)]+)\)$/i);
  if (fn) {
    const [r, g, b] = fn[1].split(/[,\s/]+/).filter(Boolean).map(Number);
    if ([r, g, b].every(Number.isFinite)) return [r, g, b];
  }
  throw new Error(`unsupported colour ${color}`);
}

/**
 * The surface a colour paints when drawn at `opacity` over `surface` (alpha compositing, the way the browser
 * does it — MUI's `getContrastRatio` ignores alpha).
 */
export function paintedOver(color: string, opacity: number, surface: string): string {
  const [cr, cg, cb] = rgb(color);
  const [sr, sg, sb] = rgb(surface);
  const mix = (c: number, s: number) => Math.round(c * opacity + s * (1 - opacity));
  return `rgb(${mix(cr, sr)}, ${mix(cg, sg)}, ${mix(cb, sb)})`;
}

/**
 * Black or white — whichever reads better on `background` (WCAG contrast, the higher of the two). With
 * `opacity` < 1 the background is first composited over `surface` (default: the theme-independent white).
 * An unparseable colour falls back to black.
 */
export function readableTextOn(background: string, opacity = 1, surface = '#ffffff'): '#000000' | '#ffffff' {
  let painted: string;
  try {
    painted = opacity >= 1 ? background : paintedOver(background, opacity, surface);
    rgb(painted);
  } catch {
    return '#000000';
  }
  return getContrastRatio('#000000', painted) >= getContrastRatio('#ffffff', painted) ? '#000000' : '#ffffff';
}

// ── MUI palette augmentation ────────────────────────────────────────

declare module '@mui/material/styles' {
  interface Palette {
    phase: Readonly<Record<PhaseColorKey, string>>;
    metric: Readonly<Record<MetricColorKey, string>>;
    eventCategory: Readonly<Record<CalendarEventCategory, string>>;
  }
  interface PaletteOptions {
    phase?: Readonly<Record<PhaseColorKey, string>>;
    metric?: Readonly<Record<MetricColorKey, string>>;
    eventCategory?: Readonly<Record<CalendarEventCategory, string>>;
  }
}
