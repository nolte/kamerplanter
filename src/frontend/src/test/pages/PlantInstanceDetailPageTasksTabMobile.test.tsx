import { cleanup, screen, within } from '@testing-library/react';
import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { http, HttpResponse } from 'msw';
import i18n from 'i18next';
import type { PlantInstance, TaskItem } from '@/api/types';
import { setActiveTenantSlug } from '@/api/client';
import { renderWithProviders } from '../helpers';
import { server } from '../mocks/server';

// Force the mobile breakpoint so the task tables render their MobileCards.
vi.mock('@mui/material/useMediaQuery', () => ({ default: () => true }));

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual<typeof import('react-router-dom')>('react-router-dom');
  return { ...actual, useParams: () => ({ key: 'pi-1' }) };
});

// Stub the interactive dialogs the page mounts; none matter for the card hooks.
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

// Import after the mocks so they are picked up.
import PlantInstanceDetailPage from '@/pages/pflanzen/PlantInstanceDetailPage';

const TASKS_ROUTE = '/pflanzen/plant-instances/pi-1#tasks';
const QUERY_TIMEOUT = { timeout: 5000 } as const;

const plant = {
  key: 'pi-1',
  instance_id: 'BASIL-0001',
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
} as unknown as PlantInstance;

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
  } as TaskItem;
}

function seed(tasks: TaskItem[]) {
  server.use(
    http.get('/api/v1/t/:tenant/plant-instances/:key', () => HttpResponse.json(plant)),
    http.get('/api/v1/plant-instances/:key', () => HttpResponse.json(plant)),
    http.get('/api/v1/t/:tenant/tasks/plants/:plantKey', () => HttpResponse.json(tasks)),
    http.get('/api/v1/t/:tenant/tasks', () => HttpResponse.json([])),
  );
}

describe('PlantInstanceDetailPage — task cards at mobile width', () => {
  beforeEach(async () => {
    await i18n.changeLanguage('de');
    setActiveTenantSlug('test-tenant');
  });

  afterEach(() => {
    cleanup();
  });

  it('keys the status/category chips and the priority field of a task card', async () => {
    seed([makeTask({ key: 'active-1', name: 'Water basil', status: 'pending', priority: 'high' })]);

    renderWithProviders(<PlantInstanceDetailPage />, { route: TASKS_ROUTE });

    const section = await screen.findByTestId('plant-tasks-active-section', {}, QUERY_TIMEOUT);
    const card = within(section).getAllByTestId('data-table-row')[0];

    // Below the breakpoint there is no <td data-testid="cell-status"> to read;
    // the page object could previously only get to these values via chip order.
    expect(within(card).getByTestId('card-title').textContent).toBe('Water basil');
    expect(within(card).getByTestId('card-chip-status').textContent).toBe(
      i18n.t('enums.taskStatus.pending'),
    );
    expect(within(card).getByTestId('card-chip-category').textContent).toBe(
      i18n.t('enums.taskCategory.care_reminder'),
    );
    expect(within(card).getByTestId('card-field-priority').textContent).toBe(
      i18n.t('enums.taskPriority.high'),
    );
  });

  it('keys the status chip of an archived task card as well', async () => {
    seed([
      makeTask({
        key: 'done-1',
        name: 'Old fertilize',
        status: 'completed',
        completed_at: '2024-06-05T00:00:00Z',
      }),
    ]);

    renderWithProviders(<PlantInstanceDetailPage />, { route: TASKS_ROUTE });

    const section = await screen.findByTestId('plant-tasks-done-section', {}, QUERY_TIMEOUT);
    const card = within(section).getAllByTestId('data-table-row')[0];

    expect(within(card).getByTestId('card-chip-status').textContent).toBe(
      i18n.t('enums.taskStatus.completed'),
    );
  });
});
