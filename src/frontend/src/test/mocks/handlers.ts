import { http, HttpResponse } from 'msw';

const mockFamilies = [
  {
    key: 'fam-1',
    name: 'Solanaceae',
    typical_nutrient_demand: 'heavy',
    common_pests: ['aphids', 'whitefly'],
    rotation_category: 'fruit',
    created_at: '2024-01-01T00:00:00Z',
    updated_at: null,
  },
  {
    key: 'fam-2',
    name: 'Fabaceae',
    typical_nutrient_demand: 'light',
    common_pests: ['bean beetle'],
    rotation_category: 'legume',
    created_at: '2024-01-02T00:00:00Z',
    updated_at: null,
  },
];

const mockSpecies = [
  {
    key: 'sp-1',
    scientific_name: 'Solanum lycopersicum',
    common_names: ['Tomato'],
    family_key: 'fam-1',
    genus: 'Solanum',
    hardiness_zones: ['9-11'],
    native_habitat: 'South America',
    growth_habit: 'herb',
    root_type: 'fibrous',
    allelopathy_score: 0.2,
    base_temp: 10,
    created_at: '2024-01-01T00:00:00Z',
    updated_at: null,
  },
];

const mockSites = [
  {
    key: 'site-1',
    name: 'Main Greenhouse',
    type: 'greenhouse',
    gps_coordinates: null,
    climate_zone: '8b',
    total_area_m2: 50,
    created_at: '2024-01-01T00:00:00Z',
    updated_at: null,
  },
];

const mockPlants = [
  {
    key: 'plant-1',
    instance_id: 'TOM-001',
    species_key: 'sp-1',
    cultivar_key: null,
    slot_key: null,
    substrate_batch_key: null,
    plant_name: 'Big Red',
    planted_on: '2024-03-15',
    removed_on: null,
    current_phase: 'vegetative',
    current_phase_key: null,
    current_phase_started_at: null,
    created_at: '2024-03-15T00:00:00Z',
    updated_at: null,
  },
];

export const handlers = [
  // Health
  http.get('/api/v1/health/live', () => {
    return HttpResponse.json({ status: 'alive' });
  }),

  // Botanical Families
  http.get('/api/v1/botanical-families', () => {
    return HttpResponse.json(mockFamilies);
  }),
  http.get('/api/v1/botanical-families/:key', ({ params }) => {
    const family = mockFamilies.find((f) => f.key === params.key);
    if (!family) return HttpResponse.json({ error_id: 'err_1', error_code: 'ENTITY_NOT_FOUND', message: 'Not found', details: [], timestamp: '', path: '', method: '' }, { status: 404 });
    return HttpResponse.json(family);
  }),
  http.post('/api/v1/botanical-families', async ({ request }) => {
    const body = (await request.json()) as Record<string, unknown>;
    return HttpResponse.json({ key: 'fam-new', ...body, created_at: new Date().toISOString(), updated_at: null }, { status: 201 });
  }),

  // Species
  http.get('/api/v1/species', () => {
    return HttpResponse.json({ items: mockSpecies, total: mockSpecies.length, offset: 0, limit: 50 });
  }),
  http.get('/api/v1/species/:key', ({ params }) => {
    const species = mockSpecies.find((s) => s.key === params.key);
    if (!species) return HttpResponse.json({ error_id: 'err_1', error_code: 'ENTITY_NOT_FOUND', message: 'Not found', details: [], timestamp: '', path: '', method: '' }, { status: 404 });
    return HttpResponse.json(species);
  }),

  // Sites (tenant-scoped)
  http.get('/api/v1/t/:tenant/sites', () => {
    return HttpResponse.json(mockSites);
  }),
  // Sites (non-scoped fallback for tests)
  http.get('/api/v1/sites', () => {
    return HttpResponse.json(mockSites);
  }),

  // Substrates
  http.get('/api/v1/substrates', () => {
    return HttpResponse.json([]);
  }),

  // Plant instances (tenant-scoped + fallback)
  http.get('/api/v1/t/:tenant/plant-instances', () => {
    return HttpResponse.json(mockPlants);
  }),
  http.get('/api/v1/plant-instances', () => {
    return HttpResponse.json(mockPlants);
  }),
  http.get('/api/v1/t/:tenant/plant-instances/:key', ({ params }) => {
    const plant = mockPlants.find((p) => p.key === params.key);
    if (!plant) return HttpResponse.json({ error_id: 'err_1', error_code: 'ENTITY_NOT_FOUND', message: 'Not found', details: [], timestamp: '', path: '', method: '' }, { status: 404 });
    return HttpResponse.json(plant);
  }),
  http.get('/api/v1/plant-instances/:key', ({ params }) => {
    const plant = mockPlants.find((p) => p.key === params.key);
    if (!plant) return HttpResponse.json({ error_id: 'err_1', error_code: 'ENTITY_NOT_FOUND', message: 'Not found', details: [], timestamp: '', path: '', method: '' }, { status: 404 });
    return HttpResponse.json(plant);
  }),

  // Calculations
  http.post('/api/v1/calculations/vpd', () => {
    return HttpResponse.json({ vpd_kpa: 1.05, status: 'optimal', recommendation: 'VPD is in optimal range for vegetative growth' });
  }),
  http.post('/api/v1/calculations/gdd', () => {
    return HttpResponse.json({ accumulated_gdd: 45.5, days_counted: 3 });
  }),
  http.post('/api/v1/calculations/slot-capacity', () => {
    return HttpResponse.json({ max_capacity: 111, optimal_range: [89, 100], plants_per_m2: 11.1 });
  }),
];
