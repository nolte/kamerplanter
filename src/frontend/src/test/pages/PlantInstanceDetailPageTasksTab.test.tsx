import { screen, waitFor, fireEvent } from '@testing-library/react';
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
 * Seed the tenant-scoped task list. ``getList`` is re-read on every GET so a
 * mutation followed by a refetch observes the updated collection (#578).
 */
function seedTasks(getList: () => TaskItem[]) {
  server.use(
    http.get('/api/v1/t/:tenant/tasks', () => HttpResponse.json(getList())),
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

  it('refetches after a quick-complete so the task moves to the archived section', async () => {
    seedPlant(makePlant());
    let completed = false;
    seedTasks(() =>
      completed
        ? [makeTask({ key: 'active-1', name: 'Water basil', status: 'completed', completed_at: '2024-06-11T00:00:00Z' })]
        : [makeTask({ key: 'active-1', name: 'Water basil', status: 'pending' })],
    );
    server.use(
      http.post('/api/v1/t/:tenant/tasks/:key/complete', () => {
        completed = true;
        return HttpResponse.json(
          makeTask({ key: 'active-1', name: 'Water basil', status: 'completed', completed_at: '2024-06-11T00:00:00Z' }),
        );
      }),
    );

    renderWithProviders(<PlantInstanceDetailPage />, { route: TASKS_ROUTE });

    const completeBtn = await screen.findByTestId('quick-complete-active-1', {}, QUERY_TIMEOUT);
    fireEvent.click(completeBtn);

    // After the refetch the task is no longer pending: the quick-complete button
    // (only rendered for active tasks) disappears, and the done-summary reflects it.
    await waitFor(
      () => expect(screen.queryByTestId('quick-complete-active-1')).toBeNull(),
      QUERY_TIMEOUT,
    );
    await screen.findByText(
      `${i18n.t('pages.plantInstances.taskTabSummaryDone')}: 1`,
      {},
      QUERY_TIMEOUT,
    );
  });

  it('shows an error state with retry when the task load fails', async () => {
    seedPlant(makePlant());
    let attempt = 0;
    server.use(
      http.get('/api/v1/t/:tenant/tasks', () => {
        attempt += 1;
        // Fail the tab load (2nd GET: the 1st is the page's care-reminder badge
        // query in load()). Any failure must surface the error state, never the
        // silent empty state.
        return HttpResponse.json({ error_code: 'INTERNAL_ERROR', message: 'boom' }, { status: 500 });
      }),
    );

    renderWithProviders(<PlantInstanceDetailPage />, { route: TASKS_ROUTE });

    await screen.findByTestId('error-display', {}, QUERY_TIMEOUT);
    expect(screen.queryByTestId('empty-state')).toBeNull();
    expect(attempt).toBeGreaterThan(0);
  });
});
