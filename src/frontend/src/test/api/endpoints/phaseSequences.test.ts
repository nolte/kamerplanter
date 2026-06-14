import { describe, it, expect, beforeEach, vi } from 'vitest';

const mocks = vi.hoisted(() => {
  const client = {
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
    patch: vi.fn(),
    delete: vi.fn(),
  };
  return { client };
});

vi.mock('@/api/client', () => ({
  __esModule: true,
  default: mocks.client,
  tenantClient: mocks.client,
}));

import * as seq from '@/api/endpoints/phaseSequences';

const client = mocks.client;

beforeEach(() => {
  vi.clearAllMocks();
});

describe('phaseSequences endpoints — species sequence & definitions', () => {
  it('getSpeciesPhaseSequence gets sequence for species', async () => {
    client.get.mockResolvedValue({ data: null });
    await seq.getSpeciesPhaseSequence('sp1');
    expect(client.get).toHaveBeenCalledWith('/species/sp1/phase-sequence');
  });

  it('listPhaseDefinitions gets with pagination only', async () => {
    client.get.mockResolvedValue({ data: [] });
    await seq.listPhaseDefinitions(5, 10);
    expect(client.get).toHaveBeenCalledWith('/phase-definitions', {
      params: { offset: 5, limit: 10 },
    });
  });

  it('listPhaseDefinitions adds name filter when provided', async () => {
    client.get.mockResolvedValue({ data: [] });
    await seq.listPhaseDefinitions(0, 50, 'Veg');
    expect(client.get).toHaveBeenCalledWith('/phase-definitions', {
      params: { offset: 0, limit: 50, name: 'Veg' },
    });
  });

  it('createPhaseDefinition posts payload', async () => {
    client.post.mockResolvedValue({ data: { key: 'pd1' } });
    const payload = { name: 'Veg' } as never;
    await seq.createPhaseDefinition(payload);
    expect(client.post).toHaveBeenCalledWith('/phase-definitions', payload);
  });

  it('getPhaseDefinition gets definition by key', async () => {
    client.get.mockResolvedValue({ data: { key: 'pd1' } });
    await seq.getPhaseDefinition('pd1');
    expect(client.get).toHaveBeenCalledWith('/phase-definitions/pd1');
  });

  it('updatePhaseDefinition puts definition by key', async () => {
    client.put.mockResolvedValue({ data: { key: 'pd1' } });
    const payload = { name: 'X' } as never;
    await seq.updatePhaseDefinition('pd1', payload);
    expect(client.put).toHaveBeenCalledWith('/phase-definitions/pd1', payload);
  });

  it('deletePhaseDefinition deletes by key', async () => {
    client.delete.mockResolvedValue({ data: undefined });
    await seq.deletePhaseDefinition('pd1');
    expect(client.delete).toHaveBeenCalledWith('/phase-definitions/pd1');
  });

  it('listSequencesForDefinition gets sequences for definition', async () => {
    client.get.mockResolvedValue({ data: [] });
    await seq.listSequencesForDefinition('pd1');
    expect(client.get).toHaveBeenCalledWith('/phase-definitions/pd1/sequences');
  });
});

describe('phaseSequences endpoints — sequences', () => {
  it('listPhaseSequences gets paginated sequences', async () => {
    client.get.mockResolvedValue({ data: [] });
    await seq.listPhaseSequences(5, 10);
    expect(client.get).toHaveBeenCalledWith('/phase-sequences', {
      params: { offset: 5, limit: 10 },
    });
  });

  it('createPhaseSequence posts payload', async () => {
    client.post.mockResolvedValue({ data: { key: 'ps1' } });
    const payload = { name: 'Annual' } as never;
    await seq.createPhaseSequence(payload);
    expect(client.post).toHaveBeenCalledWith('/phase-sequences', payload);
  });

  it('getPhaseSequence gets sequence by key', async () => {
    client.get.mockResolvedValue({ data: { key: 'ps1' } });
    await seq.getPhaseSequence('ps1');
    expect(client.get).toHaveBeenCalledWith('/phase-sequences/ps1');
  });

  it('updatePhaseSequence puts sequence by key', async () => {
    client.put.mockResolvedValue({ data: { key: 'ps1' } });
    const payload = { name: 'X' } as never;
    await seq.updatePhaseSequence('ps1', payload);
    expect(client.put).toHaveBeenCalledWith('/phase-sequences/ps1', payload);
  });

  it('deletePhaseSequence deletes by key', async () => {
    client.delete.mockResolvedValue({ data: undefined });
    await seq.deletePhaseSequence('ps1');
    expect(client.delete).toHaveBeenCalledWith('/phase-sequences/ps1');
  });

  it('listSpeciesForSequence gets species for sequence', async () => {
    client.get.mockResolvedValue({ data: [] });
    await seq.listSpeciesForSequence('ps1');
    expect(client.get).toHaveBeenCalledWith('/phase-sequences/ps1/species');
  });
});

describe('phaseSequences endpoints — sequence entries', () => {
  it('listSequenceEntries gets entries for sequence', async () => {
    client.get.mockResolvedValue({ data: [] });
    await seq.listSequenceEntries('ps1');
    expect(client.get).toHaveBeenCalledWith('/phase-sequences/ps1/entries');
  });

  it('createSequenceEntry posts entry payload', async () => {
    client.post.mockResolvedValue({ data: { key: 'en1' } });
    const payload = { phase_key: 'pd1' } as never;
    await seq.createSequenceEntry('ps1', payload);
    expect(client.post).toHaveBeenCalledWith('/phase-sequences/ps1/entries', payload);
  });

  it('updateSequenceEntry puts entry by composite key', async () => {
    client.put.mockResolvedValue({ data: { key: 'en1' } });
    const payload = { sequence_order: 2 } as never;
    await seq.updateSequenceEntry('ps1', 'en1', payload);
    expect(client.put).toHaveBeenCalledWith('/phase-sequences/ps1/entries/en1', payload);
  });

  it('deleteSequenceEntry deletes by composite key', async () => {
    client.delete.mockResolvedValue({ data: undefined });
    await seq.deleteSequenceEntry('ps1', 'en1');
    expect(client.delete).toHaveBeenCalledWith('/phase-sequences/ps1/entries/en1');
  });

  it('reorderEntries posts entries array to reorder', async () => {
    client.post.mockResolvedValue({ data: [] });
    const entries = [{ key: 'en1', sequence_order: 0 }];
    await seq.reorderEntries('ps1', entries);
    expect(client.post).toHaveBeenCalledWith('/phase-sequences/ps1/entries/reorder', {
      entries,
    });
  });
});
