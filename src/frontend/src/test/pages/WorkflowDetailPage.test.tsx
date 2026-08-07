import { cleanup, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { http, HttpResponse } from 'msw';
import i18n from 'i18next';
import { renderWithProviders } from '../helpers';
import { server } from '../mocks/server';
import type {
  WorkflowTemplate,
  TaskTemplate,
  WorkflowPhase,
} from '@/api/types';
import type { WorkflowExecutionEnriched } from '@/api/endpoints/tasks';

// Keep the real navigate (useTabUrl drives tab switching through it); only the
// route param is stubbed so the page resolves a workflow key.
vi.mock('react-router-dom', async (orig) => {
  const actual = await orig<typeof import('react-router-dom')>();
  return { ...actual, useParams: () => ({ key: 'wf-1' }) };
});

import WorkflowDetailPage from '@/pages/aufgaben/WorkflowDetailPage';

const WF_URL = '/api/v1/t/test-tenant/tasks/workflows/:key';
const TEMPLATES_URL = '/api/v1/t/test-tenant/tasks/workflows/:key/templates';
const EXECUTIONS_URL = '/api/v1/t/test-tenant/tasks/workflows/:key/executions';
const PHASES_URL = '/api/v1/t/test-tenant/tasks/workflows/:key/phases';
const DELETE_URL = '/api/v1/t/test-tenant/tasks/workflows/:key';
const UPDATE_URL = '/api/v1/t/test-tenant/tasks/workflows/:key';
const TEMPLATE_ITEM_URL = '/api/v1/t/test-tenant/tasks/templates/:key';
const TEMPLATE_CREATE_URL = '/api/v1/t/test-tenant/tasks/templates';
const PHASE_REORDER_URL = '/api/v1/t/test-tenant/tasks/phases/reorder';
const PHASE_ITEM_URL = '/api/v1/t/test-tenant/tasks/phases/:key';

function makeWorkflow(overrides: Partial<WorkflowTemplate> = {}): WorkflowTemplate {
  return {
    key: 'wf-1',
    name: 'Tomaten-Workflow',
    description: 'Ein Workflow.',
    created_by: 'user-1',
    version: '1.0',
    species_compatible: [],
    growth_system: null,
    difficulty_level: 'beginner',
    category: 'general',
    tags: [],
    is_system: false,
    auto_generated: false,
    species_key: null,
    species_name: '',
    total_duration_days: 0,
    assigned_entity_count: 0,
    target_entity_types: ['plant_instance'],
    phase_sequence_key: null,
    created_at: '2024-01-01T00:00:00Z',
    updated_at: null,
    ...overrides,
  };
}

function makeTemplate(overrides: Partial<TaskTemplate> = {}): TaskTemplate {
  return {
    key: 'tt-1',
    name: 'Watering',
    name_de: 'Gießen',
    instruction: '',
    instruction_de: '',
    description: 'Water the plant.',
    description_de: 'Pflanze gießen.',
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
  };
}

function makePhase(overrides: Partial<WorkflowPhase> = {}): WorkflowPhase {
  return {
    key: 'p1',
    workflow_template_key: 'wf-1',
    name: 'Vegetative',
    description: '',
    phase_order: 1,
    duration_days: 14,
    stress_tolerance: 'low',
    trigger_phase: 'veg',
    created_at: '2024-01-01T00:00:00Z',
    updated_at: null,
    ...overrides,
  };
}

function makeExecution(
  overrides: Partial<WorkflowExecutionEnriched> = {},
): WorkflowExecutionEnriched {
  return {
    key: 'ex-1',
    entity_key: 'plant-1',
    entity_type: 'plant_instance',
    entity_name: 'Tomato #1',
    plant_removed: false,
    species_name: 'Solanum lycopersicum',
    completion_percentage: 50,
    on_schedule: true,
    started_at: '2024-02-01T00:00:00Z',
    completed_at: null,
    ...overrides,
  };
}

interface WfState {
  workflow?: WorkflowTemplate;
  templates?: TaskTemplate[];
  executions?: WorkflowExecutionEnriched[];
  phases?: WorkflowPhase[];
}

function useWorkflow(state: WfState = {}) {
  const {
    workflow = makeWorkflow(),
    templates = [],
    executions = [],
    phases = [],
  } = state;
  server.use(
    http.get(WF_URL, () => HttpResponse.json(workflow)),
    http.get(TEMPLATES_URL, () => HttpResponse.json(templates)),
    http.get(EXECUTIONS_URL, () => HttpResponse.json(executions)),
    http.get(PHASES_URL, () => HttpResponse.json(phases)),
    // Edit-tab species picker (lazy) + activity catalog + favorites.
    http.get('/api/v1/species', () => HttpResponse.json({ items: [], total: 0 })),
    http.get('/api/v1/species/:key', () =>
      HttpResponse.json({ key: 'sp-1', scientific_name: 'Solanum lycopersicum', common_names: ['Tomato'] }),
    ),
    http.get('/api/v1/activities', () => HttpResponse.json([])),
    http.get('/api/v1/t/test-tenant/favorites', () => HttpResponse.json([])),
  );
}

describe('WorkflowDetailPage', () => {
  beforeEach(() => {
    i18n.changeLanguage('de');
  });

  afterEach(() => {
    // Unmount before resetting the language: the file's afterEach runs before
    // testing-library's auto-cleanup (LIFO), so an i18n reset here would
    // otherwise re-render every still-mounted useTranslation() consumer
    // outside act(). Unmounting first makes the reset touch nothing.
    cleanup();
    i18n.changeLanguage('en');
  });

  it('renders the loaded workflow detail', async () => {
    useWorkflow();
    renderWithProviders(<WorkflowDetailPage />, { route: '/aufgaben/workflows/wf-1' });

    expect(await screen.findByTestId('workflow-detail-page')).toBeInTheDocument();
    expect(screen.getAllByText('Tomaten-Workflow').length).toBeGreaterThan(0);
  });

  it('renders detail-tab metadata rows and the assigned executions table', async () => {
    useWorkflow({
      workflow: makeWorkflow({
        tags: ['spring'],
        species_compatible: ['Solanum lycopersicum'],
        target_entity_types: ['plant_instance', 'tank'],
        phase_sequence_key: 'seq-9',
      }),
      templates: [makeTemplate()],
      executions: [makeExecution()],
    });
    renderWithProviders(<WorkflowDetailPage />, { route: '/aufgaben/workflows/wf-1' });

    await screen.findByTestId('workflow-detail-page');
    // description + version rows
    expect(screen.getByText('Ein Workflow.')).toBeInTheDocument();
    // phase-sequence link
    expect(
      screen.getByRole('link', { name: i18n.t('pages.phaseSequences.viewPhaseSequence') }),
    ).toBeInTheDocument();
    // execution row rendered (species also appears as a compatibility chip)
    expect(screen.getAllByText('Solanum lycopersicum').length).toBeGreaterThan(0);
    expect(screen.getByText('50%')).toBeInTheDocument();
  });

  it('toggles the hide-inactive switch to reveal completed executions', async () => {
    useWorkflow({
      executions: [
        makeExecution({ completion_percentage: 100, completed_at: '2024-03-01T00:00:00Z' }),
      ],
    });
    const user = userEvent.setup();
    renderWithProviders(<WorkflowDetailPage />, { route: '/aufgaben/workflows/wf-1' });

    await screen.findByTestId('workflow-detail-page');
    // All executions completed -> inactive message shown while hideInactive is on.
    expect(screen.getByText(i18n.t('pages.tasks.allExecutionsInactive'))).toBeInTheDocument();

    // Details tab has a single switch: the hide-inactive toggle.
    await user.click(screen.getByRole('switch'));
    expect(await screen.findByText('Solanum lycopersicum')).toBeInTheDocument();
  });

  it('renders the templates tab grouped by phase', async () => {
    useWorkflow({ templates: [makeTemplate()], phases: [makePhase()] });
    const user = userEvent.setup();
    renderWithProviders(<WorkflowDetailPage />, { route: '/aufgaben/workflows/wf-1' });

    await screen.findByTestId('workflow-detail-page');
    await user.click(screen.getByRole('tab', { name: i18n.t('pages.tasks.taskTemplates') }));

    // Template name (DE) shown within its phase group.
    expect(await screen.findByText('Gießen')).toBeInTheDocument();

    // The per-phase-group "add activity" button opens the catalog dialog.
    const addButtons = screen.getAllByRole('button', {
      name: i18n.t('pages.tasks.addActivityFromCatalog'),
    });
    await user.click(addButtons[addButtons.length - 1]);
    expect((await screen.findAllByRole('dialog')).length).toBeGreaterThan(0);
  });

  it('renders an unassigned, disabled, manual template with placeholder duration', async () => {
    useWorkflow({
      templates: [
        makeTemplate({
          key: 'tt-un',
          workflow_phase_key: null,
          activity_key: null,
          enabled: false,
          is_optional: false,
          estimated_duration_minutes: null,
          stress_level: 'unknown-x',
        }),
      ],
      phases: [],
    });
    const user = userEvent.setup();
    renderWithProviders(<WorkflowDetailPage />, { route: '/aufgaben/workflows/wf-1' });

    await screen.findByTestId('workflow-detail-page');
    await user.click(screen.getByRole('tab', { name: i18n.t('pages.tasks.taskTemplates') }));

    // Unassigned phase group heading.
    expect(await screen.findByText(i18n.t('pages.tasks.unassignedPhase'))).toBeInTheDocument();
    // Manual source chip (no activity link).
    expect(screen.getByText(i18n.t('pages.tasks.sourceManual'))).toBeInTheDocument();
    // Missing estimated duration renders an em dash.
    expect(screen.getAllByText('—').length).toBeGreaterThan(0);
  });

  it('aggregates executions and colours off-schedule progress', async () => {
    useWorkflow({
      executions: [
        makeExecution({ key: 'ex-a', entity_key: 'p-a', on_schedule: false, completion_percentage: 30 }),
        makeExecution({ key: 'ex-b', entity_key: 'p-b', plant_removed: true, completion_percentage: 80 }),
      ],
    });
    renderWithProviders(<WorkflowDetailPage />, { route: '/aufgaben/workflows/wf-1' });

    await screen.findByTestId('workflow-detail-page');
    // Standalone-plants label (no run grouping) + aggregated progress.
    expect(screen.getByText(i18n.t('pages.runs.standalonePlants'))).toBeInTheDocument();
    expect(screen.getByText('55%')).toBeInTheDocument();
  });

  it('toggles a task template enabled state', async () => {
    let putCalled = false;
    useWorkflow({ templates: [makeTemplate()], phases: [makePhase()] });
    server.use(
      http.put(TEMPLATE_ITEM_URL, () => {
        putCalled = true;
        return HttpResponse.json(makeTemplate({ enabled: false }));
      }),
    );
    const user = userEvent.setup();
    renderWithProviders(<WorkflowDetailPage />, { route: '/aufgaben/workflows/wf-1' });

    await screen.findByTestId('workflow-detail-page');
    await user.click(screen.getByRole('tab', { name: i18n.t('pages.tasks.taskTemplates') }));
    await screen.findByText('Gießen');

    // The per-template enable switch.
    await user.click(screen.getAllByRole('switch')[0]);
    await waitFor(() => expect(putCalled).toBe(true));
  });

  it('duplicates a task template', async () => {
    let created = false;
    useWorkflow({ templates: [makeTemplate()], phases: [makePhase()] });
    server.use(
      http.post(TEMPLATE_CREATE_URL, () => {
        created = true;
        return HttpResponse.json(makeTemplate({ key: 'tt-2' }));
      }),
    );
    const user = userEvent.setup();
    renderWithProviders(<WorkflowDetailPage />, { route: '/aufgaben/workflows/wf-1' });

    await screen.findByTestId('workflow-detail-page');
    await user.click(screen.getByRole('tab', { name: i18n.t('pages.tasks.taskTemplates') }));
    await screen.findByText('Gießen');

    await user.click(screen.getByRole('button', { name: i18n.t('pages.tasks.duplicateTemplate') }));
    await waitFor(() => expect(created).toBe(true));
    expect(
      await screen.findByText(i18n.t('pages.tasks.taskTemplateDuplicated')),
    ).toBeInTheDocument();
  });

  it('deletes a task template through the confirm dialog', async () => {
    let deletedKey: string | null = null;
    useWorkflow({ templates: [makeTemplate()], phases: [makePhase()] });
    server.use(
      http.delete(TEMPLATE_ITEM_URL, ({ params }) => {
        deletedKey = params.key as string;
        return new HttpResponse(null, { status: 204 });
      }),
    );
    const user = userEvent.setup();
    renderWithProviders(<WorkflowDetailPage />, { route: '/aufgaben/workflows/wf-1' });

    await screen.findByTestId('workflow-detail-page');
    await user.click(screen.getByRole('tab', { name: i18n.t('pages.tasks.taskTemplates') }));
    await screen.findByText('Gießen');

    await user.click(screen.getByRole('button', { name: i18n.t('common.delete') }));
    await user.click(await screen.findByTestId('confirm-dialog-confirm'));

    await waitFor(() => expect(deletedKey).toBe('tt-1'));
    expect(
      await screen.findByText(i18n.t('pages.tasks.taskTemplateDeleted')),
    ).toBeInTheDocument();
  });

  it('reorders and deletes a workflow phase', async () => {
    let reordered = false;
    let deletedPhase: string | null = null;
    useWorkflow({
      templates: [makeTemplate({ workflow_phase_key: 'p1' })],
      phases: [makePhase({ key: 'p1', name: 'Vegetative', phase_order: 1 }), makePhase({ key: 'p2', name: 'Flowering', phase_order: 2, trigger_phase: 'flower' })],
    });
    server.use(
      http.put(PHASE_REORDER_URL, () => {
        reordered = true;
        return HttpResponse.json([
          makePhase({ key: 'p1', phase_order: 2 }),
          makePhase({ key: 'p2', phase_order: 1 }),
        ]);
      }),
      http.delete(PHASE_ITEM_URL, ({ params }) => {
        deletedPhase = params.key as string;
        return new HttpResponse(null, { status: 204 });
      }),
    );
    const user = userEvent.setup();
    renderWithProviders(<WorkflowDetailPage />, { route: '/aufgaben/workflows/wf-1' });

    await screen.findByTestId('workflow-detail-page');
    await user.click(screen.getByRole('tab', { name: i18n.t('pages.tasks.taskTemplates') }));
    await screen.findAllByText('Vegetative');

    // Move the first phase down, then move the second phase up.
    await user.click(screen.getAllByRole('button', { name: i18n.t('pages.tasks.movePhaseDown') })[0]);
    await waitFor(() => expect(reordered).toBe(true));
    await user.click(screen.getAllByRole('button', { name: i18n.t('pages.tasks.movePhaseUp') })[1]);

    // Delete the first phase.
    await user.click(screen.getAllByRole('button', { name: i18n.t('pages.tasks.deletePhase') })[0]);
    await user.click(await screen.findByTestId('confirm-dialog-confirm'));
    await waitFor(() => expect(deletedPhase).not.toBeNull());
  });

  it('opens the edit-phase dialog', async () => {
    useWorkflow({ phases: [makePhase()] });
    const user = userEvent.setup();
    renderWithProviders(<WorkflowDetailPage />, { route: '/aufgaben/workflows/wf-1' });

    await screen.findByTestId('workflow-detail-page');
    await user.click(screen.getByRole('tab', { name: i18n.t('pages.tasks.taskTemplates') }));
    await screen.findAllByText('Vegetative');

    await user.click(screen.getAllByRole('button', { name: i18n.t('pages.tasks.editPhase') })[0]);
    expect((await screen.findAllByRole('dialog')).length).toBeGreaterThan(0);
  });

  it('opens the linked activity from a catalog-sourced template', async () => {
    useWorkflow({
      templates: [makeTemplate({ activity_key: 'act-1' })],
      phases: [makePhase()],
    });
    const user = userEvent.setup();
    renderWithProviders(<WorkflowDetailPage />, { route: '/aufgaben/workflows/wf-1' });

    await screen.findByTestId('workflow-detail-page');
    await user.click(screen.getByRole('tab', { name: i18n.t('pages.tasks.taskTemplates') }));
    await screen.findByText('Gießen');

    // Navigating away is the last action (it resets the tab route param).
    await user.click(screen.getByRole('button', { name: i18n.t('pages.tasks.openActivity') }));
  });

  it('opens the create-phase dialog', async () => {
    useWorkflow({ phases: [makePhase()] });
    const user = userEvent.setup();
    renderWithProviders(<WorkflowDetailPage />, { route: '/aufgaben/workflows/wf-1' });

    await screen.findByTestId('workflow-detail-page');
    await user.click(screen.getByRole('tab', { name: i18n.t('pages.tasks.taskTemplates') }));
    await user.click(await screen.findByRole('button', { name: i18n.t('pages.tasks.createPhase') }));
    expect((await screen.findAllByRole('dialog')).length).toBeGreaterThan(0);
  });

  it('opens the manual task-template dialog', async () => {
    useWorkflow({ phases: [makePhase()] });
    const user = userEvent.setup();
    renderWithProviders(<WorkflowDetailPage />, { route: '/aufgaben/workflows/wf-1' });

    await screen.findByTestId('workflow-detail-page');
    await user.click(screen.getByRole('tab', { name: i18n.t('pages.tasks.taskTemplates') }));
    await user.click(await screen.findByRole('button', { name: i18n.t('pages.tasks.createManually') }));
    expect((await screen.findAllByRole('dialog')).length).toBeGreaterThan(0);
  });

  it('adds an activity from the catalog dialog', async () => {
    let created = false;
    useWorkflow({ phases: [makePhase()] });
    server.use(
      http.get('/api/v1/activities', () =>
        HttpResponse.json([
          {
            key: 'act-1',
            tenant_key: 't',
            name: 'Pruning',
            name_de: 'Beschneiden',
            description: 'Prune it',
            description_de: 'Schneiden',
            category: 'pruning',
            stress_level: 'medium',
            skill_level: 'beginner',
            recovery_days_default: 2,
            recovery_days_by_species: {},
            forbidden_phases: [],
            restricted_sub_phases: [],
            tools_required: ['scissors'],
            estimated_duration_minutes: 10,
            requires_photo: false,
            species_compatible: [],
            is_system: false,
            sort_order: 1,
            tags: [],
            created_at: null,
            updated_at: null,
          },
        ]),
      ),
      http.post(TEMPLATE_CREATE_URL, () => {
        created = true;
        return HttpResponse.json(makeTemplate({ key: 'tt-new', activity_key: 'act-1' }));
      }),
    );
    const user = userEvent.setup();
    renderWithProviders(<WorkflowDetailPage />, { route: '/aufgaben/workflows/wf-1' });

    await screen.findByTestId('workflow-detail-page');
    await user.click(screen.getByRole('tab', { name: i18n.t('pages.tasks.taskTemplates') }));

    // Top-level "add activity from catalog" button.
    await user.click(
      (await screen.findAllByRole('button', { name: i18n.t('pages.tasks.addActivityFromCatalog') }))[0],
    );
    // Select the catalog activity.
    const activity = await screen.findByText('Beschneiden');
    await user.click(activity);
    // Confirm add (dialog action button).
    const dialog = screen.getAllByRole('dialog').slice(-1)[0];
    await user.click(
      within(dialog).getByRole('button', { name: i18n.t('pages.tasks.addActivityFromCatalog') }),
    );

    await waitFor(() => expect(created).toBe(true));
    expect(
      await screen.findByText(i18n.t('pages.tasks.taskTemplateCreated')),
    ).toBeInTheDocument();
  });

  it('resolves a species breadcrumb when the workflow has a species key', async () => {
    useWorkflow({ workflow: makeWorkflow({ species_key: 'sp-1', species_name: 'Tomato' }) });
    renderWithProviders(<WorkflowDetailPage />, { route: '/aufgaben/workflows/wf-1' });

    expect(await screen.findByTestId('workflow-detail-page')).toBeInTheDocument();
  });

  it('renders catalog-sourced templates with source chip and open-activity action, and edits day offset', async () => {
    let putCalled = false;
    useWorkflow({
      templates: [makeTemplate({ activity_key: 'act-1', is_optional: true })],
      phases: [makePhase()],
    });
    server.use(
      http.put(TEMPLATE_ITEM_URL, () => {
        putCalled = true;
        return HttpResponse.json(makeTemplate());
      }),
    );
    const user = userEvent.setup();
    renderWithProviders(<WorkflowDetailPage />, { route: '/aufgaben/workflows/wf-1' });

    await screen.findByTestId('workflow-detail-page');
    await user.click(screen.getByRole('tab', { name: i18n.t('pages.tasks.taskTemplates') }));
    await screen.findByText('Gießen');

    // Catalog source chip + optional chip present.
    expect(screen.getByText(i18n.t('pages.tasks.sourceCatalog'))).toBeInTheDocument();
    expect(screen.getByText(i18n.t('pages.activityPlan.optional'))).toBeInTheDocument();
    // Open-activity action is available for catalog-linked templates.
    expect(
      screen.getByRole('button', { name: i18n.t('pages.tasks.openActivity') }),
    ).toBeInTheDocument();

    // Change the day-offset spin field (no modal in the way).
    const offset = screen.getAllByRole('spinbutton')[0];
    await user.clear(offset);
    await user.type(offset, '7');
    await waitFor(() => expect(putCalled).toBe(true));

    // Then open the template edit dialog (last action).
    await user.click(screen.getByRole('button', { name: i18n.t('common.edit') }));
    expect((await screen.findAllByRole('dialog')).length).toBeGreaterThan(0);
  });

  it('filters the activity catalog dialog by search, favorites and compatibility', async () => {
    useWorkflow({
      workflow: makeWorkflow({ species_compatible: ['Solanum lycopersicum'] }),
      phases: [makePhase()],
    });
    server.use(
      http.get('/api/v1/activities', () =>
        HttpResponse.json([
          {
            key: 'act-1', tenant_key: 't', name: 'Pruning', name_de: 'Beschneiden',
            description: 'Prune it', description_de: 'Schneiden', category: 'pruning',
            stress_level: 'medium', skill_level: 'beginner', recovery_days_default: 2,
            recovery_days_by_species: {}, forbidden_phases: [], restricted_sub_phases: [],
            tools_required: ['scissors'], estimated_duration_minutes: 10, requires_photo: false,
            species_compatible: ['Solanum lycopersicum'], is_system: false, sort_order: 1,
            tags: ['maintenance'], created_at: null, updated_at: null,
          },
          {
            key: 'act-2', tenant_key: 't', name: 'Fertilize', name_de: 'Düngen',
            description: 'Feed it', description_de: 'Füttern', category: 'fertilizing',
            stress_level: 'low', skill_level: 'beginner', recovery_days_default: 1,
            recovery_days_by_species: {}, forbidden_phases: [], restricted_sub_phases: [],
            tools_required: [], estimated_duration_minutes: 5, requires_photo: false,
            species_compatible: [], is_system: false, sort_order: 2,
            tags: [], created_at: null, updated_at: null,
          },
        ]),
      ),
      http.get('/api/v1/t/test-tenant/favorites', ({ request }) => {
        const url = new URL(request.url);
        if (url.searchParams.get('type') === 'activities') {
          return HttpResponse.json([{ target_key: 'act-1' }]);
        }
        return HttpResponse.json([]);
      }),
    );
    const user = userEvent.setup();
    renderWithProviders(<WorkflowDetailPage />, { route: '/aufgaben/workflows/wf-1' });

    await screen.findByTestId('workflow-detail-page');
    await user.click(screen.getByRole('tab', { name: i18n.t('pages.tasks.taskTemplates') }));
    await user.click(
      (await screen.findAllByRole('button', { name: i18n.t('pages.tasks.addActivityFromCatalog') }))[0],
    );

    // Both activities visible initially.
    expect(await screen.findByText('Beschneiden')).toBeInTheDocument();
    expect(screen.getByText('Düngen')).toBeInTheDocument();

    // Favorites filter -> only the favorited activity remains.
    await user.click(screen.getByRole('button', { name: i18n.t('common.favorites') }));
    await waitFor(() => expect(screen.queryByText('Düngen')).not.toBeInTheDocument());
    expect(screen.getByText('Beschneiden')).toBeInTheDocument();

    // Compatible filter (workflow has a compatible species).
    await user.click(screen.getByRole('button', { name: i18n.t('pages.tasks.compatibleOnly') }));
    expect(screen.getByText('Beschneiden')).toBeInTheDocument();

    // Back to all + text search.
    await user.click(screen.getByRole('button', { name: i18n.t('common.all') }));
    const dialog = screen.getAllByRole('dialog').slice(-1)[0];
    await user.type(
      within(dialog).getByPlaceholderText(i18n.t('pages.tasks.searchActivities')),
      'düngen',
    );
    await waitFor(() => expect(screen.queryByText('Beschneiden')).not.toBeInTheDocument());
    expect(screen.getByText('Düngen')).toBeInTheDocument();

    // Expand the activity description.
    await user.click(within(dialog).getByRole('button', { name: i18n.t('pages.tasks.showDescription') }));
  });

  it('renders the edit-tab species picker and resets it via cancel', async () => {
    useWorkflow({
      workflow: makeWorkflow({ species_compatible: ['Solanum lycopersicum'] }),
    });
    server.use(
      http.get('/api/v1/species', () =>
        HttpResponse.json({
          items: [
            { key: 'sp-1', scientific_name: 'Solanum lycopersicum', common_names: ['Tomato'], plant_category: 'vegetable', family_name: 'Solanaceae' },
            { key: 'sp-2', scientific_name: 'Ocimum basilicum', common_names: ['Basil'], plant_category: 'herb', family_name: 'Lamiaceae' },
          ],
          total: 2,
        }),
      ),
      http.get('/api/v1/t/test-tenant/favorites', ({ request }) => {
        const url = new URL(request.url);
        if (url.searchParams.get('type') === 'species') {
          return HttpResponse.json([{ target_key: 'sp-1' }]);
        }
        return HttpResponse.json([]);
      }),
    );
    const user = userEvent.setup();
    renderWithProviders(<WorkflowDetailPage />, { route: '/aufgaben/workflows/wf-1' });

    await screen.findByTestId('workflow-detail-page');
    await user.click(screen.getByRole('tab', { name: i18n.t('common.edit') }));

    // Preselected compatible species chip.
    expect(await screen.findByText('Tomato')).toBeInTheDocument();

    // Open the species Autocomplete to render its options.
    const picker = screen.getByPlaceholderText(i18n.t('common.search'));
    await user.click(picker);
    // Select the second species option (exercises the onChange handler).
    await user.click(await screen.findByRole('option', { name: /Basil/ }));
    expect(await screen.findByText('Basil')).toBeInTheDocument();

    // Toggle the favorites species filter chip.
    await user.click(screen.getByRole('button', { name: i18n.t('common.favorites') }));

    // Cancel resets the form.
    await user.click(screen.getByTestId('form-cancel-button'));
    expect(screen.getByTestId('workflow-detail-page')).toBeInTheDocument();
  });

  it('resolves compatible species by key and tolerates failing breadcrumb/favorites lookups', async () => {
    useWorkflow({
      workflow: makeWorkflow({ species_key: 'sp-x', species_compatible: ['sp-2'] }),
    });
    server.use(
      http.get('/api/v1/species/:key', () => new HttpResponse(null, { status: 500 })),
      http.get('/api/v1/species', () =>
        HttpResponse.json({
          items: [
            { key: 'sp-1', scientific_name: 'Solanum lycopersicum', common_names: ['Tomato'], plant_category: null, family_name: 'Solanaceae' },
            { key: 'sp-2', scientific_name: 'Ocimum basilicum', common_names: [], plant_category: 'herb', family_name: 'Lamiaceae' },
          ],
          total: 2,
        }),
      ),
      http.get('/api/v1/t/test-tenant/favorites', () => new HttpResponse(null, { status: 500 })),
    );
    const user = userEvent.setup();
    renderWithProviders(<WorkflowDetailPage />, { route: '/aufgaben/workflows/wf-1' });

    await screen.findByTestId('workflow-detail-page');
    await user.click(screen.getByRole('tab', { name: i18n.t('common.edit') }));

    // species_compatible referenced sp-2 by key -> preselected as a chip.
    expect(await screen.findByText('Ocimum basilicum')).toBeInTheDocument();
  });

  it('saves workflow edits from the edit tab', async () => {
    let updated = false;
    useWorkflow();
    server.use(
      http.put(UPDATE_URL, () => {
        updated = true;
        return HttpResponse.json(makeWorkflow({ name: 'Renamed' }));
      }),
    );
    const user = userEvent.setup();
    renderWithProviders(<WorkflowDetailPage />, { route: '/aufgaben/workflows/wf-1' });

    await screen.findByTestId('workflow-detail-page');
    await user.click(screen.getByRole('tab', { name: i18n.t('common.edit') }));

    const nameField = await screen.findByLabelText(i18n.t('pages.tasks.workflowName'), {
      exact: false,
    });
    await user.type(nameField, ' v2');
    await user.click(screen.getByTestId('form-submit-button'));

    await waitFor(() => expect(updated).toBe(true));
    expect(
      await screen.findByText(i18n.t('pages.tasks.workflowUpdated')),
    ).toBeInTheDocument();
  });

  it('deletes the workflow from the edit tab through the confirm dialog', async () => {
    let deletedKey: string | null = null;
    useWorkflow();
    server.use(
      http.delete(DELETE_URL, ({ params }) => {
        deletedKey = params.key as string;
        return new HttpResponse(null, { status: 204 });
      }),
    );
    const user = userEvent.setup();
    renderWithProviders(<WorkflowDetailPage />, { route: '/aufgaben/workflows/wf-1' });

    await screen.findByTestId('workflow-detail-page');
    await user.click(screen.getByRole('tab', { name: i18n.t('common.edit') }));

    await user.click(
      await screen.findByRole('button', { name: i18n.t('pages.tasks.deleteWorkflow') }),
    );
    await user.click(await screen.findByTestId('confirm-dialog-confirm'));

    await waitFor(() => expect(deletedKey).toBe('wf-1'));
  });

  it('surfaces an error when the workflow delete fails', async () => {
    useWorkflow();
    server.use(http.delete(DELETE_URL, () => new HttpResponse(null, { status: 500 })));
    const user = userEvent.setup();
    renderWithProviders(<WorkflowDetailPage />, { route: '/aufgaben/workflows/wf-1' });

    await screen.findByTestId('workflow-detail-page');
    await user.click(screen.getByRole('tab', { name: i18n.t('common.edit') }));

    await user.click(
      await screen.findByRole('button', { name: i18n.t('pages.tasks.deleteWorkflow') }),
    );
    await user.click(await screen.findByTestId('confirm-dialog-confirm'));

    expect(await screen.findByText(i18n.t('errors.server'))).toBeInTheDocument();
  });

  it('renders the copy-as-template action for a system workflow and hides the delete button', async () => {
    useWorkflow({ workflow: makeWorkflow({ is_system: true }) });
    const user = userEvent.setup();
    renderWithProviders(<WorkflowDetailPage />, { route: '/aufgaben/workflows/wf-1' });

    await screen.findByTestId('workflow-detail-page');
    // System workflows expose a disabled copy-as-template button.
    expect(screen.getByTestId('copy-workflow-as-template-button')).toBeDisabled();

    // The edit tab hides the delete-workflow button for system data.
    await user.click(screen.getByRole('tab', { name: i18n.t('common.edit') }));
    await waitFor(() =>
      expect(
        screen.queryByRole('button', { name: i18n.t('pages.tasks.deleteWorkflow') }),
      ).not.toBeInTheDocument(),
    );
  });

  // ── #965 item 3: a system workflow's children are read-only ──
  //
  // The backend now answers every child write below with a 422. Leaving the
  // buttons in place would turn each of them into an error toast, which is worse
  // than not offering them: the page would keep promising an edit it cannot
  // perform. So the whole write surface of the templates tab is replaced by one
  // explanation, and these tests pin *both* halves — the actions are gone, and
  // the data plus the read-only jump to the linked activity are still there.

  it('replaces the templates-tab write actions with one explanation for a system workflow', async () => {
    useWorkflow({
      workflow: makeWorkflow({ is_system: true }),
      templates: [makeTemplate({ activity_key: 'act-1' })],
      phases: [makePhase()],
    });
    const user = userEvent.setup();
    renderWithProviders(<WorkflowDetailPage />, { route: '/aufgaben/workflows/wf-1' });

    await screen.findByTestId('workflow-detail-page');
    await user.click(screen.getByRole('tab', { name: i18n.t('pages.tasks.taskTemplates') }));

    expect(await screen.findByTestId('system-workflow-children-readonly')).toHaveTextContent(
      i18n.t('pages.tasks.systemWorkflowChildrenReadOnly'),
    );

    // Nothing that would write a child is offered any more.
    expect(screen.queryByTestId('create-workflow-phase-button')).not.toBeInTheDocument();
    expect(screen.queryByTestId('create-task-template-button')).not.toBeInTheDocument();
    expect(screen.queryByTestId('add-activity-from-catalog-button')).not.toBeInTheDocument();
    expect(screen.queryByTestId('add-activity-to-phase-p1')).not.toBeInTheDocument();
    expect(screen.queryByTestId('duplicate-task-template-tt-1')).not.toBeInTheDocument();
    expect(screen.queryByTestId('edit-task-template-tt-1')).not.toBeInTheDocument();
    expect(screen.queryByTestId('delete-task-template-tt-1')).not.toBeInTheDocument();
    expect(
      screen.queryByRole('button', { name: i18n.t('pages.tasks.movePhaseUp') }),
    ).not.toBeInTheDocument();
    expect(
      screen.queryByRole('button', { name: i18n.t('pages.tasks.editPhase') }),
    ).not.toBeInTheDocument();
    expect(
      screen.queryByRole('button', { name: i18n.t('pages.tasks.deletePhase') }),
    ).not.toBeInTheDocument();

    // The catalogue itself stays fully visible — #324 is what over-strictness costs.
    expect(screen.getByTestId('task-template-row-tt-1')).toBeInTheDocument();
    expect(screen.getByText('Gießen')).toBeInTheDocument();
    expect(screen.getByTestId('open-activity-tt-1')).toBeInTheDocument();

    // The two inline editors write through the same refused endpoint.
    expect(screen.getAllByRole('switch')[0]).toBeDisabled();
    expect(screen.getAllByRole('spinbutton')[0]).toBeDisabled();
  });

  it("keeps the templates-tab write actions for the tenant's own workflow", async () => {
    useWorkflow({ templates: [makeTemplate()], phases: [makePhase()] });
    const user = userEvent.setup();
    renderWithProviders(<WorkflowDetailPage />, { route: '/aufgaben/workflows/wf-1' });

    await screen.findByTestId('workflow-detail-page');
    await user.click(screen.getByRole('tab', { name: i18n.t('pages.tasks.taskTemplates') }));

    expect(await screen.findByTestId('create-workflow-phase-button')).toBeInTheDocument();
    expect(screen.getByTestId('create-task-template-button')).toBeInTheDocument();
    expect(screen.getByTestId('add-activity-from-catalog-button')).toBeInTheDocument();
    expect(screen.getByTestId('duplicate-task-template-tt-1')).toBeInTheDocument();
    expect(screen.getByTestId('delete-task-template-tt-1')).toBeInTheDocument();
    expect(screen.queryByTestId('system-workflow-children-readonly')).not.toBeInTheDocument();
    expect(screen.getAllByRole('switch')[0]).toBeEnabled();
  });

  it('renders an error state when the workflow fails to load', async () => {
    server.use(
      http.get(WF_URL, () => new HttpResponse(null, { status: 500 })),
      http.get(TEMPLATES_URL, () => HttpResponse.json([])),
      http.get(EXECUTIONS_URL, () => HttpResponse.json([])),
      http.get(PHASES_URL, () => HttpResponse.json([])),
    );
    renderWithProviders(<WorkflowDetailPage />, { route: '/aufgaben/workflows/wf-1' });

    // ErrorDisplay renders the stringified error; the page chrome is absent.
    await waitFor(() =>
      expect(screen.queryByTestId('workflow-detail-page')).not.toBeInTheDocument(),
    );
    expect(screen.getAllByRole('alert').length).toBeGreaterThan(0);
  });
});
