import { describe, it, expect, beforeEach, vi } from 'vitest';

const mocks = vi.hoisted(() => {
  const make = () => ({
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
    patch: vi.fn(),
    delete: vi.fn(),
  });
  // ipm.ts uses the default (global) client for global IPM master data and
  // the tenantClient for plant-scoped resources. Keep them distinct so each
  // test asserts the correct collaborator was used.
  return { globalClient: make(), tenantClient: make() };
});

vi.mock('@/api/client', () => ({
  __esModule: true,
  default: mocks.globalClient,
  tenantClient: mocks.tenantClient,
}));

import * as ipm from '@/api/endpoints/ipm';

const globalClient = mocks.globalClient;
const tenantClient = mocks.tenantClient;

beforeEach(() => {
  vi.clearAllMocks();
});

describe('ipm endpoints — pests (global client)', () => {
  it('listPests gets pests with pagination via global client', async () => {
    globalClient.get.mockResolvedValue({ data: [] });
    await ipm.listPests();
    expect(globalClient.get).toHaveBeenCalledWith('/ipm/pests', {
      params: { offset: 0, limit: 50 },
    });
    expect(tenantClient.get).not.toHaveBeenCalled();
  });

  it('getPest gets pest by key via global client', async () => {
    globalClient.get.mockResolvedValue({ data: { key: 'pe1' } });
    await ipm.getPest('pe1');
    expect(globalClient.get).toHaveBeenCalledWith('/ipm/pests/pe1');
  });

  it('createPest posts pest via global client', async () => {
    globalClient.post.mockResolvedValue({ data: { key: 'pe1' } });
    const payload = { name: 'Aphid' } as never;
    await ipm.createPest(payload);
    expect(globalClient.post).toHaveBeenCalledWith('/ipm/pests', payload);
  });

  it('updatePest puts pest via global client', async () => {
    globalClient.put.mockResolvedValue({ data: { key: 'pe1' } });
    const payload = { name: 'X' } as never;
    await ipm.updatePest('pe1', payload);
    expect(globalClient.put).toHaveBeenCalledWith('/ipm/pests/pe1', payload);
  });

  it('deletePest deletes pest via global client', async () => {
    globalClient.delete.mockResolvedValue({ data: undefined });
    await ipm.deletePest('pe1');
    expect(globalClient.delete).toHaveBeenCalledWith('/ipm/pests/pe1');
  });
});

describe('ipm endpoints — diseases (global client)', () => {
  it('listDiseases gets diseases with pagination', async () => {
    globalClient.get.mockResolvedValue({ data: [] });
    await ipm.listDiseases(2, 8);
    expect(globalClient.get).toHaveBeenCalledWith('/ipm/diseases', {
      params: { offset: 2, limit: 8 },
    });
  });

  it('getDisease gets disease by key', async () => {
    globalClient.get.mockResolvedValue({ data: { key: 'd1' } });
    await ipm.getDisease('d1');
    expect(globalClient.get).toHaveBeenCalledWith('/ipm/diseases/d1');
  });

  it('createDisease posts disease', async () => {
    globalClient.post.mockResolvedValue({ data: { key: 'd1' } });
    const payload = { name: 'Mildew' } as never;
    await ipm.createDisease(payload);
    expect(globalClient.post).toHaveBeenCalledWith('/ipm/diseases', payload);
  });

  it('updateDisease puts disease', async () => {
    globalClient.put.mockResolvedValue({ data: { key: 'd1' } });
    const payload = { name: 'X' } as never;
    await ipm.updateDisease('d1', payload);
    expect(globalClient.put).toHaveBeenCalledWith('/ipm/diseases/d1', payload);
  });

  it('deleteDisease deletes disease', async () => {
    globalClient.delete.mockResolvedValue({ data: undefined });
    await ipm.deleteDisease('d1');
    expect(globalClient.delete).toHaveBeenCalledWith('/ipm/diseases/d1');
  });
});

