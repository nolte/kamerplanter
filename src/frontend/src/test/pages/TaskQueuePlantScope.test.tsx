/**
 * The task queue's plant filter is a server-side scope (#1484).
 *
 * `GET /tasks/queue` answers at most 200 rows (`TaskService.get_task_queue`
 * takes the `get_pending_tasks(0, 200)` branch when no `plant_key` is given;
 * with one it takes the unbounded `get_tasks_for_plant` branch). The page used
 * to ask without the parameter and narrow the answer afterwards, so a plant
 * whose tasks sat past the cut was reported as having no work at all.
 *
 * The MSW handlers below model exactly those two server branches, so a test
 * that passes here could not pass against a server that caps.
 */
import { cleanup, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { delay, http, HttpResponse } from 'msw';
import i18n from 'i18next';
import { renderWithProviders } from '../helpers';
import { server } from '../mocks/server';
import type { PlantInstance, TaskItem } from '@/api/types';

vi.mock('react-router-dom', async (orig) => {
  const actual = await orig<typeof import('react-router-dom')>();
  return { ...actual, useNavigate: () => vi.fn() };
});

import TaskQueuePage from '@/pages/aufgaben/TaskQueuePage';
import taskQueuePageSource from '@/pages/aufgaben/TaskQueuePage.tsx?raw';

const TASKS = '/api/v1/t/:tenant/tasks';
const CARE = '/api/v1/t/:tenant/care-reminders';
const PLANTS = '/api/v1/t/:tenant/plant-instances';

/** The cap the queue endpoint applies when it is asked without a plant scope. */
const QUEUE_CAP = 200;

const TARGET_PLANT_KEY = 'plant-beyond-the-cap';
const TARGET_TASK_NAME = 'Repot the fig';

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

function makePlant(key: string, name: string): PlantInstance {
  return {
    key,
    instance_id: key.toUpperCase(),
    species_key: 'species-1',
    cultivar_key: null,
    site_key: null,
    location_key: null,
    slot_key: null,
    substrate_batch_key: null,
    substrate_key: null,
    plant_name: name,
    planted_on: '2024-01-01',
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
    created_at: '2024-01-01T00:00:00Z',
    updated_at: null,
  };
}

/** 200 unrelated pending tasks plus one for the plant under test, in that order. */
const FILLER_TASKS: TaskItem[] = Array.from({ length: QUEUE_CAP }, (_, i) =>
  makeTask({
    key: `filler-${i}`,
    name: `Filler task ${i}`,
    name_de: `Fülleraufgabe ${i}`,
    entity_type: 'plant_instance',
    entity_key: `plant-filler-${i}`,
  }),
);
const TARGET_TASK = makeTask({
  key: 'target-task',
  name: TARGET_TASK_NAME,
  name_de: TARGET_TASK_NAME,
  entity_type: 'plant_instance',
  entity_key: TARGET_PLANT_KEY,
});
const ALL_QUEUE_TASKS = [...FILLER_TASKS, TARGET_TASK];

/** The same two branches, but cheap: only the cap test needs 201 rendered cards. */
const SMALL_QUEUE_TASKS = [FILLER_TASKS[0], TARGET_TASK];

const PLANTS_FIXTURE = [
  makePlant(TARGET_PLANT_KEY, 'Feige Gustav'),
  makePlant('plant-filler-0', 'Basilikum Bea'),
];

/** Every `plant_key` the page sent to `GET /tasks/queue`, in order. */
let queueScopes: (string | null)[] = [];
/** Every `entity_key` the page sent to `GET /tasks` (the completed list). */
let completedScopes: (string | null)[] = [];

function seed(queueTasks: TaskItem[] = SMALL_QUEUE_TASKS) {
  queueScopes = [];
  completedScopes = [];
  server.use(
    http.get(`${TASKS}/queue`, ({ request }) => {
      const plantKey = new URL(request.url).searchParams.get('plant_key');
      queueScopes.push(plantKey);
      if (plantKey) {
        // Server branch `get_tasks_for_plant` — scoped and uncapped.
        return HttpResponse.json(queueTasks.filter((t) => t.entity_key === plantKey));
      }
      // Server branch `get_pending_tasks(0, 200)` — unscoped and capped.
      return HttpResponse.json(queueTasks.slice(0, QUEUE_CAP));
    }),
    http.get(`${TASKS}/overdue`, () => HttpResponse.json([])),
    http.get(`${CARE}/dashboard`, () => HttpResponse.json([])),
    http.get(PLANTS, () => HttpResponse.json(PLANTS_FIXTURE)),
    http.get(TASKS, ({ request }) => {
      const url = new URL(request.url);
      completedScopes.push(url.searchParams.get('entity_key'));
      return HttpResponse.json([]);
    }),
  );
}

/** Pick a plant in the queue's plant filter by its displayed name. */
async function selectPlantFilter(name: string) {
  const input = within(screen.getByTestId('filter-plant')).getByRole('combobox');
  await userEvent.click(input);
  await userEvent.type(input, name.slice(0, 5));
  const option = await screen.findByRole('option', { name: new RegExp(name, 'i') });
  await userEvent.click(option);
}

describe('TaskQueuePage — the plant filter is a server-side scope (#1484)', () => {
  beforeEach(() => {
    seed();
    i18n.changeLanguage('de');
  });
  afterEach(cleanup);

  it('shows a plant whose task sits past the 200-row cap', async () => {
    seed(ALL_QUEUE_TASKS);
    renderWithProviders(<TaskQueuePage />, { route: '/aufgaben/queue' });

    // The unscoped answer is capped, so the target task is genuinely absent.
    await screen.findByText('Fülleraufgabe 0');
    expect(screen.queryByText(TARGET_TASK_NAME)).not.toBeInTheDocument();

    await selectPlantFilter('Feige Gustav');

    // Selecting the plant re-queries the server with the scope…
    await waitFor(() => expect(queueScopes).toContain(TARGET_PLANT_KEY));
    // …and the task the cap had hidden is on the page.
    expect(await screen.findByText(TARGET_TASK_NAME)).toBeInTheDocument();
    expect(screen.queryByText('Fülleraufgabe 0')).not.toBeInTheDocument();
  });

  it('renders the filtered empty state when the scoped query answers nothing', async () => {
    // Rows in the queue, but none for the selected plant.
    seed([FILLER_TASKS[0]]);
    renderWithProviders(<TaskQueuePage />, { route: '/aufgaben/queue' });
    await screen.findByText('Fülleraufgabe 0');

    await selectPlantFilter('Feige Gustav');

    await waitFor(() => expect(queueScopes).toContain(TARGET_PLANT_KEY));
    expect(
      await screen.findByText(i18n.t('pages.tasks.noTasksFiltered')),
    ).toBeInTheDocument();
  });

  it('keeps the filter bar mounted while the scoped query is in flight', async () => {
    // The page-wide skeleton is the first paint's gate. If it also covered the
    // refetch a filter change now triggers, the combobox the user just used
    // would be unmounted under their hands on every pick. A delayed answer holds
    // the page in the in-flight state long enough to read it.
    server.use(
      http.get(`${TASKS}/queue`, async ({ request }) => {
        const plantKey = new URL(request.url).searchParams.get('plant_key');
        queueScopes.push(plantKey);
        if (!plantKey) return HttpResponse.json(SMALL_QUEUE_TASKS.slice(0, QUEUE_CAP));
        await delay(500);
        return HttpResponse.json([TARGET_TASK]);
      }),
    );
    renderWithProviders(<TaskQueuePage />, { route: '/aufgaben/queue' });
    await screen.findByText('Fülleraufgabe 0');

    await selectPlantFilter('Feige Gustav');

    await waitFor(() => expect(queueScopes).toContain(TARGET_PLANT_KEY));
    expect(screen.getByTestId('task-queue-page')).toBeInTheDocument();
    expect(screen.queryByTestId('loading-skeleton')).not.toBeInTheDocument();
    expect(screen.getByTestId('filter-plant')).toBeInTheDocument();

    expect(await screen.findByText(TARGET_TASK_NAME)).toBeInTheDocument();
  });

  it('scopes the completed list through entity_type/entity_key, not through a client filter', async () => {
    renderWithProviders(<TaskQueuePage />, { route: '/aufgaben/queue' });
    await screen.findByText('Fülleraufgabe 0');

    await selectPlantFilter('Feige Gustav');
    await waitFor(() => expect(queueScopes).toContain(TARGET_PLANT_KEY));

    await userEvent.click(within(screen.getByTestId('show-completed-toggle')).getByRole('switch'));

    await waitFor(() => expect(completedScopes).toContain(TARGET_PLANT_KEY));
  });

  describe('every reload of the queue carries the active scope', () => {
    // The exhaustive proof is the single-call-site guard below; these are the
    // paths that can be driven through the UI without opening a dialog.
    const paths: { name: string; act: () => Promise<void> }[] = [
      {
        name: 'starting a task',
        act: async () => {
          await userEvent.click(await screen.findByTestId('start-task-target-task'));
        },
      },
      {
        name: 'completing a task',
        act: async () => {
          await userEvent.click(await screen.findByTestId('complete-task-target-task'));
        },
      },
      {
        name: 'skipping a task',
        act: async () => {
          await userEvent.click(await screen.findByTestId('skip-task-target-task'));
        },
      },
      {
        name: 'generating care reminders',
        act: async () => {
          await userEvent.click(await screen.findByTestId('generate-reminders-button'));
        },
      },
    ];

    it.each(paths)('after $name', async ({ act }) => {
      server.use(
        http.post(`${TASKS}/:key/start`, () => HttpResponse.json(TARGET_TASK)),
        http.post(`${TASKS}/:key/complete`, () => HttpResponse.json(TARGET_TASK)),
        http.post(`${TASKS}/:key/skip`, () => HttpResponse.json(TARGET_TASK)),
        http.post(`${TASKS}/generate-care-reminders`, () =>
          HttpResponse.json({ created: 0, skipped: 0 }),
        ),
      );
      renderWithProviders(<TaskQueuePage />, { route: '/aufgaben/queue' });
      await screen.findByText('Fülleraufgabe 0');

      await selectPlantFilter('Feige Gustav');
      await waitFor(() => expect(queueScopes).toContain(TARGET_PLANT_KEY));
      await screen.findByText(TARGET_TASK_NAME);
      const before = queueScopes.length;

      await act();

      await waitFor(() => expect(queueScopes.length).toBeGreaterThan(before));
      // Not one of the reloads after the action dropped the scope.
      expect(queueScopes.slice(before)).not.toContain(null);
    });
  });

  it('issues queue and completed reloads from exactly one call site each', () => {
    // The class this closes is "a reload that forgets the scope". Counting the
    // *identifier* rather than a call spelling is what makes the guard hold: a
    // tenth `dispatch(fetchTaskQueue())` — however it is written, wrapped in
    // `void`, split over lines or spaced differently — raises the count.
    const body = taskQueuePageSource
      .split('\n')
      .filter((line) => !line.startsWith('import '))
      .join('\n');

    expect(body.match(/fetchTaskQueue/g) ?? []).toHaveLength(1);
    expect(body.match(/fetchCompletedTasks/g) ?? []).toHaveLength(1);
    // …and that one call site passes the scope.
    expect(body).toContain('dispatch(fetchTaskQueue(filterPlantKey ?? undefined))');
    expect(body).toContain('dispatch(fetchCompletedTasks(filterPlantKey ?? undefined))');
  });
});
