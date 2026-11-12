import type {
  Cultivar,
  PlantCultivarSummary,
  PlantSpeciesSummary,
} from '@/api/types';

/**
 * Central helpers for rendering a human-readable plant name.
 *
 * A plant instance is identified by a terse `instance_id` (e.g. `BASIL-001`),
 * which is great for re-finding a physical plant but says nothing about *what*
 * it is. These helpers derive a speaking name from the richest data available,
 * falling back gracefully so a label is always produced.
 *
 * Priority for the speaking name:
 *   1. `plant_name` (the user's own label, if set)
 *   2. species common name in the UI language (see `getLocalizedCommonName`) +
 *      optional cultivar
 *   3. `instance_id` (last-resort fallback)
 *
 * Both the denormalized summaries embedded in plant responses
 * (`PlantInstance.species` / `.cultivar`) and explicitly passed
 * `Species` / `Cultivar` models are accepted, so callers can use whichever
 * data they already have loaded.
 */

/**
 * Anything that carries species names: a full `Species`, the denormalized
 * `PlantSpeciesSummary`, a companion/phase-sequence species row, ... Every field is
 * optional so each of those shapes fits without a cast.
 */
type SpeciesNameSource = {
  scientific_name?: string | null;
  common_names?: readonly string[] | null;
  common_names_i18n?: Readonly<Partial<Record<string, readonly string[]>>> | null;
};
type CultivarLike = Pick<PlantCultivarSummary, 'name'>;

/** Minimal plant shape the helpers operate on (covers PlantInstance & PlantInRun). */
type PlantLike = {
  instance_id: string;
  plant_name?: string | null;
  species?: PlantSpeciesSummary | null;
  cultivar?: PlantCultivarSummary | null;
};

/** The language the species name falls back to when the UI language has none (REQ-001). */
export const COMMON_NAME_FALLBACK_LANGUAGE = 'de';

function nonEmpty(value: string | null | undefined): string | null {
  const trimmed = value?.trim();
  return trimmed ? trimmed : null;
}

function firstNonEmpty(names: readonly string[] | null | undefined): string | null {
  for (const name of names ?? []) {
    const value = nonEmpty(name);
    if (value) return value;
  }
  return null;
}

/**
 * Reduce an i18next language tag to the key of `common_names_i18n`:
 * `de-DE` -> `de`, `EN_us` -> `en`; empty/missing -> the `de` fallback.
 */
export function normalizeNameLanguage(language: string | null | undefined): string {
  const base = language?.trim().toLowerCase().split(/[-_]/)[0];
  return base || COMMON_NAME_FALLBACK_LANGUAGE;
}

/**
 * The single source of the layperson-facing species name (REQ-001, UI-NFR-007
 * R-009a, #2902). Returns `null` only when no name at all is available.
 *
 * `common_names` is a flat, language-MIXED list whose order carries no language
 * meaning — `species.yaml` lists the English name first for most species — so its
 * first entry is never the display name of a language-tagged species. The language
 * comes from `common_names_i18n`:
 *
 * 1. **The species has a language map** (at least one language key): the first name
 *    of the UI language -> the first name of `de` -> the scientific name. The
 *    untagged rest of `common_names` is NOT consulted: if the map has no name for the
 *    UI language nor for German, any entry of `common_names` would be a name of some
 *    other language, so the neutral scientific name wins.
 * 2. **No language map** (absent, `null` or `{}`): the names are untagged — a species
 *    a tenant created through the form or the CSV import, an identification
 *    suggestion from an external adapter, or older cached data. There the first entry
 *    of `common_names` is exactly what the user typed (or the adapter returned), so it
 *    is the best name available; then the scientific name. The backend serves `{}` for
 *    "no map", which is why an empty object counts as absent.
 *
 * `language` is the UI language (`i18n.language`); it is normalized, so `de-DE`
 * works. Components pass `useTranslation().i18n.language` so they re-render on a
 * language change; pure functions take it as a parameter.
 */
export function getLocalizedCommonName(
  species: SpeciesNameSource | null | undefined,
  language: string | null | undefined,
): string | null {
  if (!species) return null;
  const scientific = nonEmpty(species.scientific_name);
  const map = species.common_names_i18n;
  if (map && Object.keys(map).length > 0) {
    const lang = normalizeNameLanguage(language);
    return (
      firstNonEmpty(map[lang]) ?? firstNonEmpty(map[COMMON_NAME_FALLBACK_LANGUAGE]) ?? scientific
    );
  }
  return firstNonEmpty(species.common_names) ?? scientific;
}

