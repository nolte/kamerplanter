import client from '../client';
import type {
  CurrentPhaseResponse,
  PhaseHistoryDateUpdate,
  PhaseHistoryEntry,
  TransitionRequest,
  PlantInstance,
  GrowthPhase,
  GrowthPhaseCreate,
  LifecycleConfig,
  LifecycleConfigCreate,
  RequirementProfile,
  RequirementProfileCreate,
  NutrientProfile,
  NutrientProfileCreate,
} from '../types';

// Phase Control (per plant)

export async function getCurrentPhase(plantKey: string): Promise<CurrentPhaseResponse> {
  const { data } = await client.get<CurrentPhaseResponse>(
    `/plant-instances/${plantKey}/phases/current`,
  );
  return data;
}

export async function transitionPhase(
  plantKey: string,
  payload: TransitionRequest,
): Promise<PlantInstance> {
  const { data } = await client.post<PlantInstance>(
    `/plant-instances/${plantKey}/phases/transition`,
    payload,
  );
  return data;
}

export async function getPhaseHistory(plantKey: string): Promise<PhaseHistoryEntry[]> {
  const { data } = await client.get<PhaseHistoryEntry[]>(
    `/plant-instances/${plantKey}/phases/history`,
  );
  return data;
}

export async function updatePhaseHistoryDates(
  plantKey: string,
  historyKey: string,
  payload: PhaseHistoryDateUpdate,
): Promise<PhaseHistoryEntry> {
  const { data } = await client.patch<PhaseHistoryEntry>(
    `/plant-instances/${plantKey}/phases/history/${historyKey}`,
    payload,
  );
  return data;
}

export async function deletePhaseHistory(
  plantKey: string,
  historyKey: string,
): Promise<void> {
  await client.delete(`/plant-instances/${plantKey}/phases/history/${historyKey}`);
}

// Growth Phases (lifecycle definitions)

export async function listGrowthPhases(lifecycleKey: string): Promise<GrowthPhase[]> {
  const { data } = await client.get<GrowthPhase[]>('/growth-phases', {
    params: { lifecycle_key: lifecycleKey },
  });
  return data;
}

export async function getGrowthPhase(key: string): Promise<GrowthPhase> {
  const { data } = await client.get<GrowthPhase>(`/growth-phases/${key}`);
  return data;
}

export async function createGrowthPhase(payload: GrowthPhaseCreate): Promise<GrowthPhase> {
  const { data } = await client.post<GrowthPhase>('/growth-phases', payload);
  return data;
}

export async function updateGrowthPhase(
  key: string,
  payload: GrowthPhaseCreate,
): Promise<GrowthPhase> {
  const { data } = await client.put<GrowthPhase>(`/growth-phases/${key}`, payload);
  return data;
}

export async function deleteGrowthPhase(key: string): Promise<void> {
  await client.delete(`/growth-phases/${key}`);
}

// Lifecycle Config (per species)

export async function getLifecycleConfig(speciesKey: string): Promise<LifecycleConfig> {
  const { data } = await client.get<LifecycleConfig>(`/species/${speciesKey}/lifecycle`);
  return data;
}

export async function createLifecycleConfig(
  speciesKey: string,
  payload: Omit<LifecycleConfigCreate, 'species_key'>,
): Promise<LifecycleConfig> {
  const { data } = await client.post<LifecycleConfig>(`/species/${speciesKey}/lifecycle`, {
    ...payload,
    species_key: speciesKey,
  });
  return data;
}

export async function updateLifecycleConfig(
  speciesKey: string,
  key: string,
  payload: Omit<LifecycleConfigCreate, 'species_key'>,
): Promise<LifecycleConfig> {
  const { data } = await client.put<LifecycleConfig>(
    `/species/${speciesKey}/lifecycle/${key}`,
    { ...payload, species_key: speciesKey },
  );
  return data;
}

// Profiles

export async function getRequirementProfile(
  phaseKey: string,
): Promise<RequirementProfile> {
  const { data } = await client.get<RequirementProfile>(
    `/profiles/requirements/${phaseKey}`,
  );
  return data;
}

export async function createRequirementProfile(
  payload: RequirementProfileCreate,
): Promise<RequirementProfile> {
  const { data } = await client.post<RequirementProfile>('/profiles/requirements', payload);
  return data;
}

export async function updateRequirementProfile(
  key: string,
  payload: RequirementProfileCreate,
): Promise<RequirementProfile> {
  const { data } = await client.put<RequirementProfile>(`/profiles/requirements/${key}`, payload);
  return data;
}

export async function getNutrientProfile(phaseKey: string): Promise<NutrientProfile> {
  const { data } = await client.get<NutrientProfile>(`/profiles/nutrients/${phaseKey}`);
  return data;
}

export async function createNutrientProfile(
  payload: NutrientProfileCreate,
): Promise<NutrientProfile> {
  const { data } = await client.post<NutrientProfile>('/profiles/nutrients', payload);
  return data;
}

export async function updateNutrientProfile(
  key: string,
  payload: NutrientProfileCreate,
): Promise<NutrientProfile> {
  const { data } = await client.put<NutrientProfile>(`/profiles/nutrients/${key}`, payload);
  return data;
}

export async function generateDefaultProfiles(
  phaseKey: string,
): Promise<{ requirement: RequirementProfile; nutrient: NutrientProfile }> {
  const { data } = await client.post<{
    requirement: RequirementProfile;
    nutrient: NutrientProfile;
  }>(`/profiles/generate-defaults/${phaseKey}`);
  return data;
}
