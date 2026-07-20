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
    // ADR-006 E6: tomato is a facultative species (annual or overwintered
    // perennial), so the per-instance cultivation-cycle choice is offered.
    cultivation_flexible: true,
    created_at: '2024-01-01T00:00:00Z',
    updated_at: null,
  },
];

export const mockSuccessionPlans = [
  {
    key: 'sp-1',
    name: 'Salat Staffelanbau',
    species_key: 'sp-1',
    cultivar_key: null,
    interval_days: 21,
    start_date: '2024-04-01',
    end_date: '2024-09-01',
    plants_per_batch: 6,
    total_batches: 8,
    completed_batches: 2,
    status: 'active',
    reminder_days_before: 3,
    location_key: null,
    notes: null,
    created_at: '2024-01-01T00:00:00Z',
    updated_at: null,
  },
  {
    key: 'sp-2',
    name: 'Radieschen Sukzession',
    species_key: 'sp-1',
    cultivar_key: null,
    interval_days: 14,
    start_date: '2024-03-15',
    end_date: '2024-06-15',
    plants_per_batch: 12,
    total_batches: 0,
    completed_batches: 0,
    status: 'planned',
    reminder_days_before: 2,
    location_key: null,
    notes: null,
    created_at: '2024-01-02T00:00:00Z',
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

const mockLocations = [
  {
    key: 'loc-1',
    site_key: 'site-1',
    name: 'Zone A',
    location_type_key: 'lt-bed',
    parent_location_key: null,
    depth: 0,
    path: 'Zone A',
    created_at: '2024-01-01T00:00:00Z',
    updated_at: null,
  },
];

const mockSlots = [
  {
    key: 'slot-1',
    location_key: 'loc-1',
    slot_id: 'A1',
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

// Exported so substrate-list/detail tests can seed a populated list locally
// via server.use() without mutating the (intentionally empty) global handler.
export const mockSubstrates = [
  {
    key: 'sub-1',
    type: 'coco',
    brand: 'CocoBrand',
    name_de: 'Kokos Substrat',
    name_en: 'Coco Substrate',
    is_mix: false,
    mix_components: [],
    ph_base: 6.0,
    ec_base_ms: 0.4,
    water_retention: 'medium',
    air_porosity_percent: 30,
    composition: {},
    buffer_capacity: 'medium',
    reusable: true,
    max_reuse_cycles: 3,
    water_holding_capacity_percent: null,
    easily_available_water_percent: null,
    cec_meq_per_100g: null,
    particle_size_mm: null,
    bulk_density_g_per_l: null,
    irrigation_strategy: null,
    created_at: '2024-01-01T00:00:00Z',
    updated_at: null,
  },
  {
    key: 'sub-2',
    type: 'perlite',
    brand: null,
    name_de: 'Perlit',
    name_en: 'Perlite',
    is_mix: false,
    mix_components: [],
    ph_base: 7.0,
    ec_base_ms: 0.1,
    water_retention: 'low',
    air_porosity_percent: 60,
    composition: {},
    buffer_capacity: 'low',
    reusable: false,
    max_reuse_cycles: 1,
    water_holding_capacity_percent: null,
    easily_available_water_percent: null,
    cec_meq_per_100g: null,
    particle_size_mm: null,
    bulk_density_g_per_l: null,
    irrigation_strategy: null,
    created_at: '2024-01-02T00:00:00Z',
    updated_at: null,
  },
];

// Minimal fertilizer catalogue for the nutrient-calculations selectors (#610).
// The page only reads key/product_name/brand, so partial objects suffice.
export const mockFertilizers = [
  { key: 'grow', product_name: 'Grow A', brand: 'BrandX' },
  { key: 'bloom', product_name: 'Bloom B', brand: 'BrandX' },
  { key: 'compost', product_name: 'Compost', brand: 'Nature' },
  { key: 'liquid-manure', product_name: 'Jauche Liquid', brand: 'Nature' },
  { key: 'calmag', product_name: 'CalMag Plus', brand: 'BrandX' },
  { key: 'si', product_name: 'Silica Boost', brand: 'BrandX' },
  { key: 'base', product_name: 'Base Nute', brand: 'BrandX' },
];

export const handlers = [
  // Health
  http.get('/api/v1/health/live', () => {
    return HttpResponse.json({ status: 'alive' });
  }),

  // Fertilizers catalogue (tenant-scoped) — offset/limit paging aware so the
  // fetchAllFertilizers pager terminates after a single short page.
  http.get('/api/v1/t/:tenant/fertilizers', ({ request }) => {
    const url = new URL(request.url);
    const offset = Number(url.searchParams.get('offset') ?? '0');
    return HttpResponse.json(offset > 0 ? [] : mockFertilizers);
  }),
  http.get('/api/v1/fertilizers', ({ request }) => {
    const url = new URL(request.url);
    const offset = Number(url.searchParams.get('offset') ?? '0');
    return HttpResponse.json(offset > 0 ? [] : mockFertilizers);
  }),

  // Auth
  http.post('/api/v1/auth/login', () => {
    return HttpResponse.json({ access_token: 'jwt-msw', token_type: 'bearer' });
  }),
  http.post('/api/v1/auth/register', async ({ request }) => {
    const body = (await request.json()) as Record<string, unknown>;
    return HttpResponse.json(
      { key: 'user-new', email: body.email, display_name: body.display_name },
      { status: 201 },
    );
  }),
  http.post('/api/v1/auth/refresh', () => {
    return HttpResponse.json({ access_token: 'jwt-refreshed', token_type: 'bearer' });
  }),
  http.post('/api/v1/auth/logout', () => {
    return new HttpResponse(null, { status: 204 });
  }),
  http.get('/api/v1/users/me', () => {
    return HttpResponse.json({ key: 'user-1', email: 'demo@kamerplanter.local', display_name: 'Demo' });
  }),
  // OAuth providers (login page) — default: none configured
  http.get('/api/v1/auth/oauth/providers', () => {
    return HttpResponse.json([]);
  }),
  // Linked login providers for the current user — default: none linked
  http.get('/api/v1/users/me/providers', () => {
    return HttpResponse.json([]);
  }),

  // User preferences (tenant-scoped + fallback)
  http.get('/api/v1/t/:tenant/user-preferences', () => {
    return HttpResponse.json({ experience_level: 'intermediate', locale: 'de', theme: 'light' });
  }),
  http.get('/api/v1/user-preferences', () => {
    return HttpResponse.json({ experience_level: 'intermediate', locale: 'de', theme: 'light' });
  }),
  http.patch('/api/v1/t/:tenant/user-preferences', async ({ request }) => {
    const body = (await request.json()) as Record<string, unknown>;
    return HttpResponse.json({ experience_level: 'intermediate', locale: 'de', theme: 'light', ...body });
  }),
  http.patch('/api/v1/user-preferences', async ({ request }) => {
    const body = (await request.json()) as Record<string, unknown>;
    return HttpResponse.json({ experience_level: 'intermediate', locale: 'de', theme: 'light', ...body });
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
  http.post('/api/v1/species', async ({ request }) => {
    const body = (await request.json()) as Record<string, unknown>;
    return HttpResponse.json({ key: 'sp-new', ...body, created_at: new Date().toISOString(), updated_at: null }, { status: 201 });
  }),
  // Reference-image gallery (REQ-029-A) — default empty; specific tests override.
  http.get('/api/v1/species/:key/reference-images', ({ params }) => {
    return HttpResponse.json({ species_key: params.key, count: 0, images: [] });
  }),
  // Species phase sequence (plant-instance create dialog, issue #626). Default:
  // no sequence → the dialog falls back to the LifecycleConfig growth phases.
  // Tests for PhaseSequence-backed species override this handler.
  http.get('/api/v1/species/:key/phase-sequence', () => {
    return HttpResponse.json(null);
  }),
  // Lifecycle config + growth phases (plant-instance create dialog)
  http.get('/api/v1/species/:key/lifecycle', ({ params }) => {
    return HttpResponse.json({
      key: `lc-${params.key}`,
      species_key: params.key,
      cycle_type: 'annual',
      typical_lifespan_years: null,
      dormancy_required: false,
      vernalization_required: false,
      vernalization_min_days: null,
      photoperiod_type: 'day_neutral',
      critical_day_length_hours: null,
      phase_sequence_key: null,
      created_at: '2024-01-01T00:00:00Z',
      updated_at: null,
    });
  }),
  http.get('/api/v1/growth-phases', () => {
    return HttpResponse.json([
      {
        key: 'gp-veg',
        name: 'vegetative',
        display_name: 'Vegetativ',
        description: '',
        lifecycle_key: 'lc-sp-1',
        typical_duration_days: 30,
        sequence_order: 1,
        is_terminal: false,
        allows_harvest: false,
        stress_tolerance: 'medium',
        watering_interval_days: null,
        created_at: '2024-01-01T00:00:00Z',
        updated_at: null,
      },
      {
        key: 'gp-flower',
        name: 'flowering',
        display_name: 'Blüte',
        description: '',
        lifecycle_key: 'lc-sp-1',
        typical_duration_days: 60,
        sequence_order: 2,
        is_terminal: true,
        allows_harvest: true,
        stress_tolerance: 'low',
        watering_interval_days: null,
        created_at: '2024-01-01T00:00:00Z',
        updated_at: null,
      },
    ]);
  }),

  // Sites (tenant-scoped)
  http.get('/api/v1/t/:tenant/sites', () => {
    return HttpResponse.json(mockSites);
  }),
  // Sites (non-scoped fallback for tests)
  http.get('/api/v1/sites', () => {
    return HttpResponse.json(mockSites);
  }),
  http.get('/api/v1/t/:tenant/sites/:key', ({ params }) => {
    const site = mockSites.find((s) => s.key === params.key);
    if (!site) return HttpResponse.json({ error_id: 'err_1', error_code: 'ENTITY_NOT_FOUND', message: 'Not found', details: [], timestamp: '', path: '', method: '' }, { status: 404 });
    return HttpResponse.json(site);
  }),

  // Locations (tenant-scoped)
  http.get('/api/v1/t/:tenant/locations', () => {
    return HttpResponse.json(mockLocations);
  }),
  http.get('/api/v1/t/:tenant/locations/:key', ({ params }) => {
    const loc = mockLocations.find((l) => l.key === params.key);
    if (!loc) return HttpResponse.json({ error_id: 'err_1', error_code: 'ENTITY_NOT_FOUND', message: 'Not found', details: [], timestamp: '', path: '', method: '' }, { status: 404 });
    return HttpResponse.json(loc);
  }),

  // Slots (tenant-scoped)
  http.get('/api/v1/t/:tenant/slots', () => {
    return HttpResponse.json(mockSlots);
  }),
  http.get('/api/v1/t/:tenant/slots/:key', ({ params }) => {
    const slot = mockSlots.find((s) => s.key === params.key);
    if (!slot) return HttpResponse.json({ error_id: 'err_1', error_code: 'ENTITY_NOT_FOUND', message: 'Not found', details: [], timestamp: '', path: '', method: '' }, { status: 404 });
    return HttpResponse.json(slot);
  }),
  http.get('/api/v1/slots/:key', ({ params }) => {
    const slot = mockSlots.find((s) => s.key === params.key);
    if (!slot) return HttpResponse.json({ error_id: 'err_1', error_code: 'ENTITY_NOT_FOUND', message: 'Not found', details: [], timestamp: '', path: '', method: '' }, { status: 404 });
    return HttpResponse.json(slot);
  }),

  // Location types (non-scoped)
  http.get('/api/v1/location-types', () => {
    return HttpResponse.json([
      { key: 'lt-bed', name: 'Beet', code: 'bed', icon: 'Grass', allowed_child_types: [] },
    ]);
  }),

  // Location tree (tenant-scoped)
  http.get('/api/v1/t/:tenant/sites/:key/location-tree', () => {
    return HttpResponse.json([
      {
        key: 'loc-1',
        name: 'Zone A',
        location_type_key: 'lt-bed',
        slot_count: 2,
        active_plant_count: 1,
        tank_name: null,
        children: [],
      },
    ]);
  }),

  // Create site / location (tenant-scoped)
  http.post('/api/v1/t/:tenant/sites', async ({ request }) => {
    const body = (await request.json()) as Record<string, unknown>;
    return HttpResponse.json({ key: 'site-new', ...body, created_at: new Date().toISOString(), updated_at: null }, { status: 201 });
  }),
  http.post('/api/v1/t/:tenant/locations', async ({ request }) => {
    const body = (await request.json()) as Record<string, unknown>;
    return HttpResponse.json({ key: 'loc-new', ...body, created_at: new Date().toISOString(), updated_at: null }, { status: 201 });
  }),
  // Create site / location (non-scoped fallback for tests without active tenant)
  http.post('/api/v1/sites', async ({ request }) => {
    const body = (await request.json()) as Record<string, unknown>;
    return HttpResponse.json({ key: 'site-new', ...body, created_at: new Date().toISOString(), updated_at: null }, { status: 201 });
  }),
  http.post('/api/v1/locations', async ({ request }) => {
    const body = (await request.json()) as Record<string, unknown>;
    return HttpResponse.json({ key: 'loc-new', ...body, created_at: new Date().toISOString(), updated_at: null }, { status: 201 });
  }),
  // Locations / slots (non-scoped fallback)
  http.get('/api/v1/locations', () => {
    return HttpResponse.json(mockLocations);
  }),
  http.get('/api/v1/slots', () => {
    return HttpResponse.json(mockSlots);
  }),
  // Location tree (non-scoped fallback)
  http.get('/api/v1/sites/:key/location-tree', () => {
    return HttpResponse.json([
      {
        key: 'loc-1',
        name: 'Zone A',
        location_type_key: 'lt-bed',
        slot_count: 2,
        active_plant_count: 1,
        tank_name: null,
        children: [],
      },
    ]);
  }),

  // Substrates — global list stays empty (preserves existing empty-state test).
  // Substrate-detail tests seed a populated list locally via server.use().
  http.get('/api/v1/substrates', () => {
    return HttpResponse.json([]);
  }),
  http.post('/api/v1/substrates', async ({ request }) => {
    const body = (await request.json()) as Record<string, unknown>;
    return HttpResponse.json({ key: 'sub-new', is_mix: false, mix_components: [], composition: {}, ...body, created_at: new Date().toISOString(), updated_at: null }, { status: 201 });
  }),
  http.post('/api/v1/substrates/preview-mix', async ({ request }) => {
    const body = (await request.json()) as { name_de?: string; name_en?: string; components: { substrate_key: string; fraction: number }[] };
    return HttpResponse.json({
      key: 'sub-preview',
      type: 'coco',
      brand: null,
      name_de: body.name_de ?? 'Mix',
      name_en: body.name_en ?? 'Mix',
      is_mix: true,
      mix_components: body.components,
      ph_base: 6.2,
      ec_base_ms: 0.3,
      water_retention: 'medium',
      air_porosity_percent: 40,
      composition: { coco: 0.5, perlite: 0.5 },
      buffer_capacity: 'medium',
      reusable: false,
      max_reuse_cycles: 1,
      water_holding_capacity_percent: null,
      easily_available_water_percent: null,
      cec_meq_per_100g: null,
      particle_size_mm: null,
      bulk_density_g_per_l: null,
      irrigation_strategy: 'cycle',
      created_at: '2024-01-01T00:00:00Z',
      updated_at: null,
    });
  }),
  http.post('/api/v1/substrates/mix', async ({ request }) => {
    const body = (await request.json()) as { name_de?: string; name_en?: string; components: { substrate_key: string; fraction: number }[] };
    return HttpResponse.json({
      key: 'sub-mix-new',
      type: 'coco',
      brand: null,
      name_de: body.name_de ?? 'Mix',
      name_en: body.name_en ?? 'Mix',
      is_mix: true,
      mix_components: body.components,
      ph_base: 6.2,
      ec_base_ms: 0.3,
      water_retention: 'medium',
      air_porosity_percent: 40,
      composition: { coco: 0.5, perlite: 0.5 },
      buffer_capacity: 'medium',
      reusable: false,
      max_reuse_cycles: 1,
      water_holding_capacity_percent: null,
      easily_available_water_percent: null,
      cec_meq_per_100g: null,
      particle_size_mm: null,
      bulk_density_g_per_l: null,
      irrigation_strategy: null,
      created_at: '2024-01-01T00:00:00Z',
      updated_at: null,
    }, { status: 201 });
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

  http.post('/api/v1/t/:tenant/plant-instances', async ({ request }) => {
    const body = (await request.json()) as Record<string, unknown>;
    return HttpResponse.json({ key: 'plant-new', ...body, created_at: new Date().toISOString(), updated_at: null }, { status: 201 });
  }),
  http.post('/api/v1/plant-instances', async ({ request }) => {
    const body = (await request.json()) as Record<string, unknown>;
    return HttpResponse.json({ key: 'plant-new', ...body, created_at: new Date().toISOString(), updated_at: null }, { status: 201 });
  }),

  // Planting runs (tenant-scoped + non-scoped fallback) — list used for plant→run mapping
  http.get('/api/v1/t/:tenant/planting-runs', () => {
    return HttpResponse.json([]);
  }),
  http.get('/api/v1/planting-runs', () => {
    return HttpResponse.json([]);
  }),

  // REQ-013 §2 Succession plans (tenant-scoped) — defaults; per-test overrides via server.use()
  http.get('/api/v1/t/:tenant/succession-plans', () => {
    return HttpResponse.json([]);
  }),
  http.post('/api/v1/t/:tenant/succession-plans', async ({ request }) => {
    const body = (await request.json()) as Record<string, unknown>;
    return HttpResponse.json(
      {
        key: 'sp-new',
        total_batches: 0,
        completed_batches: 0,
        status: 'planned',
        created_at: '2024-01-01T00:00:00Z',
        updated_at: null,
        ...body,
      },
      { status: 201 },
    );
  }),
  http.get('/api/v1/t/:tenant/succession-plans/:key', ({ params }) => {
    return HttpResponse.json({ ...mockSuccessionPlans[0], key: params.key });
  }),
  http.put('/api/v1/t/:tenant/succession-plans/:key', async ({ params, request }) => {
    const body = (await request.json()) as Record<string, unknown>;
    return HttpResponse.json({ ...mockSuccessionPlans[0], key: params.key, ...body });
  }),
  http.delete('/api/v1/t/:tenant/succession-plans/:key', () => {
    return new HttpResponse(null, { status: 204 });
  }),
  http.post('/api/v1/t/:tenant/succession-plans/:key/generate', ({ params }) => {
    return HttpResponse.json(
      {
        plan: {
          ...mockSuccessionPlans[0],
          key: params.key,
          total_batches: 8,
          completed_batches: 8,
          status: 'active',
        },
        generated_count: 8,
        runs: Array.from({ length: 8 }, (_, i) => ({
          run_key: `run-${i + 1}`,
          name: `Salat Staffel ${i + 1}`,
          succession_sequence: i + 1,
          succession_total: 8,
          planned_start_date: `2024-04-${String(1 + i * 3).padStart(2, '0')}`,
        })),
      },
      { status: 201 },
    );
  }),
  http.post('/api/v1/t/:tenant/succession-plans/:key/generate-next', ({ params }) => {
    return HttpResponse.json(
      {
        plan: { ...mockSuccessionPlans[0], key: params.key, completed_batches: 1 },
        generated: true,
        run: {
          run_key: 'run-1',
          name: 'Salat Staffel 1',
          succession_sequence: 1,
          succession_total: 8,
          planned_start_date: '2024-04-01',
        },
      },
      { status: 201 },
    );
  }),

  // REQ-022 Overwintering profiles (tenant-scoped + non-scoped fallback)
  http.get('/api/v1/t/:tenant/overwintering-profiles/hardiness-overview', () => {
    return HttpResponse.json({ green: 0, yellow: 0, red: 0, total: 0, red_plants: [] });
  }),
  http.get('/api/v1/overwintering-profiles/hardiness-overview', () => {
    return HttpResponse.json({ green: 0, yellow: 0, red: 0, total: 0, red_plants: [] });
  }),
  http.get('/api/v1/t/:tenant/overwintering-profiles', () => {
    return HttpResponse.json([]);
  }),
  http.get('/api/v1/overwintering-profiles', () => {
    return HttpResponse.json([]);
  }),
  http.post('/api/v1/t/:tenant/overwintering-profiles', async ({ request }) => {
    const body = (await request.json()) as Record<string, unknown>;
    return HttpResponse.json({ key: 'ow-new', auto_generated: false, ...body, created_at: new Date().toISOString(), updated_at: null }, { status: 201 });
  }),
  http.post('/api/v1/overwintering-profiles', async ({ request }) => {
    const body = (await request.json()) as Record<string, unknown>;
    return HttpResponse.json({ key: 'ow-new', auto_generated: false, ...body, created_at: new Date().toISOString(), updated_at: null }, { status: 201 });
  }),

  // REQ-047 Season & overwintering automation (tenant-scoped defaults)
  http.get('/api/v1/t/:tenant/season/overview', () => {
    return HttpResponse.json({ states: [] });
  }),
  http.get('/api/v1/t/:tenant/plants/:plantKey/overwintering/status', () => {
    // Consistent with the 404 profile default below: winter-hardy, no profile,
    // on a frost-relevant (overwinterable) site.
    return HttpResponse.json({
      has_profile: false,
      hardiness_light: 'green',
      will_materialize: false,
      site_overwinterable: true,
    });
  }),
  http.get('/api/v1/t/:tenant/plants/:plantKey/overwintering', () => {
    return new HttpResponse(null, { status: 404 });
  }),

  // Cultivars (nested under species)
  http.get('/api/v1/species/:key/cultivars', () => {
    return HttpResponse.json([]);
  }),

  // Privacy / DSGVO (PrivacySettingsPage) — defaults; per-test overrides via server.use()
  http.get('/api/v1/privacy/consents', () => {
    return HttpResponse.json([]);
  }),
  http.post('/api/v1/privacy/export', () => {
    return HttpResponse.json({ key: 'exp-1', status: 'pending', requested_at: '2024-01-01T00:00:00Z', completed_at: null });
  }),
  http.post('/api/v1/privacy/erasure', () => {
    return new HttpResponse(null, { status: 202 });
  }),
  http.post('/api/v1/privacy/restrict', async ({ request }) => {
    const body = (await request.json()) as Record<string, unknown>;
    return HttpResponse.json({ key: 'restr-1', notes: null, created_at: '2024-01-01T00:00:00Z', lifted_at: null, ...body });
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
