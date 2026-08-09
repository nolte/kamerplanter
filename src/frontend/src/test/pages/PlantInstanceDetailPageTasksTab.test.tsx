import { screen, waitFor, fireEvent, within } from '@testing-library/react';
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { http, HttpResponse } from 'msw';
import i18n from 'i18next';
import type { PlantInstance, TaskItem } from '@/api/types';
import { setActiveTenantSlug } from '@/api/client';

// The detail page reads its target key from the route via useParams. Provide a
// stable key without depending on a matched route path.
let currentKey = 'pi-1';
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual<typeof import('react-router-dom')>('react-router-dom');
  return {
    ...actual,
    useParams: () => ({ key: currentKey }),
  };
});

// Stub the interactive dialogs the page mounts (they read redux slices the shared
// test store does not preload); none are relevant to the Tasks-tab behaviour (#578).
vi.mock('@/pages/pflege/components/CareConfirmDialog', () => ({ default: () => null }));
vi.mock('@/pages/pflege/components/CareProfileEditDialog', () => ({ default: () => null }));
vi.mock('@/pages/giessprotokoll/WateringLogCreateDialog', () => ({ default: () => null }));
vi.mock('@/pages/duengung/NutrientPlanAssignDialog', () => ({ default: () => null }));
vi.mock('@/pages/pflanzen/PhaseTransitionDialog', () => ({ default: () => null }));
vi.mock('@/pages/pflanzen/TerminationDialog', () => ({ default: () => null }));
vi.mock('@/pages/pflanzen/PlantTagDialog', () => ({ default: () => null }));
vi.mock('@/components/print/PlantLabelDialog', () => ({ PlantLabelDialog: () => null }));
vi.mock('@/components/pests/PestScanButton', () => ({ default: () => null }));
vi.mock('@/pages/aufgaben/TaskCreateDialog', () => ({ default: () => null }));

import PlantInstanceDetailPage from '@/pages/pflanzen/PlantInstanceDetailPage';
import { renderWithProviders } from '../helpers';
import { server } from '../mocks/server';

const TASKS_ROUTE = '/pflanzen/plant-instances/pi-1#tasks';

function makePlant(overrides: Partial<PlantInstance> = {}): PlantInstance {
  return {
    key: 'pi-1',
    instance_id: 'BASIL-0001',
    // A species key without a master-data record: getSpecies 404s and the
    // species-dependent panels stay unrendered, keeping the test focused.
    species_key: 'sp-missing',
    cultivar_key: null,
    site_key: null,
    location_key: null,
    slot_key: null,
    substrate_batch_key: null,
    substrate_key: null,
    plant_name: 'Basil',
    planted_on: '2024-06-01',
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
    created_at: '2024-06-01T00:00:00Z',
    updated_at: null,
    ...overrides,
  };
}

function makeTask(overrides: Partial<TaskItem> = {}): TaskItem {
  return {
    key: 'task-1',
    name: 'Task 1',
    name_de: 'Task 1',
    instruction: '',
    instruction_de: '',
    category: 'care_reminder',
    entity_key: 'pi-1',
    entity_type: 'plant_instance',
    due_date: '2024-06-10',
    scheduled_time: null,
    status: 'pending',
    priority: 'medium',
    skill_level: 'beginner',
    stress_level: 'low',
    estimated_duration_minutes: null,
    actual_duration_minutes: null,
    requires_photo: false,
    photo_refs: [],
    timer_duration_seconds: null,
    timer_label: null,
    completion_notes: null,
    difficulty_rating: null,
    quality_rating: null,
    tags: [],
    checklist: [],
    assigned_to_user_key: null,
    recurrence_rule: null,
    recurrence_end_date: null,
    origin: 'user',
    source: '',
    source_run_ref: null,
    external_ref: null,
    parent_recurring_task_key: null,
    trigger_phase: null,
    trigger_phase_override: null,
    reopened_at: null,
    reopened_from_status: null,
    started_at: null,
    completed_at: null,
    activity_key: null,
    template_key: null,
    workflow_execution_key: null,
    watering_event_key: null,
    created_at: '2024-06-01T00:00:00Z',
    updated_at: null,
    ...overrides,
  };
}

/** Seed the tenant-scoped instance endpoint so the page's main load() completes. */
function seedPlant(plant: PlantInstance) {
  const handler = http.get('/api/v1/t/:tenant/plant-instances/:key', ({ params }) => {
    if (params.key === plant.key) return HttpResponse.json(plant);
    return HttpResponse.json(
      { error_id: 'e', error_code: 'ENTITY_NOT_FOUND', message: 'Not found', details: [], timestamp: '', path: '', method: '' },
      { status: 404 },
    );
  });
  server.use(handler, http.get('/api/v1/plant-instances/:key', ({ params }) => {
    if (params.key === plant.key) return HttpResponse.json(plant);
    return HttpResponse.json({ error_code: 'ENTITY_NOT_FOUND', message: 'Not found' }, { status: 404 });
  }));
}

