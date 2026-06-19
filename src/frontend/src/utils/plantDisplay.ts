import type {
  Cultivar,
  PlantCultivarSummary,
  PlantSpeciesSummary,
  Species,
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
 *   2. species common name (or scientific name) + optional cultivar
 *   3. `instance_id` (last-resort fallback)
 *
 * Both the denormalized summaries embedded in plant responses
 * (`PlantInstance.species` / `.cultivar`) and explicitly passed
 * `Species` / `Cultivar` models are accepted, so callers can use whichever
 * data they already have loaded.
 */

type SpeciesLike = Pick<PlantSpeciesSummary, 'scientific_name' | 'common_names'>;
type CultivarLike = Pick<PlantCultivarSummary, 'name'>;

/** Minimal plant shape the helpers operate on (covers PlantInstance & PlantInRun). */
type PlantLike = {
  instance_id: string;
  plant_name?: string | null;
  species?: PlantSpeciesSummary | null;
  cultivar?: PlantCultivarSummary | null;
};

function nonEmpty(value: string | null | undefined): string | null {
  const trimmed = value?.trim();
  return trimmed ? trimmed : null;
}

/**
 * Build the botanical label for a species (+ optional cultivar), e.g.
 * "Basilikum – Genovese". Returns `null` when no species data is available.
 */
export function getSpeciesLabel(
  species?: SpeciesLike | Species | null,
  cultivar?: CultivarLike | Cultivar | null,
): string | null {
  if (!species) return null;
  const base = nonEmpty(species.common_names?.[0]) ?? nonEmpty(species.scientific_name);
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
  species?: SpeciesLike | Species | null,
  cultivar?: CultivarLike | Cultivar | null,
): string {
  const userName = nonEmpty(plant.plant_name);
  if (userName) return userName;

  const speciesLabel = getSpeciesLabel(species ?? plant.species, cultivar ?? plant.cultivar);
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
  species?: SpeciesLike | Species | null,
  cultivar?: CultivarLike | Cultivar | null,
): string {
  const name = getPlantDisplayName(plant, species, cultivar);
  return name === plant.instance_id ? plant.instance_id : `${plant.instance_id} (${name})`;
}

export type { PlantLike };
