import { cleanup, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { http, HttpResponse } from 'msw';
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