/**
 * All common names for a joined list display ("Erbse, Pea"): the names of the UI
 * language first (in their preference order), then the remaining `common_names` in
 * stored order. Every name stays — this only reorders; searching is unaffected.
 */
export function orderCommonNamesForLanguage(
  species: SpeciesNameSource | null | undefined,
  language: string | null | undefined,
): string[] {
  const all = (species?.common_names ?? []).filter((name) => nonEmpty(name));
  const preferred = (species?.common_names_i18n?.[normalizeNameLanguage(language)] ?? []).filter(
    (name) => all.includes(name),
  );
  return [...preferred, ...all.filter((name) => !preferred.includes(name))];
}

/**
 * The common names that are NOT the displayed one, for the secondary line of a picker
 * option — shows why an English search term matched in the German UI. Deduplicated
 * case-insensitively; empty when the species has no other name.
 */
export function getAlternativeCommonNames(
  species: SpeciesNameSource | null | undefined,
  language: string | null | undefined,
): string[] {
  const shown = getLocalizedCommonName(species, language)?.toLowerCase();
  const seen = new Set<string>();
  const result: string[] = [];
  for (const name of orderCommonNamesForLanguage(species, language)) {
    const key = name.trim().toLowerCase();
    if (key === shown || seen.has(key)) continue;
    seen.add(key);
    result.push(name.trim());
  }
  return result;
}

/**
 * "Common (Scientific)" — the picker/option label shape, e.g. "Erbse (Pisum sativum)".
 * Only the scientific name when there is no distinct common name.
 */
export function formatSpeciesNameWithScientific(
  commonName: string | null | undefined,
  scientificName: string,
): string {
  const common = nonEmpty(commonName);
  return common && common !== scientificName ? `${common} (${scientificName})` : scientificName;
}

/**
 * Picker/option label of a species with the common name in `language`
 * (see {@link getLocalizedCommonName}), e.g. "Erbse (Pisum sativum)" in the German UI.
 */
export function getSpeciesOptionLabel(
  species: SpeciesNameSource & { scientific_name: string },
  language: string | null | undefined,
): string {
  return formatSpeciesNameWithScientific(getLocalizedCommonName(species, language), species.scientific_name);
}

/**
 * Build the botanical label for a species (+ optional cultivar), e.g.
 * "Basilikum – Genovese", with the species name in `language`
 * (see {@link getLocalizedCommonName}). Returns `null` when no species data is available.
 */
export function getSpeciesLabel(
  species: SpeciesNameSource | null | undefined,
  language: string | null | undefined,
  cultivar?: CultivarLike | Cultivar | null,
): string | null {
  const base = getLocalizedCommonName(species, language);
  if (!base) return null;
  const cultivarName = nonEmpty(cultivar?.name);
  return cultivarName ? `${base} – ${cultivarName}` : base;
}

/**
 * Derive the speaking name of a plant. Explicitly passed `species`/`cultivar`
 * take precedence over the summaries embedded in the plant object.
 */
export function getPlantDisplayName(
  plant: PlantLike,
  language: string | null | undefined,
  species?: SpeciesNameSource | null,
  cultivar?: CultivarLike | Cultivar | null,
): string {
  const userName = nonEmpty(plant.plant_name);
  if (userName) return userName;

  const speciesLabel = getSpeciesLabel(species ?? plant.species, language, cultivar ?? plant.cultivar);
  if (speciesLabel) return speciesLabel;

  return plant.instance_id;
}

/**
 * Combine the `instance_id` with the speaking name, e.g.
 * "BASIL-001 (Basilikum – Genovese)". When the speaking name resolves to the
 * `instance_id` itself, only the id is returned (no redundant parentheses).
 */
export function getPlantLabel(
  plant: PlantLike,
  language: string | null | undefined,
  species?: SpeciesNameSource | null,
  cultivar?: CultivarLike | Cultivar | null,
): string {
  const name = getPlantDisplayName(plant, language, species, cultivar);
  return name === plant.instance_id ? plant.instance_id : `${plant.instance_id} (${name})`;
}

export type { PlantLike, SpeciesNameSource };
