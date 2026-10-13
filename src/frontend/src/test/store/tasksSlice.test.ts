import { describe, it, expect, vi, beforeEach } from 'vitest';
import { configureStore } from '@reduxjs/toolkit';
import reducer, {
  clearCurrentTask,
  clearError,
  fetchWorkflows,
  fetchWorkflow,
  deleteWorkflowThunk,
  fetchTaskTemplates,
  fetchTasks,
  fetchTask,
  fetchTaskQueue,
  fetchCompletedTasks,
  fetchOverdueTasks,
  setQueueScope,
  resetQueue,
  EMPTY_QUEUE_SCOPE,
} from '@/store/slices/tasksSlice';
import { MACHINE_TASK_ORIGINS } from '@/api/types';
import * as tasksApi from '@/api/endpoints/tasks';

// Isolated module mock — no real HTTP, no handlers.ts.
vi.mock('@/api/endpoints/tasks');

function makeTasksStore() {
  return configureStore({ reducer: { tasks: reducer } });
}

const baseState = {
  workflows: [],
  taskTemplates: [],
  tasks: [],
  currentTask: null,
  taskQueue: [],
  overdueTasks: [],
  completedTasks: [],
  queueScope: EMPTY_QUEUE_SCOPE,
  taskQueueScope: EMPTY_QUEUE_SCOPE,
  completedTasksScope: EMPTY_QUEUE_SCOPE,
  pendingQueueRequestId: null,
  pendingCompletedRequestId: null,
  queueLoading: false,
  queueError: null,
  queueLoaded: false,
  completedTasksLoading: false,
  completedTasksError: null,
  loading: false,
  error: null,
};

/**
 * The three action shapes the queue thunks emit, with the `requestId`
 * `createAsyncThunk` mints. The id is not decoration here: the reducer uses it to
 * decide whether an answer belongs to the query now in flight, so a test that
 * omitted it would be describing an action Redux never dispatches.
 */
const RID = 'request-1';

function queuePending(requestId = RID) {
  return { type: fetchTaskQueue.pending.type, meta: { requestId, arg: undefined } };
}
function queueFulfilled(payload: unknown, requestId = RID) {
  return { type: fetchTaskQueue.fulfilled.type, payload, meta: { requestId, arg: undefined } };
}
function queueRejected(payload: unknown, requestId = RID, error: unknown = {}) {
  return { type: fetchTaskQueue.rejected.type, payload, error, meta: { requestId, arg: undefined } };
}
function completedPending(requestId = RID) {
  return { type: fetchCompletedTasks.pending.type, meta: { requestId, arg: undefined } };
}
function completedFulfilled(payload: unknown, requestId = RID) {
  return { type: fetchCompletedTasks.fulfilled.type, payload, meta: { requestId, arg: undefined } };
}
function completedRejected(payload: unknown, requestId = RID) {
  return { type: fetchCompletedTasks.rejected.type, payload, error: {}, meta: { requestId, arg: undefined } };
}

/** `baseState` with a queue query of `requestId` in flight. */
function queueInFlight(overrides: Record<string, unknown> = {}, requestId = RID) {
  return { ...baseState, ...overrides, queueLoading: true, pendingQueueRequestId: requestId };
}

