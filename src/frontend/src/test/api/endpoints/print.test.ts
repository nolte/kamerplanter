import { describe, it, expect, beforeEach, vi } from 'vitest';

const mocks = vi.hoisted(() => {
  const client = {
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
    patch: vi.fn(),
    delete: vi.fn(),
  };
  // i18n is doubled as a stub returning a fixed language so the default
  // locale used by the endpoints is deterministic.
  const i18n = { language: 'de' };
  return { client, i18n };
});

vi.mock('@/api/client', () => ({
  __esModule: true,
  default: mocks.client,
  tenantClient: mocks.client,
}));

vi.mock('@/i18n/i18n', () => ({
  __esModule: true,
  default: mocks.i18n,
}));

import * as print from '@/api/endpoints/print';

const client = mocks.client;

beforeEach(() => {
  vi.clearAllMocks();
  mocks.i18n.language = 'de';
});

describe('print endpoints — nutrient plan PDF', () => {
  it('downloadNutrientPlanPdf gets blob with active locale', async () => {
    const blob = new Blob(['pdf']);
    client.get.mockResolvedValue({ data: blob });
    await expect(print.downloadNutrientPlanPdf('p1')).resolves.toBe(blob);
    expect(client.get).toHaveBeenCalledWith('/print/nutrient-plan/p1', {
      params: { locale: 'de' },
      responseType: 'blob',
    });
  });

  it('downloadNutrientPlanPdf uses explicit locale override', async () => {
    client.get.mockResolvedValue({ data: new Blob() });
    await print.downloadNutrientPlanPdf('p1', 'en');
    expect(client.get).toHaveBeenCalledWith('/print/nutrient-plan/p1', {
      params: { locale: 'en' },
      responseType: 'blob',
    });
  });
});

describe('print endpoints — care checklist PDF', () => {
  it('downloadCareChecklistPdf gets blob with locale only', async () => {
    client.get.mockResolvedValue({ data: new Blob() });
    await print.downloadCareChecklistPdf();
    expect(client.get).toHaveBeenCalledWith('/print/care-checklist', {
      params: { locale: 'de' },
      responseType: 'blob',
    });
  });

  it('downloadCareChecklistPdf adds date param when provided', async () => {
    client.get.mockResolvedValue({ data: new Blob() });
    await print.downloadCareChecklistPdf('2026-06-14', 'en');
    expect(client.get).toHaveBeenCalledWith('/print/care-checklist', {
      params: { locale: 'en', date: '2026-06-14' },
      responseType: 'blob',
    });
  });
});

describe('print endpoints — plant labels PDF', () => {
  it('downloadPlantLabelsPdf joins plant keys and uses active locale', async () => {
    client.get.mockResolvedValue({ data: new Blob() });
    await print.downloadPlantLabelsPdf(['a', 'b']);
    expect(client.get).toHaveBeenCalledWith('/print/plant-labels', {
      params: { plant_keys: 'a,b', locale: 'de' },
      responseType: 'blob',
    });
  });

  it('downloadPlantLabelsPdf adds fields, layout, qr size and locale', async () => {
    client.get.mockResolvedValue({ data: new Blob() });
    await print.downloadPlantLabelsPdf(
      ['a'],
      ['name', 'scientific_name'],
      'grid_2x4',
      30,
      'en',
    );
    expect(client.get).toHaveBeenCalledWith('/print/plant-labels', {
      params: {
        plant_keys: 'a',
        locale: 'en',
        fields: 'name,scientific_name',
        layout: 'grid_2x4',
        qr_size_mm: '30',
      },
      responseType: 'blob',
    });
  });

  it('downloadPlantLabelsPdf omits empty field list', async () => {
    client.get.mockResolvedValue({ data: new Blob() });
    await print.downloadPlantLabelsPdf(['a'], []);
    const [, opts] = client.get.mock.calls[0];
    expect((opts as { params: Record<string, unknown> }).params).not.toHaveProperty('fields');
  });

  it('downloadPlantLabelsPdf falls back to "de" when i18n has no language', async () => {
    mocks.i18n.language = undefined as never;
    client.get.mockResolvedValue({ data: new Blob() });
    await print.downloadPlantLabelsPdf(['a']);
    expect(client.get).toHaveBeenCalledWith('/print/plant-labels', {
      params: { plant_keys: 'a', locale: 'de' },
      responseType: 'blob',
    });
  });
});
