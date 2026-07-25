import { cleanup, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { http, HttpResponse, delay } from 'msw';
import i18n from 'i18next';
import { renderWithProviders } from '../helpers';
import { server } from '../mocks/server';
import type { TaskItem } from '@/api/types';

const mockNavigate = vi.fn();
vi.mock('react-router-dom', async (orig) => {
  const actual = await orig<typeof import('react-router-dom')>();
  return { ...actual, useNavigate: () => mockNavigate };
});

import TaskQueuePage from '@/pages/aufgaben/TaskQueuePage';

const TASKS = '/api/v1/t/:tenant/tasks';
const CARE = '/api/v1/t/:tenant/care-reminders';

function makeTask(overrides: Partial<TaskItem> = {}): TaskItem {
  return {
    key: 'task-active',
    name: 'Water tomato',
    name_de: 'Tomate giessen',
    instruction: '',
    instruction_de: '',
    category: 'maintenance',
    entity_key: null,
    entity_type: null,
    due_date: null,
    scheduled_time: null,
    status: 'pending',
    priority: 'medium',
    skill_level: 'beginner',
    stress_level: 'none',
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
    created_at: '2024-01-01T00:00:00Z',
    updated_at: null,
    ...overrides,
  };
}

const activeTask = makeTask({ key: 'task-active', name: 'Water tomato', name_de: 'Tomate giessen' });
const completedTask = makeTask({
  key: 'task-done',
  name: 'Prune basil',
  name_de: 'Basilikum beschneiden',
  status: 'completed',
  completed_at: '2024-02-01T10:00:00Z',
});

let listTasksCalls: number;

function seedHandlers() {
  listTasksCalls = 0;
  server.use(
    http.get(`${TASKS}/queue`, () => HttpResponse.json([activeTask])),
    http.get(`${TASKS}/overdue`, () => HttpResponse.json([])),
    http.get(`${CARE}/dashboard`, () => HttpResponse.json([])),
    http.get(TASKS, ({ request }) => {
      listTasksCalls += 1;
      const url = new URL(request.url);
      if (url.searchParams.get('status') === 'completed') {
        return HttpResponse.json([completedTask]);
      }
      return HttpResponse.json([]);
    }),
  );
}

describe('TaskQueuePage — completed-tasks toggle (#606)', () => {
  beforeEach(() => {
    seedHandlers();
    i18n.changeLanguage('de');
  });

  afterEach(() => {
    cleanup();
    mockNavigate.mockReset();
  });

  it('renders active tasks without the completed section by default', async () => {
    renderWithProviders(<TaskQueuePage />, { route: '/aufgaben/queue' });

    expect(await screen.findByText('Tomate giessen')).toBeInTheDocument();
    expect(screen.queryByTestId('task-section-completed')).not.toBeInTheDocument();
    expect(listTasksCalls).toBe(0);
  });

  it('reveals completed tasks when the toggle is switched on', async () => {
    renderWithProviders(<TaskQueuePage />, { route: '/aufgaben/queue' });

    await screen.findByText('Tomate giessen');

    const toggle = screen.getByTestId('show-completed-toggle');
    await userEvent.click(toggle);

    const section = await screen.findByTestId('task-section-completed');
    expect(within(section).getByText('Basilikum beschneiden')).toBeInTheDocument();
    await waitFor(() => expect(listTasksCalls).toBeGreaterThan(0));
  });
});

describe('TaskQueuePage — task card navigation target', () => {
  const plantTask = makeTask({
    key: 'task-active',
    entity_type: 'plant_instance',
    entity_key: 'plant-1',
  });

  beforeEach(() => {
    listTasksCalls = 0;
    server.use(
      http.get(`${TASKS}/queue`, () => HttpResponse.json([plantTask])),
      http.get(`${TASKS}/overdue`, () => HttpResponse.json([])),
      http.get(`${CARE}/dashboard`, () => HttpResponse.json([])),
      http.get(TASKS, () => HttpResponse.json([])),
    );
    i18n.changeLanguage('de');
  });

  afterEach(() => {
    cleanup();
    mockNavigate.mockReset();
  });

  it('keeps the plant link outside the card action area', async () => {
    renderWithProviders(<TaskQueuePage />, { route: '/aufgaben/queue' });

    const plantLink = await screen.findByTestId('plant-link-task-active');
    const actionArea = screen.getByTestId('task-card-task-active');

    // Interactive nesting is what made the card's tap target ambiguous: with the
    // link inside the action area, the geometric centre of a reflowed mobile
    // card landed on the link and opened the plant instead of the task.
    expect(actionArea.contains(plantLink)).toBe(false);
    expect(within(actionArea).queryByRole('link')).toBeNull();
    expect(plantLink).toHaveAttribute('href', '/pflanzen/plant-instances/plant-1');
  });

  it('navigates to the task detail when the card itself is activated', async () => {
    renderWithProviders(<TaskQueuePage />, { route: '/aufgaben/queue' });

    await screen.findByTestId('plant-link-task-active');
    await userEvent.click(screen.getByTestId('task-card-task-active'));

    expect(mockNavigate).toHaveBeenCalledWith('/aufgaben/tasks/task-active');
  });
});

describe('TaskQueuePage — loading gate covers the plant list', () => {
  const plantTask = makeTask({
    key: 'task-active',
    entity_type: 'plant_instance',
    entity_key: 'plant-1',
  });

  beforeEach(() => {
    listTasksCalls = 0;
    server.use(
      http.get(`${TASKS}/queue`, () => HttpResponse.json([plantTask])),
      http.get(`${TASKS}/overdue`, () => HttpResponse.json([])),
      http.get(`${CARE}/dashboard`, () => HttpResponse.json([])),
      http.get(TASKS, () => HttpResponse.json([])),
      // The plant list is the slowest of the four mount requests — exactly the
      // situation the production defect needed to surface.
      http.get('/api/v1/t/:tenant/plant-instances', async () => {
        await delay(500);
        return HttpResponse.json([
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
        ]);
      }),
    );
    i18n.changeLanguage('de');
  });

  afterEach(() => {
    cleanup();
    mockNavigate.mockReset();
  });

  it('keeps the skeleton up until the plant names have arrived', async () => {
    const { store } = renderWithProviders(<TaskQueuePage />, { route: '/aufgaben/queue' });

    // Tasks and care reminders have settled …
    await waitFor(() => {
      expect(store.getState().tasks.loading).toBe(false);
      expect(store.getState().careReminders.loading).toBe(false);
    });

    // … but the plant list has not, and it decides whether a card renders its
    // plant-shortcut row. Clearing the indicator here used to paint the cards
    // and then reflow them, so taps aimed at a card's action row landed on the
    // container that had moved into place.
    expect(screen.getByTestId('loading-skeleton')).toBeInTheDocument();
    expect(screen.queryByTestId('task-card-task-active')).toBeNull();
  });

  it('paints the plant shortcut with the very first card render', async () => {
    renderWithProviders(<TaskQueuePage />, { route: '/aufgaben/queue' });

    // The moment the card exists the shortcut must exist too — no late row.
    await screen.findByTestId('task-card-task-active', {}, { timeout: 5000 });
    expect(screen.getByTestId('plant-link-task-active')).toBeInTheDocument();
  });
});

describe('TaskQueuePage — card action touch targets', () => {
  const careEntry = {
    plant_key: 'plant-1',
    plant_name: 'Big Red',
    species_name: null,
    reminder_type: 'watering',
    urgency: 'overdue',
    due_date: '2024-01-01',
    care_profile_key: 'cp-1',
    task_key: null,
  };

  beforeEach(() => {
    listTasksCalls = 0;
    server.use(
      http.get(`${TASKS}/queue`, () => HttpResponse.json([activeTask])),
      http.get(`${TASKS}/overdue`, () => HttpResponse.json([])),
      http.get(`${CARE}/dashboard`, () => HttpResponse.json([careEntry])),
      http.get(TASKS, () => HttpResponse.json([])),
    );
    i18n.changeLanguage('de');
  });

  afterEach(() => {
    cleanup();
    mockNavigate.mockReset();
  });

  it('gives every card action a 48x48 touch target', async () => {
    renderWithProviders(<TaskQueuePage />, { route: '/aufgaben/queue' });

    await screen.findByTestId('start-task-task-active');
    // 40px targets flush against a large card link is mis-tap geometry;
    // UI-NFR-001 R-011 requires 48x48 for every interactive element.
    for (const testId of [
      'start-task-task-active',
      'complete-task-task-active',
      'skip-task-task-active',
      'care-edit-profile-care-plant-1-watering',
      'care-confirm-care-plant-1-watering',
      'care-snooze-care-plant-1-watering',
    ]) {
      const style = window.getComputedStyle(screen.getByTestId(testId));
      expect(`${testId}:${style.minWidth}`).toBe(`${testId}:48px`);
      expect(`${testId}:${style.minHeight}`).toBe(`${testId}:48px`);
    }
  });
});
