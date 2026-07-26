import { cleanup, screen } from '@testing-library/react';
import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { http, HttpResponse } from 'msw';
import i18n from 'i18next';
import { renderWithProviders } from '../helpers';
import { server } from '../mocks/server';
import type { TaskItem } from '@/api/types';

// Force the compact breakpoint (< sm). This is the 393px mobile profile, where
// three 48px action targets beside the card content left the task name ~50px of
// the content column.
vi.mock('@mui/material/useMediaQuery', () => ({ default: () => true }));

vi.mock('react-router-dom', async (orig) => {
  const actual = await orig<typeof import('react-router-dom')>();
  return { ...actual, useNavigate: () => vi.fn() };
});

// Import after the mocks so they are picked up.
import TaskQueuePage from '@/pages/aufgaben/TaskQueuePage';

const TASKS = '/api/v1/t/:tenant/tasks';
const CARE = '/api/v1/t/:tenant/care-reminders';

const plantTask = {
  key: 'task-active',
  name: 'Water tomato',
  name_de: 'Tomate giessen',
  instruction: '',
  instruction_de: '',
  category: 'maintenance',
  entity_key: 'plant-1',
  entity_type: 'plant_instance',
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
} as unknown as TaskItem;

describe('TaskQueuePage — compact card layout (UI-NFR-001 R-002/R-011/R-012)', () => {
  beforeEach(() => {
    server.use(
      http.get(`${TASKS}/queue`, () => HttpResponse.json([plantTask])),
      http.get(`${TASKS}/overdue`, () => HttpResponse.json([])),
      http.get(`${CARE}/dashboard`, () => HttpResponse.json([])),
      http.get(TASKS, () => HttpResponse.json([])),
      http.get('/api/v1/t/:tenant/plant-instances', () =>
        HttpResponse.json([
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
        ]),
      ),
    );
    i18n.changeLanguage('de');
  });

  afterEach(() => {
    cleanup();
  });

  it('moves the action row below the card content instead of beside it', async () => {
    renderWithProviders(<TaskQueuePage />, { route: '/aufgaben/queue' });

    const actionArea = await screen.findByTestId('task-card-task-active');
    // The column that holds the card's own action area. Beside it, the action
    // row is a sibling of this column; below it, a child.
    const contentColumn = actionArea.parentElement;
    if (contentColumn === null) throw new Error('card content column not rendered');

    for (const id of ['complete-task-task-active', 'skip-task-task-active', 'start-task-task-active']) {
      expect(contentColumn.contains(screen.getByTestId(id))).toBe(true);
    }
  });

  it('keeps every action target at the 48px touch minimum, separated by 8px', async () => {
    renderWithProviders(<TaskQueuePage />, { route: '/aufgaben/queue' });

    const complete = await screen.findByTestId('complete-task-task-active');
    const style = window.getComputedStyle(complete);
    expect(style.minWidth).toBe('48px');
    expect(style.minHeight).toBe('48px');

    // R-012 (SHOULD): 8px between neighbouring targets, not 4px.
    const row = complete.parentElement;
    if (row == null) throw new Error('action row not rendered');
    expect(window.getComputedStyle(row).gap).toBe('8px');
  });

  it('gives the plant shortcut a full-size touch target', async () => {
    renderWithProviders(<TaskQueuePage />, { route: '/aufgaben/queue' });

    const plantLink = await screen.findByTestId('plant-link-task-active');
    // UI-NFR-001 R-011 (MUST). It sits directly under the card's own action
    // area, so an undersized target here is the likeliest mis-tap on the page.
    expect(window.getComputedStyle(plantLink).minHeight).toBe('48px');
  });
});
