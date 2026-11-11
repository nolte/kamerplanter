/**
 * REQ-053 WP 10.10 (#2831, R-7.2, W-008, Anhang A 62): tasks on a compost, water source or storage object in the
 * properties panel.
 *
 * Pinned: the section reaches the panel of exactly those three classes (a bench - `furniture` - a trellis or a path
 * gets none, the server would answer 422); it lists the object's open tasks (`GET /tasks` with `entity_type =
 * garden_object`, the object's key, once per open status); "Aufgabe anlegen" opens the bed's task dialog with the
 * object as its target and posts `entity_type = garden_object` without the bed's "for every plant"; offline and for
 * an object not saved yet the action is locked with a hint and nothing is read; a viewer sees the list but no action;
 * axe is clean.
 */
import { act, cleanup, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { http, HttpResponse } from 'msw';
import { afterEach, beforeEach, describe, expect, it } from 'vitest';
import type { TaskItem } from '@/api/types';
import { expectNoA11yViolations } from '@/test/a11y/expectNoA11yViolations';
import { gardenObject, planResponse } from '@/test/gardenPlanFixtures';
import { authState, createTestStore, renderWithProviders, tenantState } from '@/test/helpers';
import { server } from '@/test/mocks/server';
import { normalizePlan } from '../model/planModel';
import type { GardenObjectType } from '../model/types';
import { setSelection } from '../state/gardenPlanSlice';
import { openPanelTab, setupEditor } from './editorTestKit';
import ObjectTasksSection from './ObjectTasksSection';

const TASKS = '/api/v1/t/:tenant/tasks';

function task(key: string, overrides: Partial<TaskItem> = {}): TaskItem {
  return {
    key,
    name: 'Turn the compost',
    name_de: '',
    instruction: '',
    instruction_de: '',
    category: 'maintenance',
    origin: 'user',
    source: '',
    source_run_ref: null,
    external_ref: null,
    entity_key: 'go_compost',
    entity_type: 'garden_object',
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
    ...overrides,
  } as TaskItem;
}

interface Backend {
  /** The query strings of every `GET /tasks`. */
  reads: URLSearchParams[];
  /** The bodies of every `POST /tasks`. */
  posts: Record<string, unknown>[];
}

/** `GET /tasks` answers the open tasks by status; `POST /tasks` adds one (pending) and answers it. */
function useTaskBackend(initial: TaskItem[] = [], options: { failRead?: boolean } = {}): Backend {
  const backend: Backend = { reads: [], posts: [] };
  const stored = [...initial];
  server.use(
    http.get(TASKS, ({ request }) => {
      const params = new URL(request.url).searchParams;
      backend.reads.push(params);
      if (options.failRead) {
        return HttpResponse.json({ error_code: 'INTERNAL', message: 'boom', details: [] }, { status: 500 });
      }
      return HttpResponse.json(
        stored.filter(
          (item) =>
            item.status === params.get('status') &&
            item.entity_type === params.get('entity_type') &&
            item.entity_key === params.get('entity_key'),
        ),
      );
    }),
    http.post(TASKS, async ({ request }) => {
      const body = (await request.json()) as Record<string, unknown>;
      backend.posts.push(body);
      const created = task(`t_${stored.length + 1}`, {
        name: String(body.name),
        category: String(body.category),
        entity_type: String(body.entity_type),
        entity_key: String(body.entity_key),
        due_date: (body.due_date as string | undefined) ?? null,
      });
      stored.push(created);
      return HttpResponse.json(created, { status: 201 });
    }),
  );
  return backend;
}

function setOnline(value: boolean) {
  Object.defineProperty(window.navigator, 'onLine', { configurable: true, get: () => value });
  act(() => {
    window.dispatchEvent(new Event(value ? 'online' : 'offline'));
  });
}

function renderSection(
  objectKey = 'go_compost',
  objectType: GardenObjectType = 'compost',
  role: 'viewer' | 'grower' = 'grower',
) {
  return renderWithProviders(
    <ObjectTasksSection objectKey={objectKey} objectType={objectType} objectName="Compost heap" />,
    { store: createTestStore({ ...tenantState(role), ...authState() }) },
  );
}

beforeEach(() => setOnline(true));
afterEach(() => {
  cleanup();
  setOnline(true);
});

describe('which objects get the action (R-7.2)', () => {
  function objectsPlan() {
    const area = (x: number) => ({ kind: 'rect' as const, origin: [x, 2] as [number, number], width_m: 1, length_m: 1, rotation_deg: 0 });
    return normalizePlan(
      planResponse({
        plan: {
          boundary: { kind: 'rect', origin: [0, 0], width_m: 20, length_m: 20, rotation_deg: 0 },
          north_angle_deg: 0,
          default_grid_m: 0.1,
          adjacency_factor: 1.5,
          plan_revision: 7,
        },
        locations: [],
        slots: [],
        plants: [],
        garden_objects: [
          gardenObject('go_compost', 2, 2, {
            object_type: 'compost',
            label: 'Compost heap',
            geometry: area(2),
            bbox: [2, 2, 3, 3],
            props: { object_type: 'compost' },
          }),
          gardenObject('go_barrel', 5, 2, {
            object_type: 'water_source',
            label: 'Rain barrel',
            geometry: { kind: 'point', origin: [5, 2] },
            bbox: [5, 2, 5, 2],
            props: { object_type: 'water_source', water_source_kind: 'rain_barrel' },
          }),
          gardenObject('go_shed', 8, 2, {
            object_type: 'storage',
            label: 'Shed',
            geometry: area(8),
            bbox: [8, 2, 9, 3],
            props: { object_type: 'storage' },
          }),
          gardenObject('go_bench', 11, 2, {
            object_type: 'furniture',
            label: 'Bench',
            geometry: area(11),
            bbox: [11, 2, 12, 3],
            props: { object_type: 'furniture' },
          }),
          gardenObject('go_trellis', 14, 2, {
            object_type: 'trellis',
            label: 'Bean trellis',
            geometry: { kind: 'polyline', width_m: 0.1, points: [[14, 2], [15, 2]] },
            bbox: [14, 2, 15, 2],
            props: { object_type: 'trellis', height_m: 1.8 },
          }),
        ],
      }),
    );
  }

  function select(key: string) {
    const t = setupEditor({ plan: objectsPlan() });
    t.after(() => {
      act(() => {
        t.store.dispatch(setSelection([{ entity: 'garden_object', key }]));
      });
    });
    openPanelTab('properties');
    t.rerender();
    return t;
  }

  it.each([
    ['go_compost', 'compost'],
    ['go_barrel', 'water_source'],
    ['go_shed', 'storage'],
  ])('offers tasks on %s (%s) and lists its open tasks', async (key, type) => {
    const backend = useTaskBackend([task('t_open', { entity_key: key, name: 'Look after it' })]);
    select(key);

    const section = await screen.findByTestId('garden-plan-panel-object-tasks');
    expect(section).toHaveAttribute('data-object-type', type);
    expect(await within(section).findByTestId('garden-plan-panel-object-task-t_open')).toHaveTextContent('Look after it');
    expect(within(section).getByTestId('garden-plan-panel-object-task-add')).toBeEnabled();
    // One read per open status, each filtered to this object.
    expect(backend.reads.map((params) => params.get('status')).sort()).toEqual(['in_progress', 'pending']);
    for (const params of backend.reads) {
      expect(params.get('entity_type')).toBe('garden_object');
      expect(params.get('entity_key')).toBe(key);
    }
  });

  it.each(['go_bench', 'go_trellis'])('offers no tasks on %s', async (key) => {
    const backend = useTaskBackend();
    select(key);

    await screen.findByTestId('garden-plan-panel-object-props');
    expect(screen.queryByTestId('garden-plan-panel-object-tasks')).toBeNull();
    expect(backend.reads).toHaveLength(0);
  });
});

describe('the open tasks', () => {
  it('lists them by due date, marks the overdue one and says when there are none', async () => {
    useTaskBackend([
      task('t_late', { name: 'Turn the compost', due_date: '2020-03-01T23:59:00Z' }),
      task('t_later', { name: 'Sift the compost', due_date: '2999-04-01T23:59:00Z', status: 'in_progress' }),
    ]);
    renderSection();

    const list = await screen.findByTestId('garden-plan-panel-object-tasks-list');
    const rows = within(list).getAllByRole('listitem');
    expect(rows.map((row) => row.getAttribute('data-testid'))).toEqual([
      'garden-plan-panel-object-task-t_late',
      'garden-plan-panel-object-task-t_later',
    ]);
    expect(rows[0]).toHaveAttribute('data-overdue', 'true');
    expect(rows[0]).toHaveTextContent(/overdue since/);
    expect(rows[1]).toHaveAttribute('data-overdue', 'false');
    expect(rows[1]).toHaveTextContent(/due /);
    expect(rows[0]).toHaveTextContent('Maintenance');
  });

  it('says there are none', async () => {
    useTaskBackend();
    renderSection();
    expect(await screen.findByTestId('garden-plan-panel-object-tasks-empty')).toHaveTextContent(
      'No tasks are open for this object.',
    );
  });

  it('explains a failed read and reads again on "Try again"', async () => {
    const backend = useTaskBackend([], { failRead: true });
    const user = userEvent.setup();
    renderSection();

    const error = await screen.findByTestId('garden-plan-panel-object-tasks-error');
    const before = backend.reads.length;
    await user.click(within(error).getByRole('button', { name: 'Try again' }));
    await waitFor(() => expect(backend.reads.length).toBeGreaterThan(before));
  });
});

describe('add a task (the bed dialog with the object as target)', () => {
  it('posts entity_type garden_object with an object category and shows the new task', async () => {
    const backend = useTaskBackend();
    const user = userEvent.setup();
    renderSection();
    await screen.findByTestId('garden-plan-panel-object-tasks-empty');

    await user.click(screen.getByTestId('garden-plan-panel-object-task-add'));
    const dialog = await screen.findByTestId('care-task-dialog');
    expect(dialog).toHaveAttribute('data-target', 'garden_object');
    expect(within(dialog).getByRole('heading', { name: 'New task for Compost heap' })).toBeInTheDocument();
    // No "for every plant" on an object.
    expect(within(dialog).queryByTestId('care-task-scope-plants')).toBeNull();
    expect(within(dialog).getByTestId('care-task-object-hint')).toBeInTheDocument();

    // The object categories only: no bed work on a compost heap.
    await user.click(within(dialog).getByRole('combobox', { name: 'Category' }));
    const options = within(screen.getByRole('listbox'))
      .getAllByRole('option')
      .map((option) => option.textContent);
    expect(options).toHaveLength(5);
    expect(options).not.toContain('Sowing');
    await user.click(within(screen.getByRole('listbox')).getByRole('option', { name: 'Cleaning' }));

    await user.click(within(dialog).getByTestId('care-task-submit'));

    await waitFor(() => expect(backend.posts).toHaveLength(1));
    expect(backend.posts[0]).toEqual({ name: 'Cleaning', category: 'cleaning', entity_type: 'garden_object', entity_key: 'go_compost' });
    expect(backend.posts[0]).not.toHaveProperty('for_each_plant');
    await waitFor(() => expect(screen.queryByTestId('care-task-dialog')).toBeNull());
    expect(await screen.findByTestId('garden-plan-panel-object-task-t_1')).toHaveTextContent('Cleaning');
    expect(await screen.findByText('Task for Compost heap added.')).toBeInTheDocument();
  });

  it('has no accessibility violations with the list and with the dialog open', async () => {
    useTaskBackend([task('t_open', { due_date: '2999-04-01T23:59:00Z' })]);
    const user = userEvent.setup();
    const { container } = renderSection();
    await screen.findByTestId('garden-plan-panel-object-task-t_open');
    await expectNoA11yViolations(container);

    await user.click(screen.getByTestId('garden-plan-panel-object-task-add'));
    await screen.findByTestId('care-task-dialog');
    await expectNoA11yViolations(document.body);
  });
});

describe('locked: offline, not saved, viewer', () => {
  it('locks the action with a hint and reads nothing while offline (G-W9)', async () => {
    const backend = useTaskBackend();
    setOnline(false);
    renderSection();

    expect(screen.getByTestId('garden-plan-panel-object-tasks-offline')).toHaveTextContent('Without a connection');
    expect(screen.getByTestId('garden-plan-panel-object-task-add')).toBeDisabled();
    expect(backend.reads).toHaveLength(0);
  });

  it('reads once the connection is back', async () => {
    const backend = useTaskBackend();
    setOnline(false);
    renderSection();
    setOnline(true);

    expect(await screen.findByTestId('garden-plan-panel-object-tasks-empty')).toBeInTheDocument();
    expect(screen.getByTestId('garden-plan-panel-object-task-add')).toBeEnabled();
    expect(backend.reads.length).toBeGreaterThan(0);
  });

  it('asks to save an object the server does not know yet', () => {
    const backend = useTaskBackend();
    renderSection('tmp1abcd');

    expect(screen.getByTestId('garden-plan-panel-object-tasks-unsaved')).toHaveTextContent('Save the plan first');
    expect(screen.getByTestId('garden-plan-panel-object-task-add')).toBeDisabled();
    expect(backend.reads).toHaveLength(0);
  });

  it('shows a viewer the open tasks but no action', async () => {
    useTaskBackend([task('t_open')]);
    renderSection('go_compost', 'compost', 'viewer');

    expect(await screen.findByTestId('garden-plan-panel-object-task-t_open')).toBeInTheDocument();
    expect(screen.queryByTestId('garden-plan-panel-object-task-add')).toBeNull();
  });
});
