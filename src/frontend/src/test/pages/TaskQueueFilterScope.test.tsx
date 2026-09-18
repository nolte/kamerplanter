/**
 * The task queue's category and origin filters are server-side scopes (#1503).
 *
 * The same shape #1484 closed for the plant filter, on the two filters the
 * endpoint did not yet accept: `GET /tasks/queue` answers at most
 * `TaskService.QUEUE_LIMIT` rows and `GET /tasks` at most the 100 the completed
 * list asks for, so narrowing either answer in the page could only ever see what
 * the cap had already let through. A task matching the selected category — but
 * sorting past the cut — was simply not in the payload, and the page reported
 * "no tasks for this filter" for a filter that has matches.
 *
 * The handlers below model **both** server branches: they read `category` and
 * the repeatable `origin` off the query and narrow *before* they cap. A page
 * that filtered its own answer therefore cannot pass here.
 */
import { cleanup, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { http, HttpResponse } from 'msw';
import i18n from 'i18next';
import { renderWithProviders } from '../helpers';
import { server } from '../mocks/server';
import type { TaskItem } from '@/api/types';
import { MACHINE_TASK_ORIGINS } from '@/api/types';

vi.mock('react-router-dom', async (orig) => {
  const actual = await orig<typeof import('react-router-dom')>();
  return { ...actual, useNavigate: () => vi.fn() };
});

import TaskQueuePage from '@/pages/aufgaben/TaskQueuePage';

const TASKS = '/api/v1/t/:tenant/tasks';
const CARE = '/api/v1/t/:tenant/care-reminders';
const PLANTS = '/api/v1/t/:tenant/plant-instances';

/**
 * The row count the handlers cap their answer at.
 *
 * The real server caps the queue at 200 (`TaskService.QUEUE_LIMIT`) and the
 * completed list at the 100 the page requests. What is under test is that the
 * page asks the *server*, and the page holds no copy of either number — so the
 * property is "the answer is capped and the match sorts past the cut", which any
 * cap exhibits. It is modelled small because each modelled row is a rendered
 * task card: ~17 ms each, measured, and a 200-row fixture is what drove the
 * sibling file's case past the 30 s test timeout under suite load (#1526).
 */
const CAP = 12;

const TARGET_NAME = 'Umtopfen der Feige';

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

/** `CAP` ordinary maintenance tasks, then the one the filters are meant to find. */
function rowsWithTargetPastTheCap(target: Partial<TaskItem>): TaskItem[] {
  const fillers = Array.from({ length: CAP }, (_, i) =>
    makeTask({ key: `filler-${i}`, name: `Filler ${i}`, name_de: `Füller ${i}` }),
  );
  return [...fillers, makeTask({ key: 'target', name: TARGET_NAME, name_de: TARGET_NAME, ...target })];
}

/** Every `(category, origins)` pair the page sent to `GET /tasks/queue`. */
let queueQueries: { category: string | null; origins: string[] }[] = [];
/** The same for `GET /tasks`, the completed list. */
let completedQueries: { category: string | null; origins: string[] }[] = [];

function narrow(rows: TaskItem[], url: URL): TaskItem[] {
  const category = url.searchParams.get('category');
  const origins = url.searchParams.getAll('origin');
  return rows.filter(
    (t) => (!category || t.category === category) && (!origins.length || origins.includes(t.origin)),
  );
}

function seed(queueRows: TaskItem[], completedRows: TaskItem[] = []) {
  queueQueries = [];
  completedQueries = [];
  server.use(
    http.get(`${TASKS}/queue`, ({ request }) => {
      const url = new URL(request.url);
      queueQueries.push({
        category: url.searchParams.get('category'),
        origins: url.searchParams.getAll('origin'),
      });
      // Narrow first, cap second — the order the server works in, and the whole
      // point: the page cannot recover a row the cap dropped.
      return HttpResponse.json(narrow(queueRows, url).slice(0, CAP));
    }),
    http.get(`${TASKS}/overdue`, () => HttpResponse.json([])),
    http.get(`${CARE}/dashboard`, () => HttpResponse.json([])),
    http.get(PLANTS, () => HttpResponse.json([])),
    http.get(TASKS, ({ request }) => {
      const url = new URL(request.url);
      completedQueries.push({
        category: url.searchParams.get('category'),
        origins: url.searchParams.getAll('origin'),
      });
      return HttpResponse.json(narrow(completedRows, url).slice(0, CAP));
    }),
  );
}

/** Pick a category in the queue's category select by its enum key. */
async function selectCategory(category: string) {
  await userEvent.click(within(screen.getByTestId('filter-category')).getByRole('combobox'));
  await userEvent.click(
    await screen.findByRole('option', { name: i18n.t(`enums.taskCategory.${category}`) }),
  );
}

describe('TaskQueuePage — category and origin are server-side scopes (#1503)', () => {
  beforeEach(() => {
    i18n.changeLanguage('de');
  });
  afterEach(cleanup);

  describe('the category filter', () => {
    it('reaches a task the cap had dropped', async () => {
      seed(rowsWithTargetPastTheCap({ category: 'ipm' }));
      renderWithProviders(<TaskQueuePage />, { route: '/aufgaben/queue' });

      // The premise: unfiltered, the target is genuinely absent from the answer.
      await screen.findByText('Füller 0');
      expect(screen.queryByText(TARGET_NAME)).not.toBeInTheDocument();

      await selectCategory('ipm');

      expect(await screen.findByText(TARGET_NAME)).toBeInTheDocument();
      expect(screen.queryByText('Füller 0')).not.toBeInTheDocument();
    });

    it('asks for it in the query rather than narrowing the answer', async () => {
      seed(rowsWithTargetPastTheCap({ category: 'ipm' }));
      renderWithProviders(<TaskQueuePage />, { route: '/aufgaben/queue' });
      await screen.findByText('Füller 0');

      await selectCategory('ipm');

      await waitFor(() => expect(queueQueries.map((q) => q.category)).toContain('ipm'));
    });

    it('drops the parameter again when the selection returns to "all"', async () => {
      seed(rowsWithTargetPastTheCap({ category: 'ipm' }));
      renderWithProviders(<TaskQueuePage />, { route: '/aufgaben/queue' });
      await screen.findByText('Füller 0');

      await selectCategory('ipm');
      await screen.findByText(TARGET_NAME);
      // The first option of the select is "all".
      await userEvent.click(within(screen.getByTestId('filter-category')).getByRole('combobox'));
      await userEvent.click(await screen.findByRole('option', { name: i18n.t('common.all') }));

      expect(await screen.findByText('Füller 0')).toBeInTheDocument();
      await waitFor(() => expect(queueQueries[queueQueries.length - 1].category).toBeNull());
    });
  });

  describe('the origin filter', () => {
    it('reaches a machine task the cap had dropped', async () => {
      seed(rowsWithTargetPastTheCap({ origin: 'pipeline', source: 'goose/leaf-analysis' }));
      renderWithProviders(<TaskQueuePage />, { route: '/aufgaben/queue' });
      await screen.findByText('Füller 0');
      expect(screen.queryByText(TARGET_NAME)).not.toBeInTheDocument();

      await userEvent.click(screen.getByTestId('filter-origin-machine'));

      expect(await screen.findByText(TARGET_NAME)).toBeInTheDocument();
      // One request for the whole partition, not one per origin.
      await waitFor(() =>
        expect(queueQueries.map((q) => q.origins)).toContainEqual([...MACHINE_TASK_ORIGINS]),
      );
    });
  });

  describe('the two compose', () => {
    it('a category and an origin are one query, not two narrowings', async () => {
      const rows = rowsWithTargetPastTheCap({ category: 'ipm', origin: 'system' });
      // A decoy that each filter alone would keep, and only their conjunction drops.
      rows.splice(0, 0, makeTask({ key: 'decoy', name: 'Decoy', name_de: 'Köder', category: 'ipm' }));
      seed(rows);
      renderWithProviders(<TaskQueuePage />, { route: '/aufgaben/queue' });
      await screen.findByText('Füller 0');

      await selectCategory('ipm');
      await screen.findByText('Köder');
      await userEvent.click(screen.getByTestId('filter-origin-machine'));

      expect(await screen.findByText(TARGET_NAME)).toBeInTheDocument();
      await waitFor(() => expect(screen.queryByText('Köder')).not.toBeInTheDocument());
      expect(queueQueries[queueQueries.length - 1]).toEqual({
        category: 'ipm',
        origins: [...MACHINE_TASK_ORIGINS],
      });
    });
  });

  describe('the completed list', () => {
    it('carries the same scope into its own query', async () => {
      const completed = [
        ...Array.from({ length: CAP }, (_, i) =>
          makeTask({ key: `done-${i}`, name: `Erledigt ${i}`, name_de: `Erledigt ${i}`, status: 'completed' }),
        ),
        makeTask({
          key: 'done-target',
          name: TARGET_NAME,
          name_de: TARGET_NAME,
          status: 'completed',
          category: 'ipm',
        }),
      ];
      seed(rowsWithTargetPastTheCap({ category: 'ipm' }), completed);
      renderWithProviders(<TaskQueuePage />, { route: '/aufgaben/queue' });
      await screen.findByText('Füller 0');

      await userEvent.click(within(screen.getByTestId('show-completed-toggle')).getByRole('switch'));
      await screen.findByText('Erledigt 0');
      await selectCategory('ipm');

      await waitFor(() => expect(completedQueries.map((q) => q.category)).toContain('ipm'));
      // The completed row past the cap is on the page — which is only possible
      // because the *query* carried the category.
      expect(await screen.findAllByText(TARGET_NAME)).not.toHaveLength(0);
    });
  });
});
