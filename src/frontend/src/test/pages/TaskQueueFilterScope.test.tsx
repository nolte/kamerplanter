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
import type { PlantInstance, TaskItem } from '@/api/types';
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

/** Every `(plantKey, category, origins)` triple the page sent to `GET /tasks/queue`. */
let queueQueries: { plantKey: string | null; category: string | null; origins: string[] }[] = [];
/** The same for `GET /tasks`, the completed list. */
let completedQueries: { plantKey: string | null; category: string | null; origins: string[] }[] = [];

const FILTER_PLANT_KEY = 'plant-1';
const FILTER_PLANT_NAME = 'Feige Gustav';

/** The one plant the filter offers; enough to drive the plant scope. */
const PLANTS_FIXTURE = [
  {
    key: FILTER_PLANT_KEY,
    instance_id: 'FIG-1',
    species_key: 'species-1',
    cultivar_key: null,
    site_key: null,
    location_key: null,
    slot_key: null,
    substrate_batch_key: null,
    substrate_key: null,
    plant_name: FILTER_PLANT_NAME,
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
  },
] as unknown as PlantInstance[];

function narrow(rows: TaskItem[], url: URL): TaskItem[] {
  const category = url.searchParams.get('category');
  const origins = url.searchParams.getAll('origin');
  const plantKey = url.searchParams.get('plant_key') ?? url.searchParams.get('entity_key');
  return rows.filter(
    (t) =>
      (!category || t.category === category) &&
      (!origins.length || origins.includes(t.origin)) &&
      (!plantKey || t.entity_key === plantKey),
  );
}

/** Care-dashboard entries the page merges into the same list as the tasks. */
let careEntries: unknown[] = [];

