import { cleanup, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { http, HttpResponse } from 'msw';
import i18n from 'i18next';
import { renderWithProviders } from '../helpers';
import { server } from '../mocks/server';
import type {
  PlantInstance,
  PlantInRun,
  PlantingRun,
  Location,
  Tank,
  TaskTemplate,
  WorkflowTargetType,
} from '@/api/types';
import WorkflowInstantiateDialog from '@/pages/aufgaben/WorkflowInstantiateDialog';

// Stabilise react-i18next's `t` identity for this suite. The dialog's data-load
// `useEffect` depends on `useApiError().handleError`, whose `useCallback` deps are
// `[t, notification]`. React-i18next returns a NEW `t` on every `languageChanged`
// event; under full-suite parallel load such an event can fire mid-test, which
// re-identifies `handleError`, re-runs the load effect and cancels the in-flight
// template fetch — the loading spinner then never clears, so the empty-state /
// preview never renders (a wandering, load-only flake). A single bound `t` keeps
// `handleError` stable, so the effect runs exactly once; translations still
// resolve against the current language via the i18n singleton.
vi.mock('react-i18next', async (importOriginal) => {
  const actual = await importOriginal<typeof import('react-i18next')>();
  const { default: i18nInstance } = await import('i18next');
  const stableT = i18nInstance.t.bind(i18nInstance);
  return {
    ...actual,
    useTranslation: (() => ({
      t: stableT,
      i18n: i18nInstance,
      ready: true,
    })) as unknown as typeof actual.useTranslation,
  };
});

// ── URLs (tenant-scoped; setup pins the active tenant to `test-tenant`) ──
const PLANTS_URL = '/api/v1/t/test-tenant/plant-instances';
const RUNS_URL = '/api/v1/t/test-tenant/planting-runs';
const RUN_PLANTS_URL = '/api/v1/t/test-tenant/planting-runs/:key/plants';
const SITES_URL = '/api/v1/t/test-tenant/sites';
const LOCATIONS_URL = '/api/v1/t/test-tenant/locations';
const TANKS_URL = '/api/v1/t/test-tenant/tanks';
const TEMPLATES_URL = '/api/v1/t/test-tenant/tasks/workflows/:key/templates';
const INSTANTIATE_URL = '/api/v1/t/test-tenant/tasks/workflows/:key/instantiate';

// ── Fixtures ────────────────────────────────────────────────────────
function makePlant(overrides: Partial<PlantInstance> = {}): PlantInstance {
  return {
    key: 'plant-1',
    instance_id: 'BSL-1',
    species_key: 'sp-1',
    cultivar_key: null,
    site_key: null,
    location_key: null,
    slot_key: null,
    substrate_batch_key: null,
    substrate_key: null,
    plant_name: 'Basil One',
    planted_on: '2024-03-01',
    removed_on: null,
    termination_type: null,
    termination_cause: null,
    current_phase: 'vegetative',
    current_phase_key: null,
    current_phase_started_at: null,
    container_volume_liters: null,
    substrate_type_override: null,
    species: null,
    cultivar: null,
    mother_key: null,
    created_at: '2024-03-01T00:00:00Z',
    updated_at: null,
    ...overrides,
  };
}

function makeRun(overrides: Partial<PlantingRun> = {}): PlantingRun {
  return {
    key: 'run-1',
    name: 'Run Alpha',
    run_type: 'batch',
    status: 'active',
    planned_quantity: 2,
    actual_quantity: 2,
    current_phase_key: null,
    current_phase_started_at: null,
    lifecycle_config_key: null,
    location_key: null,
    substrate_batch_key: null,
    planned_start_date: null,
    started_at: '2024-02-01T00:00:00Z',
    completed_at: null,
    source_plant_key: null,
    notes: null,
    created_at: '2024-02-01T00:00:00Z',
    updated_at: null,
    ...overrides,
  } as PlantingRun;
}

function makeRunPlant(overrides: Partial<PlantInRun> = {}): PlantInRun {
  return {
    key: 'rp-1',
    instance_id: 'RP-1',
    species_key: 'sp-1',
    cultivar_key: null,
    plant_name: 'Run Plant One',
    planted_on: '2024-02-01',
    removed_on: null,
    current_phase: 'vegetative',
    species: null,
    cultivar: null,
    detached_at: null,
    detach_reason: null,
    ...overrides,
  };
}

function makeLocation(overrides: Partial<Location> = {}): Location {
  return {
    key: 'loc-1',
    name: 'Zone A',
    ...overrides,
  } as Location;
}

function makeTank(overrides: Partial<Tank> = {}): Tank {
  return {
    key: 'tank-1',
    name: 'Tank Alpha',
    tank_type: 'nutrient',
    volume_liters: 100,
    material: 'plastic',
    has_lid: true,
    has_air_pump: false,
    has_circulation_pump: false,
    has_heater: false,
    is_light_proof: false,
    has_uv_sterilizer: false,
    has_ozone_generator: false,
    installed_on: null,
    location_key: null,
    notes: null,
    created_at: null,
    updated_at: null,
    ...overrides,
  };
}

function makeTemplate(overrides: Partial<TaskTemplate> = {}): TaskTemplate {
  return {
    key: 'tt-1',
    name: 'Watering',
    name_de: 'Gießen',
    instruction: 'Water it',
    instruction_de: '',
    description: '',
    description_de: '',
    rationale: '',
    rationale_de: '',
    category: 'watering',
    trigger_type: 'phase_entry',
    trigger_phase: 'veg',
    phase_display_name: 'Vegetative',
    phase_duration_days: 14,
    phase_stress_tolerance: 'low',
    days_offset: 2,
    stress_level: 'low',
    estimated_duration_minutes: 15,
    requires_photo: false,
    timer_duration_seconds: null,
    timer_label: null,
    tools_required: [],
    skill_level: 'beginner',
    optimal_time_of_day: null,
    workflow_template_key: 'wf-1',
    workflow_phase_key: 'p1',
    phase_definition_key: null,
    activity_key: null,
    sequence_order: 1,
    recovery_days: 1,
    is_optional: false,
    enabled: true,
    default_checklist: [],
    require_all_checklist_items: false,
    created_at: '2024-01-01T00:00:00Z',
    updated_at: null,
    ...overrides,
  } as TaskTemplate;
}

// ── Handler seeding ─────────────────────────────────────────────────
interface Seed {
  plants?: PlantInstance[];
  runs?: PlantingRun[];
  runPlants?: Record<string, PlantInRun[]>;
  locations?: Location[];
  tanks?: Tank[];
  templates?: TaskTemplate[];
  plantsError?: boolean;
  templatesError?: boolean;
  instantiate?: (entityKey: string) => Response;
}

function seed(state: Seed = {}) {
  const {
    plants = [],
    runs = [],
    runPlants = {},
    locations = [],
    tanks = [],
    templates = [],
    plantsError = false,
    templatesError = false,
    instantiate = () => HttpResponse.json({ key: 'ex-1' }) as unknown as Response,
  } = state;

  server.use(
    http.get(PLANTS_URL, () =>
      plantsError
        ? HttpResponse.json({ error_id: 'e', error_code: 'X', message: 'boom', details: [] }, { status: 500 })
        : HttpResponse.json(plants),
    ),
    http.get(RUNS_URL, () => HttpResponse.json(runs)),
    http.get(RUN_PLANTS_URL, ({ params }) =>
      HttpResponse.json(runPlants[params.key as string] ?? []),
    ),
    http.get(SITES_URL, () => HttpResponse.json([{ key: 'site-1', name: 'Site 1' }])),
    http.get(LOCATIONS_URL, () => HttpResponse.json(locations)),
    http.get(TANKS_URL, () => HttpResponse.json(tanks)),
    http.get(TEMPLATES_URL, () =>
      templatesError
        ? HttpResponse.json({ error_id: 'e', error_code: 'X', message: 'boom', details: [] }, { status: 500 })
        : HttpResponse.json(templates),
    ),
    http.post(INSTANTIATE_URL, async ({ request }) => {
      const body = (await request.json()) as { entity_key: string };
      return instantiate(body.entity_key);
    }),
  );
}

function renderDialog(props: {
  onClose?: () => void;
  onInstantiated?: () => void;
  targetEntityTypes?: WorkflowTargetType[];
  open?: boolean;
} = {}) {
  const onClose = props.onClose ?? vi.fn();
  const onInstantiated = props.onInstantiated ?? vi.fn();
  renderWithProviders(
    <WorkflowInstantiateDialog
      open={props.open ?? true}
      workflowKey="wf-1"
      targetEntityTypes={props.targetEntityTypes}
      onClose={onClose}
      onInstantiated={onInstantiated}
    />,
  );
  return { onClose, onInstantiated };
}

describe('WorkflowInstantiateDialog', () => {
  beforeEach(() => {
    i18n.changeLanguage('en');
  });
  afterEach(() => {
    // Unmount before resetting the language: the file's afterEach runs before
    // testing-library's auto-cleanup (LIFO), so an i18n reset here would
    // otherwise re-render every still-mounted useTranslation() consumer
    // outside act(). Unmounting first makes the reset touch nothing.
    cleanup();
    i18n.changeLanguage('en');
  });

  it('does not render dialog content while closed and skips loading', () => {
    const onInstantiated = vi.fn();
    seed({ plants: [makePlant()], templates: [makeTemplate()] });
    renderDialog({ open: false, onInstantiated });
    expect(screen.queryByTestId('workflow-instantiate-dialog')).not.toBeInTheDocument();
  });

  it('renders the sorted task-template preview for the default plant target', async () => {
    seed({
      plants: [makePlant()],
      templates: [
        makeTemplate({ key: 'tt-2', name: 'Second', sequence_order: 2 }),
        makeTemplate({ key: 'tt-1', name: 'First', sequence_order: 1 }),
      ],
    });
    renderDialog();

    expect(await screen.findByTestId('workflow-instantiate-dialog')).toBeInTheDocument();

    // Re-queried inside `waitFor` rather than asserted on a held reference
    // (#821). `expect(await screen.findByText('First')).toBeInTheDocument()`
    // resolves an element and *then* asserts on it, and the dialog is still
    // loading at that point: the template fetch finishes long before
    // `loadPlantData`, whose plants -> runs -> run-plants chain lands its
    // `setState` calls afterwards. That re-render replaces the list nodes, so
    // the element the assertion is holding is no longer in the document —
    // "element could not be found in the document", ~650ms in, nowhere near
    // the 5s wait budget.
    //
    // It reproduced on CI in the `Coverage` job specifically, where v8
    // instrumentation roughly doubles wall-clock and widens that window; the
    // uninstrumented `lint-test-build` run of the same commit passed. `waitFor`
    // re-runs its callback, so a re-render between attempts costs a retry
    // instead of a failure.
    await waitFor(() => {
      expect(screen.getByText('First')).toBeInTheDocument();
      expect(screen.getByText('Second')).toBeInTheDocument();
    });
    // Instantiate button starts disabled (no target selected).
    expect(screen.getByTestId('instantiate-button')).toBeDisabled();
  });

  it('instantiates a workflow for a single standalone plant', async () => {
    const posted: string[] = [];
    const onInstantiated = vi.fn();
    seed({
      plants: [makePlant()],
      templates: [makeTemplate()],
      instantiate: (key) => {
        posted.push(key);
        return HttpResponse.json({ key: 'ex-1' }) as unknown as Response;
      },
    });
    const user = userEvent.setup();
    const { onClose } = renderDialog({ onInstantiated });

    await screen.findByTestId('workflow-instantiate-dialog');
    const combo = screen.getByRole('combobox');
    await user.click(combo);
    await user.click(await screen.findByRole('option', { name: /Basil One/ }));

    const button = screen.getByTestId('instantiate-button');
    await waitFor(() => expect(button).toBeEnabled());
    await user.click(button);

    await waitFor(() => expect(onInstantiated).toHaveBeenCalled());
    expect(posted).toEqual(['plant-1']);
    expect(onClose).not.toHaveBeenCalled();
  });

  it('shows both run and standalone-plant option groups and batch-instantiates a run', async () => {
    const posted: string[] = [];
    const onInstantiated = vi.fn();
    seed({
      plants: [makePlant(), makePlant({ key: 'rp-1' })],
      runs: [makeRun(), makeRun({ key: 'run-2', name: 'Run Beta', status: 'harvesting' })],
      runPlants: {
        'run-1': [makeRunPlant({ key: 'rp-1' }), makeRunPlant({ key: 'rp-2', instance_id: 'RP-2' })],
        'run-2': [makeRunPlant({ key: 'rp-3', instance_id: 'RP-3' })],
      },
      templates: [makeTemplate()],
      instantiate: (key) => {
        posted.push(key);
        return HttpResponse.json({ key: 'ex' }) as unknown as Response;
      },
    });
    const user = userEvent.setup();
    renderDialog({ onInstantiated });

    await screen.findByTestId('workflow-instantiate-dialog');
    const combo = screen.getByRole('combobox');
    await user.click(combo);

    // Both group members are rendered (run label + standalone plant label).
    expect(await screen.findByRole('option', { name: /Run Alpha/ })).toBeInTheDocument();
    // rp-1 belongs to run-1 so it is filtered out of standalone plants; the
    // duplicate standalone plant (key plant-1) remains.
    expect(screen.getByRole('option', { name: /Basil One/ })).toBeInTheDocument();

    await user.click(screen.getByRole('option', { name: /Run Alpha/ }));
    const button = screen.getByTestId('instantiate-button');
    await waitFor(() => expect(button).toBeEnabled());
    await user.click(button);

    await waitFor(() => expect(onInstantiated).toHaveBeenCalled());
    // Both active plants of run-1 were instantiated.
    expect(posted.sort()).toEqual(['rp-1', 'rp-2']);
  });

  it('reports a partial batch when one plant fails', async () => {
    const onInstantiated = vi.fn();
    seed({
      runs: [makeRun()],
      runPlants: {
        'run-1': [makeRunPlant({ key: 'rp-1' }), makeRunPlant({ key: 'rp-2', instance_id: 'RP-2' })],
      },
      templates: [],
      instantiate: (key) =>
        key === 'rp-2'
          ? (HttpResponse.json({ error_id: 'e', error_code: 'X', message: 'boom', details: [] }, { status: 500 }) as unknown as Response)
          : (HttpResponse.json({ key: 'ex' }) as unknown as Response),
    });
    const user = userEvent.setup();
    renderDialog({ onInstantiated });

    await screen.findByTestId('workflow-instantiate-dialog');
    await user.click(screen.getByRole('combobox'));
    await user.click(await screen.findByRole('option', { name: /Run Alpha/ }));
    const button = screen.getByTestId('instantiate-button');
    await waitFor(() => expect(button).toBeEnabled());
    await user.click(button);

    await waitFor(() => expect(onInstantiated).toHaveBeenCalled());
    expect(
      await screen.findByText(i18n.t('pages.tasks.instantiatePartial', { success: 1, failed: 1 })),
    ).toBeInTheDocument();
  });

  it('reports a fully failed batch', async () => {
    const onInstantiated = vi.fn();
    seed({
      runs: [makeRun()],
      runPlants: { 'run-1': [makeRunPlant({ key: 'rp-1' })] },
      templates: [],
      instantiate: () =>
        HttpResponse.json({ error_id: 'e', error_code: 'X', message: 'boom', details: [] }, { status: 500 }) as unknown as Response,
    });
    const user = userEvent.setup();
    renderDialog({ onInstantiated });

    await screen.findByTestId('workflow-instantiate-dialog');
    await user.click(screen.getByRole('combobox'));
    await user.click(await screen.findByRole('option', { name: /Run Alpha/ }));
    const button = screen.getByTestId('instantiate-button');
    await waitFor(() => expect(button).toBeEnabled());
    await user.click(button);

    await waitFor(() => expect(onInstantiated).toHaveBeenCalled());
    expect(
      await screen.findByText(i18n.t('pages.tasks.instantiateError')),
    ).toBeInTheDocument();
  });

  it('instantiates a workflow for a location target', async () => {
    const posted: string[] = [];
    const onInstantiated = vi.fn();
    seed({
      locations: [makeLocation()],
      templates: [makeTemplate()],
      instantiate: (key) => {
        posted.push(key);
        return HttpResponse.json({ key: 'ex' }) as unknown as Response;
      },
    });
    const user = userEvent.setup();
    renderDialog({ targetEntityTypes: ['location'], onInstantiated });

    await screen.findByTestId('workflow-instantiate-dialog');
    await user.click(screen.getByRole('combobox'));
    await user.click(await screen.findByRole('option', { name: /Zone A/ }));
    const button = screen.getByTestId('instantiate-button');
    await waitFor(() => expect(button).toBeEnabled());
    await user.click(button);

    await waitFor(() => expect(onInstantiated).toHaveBeenCalled());
    expect(posted).toEqual(['loc-1']);
  });

  it('instantiates a workflow for a tank target', async () => {
    const posted: string[] = [];
    const onInstantiated = vi.fn();
    seed({
      tanks: [makeTank()],
      templates: [makeTemplate()],
      instantiate: (key) => {
        posted.push(key);
        return HttpResponse.json({ key: 'ex' }) as unknown as Response;
      },
    });
    const user = userEvent.setup();
    renderDialog({ targetEntityTypes: ['tank'], onInstantiated });

    await screen.findByTestId('workflow-instantiate-dialog');
    await user.click(screen.getByRole('combobox'));
    await user.click(await screen.findByRole('option', { name: /Tank Alpha/ }));
    const button = screen.getByTestId('instantiate-button');
    await waitFor(() => expect(button).toBeEnabled());
    await user.click(button);

    await waitFor(() => expect(onInstantiated).toHaveBeenCalled());
    expect(posted).toEqual(['tank-1']);
  });

  it('surfaces an error and keeps the dialog when a single-plant instantiate fails', async () => {
    const onInstantiated = vi.fn();
    seed({
      plants: [makePlant()],
      templates: [makeTemplate()],
      instantiate: () =>
        HttpResponse.json({ error_id: 'e', error_code: 'INTERNAL_ERROR', message: 'boom', details: [] }, { status: 500 }) as unknown as Response,
    });
    const user = userEvent.setup();
    renderDialog({ onInstantiated });

    await screen.findByTestId('workflow-instantiate-dialog');
    await user.click(screen.getByRole('combobox'));
    await user.click(await screen.findByRole('option', { name: /Basil One/ }));
    const button = screen.getByTestId('instantiate-button');
    await waitFor(() => expect(button).toBeEnabled());
    await user.click(button);

    expect(await screen.findByText(i18n.t('errors.server'))).toBeInTheDocument();
    expect(onInstantiated).not.toHaveBeenCalled();
  });

  it('closes via the cancel button', async () => {
    seed({ plants: [makePlant()], templates: [makeTemplate()] });
    const user = userEvent.setup();
    const { onClose } = renderDialog();

    await screen.findByTestId('workflow-instantiate-dialog');
    await user.click(screen.getByTestId('form-cancel-button'));
    expect(onClose).toHaveBeenCalled();
  });

  it('shows the empty-template message and tolerates load failures', async () => {
    seed({ plantsError: true, templatesError: true });
    renderDialog();

    await screen.findByTestId('workflow-instantiate-dialog');
    expect(
      await screen.findByText(i18n.t('pages.tasks.noTemplates')),
    ).toBeInTheDocument();
  });

  it('renders the option detail rows for a run inside its group', async () => {
    seed({
      runs: [makeRun()],
      runPlants: { 'run-1': [makeRunPlant({ key: 'rp-1' })] },
      templates: [makeTemplate()],
    });
    const user = userEvent.setup();
    renderDialog({ targetEntityTypes: ['planting_run'] });

    await screen.findByTestId('workflow-instantiate-dialog');
    await user.click(screen.getByRole('combobox'));
    const option = await screen.findByRole('option', { name: /Run Alpha/ });
    // Rendered planted-on caption (formatDate) is present within the option.
    expect(within(option).getByText(/Run Alpha/)).toBeInTheDocument();
  });
});