describe('tasksSlice', () => {
  it('has the empty initial state', () => {
    expect(reducer(undefined, { type: 'unknown' })).toEqual(baseState);
  });

  it('clearCurrentTask resets the selected task', () => {
    const state = reducer(
      { ...baseState, currentTask: { key: 'task-1' } as never },
      clearCurrentTask(),
    );
    expect(state.currentTask).toBeNull();
  });

  it('clearError resets the error', () => {
    const state = reducer({ ...baseState, error: 'boom' }, clearError());
    expect(state.error).toBeNull();
  });

  it('fetchWorkflows.pending sets loading and clears prior error', () => {
    const state = reducer({ ...baseState, error: 'old' }, { type: fetchWorkflows.pending.type });
    expect(state.loading).toBe(true);
    expect(state.error).toBeNull();
  });

  it('fetchWorkflows.fulfilled stores workflows', () => {
    const workflows = [{ key: 'w1' }];
    const state = reducer(undefined, { type: fetchWorkflows.fulfilled.type, payload: workflows });
    expect(state.workflows).toEqual(workflows);
    expect(state.loading).toBe(false);
  });

  it('fetchWorkflows.rejected falls back to a default message', () => {
    const state = reducer(undefined, { type: fetchWorkflows.rejected.type, error: {} });
    expect(state.error).toBe('errors.loadFailed');
  });

  it('deleteWorkflowThunk.fulfilled removes the workflow by key', () => {
    const populated = { ...baseState, workflows: [{ key: 'w1' }, { key: 'w2' }] as never };
    const state = reducer(populated, { type: deleteWorkflowThunk.fulfilled.type, payload: 'w1' });
    expect(state.workflows).toEqual([{ key: 'w2' }]);
  });

  it('fetchTaskTemplates.fulfilled stores templates', () => {
    const templates = [{ key: 'tt1' }];
    const state = reducer(undefined, { type: fetchTaskTemplates.fulfilled.type, payload: templates });
    expect(state.taskTemplates).toEqual(templates);
  });

  it('fetchTasks.pending sets loading and clears prior error', () => {
    const state = reducer({ ...baseState, error: 'old' }, { type: fetchTasks.pending.type });
    expect(state.loading).toBe(true);
    expect(state.error).toBeNull();
  });

  it('fetchTasks.fulfilled stores tasks', () => {
    const tasks = [{ key: 'task-1' }];
    const state = reducer(undefined, { type: fetchTasks.fulfilled.type, payload: tasks });
    expect(state.tasks).toEqual(tasks);
  });

  it('fetchTasks.rejected falls back to a default message', () => {
    const state = reducer(undefined, { type: fetchTasks.rejected.type, error: {} });
    expect(state.error).toBe('errors.loadFailed');
  });

  it('fetchTask.fulfilled stores the current task', () => {
    const task = { key: 'task-1' };
    const state = reducer(undefined, { type: fetchTask.fulfilled.type, payload: task });
    expect(state.currentTask).toEqual(task);
  });

  it('fetchTaskQueue.pending sets the queue-only loading flag and clears prior error', () => {
    const state = reducer({ ...baseState, queueError: 'old' }, queuePending());
    expect(state.queueLoading).toBe(true);
    expect(state.queueError).toBeNull();
    // The shared flag stays out of it — `loading` belongs to the workflow and
    // task-list thunks, and the queue is the list that reloads on a filter pick.
    expect(state.loading).toBe(false);
  });

  it('fetchTaskQueue.fulfilled stores the queue and the scope it was fetched for', () => {
    const tasks = [{ key: 'task-1' }];
    const state = reducer(
      reducer(undefined, queuePending()),
      queueFulfilled({ scope: EMPTY_QUEUE_SCOPE, tasks }),
    );
    expect(state.taskQueue).toEqual(tasks);
    expect(state.taskQueueScope).toEqual(EMPTY_QUEUE_SCOPE);
    expect(state.queueLoaded).toBe(true);
  });

  it('fetchTaskQueue.rejected falls back to a default message', () => {
    const state = reducer(reducer(undefined, queuePending()), queueRejected(undefined));
    expect(state.queueError).toBe('errors.loadFailed');
    expect(state.queueLoaded).toBe(true);
  });

  it('setQueueScope points both lists at one plant and clears stale errors', () => {
    const state = reducer(
      { ...baseState, queueError: 'boom', completedTasksError: 'boom' },
      setQueueScope({ ...EMPTY_QUEUE_SCOPE, plantKey: 'plant-7' }),
    );
    expect(state.queueScope).toEqual({ plantKey: 'plant-7', category: null, origin: 'all' });
    expect(state.queueError).toBeNull();
    expect(state.completedTasksError).toBeNull();
  });

  it('setQueueScope carries the category and the origin, not only the plant', () => {
    const state = reducer(
      baseState,
      setQueueScope({ plantKey: null, category: 'ipm', origin: 'machine' }),
    );
    expect(state.queueScope).toEqual({ plantKey: null, category: 'ipm', origin: 'machine' });
  });

  it('setQueueScope with the scope already active is a no-op, so no refetch is triggered', () => {
    // The querying effect keys on the scope's fields; a fresh object carrying
    // the same values would re-query on every re-selection of the same filter.
    const active = { ...baseState, queueScope: { plantKey: 'p1', category: 'ipm', origin: 'user' as const } };
    const state = reducer(active, setQueueScope({ plantKey: 'p1', category: 'ipm', origin: 'user' }));
    expect(state.queueScope).toBe(active.queueScope);
  });

  it('setQueueScope merges its patch, so a sequence of changes composes', () => {
    // Three filter changes dispatched from one handler ("clear all filters")
    // each carried a copy of the scope as it was at render time, so the last
    // dispatch overwrote the two before it. Merging in the reducer means the
    // caller cannot compose them wrongly, because it does not compose them.
    const active = {
      ...baseState,
      queueScope: { plantKey: 'p1', category: 'ipm', origin: 'machine' as const },
    };

    const afterFirst = reducer(active, setQueueScope({ category: null }));
    const afterSecond = reducer(afterFirst, setQueueScope({ plantKey: null }));
    const afterThird = reducer(afterSecond, setQueueScope({ origin: 'all' }));

    expect(afterThird.queueScope).toEqual(EMPTY_QUEUE_SCOPE);
  });

  it('resetQueue forgets the rows, not only the scope', () => {
    // `taskQueue` is read outside the queue page — the kiosk start screen counts
    // it as "open tasks" — so a scope-only reset left a narrowed list standing as
    // a wrong number on another screen.
    const narrowed = {
      ...baseState,
      taskQueue: [{ key: 'only-ipm' }] as never,
      completedTasks: [{ key: 'done' }] as never,
      queueScope: { plantKey: 'p1', category: 'ipm', origin: 'user' as const },
      taskQueueScope: { plantKey: 'p1', category: 'ipm', origin: 'user' as const },
      queueLoaded: true,
      pendingQueueRequestId: RID,
    };

    const state = reducer(narrowed, resetQueue());

    expect(state.taskQueue).toEqual([]);
    expect(state.completedTasks).toEqual([]);
    expect(state.queueScope).toEqual(EMPTY_QUEUE_SCOPE);
    expect(state.taskQueueScope).toEqual(EMPTY_QUEUE_SCOPE);
    // The next visit must show its skeleton rather than an empty list that looks
    // like an answer.
    expect(state.queueLoaded).toBe(false);
  });

  it('an answer still in flight when the queue is reset cannot repopulate it', () => {
    const state = reducer(
      reducer(queueInFlight(), resetQueue()),
      queueFulfilled({ scope: EMPTY_QUEUE_SCOPE, tasks: [{ key: 'late' }] }),
    );

    expect(state.taskQueue).toEqual([]);
  });

  describe('an answer to a scope the user has left is dropped', () => {
    // The race is not symmetric: the unscoped query is the slow branch, so the
    // older answer arriving last was the *likely* order, not the rare one.
    it('fetchTaskQueue.fulfilled keeps the current scope\'s rows', () => {
      const scoped = queueInFlight({ queueScope: { ...EMPTY_QUEUE_SCOPE, plantKey: 'plant-B' } });
      const state = reducer(scoped, queueFulfilled({ scope: EMPTY_QUEUE_SCOPE, tasks: [{ key: 'whole-tenant' }] }));
      expect(state.taskQueue).toEqual([]);
      // The newer query owns the flag and is still running.
      expect(state.queueLoading).toBe(true);
    });

    it('fetchTaskQueue.rejected does not surface a stale failure', () => {
      const scoped = queueInFlight({ queueScope: { ...EMPTY_QUEUE_SCOPE, plantKey: 'plant-B' } });
      const state = reducer(
        scoped,
        queueRejected({ scope: { ...EMPTY_QUEUE_SCOPE, plantKey: 'plant-A' }, message: 'errors.network' }),
      );
      expect(state.queueError).toBeNull();
      expect(state.queueLoading).toBe(true);
    });

    it('a scope differing only in category is just as stale as a different plant', () => {
      // The stamp is compared field by field: an identity comparison would call
      // every answer stale, and comparing only the plant would let the previous
      // category's rows land under the new chip.
      const scoped = queueInFlight({ queueScope: { ...EMPTY_QUEUE_SCOPE, category: 'ipm' } });
      const state = reducer(
        scoped,
        queueFulfilled({ scope: { ...EMPTY_QUEUE_SCOPE, category: 'harvest' }, tasks: [{ key: 'harvest-row' }] }),
      );
      expect(state.taskQueue).toEqual([]);
    });

    it('an answer stamped with the very same scope object values is applied', () => {
      const scope = { plantKey: 'plant-B', category: 'ipm', origin: 'machine' as const };
      const scoped = queueInFlight({ queueScope: scope });
      // A structurally equal but distinct object — what the thunk actually hands
      // back after a round trip.
      const state = reducer(scoped, queueFulfilled({ scope: { ...scope }, tasks: [{ key: 'fresh' }] }));
      expect(state.taskQueue).toEqual([{ key: 'fresh' }]);
      expect(state.queueLoading).toBe(false);
    });

    it('the older of two answers to the SAME scope does not overwrite the newer', () => {
      // A → B → A. Both A answers carry the same stamp, so the scope alone cannot
      // order them: the first A's rows could land last and stay. The request id
      // is what tells them apart.
      const scope = { ...EMPTY_QUEUE_SCOPE, plantKey: 'plant-A' };
      const firstA = queueInFlight({ queueScope: scope }, 'request-A1');
      // The second query for A starts; it now owns the flag and the id.
      const secondA = reducer(firstA, queuePending('request-A2'));
      const answered = reducer(secondA, queueFulfilled({ scope, tasks: [{ key: 'fresh' }] }, 'request-A2'));

      const afterStaleAnswer = reducer(
        answered,
        queueFulfilled({ scope, tasks: [{ key: 'stale' }] }, 'request-A1'),
      );

      expect(afterStaleAnswer.taskQueue).toEqual([{ key: 'fresh' }]);
    });

    it('fetchCompletedTasks.fulfilled keeps the current scope\'s rows', () => {
      const scoped = {
        ...baseState,
        queueScope: { ...EMPTY_QUEUE_SCOPE, plantKey: 'plant-B' },
        completedTasksLoading: true,
        pendingCompletedRequestId: RID,
      };
      const state = reducer(
        scoped,
        completedFulfilled({ scope: { ...EMPTY_QUEUE_SCOPE, plantKey: 'plant-A' }, tasks: [{ key: 'a-done' }] }),
      );
      expect(state.completedTasks).toEqual([]);
      expect(state.completedTasksLoading).toBe(true);
    });
  });

  it('fetchCompletedTasks.rejected keeps the failure instead of showing an empty list', () => {
    const state = reducer(
      reducer(undefined, completedPending()),
      completedRejected({ scope: EMPTY_QUEUE_SCOPE, message: 'errors.network' }),
    );
    expect(state.completedTasksError).toBe('errors.network');
    expect(state.completedTasksLoading).toBe(false);
  });

  it('fetchOverdueTasks.fulfilled stores overdue tasks', () => {
    const overdue = [{ key: 'task-2' }];
    const state = reducer(undefined, { type: fetchOverdueTasks.fulfilled.type, payload: overdue });
    expect(state.overdueTasks).toEqual(overdue);
  });
});