/**
 * Seed the dedicated, pagination-free plant-tasks route the tab loads from
 * (``GET /tasks/plants/{key}``). ``getList`` is re-read on every GET so a mutation
 * followed by a refetch observes the updated collection (#578). The Info-tab
 * watering badge still queries the paginated ``/tasks`` list endpoint; it is kept
 * satisfied with an empty result so it never leaks into the tab's assertions.
 */
function seedTasks(getList: () => TaskItem[]) {
  server.use(
    http.get('/api/v1/t/:tenant/tasks/plants/:plantKey', () => HttpResponse.json(getList())),
    http.get('/api/v1/t/:tenant/tasks', () => HttpResponse.json([])),
  );
}

describe('PlantInstanceDetailPage — Tasks tab (#578)', () => {
  beforeEach(async () => {
    await i18n.changeLanguage('de');
    currentKey = 'pi-1';
    setActiveTenantSlug('test-tenant');
  });

  const QUERY_TIMEOUT = { timeout: 5000 } as const;

  it('lists active and archived tasks returned by the entity filter', async () => {
    seedPlant(makePlant());
    seedTasks(() => [
      makeTask({ key: 'active-1', name: 'Water basil', status: 'pending' }),
      makeTask({ key: 'done-1', name: 'Old fertilize', status: 'completed', completed_at: '2024-06-05T00:00:00Z' }),
    ]);

    renderWithProviders(<PlantInstanceDetailPage />, { route: TASKS_ROUTE });

    // Populated state: both the active and the archived task surface.
    await screen.findByText('Water basil', {}, QUERY_TIMEOUT);
    await screen.findByText('Old fertilize', {}, QUERY_TIMEOUT);
    // The empty state must NOT be shown when tasks exist.
    expect(screen.queryByTestId('empty-state')).toBeNull();
  });

  it('shows the empty state with an instance-bound create action only on a real empty result', async () => {
    seedPlant(makePlant());
    seedTasks(() => []);

    renderWithProviders(<PlantInstanceDetailPage />, { route: TASKS_ROUTE });

    await screen.findByTestId('empty-state', {}, QUERY_TIMEOUT);
    // Instance-bound primary action (not just the global queue link).
    expect(
      screen.getByText(i18n.t('pages.plantInstances.noTasksCreateCta')),
    ).toBeTruthy();
    // The secondary global-queue link is still offered.
    expect(screen.getByTestId('empty-state-queue-link')).toBeTruthy();
  });

  it('refetches after a complete so the task moves to the archived section', async () => {
    seedPlant(makePlant());
    let completed = false;
    let completeCalled = false;
    seedTasks(() =>
      completed
        ? [makeTask({ key: 'active-1', name: 'Water basil', status: 'completed', completed_at: '2024-06-11T00:00:00Z' })]
        : [makeTask({ key: 'active-1', name: 'Water basil', status: 'pending' })],
    );
    server.use(
      http.post('/api/v1/t/:tenant/tasks/:key/complete', () => {
        completed = true;
        completeCalled = true;
        return HttpResponse.json(
          makeTask({ key: 'active-1', name: 'Water basil', status: 'completed', completed_at: '2024-06-11T00:00:00Z' }),
        );
      }),
    );

    renderWithProviders(<PlantInstanceDetailPage />, { route: TASKS_ROUTE });

    const completeBtn = await screen.findByTestId('task-complete-active-1', {}, QUERY_TIMEOUT);
    fireEvent.click(completeBtn);

    // The complete endpoint was hit, and after the refetch the row leaves the
    // active section (its actions disappear) and the done-summary reflects it.
    await waitFor(() => expect(completeCalled).toBe(true), QUERY_TIMEOUT);
    await waitFor(
      () => expect(screen.queryByTestId('task-complete-active-1')).toBeNull(),
      QUERY_TIMEOUT,
    );
    await screen.findByText(
      `${i18n.t('pages.plantInstances.taskTabSummaryDone')}: 1`,
      {},
      QUERY_TIMEOUT,
    );
  });

  it('starts a pending task via the start action and refetches', async () => {
    seedPlant(makePlant());
    let started = false;
    let startCalled = false;
    seedTasks(() =>
      started
        ? [makeTask({ key: 'active-1', name: 'Water basil', status: 'in_progress', started_at: '2024-06-11T00:00:00Z' })]
        : [makeTask({ key: 'active-1', name: 'Water basil', status: 'pending' })],
    );
    server.use(
      http.post('/api/v1/t/:tenant/tasks/:key/start', () => {
        started = true;
        startCalled = true;
        return HttpResponse.json(
          makeTask({ key: 'active-1', name: 'Water basil', status: 'in_progress', started_at: '2024-06-11T00:00:00Z' }),
        );
      }),
    );

    renderWithProviders(<PlantInstanceDetailPage />, { route: TASKS_ROUTE });

    const startBtn = await screen.findByTestId('task-start-active-1', {}, QUERY_TIMEOUT);
    fireEvent.click(startBtn);

    await waitFor(() => expect(startCalled).toBe(true), QUERY_TIMEOUT);
    // An in_progress task is still active (complete/skip remain) but no longer
    // pending, so the start action is gone after the refetch.
    await waitFor(
      () => expect(screen.queryByTestId('task-start-active-1')).toBeNull(),
      QUERY_TIMEOUT,
    );
    expect(screen.getByTestId('task-complete-active-1')).toBeTruthy();
    expect(screen.getByTestId('task-skip-active-1')).toBeTruthy();
  });

  it('skips a task via the skip action and refetches into the archived section', async () => {
    seedPlant(makePlant());
    let skipped = false;
    let skipCalled = false;
    seedTasks(() =>
      skipped
        ? [makeTask({ key: 'active-1', name: 'Water basil', status: 'skipped' })]
        : [makeTask({ key: 'active-1', name: 'Water basil', status: 'pending' })],
    );
    server.use(
      http.post('/api/v1/t/:tenant/tasks/:key/skip', () => {
        skipped = true;
        skipCalled = true;
        return HttpResponse.json(makeTask({ key: 'active-1', name: 'Water basil', status: 'skipped' }));
      }),
    );

    renderWithProviders(<PlantInstanceDetailPage />, { route: TASKS_ROUTE });

    const skipBtn = await screen.findByTestId('task-skip-active-1', {}, QUERY_TIMEOUT);
    fireEvent.click(skipBtn);

    await waitFor(() => expect(skipCalled).toBe(true), QUERY_TIMEOUT);
    // A skipped task is archived → no actions at all on that row anymore.
    await waitFor(
      () => expect(screen.queryByTestId('task-skip-active-1')).toBeNull(),
      QUERY_TIMEOUT,
    );
    expect(screen.queryByTestId('task-complete-active-1')).toBeNull();
    expect(screen.queryByTestId('task-start-active-1')).toBeNull();
  });

  it('gates row actions by status: start only for pending, none for archived', async () => {
    seedPlant(makePlant());
    seedTasks(() => [
      makeTask({ key: 'pending-1', name: 'Pending task', status: 'pending' }),
      makeTask({ key: 'progress-1', name: 'Running task', status: 'in_progress' }),
      makeTask({ key: 'done-1', name: 'Done task', status: 'completed', completed_at: '2024-06-05T00:00:00Z' }),
    ]);

    renderWithProviders(<PlantInstanceDetailPage />, { route: TASKS_ROUTE });

    // Pending: full trio.
    await screen.findByTestId('task-start-pending-1', {}, QUERY_TIMEOUT);
    expect(screen.getByTestId('task-complete-pending-1')).toBeTruthy();
    expect(screen.getByTestId('task-skip-pending-1')).toBeTruthy();
    // In progress: complete + skip, but NO start.
    expect(screen.getByTestId('task-complete-progress-1')).toBeTruthy();
    expect(screen.getByTestId('task-skip-progress-1')).toBeTruthy();
    expect(screen.queryByTestId('task-start-progress-1')).toBeNull();
    // Archived (completed): no actions at all.
    expect(screen.queryByTestId('task-start-done-1')).toBeNull();
    expect(screen.queryByTestId('task-complete-done-1')).toBeNull();
    expect(screen.queryByTestId('task-skip-done-1')).toBeNull();
  });

  it('exposes the summary bar and its chips under stable test ids (TC-004-092)', async () => {
    // The Overdue/Active/Done counts are an asserted outcome of the E2E
    // cross-view journey, which addresses them by these ids — the labels are
    // translated and the MUI class names framework-generated, so neither is an
    // addressable hook. Pinning them here keeps the E2E page object from
    // breaking silently.
    seedPlant(makePlant());
    seedTasks(() => [
      makeTask({ key: 'overdue-1', name: 'Overdue task', status: 'pending', due_date: '2000-01-01' }),
      // Due far ahead, so exactly one of the two active tasks counts as overdue.
      makeTask({ key: 'active-1', name: 'Water basil', status: 'pending', due_date: '2999-01-01' }),
      makeTask({ key: 'done-1', name: 'Old fertilize', status: 'completed', completed_at: '2024-06-05T00:00:00Z' }),
    ]);

    renderWithProviders(<PlantInstanceDetailPage />, { route: TASKS_ROUTE });

    await screen.findByTestId('task-summary-bar', {}, QUERY_TIMEOUT);
    // Trailing count per chip — exactly what the E2E page object parses off it.
    expect(screen.getByTestId('task-summary-overdue').textContent).toContain(
      `${i18n.t('pages.plantInstances.taskTabSummaryOverdue')}: 1`,
    );
    expect(screen.getByTestId('task-summary-active').textContent).toContain(
      `${i18n.t('pages.plantInstances.taskTabSummaryActive')}: 2`,
    );
    expect(screen.getByTestId('task-summary-done').textContent).toContain(
      `${i18n.t('pages.plantInstances.taskTabSummaryDone')}: 1`,
    );
  });

  it('omits the overdue chip while nothing is overdue (TC-004-092)', async () => {
    // The E2E page object reads a missing overdue chip as 0; that contract only
    // holds because the frontend renders the chip solely when a task is overdue.
    seedPlant(makePlant());
    seedTasks(() => [
      makeTask({ key: 'active-1', name: 'Water basil', status: 'pending', due_date: '2999-01-01' }),
    ]);

    renderWithProviders(<PlantInstanceDetailPage />, { route: TASKS_ROUTE });

    await screen.findByTestId('task-summary-bar', {}, QUERY_TIMEOUT);
    expect(screen.queryByTestId('task-summary-overdue')).toBeNull();
    expect(screen.getByTestId('task-summary-active').textContent).toContain(
      `${i18n.t('pages.plantInstances.taskTabSummaryActive')}: 1`,
    );
  });

  it('shows an error state with retry when the task load fails', async () => {
    seedPlant(makePlant());
    let attempt = 0;
    server.use(
      // The Info-tab badge query still succeeds; only the tab's dedicated
      // plant-tasks load fails. Any failure must surface the error state, never
      // the silent empty state (#578).
      http.get('/api/v1/t/:tenant/tasks', () => HttpResponse.json([])),
      http.get('/api/v1/t/:tenant/tasks/plants/:plantKey', () => {
        attempt += 1;
        return HttpResponse.json({ error_code: 'INTERNAL_ERROR', message: 'boom' }, { status: 500 });
      }),
    );

    renderWithProviders(<PlantInstanceDetailPage />, { route: TASKS_ROUTE });

    await screen.findByTestId('error-display', {}, QUERY_TIMEOUT);
    expect(screen.queryByTestId('empty-state')).toBeNull();
    expect(attempt).toBeGreaterThan(0);
  });

  it('marks the active and the done task section with a stable hook', async () => {
    seedPlant(makePlant());
    seedTasks(() => [
      makeTask({ key: 'active-1', name: 'Water basil', status: 'pending' }),
      makeTask({ key: 'done-1', name: 'Old fertilize', status: 'completed', completed_at: '2024-06-05T00:00:00Z' }),
    ]);

    renderWithProviders(<PlantInstanceDetailPage />, { route: TASKS_ROUTE });

    // Both sections were testid-less <Box>es, so a page object had to walk an
    // XPath over the translated heading to tell "active" from "done".
    const active = await screen.findByTestId('plant-tasks-active-section', {}, QUERY_TIMEOUT);
    const done = screen.getByTestId('plant-tasks-done-section');
    expect(within(active).getByText('Water basil')).toBeInTheDocument();
    expect(within(active).queryByText('Old fertilize')).toBeNull();
    expect(within(done).getByText('Old fertilize')).toBeInTheDocument();
    // The tables themselves are discriminable too — including in the card
    // layout, where they render no <table> to hang an aria-label on.
    expect(
      within(active).getByTestId('data-table').getAttribute('data-table-section'),
    ).toBe('plant-tasks-active');
    expect(
      within(done).getByTestId('data-table').getAttribute('data-table-section'),
    ).toBe('plant-tasks-done');
  });

  it('surfaces the error state (not the empty state) on a 422 validation failure (#614)', async () => {
    // Guards the #614 root cause: the tab formerly issued ``listTasks(0, 500, …)``,
    // which 422'd against the shared ``limit<=200`` cap and was masked as "no tasks".
    // A 422 from the load path must now surface a diagnosable, retryable error.
    seedPlant(makePlant());
    server.use(
      http.get('/api/v1/t/:tenant/tasks', () => HttpResponse.json([])),
      http.get('/api/v1/t/:tenant/tasks/plants/:plantKey', () =>
        HttpResponse.json(
          { detail: [{ loc: ['query', 'limit'], msg: 'ensure this value is less than or equal to 200' }] },
          { status: 422 },
        ),
      ),
    );

    renderWithProviders(<PlantInstanceDetailPage />, { route: TASKS_ROUTE });

    await screen.findByTestId('error-display', {}, QUERY_TIMEOUT);
    expect(screen.queryByTestId('empty-state')).toBeNull();
    expect(screen.getByTestId('error-retry-button')).toBeTruthy();
  });
});
