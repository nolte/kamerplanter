import { cleanup, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { http, HttpResponse } from 'msw';
import i18n from 'i18next';
import { renderWithProviders } from '../helpers';
import { server } from '../mocks/server';
import type { TaskItem } from '@/api/types';

vi.mock('react-router-dom', async (orig) => {
  const actual = await orig<typeof import('react-router-dom')>();
  return { ...actual, useNavigate: () => vi.fn() };
});

import TaskQueuePage from '@/pages/aufgaben/TaskQueuePage';

const TASKS = '/api/v1/t/:tenant/tasks';
const CARE = '/api/v1/t/:tenant/care-reminders';

function makeTask(overrides: Partial<TaskItem> = {}): TaskItem {
  return {
    key: 'task-1',
    name: 'A task',
    name_de: 'Eine Aufgabe',
    instruction: '',
    instruction_de: '',
    category: 'maintenance',
    origin: 'user',
    source: '',
    source_run_ref: null,
    external_ref: null,
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

const userTask = makeTask({ key: 'user-task', name: 'Manual task', name_de: 'Manuelle Aufgabe' });
const machineTask = makeTask({
  key: 'machine-task',
  name: 'Pipeline finding',
  name_de: 'Pipeline-Befund',
  origin: 'pipeline',
  source: 'goose/leaf-analysis',
});

function seed() {
  server.use(
    http.get(`${TASKS}/queue`, () => HttpResponse.json([userTask, machineTask])),
    http.get(`${TASKS}/overdue`, () => HttpResponse.json([])),
    http.get(`${CARE}/dashboard`, () => HttpResponse.json([])),
    http.get(TASKS, () => HttpResponse.json([])),
  );
}

describe('TaskQueuePage — FreeStyle origin badge & filter (#1082)', () => {
  beforeEach(() => {
    seed();
    i18n.changeLanguage('de');
  });
  afterEach(cleanup);

  it('shows the machine-generated badge only on producer tasks', async () => {
    renderWithProviders(<TaskQueuePage />, { route: '/aufgaben/queue' });

    expect(await screen.findByText('Pipeline-Befund')).toBeInTheDocument();
    // The producer task carries the badge; the manual one does not.
    expect(screen.getByTestId('task-origin-badge-machine-task')).toBeInTheDocument();
    expect(screen.queryByTestId('task-origin-badge-user-task')).not.toBeInTheDocument();
  });

  it('filters to machine-generated tasks only', async () => {
    renderWithProviders(<TaskQueuePage />, { route: '/aufgaben/queue' });

    await screen.findByText('Pipeline-Befund');
    expect(screen.getByText('Manuelle Aufgabe')).toBeInTheDocument();

    await userEvent.click(screen.getByTestId('filter-origin-machine'));

    await waitFor(() => expect(screen.queryByText('Manuelle Aufgabe')).not.toBeInTheDocument());
    expect(screen.getByText('Pipeline-Befund')).toBeInTheDocument();
  });

  it('filters to manual tasks only', async () => {
    renderWithProviders(<TaskQueuePage />, { route: '/aufgaben/queue' });

    await screen.findByText('Manuelle Aufgabe');

    await userEvent.click(screen.getByTestId('filter-origin-user'));

    await waitFor(() => expect(screen.queryByText('Pipeline-Befund')).not.toBeInTheDocument());
    expect(screen.getByText('Manuelle Aufgabe')).toBeInTheDocument();
  });
});