describe('tasksSlice thunks', () => {
  const mocked = vi.mocked(tasksApi);

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('fetchWorkflows forwards paging and stores workflows', async () => {
    mocked.listWorkflows.mockResolvedValue([{ key: 'w1' }] as never);
    const store = makeTasksStore();
    await store.dispatch(fetchWorkflows({ offset: 0, limit: 10 }));
    expect(mocked.listWorkflows).toHaveBeenCalledWith(0, 10);
    expect(store.getState().tasks.workflows).toEqual([{ key: 'w1' }]);
  });

  it('fetchWorkflows surfaces a rejection as the slice error', async () => {
    mocked.listWorkflows.mockRejectedValue(new Error('load failed'));
    const store = makeTasksStore();
    await store.dispatch(fetchWorkflows({}));
    expect(store.getState().tasks.error).toBe('load failed');
  });

  it('fetchWorkflow calls getWorkflow', async () => {
    mocked.getWorkflow.mockResolvedValue({ key: 'w9' } as never);
    const store = makeTasksStore();
    await store.dispatch(fetchWorkflow('w9'));
    expect(mocked.getWorkflow).toHaveBeenCalledWith('w9');
  });

  it('deleteWorkflowThunk calls the API and removes the workflow', async () => {
    mocked.deleteWorkflow.mockResolvedValue(undefined);
    const store = configureStore({
      reducer: { tasks: reducer },
      preloadedState: { tasks: { ...baseState, workflows: [{ key: 'w1' }] as never } },
    });
    await store.dispatch(deleteWorkflowThunk('w1'));
    expect(mocked.deleteWorkflow).toHaveBeenCalledWith('w1');
    expect(store.getState().tasks.workflows).toEqual([]);
  });

  it('fetchTaskTemplates forwards the workflow key and stores templates', async () => {
    mocked.listTaskTemplates.mockResolvedValue([{ key: 'tt1' }] as never);
    const store = makeTasksStore();
    await store.dispatch(fetchTaskTemplates('w1'));
    expect(mocked.listTaskTemplates).toHaveBeenCalledWith('w1');
    expect(store.getState().tasks.taskTemplates).toEqual([{ key: 'tt1' }]);
  });

  it('fetchTasks maps filter args into the API filter object', async () => {
    mocked.listTasks.mockResolvedValue([{ key: 'task-1' }] as never);
    const store = makeTasksStore();
    await store.dispatch(
      fetchTasks({ offset: 5, limit: 10, status: 'open', category: 'watering', entityType: 'plant', entityKey: 'pl1' }),
    );
    expect(mocked.listTasks).toHaveBeenCalledWith(5, 10, {
      status: 'open',
      category: 'watering',
      entity_type: 'plant',
      entity_key: 'pl1',
    });
    expect(store.getState().tasks.tasks).toEqual([{ key: 'task-1' }]);
  });

  it('fetchTask stores the current task', async () => {
    mocked.getTask.mockResolvedValue({ key: 'task-9' } as never);
    const store = makeTasksStore();
    await store.dispatch(fetchTask('task-9'));
    expect(mocked.getTask).toHaveBeenCalledWith('task-9');
    expect(store.getState().tasks.currentTask).toEqual({ key: 'task-9' });
  });

  it('fetchTaskQueue reads the scope from the store, not from an argument', async () => {
    mocked.getTaskQueue.mockResolvedValue([{ key: 'task-q' }] as never);
    const store = makeTasksStore();
    store.dispatch(setQueueScope({ plantKey: 'pl1', category: null, origin: 'all' }));
    await store.dispatch(fetchTaskQueue());
    expect(mocked.getTaskQueue).toHaveBeenCalledWith({
      plantKey: 'pl1',
      category: null,
      origin: undefined,
    });
    expect(store.getState().tasks.taskQueue).toEqual([{ key: 'task-q' }]);
    expect(store.getState().tasks.taskQueueScope).toEqual({
      plantKey: 'pl1',
      category: null,
      origin: 'all',
    });
  });

  it('fetchTaskQueue asks the server for the category rather than filtering the answer', async () => {
    mocked.getTaskQueue.mockResolvedValue([] as never);
    const store = makeTasksStore();
    store.dispatch(setQueueScope({ plantKey: null, category: 'ipm', origin: 'all' }));
    await store.dispatch(fetchTaskQueue());
    expect(mocked.getTaskQueue).toHaveBeenCalledWith(
      expect.objectContaining({ category: 'ipm' }),
    );
  });

  it('the machine origin filter becomes every non-user origin in one request', async () => {
    mocked.getTaskQueue.mockResolvedValue([] as never);
    const store = makeTasksStore();
    store.dispatch(setQueueScope({ plantKey: null, category: null, origin: 'machine' }));
    await store.dispatch(fetchTaskQueue());
    expect(mocked.getTaskQueue).toHaveBeenCalledWith(
      expect.objectContaining({ origin: MACHINE_TASK_ORIGINS }),
    );
  });

  it('the user origin filter asks for exactly that one origin', async () => {
    mocked.getTaskQueue.mockResolvedValue([] as never);
    const store = makeTasksStore();
    store.dispatch(setQueueScope({ plantKey: null, category: null, origin: 'user' }));
    await store.dispatch(fetchTaskQueue());
    expect(mocked.getTaskQueue).toHaveBeenCalledWith(
      expect.objectContaining({ origin: ['user'] }),
    );
  });

  it('fetchCompletedTasks scopes the query through entity_type/entity_key', async () => {
    mocked.listTasks.mockResolvedValue([{ key: 'done-1' }] as never);
    const store = makeTasksStore();
    store.dispatch(setQueueScope({ plantKey: 'pl1', category: null, origin: 'all' }));
    await store.dispatch(fetchCompletedTasks());
    expect(mocked.listTasks).toHaveBeenCalledWith(0, 100, {
      status: 'completed',
      entity_type: 'plant_instance',
      entity_key: 'pl1',
    });
    expect(store.getState().tasks.completedTasks).toEqual([{ key: 'done-1' }]);
  });

  it('fetchCompletedTasks carries the category and the origin into the query too', async () => {
    // The completed list is capped at 100 rows, so narrowing its answer has the
    // same blind spot the queue had (#1503).
    mocked.listTasks.mockResolvedValue([] as never);
    const store = makeTasksStore();
    store.dispatch(setQueueScope({ plantKey: null, category: 'harvest', origin: 'machine' }));
    await store.dispatch(fetchCompletedTasks());
    expect(mocked.listTasks).toHaveBeenCalledWith(0, 100, {
      status: 'completed',
      category: 'harvest',
      origin: MACHINE_TASK_ORIGINS,
    });
  });

  it('a queue failure reaches the state as a message the page can show', async () => {
    mocked.getTaskQueue.mockRejectedValue(new Error('Network Error'));
    const store = makeTasksStore();
    await store.dispatch(fetchTaskQueue());
    expect(store.getState().tasks.queueError).toBe('Network Error');
    expect(store.getState().tasks.queueLoading).toBe(false);
  });

  it('fetchOverdueTasks stores overdue tasks', async () => {
    mocked.getOverdueTasks.mockResolvedValue([{ key: 'task-od' }] as never);
    const store = makeTasksStore();
    await store.dispatch(fetchOverdueTasks());
    expect(store.getState().tasks.overdueTasks).toEqual([{ key: 'task-od' }]);
  });
});