describe('ipm endpoints — treatments (global client)', () => {
  it('listTreatments gets treatments with pagination', async () => {
    globalClient.get.mockResolvedValue({ data: [] });
    await ipm.listTreatments();
    expect(globalClient.get).toHaveBeenCalledWith('/ipm/treatments', {
      params: { offset: 0, limit: 50 },
    });
  });

  it('getTreatment gets treatment by key', async () => {
    globalClient.get.mockResolvedValue({ data: { key: 'tr1' } });
    await ipm.getTreatment('tr1');
    expect(globalClient.get).toHaveBeenCalledWith('/ipm/treatments/tr1');
  });

  it('createTreatment posts treatment', async () => {
    globalClient.post.mockResolvedValue({ data: { key: 'tr1' } });
    const payload = { name: 'Neem' } as never;
    await ipm.createTreatment(payload);
    expect(globalClient.post).toHaveBeenCalledWith('/ipm/treatments', payload);
  });

  it('updateTreatment puts treatment', async () => {
    globalClient.put.mockResolvedValue({ data: { key: 'tr1' } });
    const payload = { name: 'X' } as never;
    await ipm.updateTreatment('tr1', payload);
    expect(globalClient.put).toHaveBeenCalledWith('/ipm/treatments/tr1', payload);
  });

  it('deleteTreatment deletes treatment', async () => {
    globalClient.delete.mockResolvedValue({ data: undefined });
    await ipm.deleteTreatment('tr1');
    expect(globalClient.delete).toHaveBeenCalledWith('/ipm/treatments/tr1');
  });
});

describe('ipm endpoints — plant-scoped (tenant client)', () => {
  it('createInspection posts via tenant client', async () => {
    tenantClient.post.mockResolvedValue({ data: { key: 'i1' } });
    const payload = { notes: 'ok' } as never;
    await ipm.createInspection('pl1', payload);
    expect(tenantClient.post).toHaveBeenCalledWith('/ipm/plants/pl1/inspections', payload);
    expect(globalClient.post).not.toHaveBeenCalled();
  });

  it('getInspections gets via tenant client with pagination', async () => {
    tenantClient.get.mockResolvedValue({ data: [] });
    await ipm.getInspections('pl1', 5, 10);
    expect(tenantClient.get).toHaveBeenCalledWith('/ipm/plants/pl1/inspections', {
      params: { offset: 5, limit: 10 },
    });
  });

  it('createTreatmentApplication posts via tenant client', async () => {
    tenantClient.post.mockResolvedValue({ data: { key: 'ta1' } });
    const payload = { treatment_key: 'tr1' } as never;
    await ipm.createTreatmentApplication('pl1', payload);
    expect(tenantClient.post).toHaveBeenCalledWith(
      '/ipm/plants/pl1/treatment-applications',
      payload,
    );
  });

  it('getTreatmentApplications gets via tenant client', async () => {
    tenantClient.get.mockResolvedValue({ data: [] });
    await ipm.getTreatmentApplications('pl1');
    expect(tenantClient.get).toHaveBeenCalledWith(
      '/ipm/plants/pl1/treatment-applications',
      { params: { offset: 0, limit: 50 } },
    );
  });

  it('getKarenzPeriods gets karenz via tenant client', async () => {
    tenantClient.get.mockResolvedValue({ data: [] });
    await ipm.getKarenzPeriods('pl1');
    expect(tenantClient.get).toHaveBeenCalledWith('/ipm/plants/pl1/karenz');
  });

  it('checkHarvestSafety gets without planned date', async () => {
    tenantClient.get.mockResolvedValue({ data: { safe: true } });
    await ipm.checkHarvestSafety('pl1');
    expect(tenantClient.get).toHaveBeenCalledWith('/ipm/plants/pl1/harvest-safety', {
      params: {},
    });
  });

  it('checkHarvestSafety adds planned_date param when provided', async () => {
    tenantClient.get.mockResolvedValue({ data: { safe: false } });
    await ipm.checkHarvestSafety('pl1', '2026-07-01');
    expect(tenantClient.get).toHaveBeenCalledWith('/ipm/plants/pl1/harvest-safety', {
      params: { planned_date: '2026-07-01' },
    });
  });
});