function seed(queueRows: TaskItem[], completedRows: TaskItem[] = [], care: unknown[] = []) {
  careEntries = care;
  queueQueries = [];
  completedQueries = [];
  server.use(
    http.get(`${TASKS}/queue`, ({ request }) => {
      const url = new URL(request.url);
      queueQueries.push({
        plantKey: url.searchParams.get('plant_key'),
        category: url.searchParams.get('category'),
        origins: url.searchParams.getAll('origin'),
      });
      // Narrow first, cap second — the order the server works in, and the whole
      // point: the page cannot recover a row the cap dropped.
      return HttpResponse.json(narrow(queueRows, url).slice(0, CAP));
    }),
    http.get(`${TASKS}/overdue`, () => HttpResponse.json([])),
    http.get(`${CARE}/dashboard`, () => HttpResponse.json(careEntries)),
    http.get(PLANTS, () => HttpResponse.json(PLANTS_FIXTURE)),
    http.get(TASKS, ({ request }) => {
      const url = new URL(request.url);
      completedQueries.push({
        plantKey: url.searchParams.get('entity_key'),
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
        plantKey: null,
        category: 'ipm',
        origins: [...MACHINE_TASK_ORIGINS],
      });
    });
  });

  describe('clearing the filters', () => {
    it('drops every scope in one query, not only the one applied last', async () => {
      // Three setters in one handler. While each of them composed the next scope
      // from a render-time copy, the last dispatch won and the two before it were
      // lost — the chips for plant and category stayed and the query kept
      // carrying them, which is worse than not offering the button.
      seed(rowsWithTargetPastTheCap({ category: 'ipm' }));
      renderWithProviders(<TaskQueuePage />, { route: '/aufgaben/queue' });
      await screen.findByText('Füller 0');

      await selectCategory('ipm');
      await waitFor(() => expect(screen.getByTestId('active-filter-category')).toBeInTheDocument());
      const plantInput = within(screen.getByTestId('filter-plant')).getByRole('combobox');
      await userEvent.click(plantInput);
      await userEvent.type(plantInput, 'Feige');
      await userEvent.click(await screen.findByRole('option', { name: new RegExp(FILTER_PLANT_NAME, 'i') }));
      await waitFor(() => expect(screen.getByTestId('active-filter-plant')).toBeInTheDocument());
      await userEvent.click(screen.getByTestId('filter-origin-machine'));
      await waitFor(() => expect(screen.getByTestId('active-filter-origin')).toBeInTheDocument());

      await userEvent.click(screen.getByTestId('clear-filters-button'));

      // Every chip is gone…
      await waitFor(() => expect(screen.queryByTestId('active-filter-origin')).not.toBeInTheDocument());
      expect(screen.queryByTestId('active-filter-category')).not.toBeInTheDocument();
      expect(screen.queryByTestId('active-filter-plant')).not.toBeInTheDocument();
      // …and so is every parameter, in the query the page actually issued.
      await waitFor(() => {
        const last = queueQueries[queueQueries.length - 1];
        expect(last).toEqual({ plantKey: null, category: null, origins: [] });
      });
    });
  });

  describe('the care source under a category scope', () => {
    // The care dashboard is *not* narrowed server-side (it is a projection over
    // at most 500 plants, not a capped page), so the page still narrows it. Two
    // things have to hold once the queue is narrowed server-side.
    const CARE_ENTRY = {
      plant_key: 'plant-1',
      plant_name: 'Feige Gustav',
      reminder_type: 'watering',
      urgency: 'due',
      due_date: '2026-01-01',
      days_until_due: 0,
    };

    it('hides the care entries when a category other than care_reminder is picked', async () => {
      seed(rowsWithTargetPastTheCap({ category: 'ipm' }), [], [CARE_ENTRY]);
      renderWithProviders(<TaskQueuePage />, { route: '/aufgaben/queue' });
      await screen.findByText('Füller 0');
      // Care entries render as their own card; unfiltered they are on the page.
      expect(await screen.findByTestId('care-card-care-plant-1-watering')).toBeInTheDocument();

      await selectCategory('ipm');

      expect(await screen.findByText(TARGET_NAME)).toBeInTheDocument();
      // A category selection is a statement about what the user wants to see. The
      // care source carries no category, so anything but `care_reminder` excludes
      // it — the same rule the origin filter already applies.
      expect(screen.queryByTestId('care-card-care-plant-1-watering')).not.toBeInTheDocument();
    });

    it('does not double the card when care_reminder itself is the scope', async () => {
      // The page de-duplicates a care entry against the care_reminder *task* that
      // already covers it, and it builds that dedup index out of `taskQueue`. Once
      // the queue is narrowed server-side, the index is only populated when the
      // scope actually contains care rows — which is exactly this case.
      const careTask = makeTask({
        key: 'care-task',
        name: 'Feige Gustav — watering',
        name_de: 'Feige Gustav — watering',
        category: 'care_reminder',
        entity_type: 'plant_instance',
        entity_key: 'plant-1',
      });
      seed([careTask], [], [CARE_ENTRY]);
      renderWithProviders(<TaskQueuePage />, { route: '/aufgaben/queue' });
      await screen.findByText('Feige Gustav — watering');

      await selectCategory('care_reminder');

      await waitFor(() => expect(queueQueries.map((q) => q.category)).toContain('care_reminder'));
      expect(await screen.findByText('Feige Gustav — watering')).toBeInTheDocument();
      // One card for the reminder, not one per source.
      expect(screen.queryByTestId('care-card-care-plant-1-watering')).not.toBeInTheDocument();
    });
  });

  describe('leaving the page', () => {
    it('does not leave the narrowed rows behind for another screen to count', async () => {
      // `state.tasks.taskQueue` is read outside this page — the kiosk start screen
      // shows its length as "open tasks" — so a list narrowed to one category and
      // then abandoned is a wrong number somewhere else. Clearing the scope alone
      // would not have helped: the rows are what is read.
      seed(rowsWithTargetPastTheCap({ category: 'ipm' }));
      const { store, unmount } = renderWithProviders(<TaskQueuePage />, { route: '/aufgaben/queue' });
      await screen.findByText('Füller 0');
      await selectCategory('ipm');
      await waitFor(() => expect(store.getState().tasks.taskQueue).toHaveLength(1));

      unmount();

      expect(store.getState().tasks.taskQueue).toEqual([]);
      expect(store.getState().tasks.queueScope).toEqual({
        plantKey: null,
        category: null,
        origin: 'all',
      });
      // …and the next visit shows its skeleton rather than an empty list that
      // reads like an answer.
      expect(store.getState().tasks.queueLoaded).toBe(false);
    });
  });

  describe('the completed list', () => {
    it('reaches a completed task the cap had dropped, in its own section', async () => {
      // Its own name, asserted inside the completed section: the queue above it
      // holds a row matching the same filter, and a page-wide text query would be
      // satisfied by *that* row while the completed list stayed unnarrowed.
      const COMPLETED_TARGET = 'Ernte dokumentiert';
      const completed = [
        ...Array.from({ length: CAP }, (_, i) =>
          makeTask({ key: `done-${i}`, name: `Erledigt ${i}`, name_de: `Erledigt ${i}`, status: 'completed' }),
        ),
        makeTask({
          key: 'done-target',
          name: COMPLETED_TARGET,
          name_de: COMPLETED_TARGET,
          status: 'completed',
          category: 'ipm',
        }),
      ];
      seed(rowsWithTargetPastTheCap({ category: 'ipm' }), completed);
      renderWithProviders(<TaskQueuePage />, { route: '/aufgaben/queue' });
      await screen.findByText('Füller 0');

      await userEvent.click(within(screen.getByTestId('show-completed-toggle')).getByRole('switch'));
      const section = await screen.findByTestId('task-section-completed');
      await within(section).findByText('Erledigt 0');
      // The premise: unfiltered, the completed answer is capped and the target is
      // genuinely absent from it.
      expect(within(section).queryByText(COMPLETED_TARGET)).not.toBeInTheDocument();

      await selectCategory('ipm');

      await waitFor(() => expect(completedQueries.map((q) => q.category)).toContain('ipm'));
      expect(
        await within(screen.getByTestId('task-section-completed')).findByText(COMPLETED_TARGET),
      ).toBeInTheDocument();
      // …and the rows the category excludes are gone from that section.
      expect(
        within(screen.getByTestId('task-section-completed')).queryByText('Erledigt 0'),
      ).not.toBeInTheDocument();
    });
  });
});
