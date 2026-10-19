/**
 * The plants of the bed sheet (REQ-053 §18.1 step 3: species, count, phase): the standing plants grouped
 * by species, cultivar and phase. Pure, so the grouping is pinned without rendering.
 */
import type { PlantStateWire } from '../planting/plantStateApi';

export interface FieldPlantGroup {
  /** Stable business key of the group: species, cultivar and phase key. */
  id: string;
  species: string;
  cultivar: string | null;
  phaseKey: string | null;
  phaseName: string | null;
  plants: PlantStateWire[];
}

function slug(value: string): string {
  return value.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/(^-|-$)/g, '') || 'none';
}

/** Groups in the order of their largest count first, then by species name. */
export function groupPlants(plants: readonly PlantStateWire[], language: string): FieldPlantGroup[] {
  const groups = new Map<string, FieldPlantGroup>();
  for (const plant of plants) {
    const species = plant.species_name || plant.scientific_name || plant.species_key;
    const cultivar = plant.cultivar_name ?? null;
    const phaseKey = plant.phase?.key ?? null;
    const id = [plant.species_key, cultivar ?? '', phaseKey ?? ''].map(slug).join('--');
    const group = groups.get(id);
    if (group) group.plants.push(plant);
    else {
      groups.set(id, {
        id,
        species,
        cultivar,
        phaseKey,
        phaseName: plant.phase?.name ?? null,
        plants: [plant],
      });
    }
  }
  const collator = new Intl.Collator(language, { sensitivity: 'base', numeric: true });
  for (const group of groups.values()) {
    group.plants.sort((a, b) => collator.compare(a.instance_id, b.instance_id));
  }
  return [...groups.values()].sort(
    (a, b) =>
      b.plants.length - a.plants.length || collator.compare(a.species, b.species) || (a.id < b.id ? -1 : a.id > b.id ? 1 : 0),
  );
}
