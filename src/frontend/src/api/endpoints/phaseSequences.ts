import client from '../client';
import type {
  PhaseDefinition,
  PhaseDefinitionCreate,
  PhaseDefinitionUpdate,
  PhaseSequence,
  PhaseSequenceCreate,
  PhaseSequenceUpdate,
  PhaseSequenceEntry,
  PhaseSequenceEntryCreate,
  PhaseSequenceEntryUpdate,
} from '../types';

// ── Species Phase Sequence ──

export async function getSpeciesPhaseSequence(
  speciesKey: string,
): Promise<PhaseSequence | null> {
  const { data } = await client.get<PhaseSequence | null>(
    `/species/${speciesKey}/phase-sequence`,
  );
  return data;
}

// ── Phase Definitions ──

export async function listPhaseDefinitions(
  offset = 0,
  limit = 50,
  name?: string,
): Promise<PhaseDefinition[]> {
  const { data } = await client.get<PhaseDefinition[]>('/phase-definitions', {
    params: { offset, limit, ...(name ? { name } : {}) },
  });
  return data;
}

export async function createPhaseDefinition(
  payload: PhaseDefinitionCreate,
): Promise<PhaseDefinition> {
  const { data } = await client.post<PhaseDefinition>('/phase-definitions', payload);
  return data;
}

export async function getPhaseDefinition(key: string): Promise<PhaseDefinition> {
  const { data } = await client.get<PhaseDefinition>(`/phase-definitions/${key}`);
  return data;
}

export async function updatePhaseDefinition(
  key: string,
  payload: PhaseDefinitionUpdate,
): Promise<PhaseDefinition> {
  const { data } = await client.put<PhaseDefinition>(
    `/phase-definitions/${key}`,
    payload,
  );
  return data;
}

export async function deletePhaseDefinition(key: string): Promise<void> {
  await client.delete(`/phase-definitions/${key}`);
}

export async function listSequencesForDefinition(
  key: string,
): Promise<PhaseSequence[]> {
  const { data } = await client.get<PhaseSequence[]>(
    `/phase-definitions/${key}/sequences`,
  );
  return data;
}

// ── Phase Sequences ──

export async function listPhaseSequences(
  offset = 0,
  limit = 50,
): Promise<PhaseSequence[]> {
  const { data } = await client.get<PhaseSequence[]>('/phase-sequences', {
    params: { offset, limit },
  });
  return data;
}

export async function createPhaseSequence(
  payload: PhaseSequenceCreate,
): Promise<PhaseSequence> {
  const { data } = await client.post<PhaseSequence>('/phase-sequences', payload);
  return data;
}

export async function getPhaseSequence(key: string): Promise<PhaseSequence> {
  const { data } = await client.get<PhaseSequence>(`/phase-sequences/${key}`);
  return data;
}

export async function updatePhaseSequence(
  key: string,
  payload: PhaseSequenceUpdate,
): Promise<PhaseSequence> {
  const { data } = await client.put<PhaseSequence>(
    `/phase-sequences/${key}`,
    payload,
  );
  return data;
}

export async function deletePhaseSequence(key: string): Promise<void> {
  await client.delete(`/phase-sequences/${key}`);
}

export async function listSpeciesForSequence(
  key: string,
): Promise<{ key: string; scientific_name: string; common_names: string[] }[]> {
  const { data } = await client.get<{ key: string; scientific_name: string; common_names: string[] }[]>(
    `/phase-sequences/${key}/species`,
  );
  return data;
}

// ── Sequence Entries ──

export async function listSequenceEntries(
  seqKey: string,
): Promise<PhaseSequenceEntry[]> {
  const { data } = await client.get<PhaseSequenceEntry[]>(
    `/phase-sequences/${seqKey}/entries`,
  );
  return data;
}

export async function createSequenceEntry(
  seqKey: string,
  payload: PhaseSequenceEntryCreate,
): Promise<PhaseSequenceEntry> {
  const { data } = await client.post<PhaseSequenceEntry>(
    `/phase-sequences/${seqKey}/entries`,
    payload,
  );
  return data;
}

export async function updateSequenceEntry(
  seqKey: string,
  key: string,
  payload: PhaseSequenceEntryUpdate,
): Promise<PhaseSequenceEntry> {
  const { data } = await client.put<PhaseSequenceEntry>(
    `/phase-sequences/${seqKey}/entries/${key}`,
    payload,
  );
  return data;
}

export async function deleteSequenceEntry(
  seqKey: string,
  key: string,
): Promise<void> {
  await client.delete(`/phase-sequences/${seqKey}/entries/${key}`);
}

export async function reorderEntries(
  seqKey: string,
  entries: { key: string; sequence_order: number }[],
): Promise<PhaseSequenceEntry[]> {
  const { data } = await client.post<PhaseSequenceEntry[]>(
    `/phase-sequences/${seqKey}/entries/reorder`,
    { entries },
  );
  return data;
}
