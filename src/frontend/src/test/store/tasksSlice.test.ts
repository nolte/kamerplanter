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
} from '@/store/slices/tasksSlice';
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
  queueScope: null,
  taskQueueScope: null,
  completedTasksScope: null,
  queueLoading: false,
  queueError: null,
  queueLoaded: false,
  completedTasksLoading: false,
  completedTasksError: null,
  loading: false,
  error: null,
};

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
    const state = reducer(
      { ...baseState, queueError: 'old' },
      { type: fetchTaskQueue.pending.type },
    );
    expect(state.queueLoading).toBe(true);
    expect(state.queueError).toBeNull();
    // The shared flag stays out of it — `loading` belongs to the workflow and
    // task-list thunks, and the queue is the list that reloads on a filter pick.
    expect(state.loading).toBe(false);
  });

  it('fetchTaskQueue.fulfilled stores the queue and the scope it was fetched for', () => {
    const tasks = [{ key: 'task-1' }];
    const state = reducer(undefined, {
      type: fetchTaskQueue.fulfilled.type,
      payload: { scope: null, tasks },
    });
    expect(state.taskQueue).toEqual(tasks);
    expect(state.taskQueueScope).toBeNull();
    expect(state.queueLoaded).toBe(true);
  });

  it('fetchTaskQueue.rejected falls back to a default message', () => {
    const state = reducer(undefined, { type: fetchTaskQueue.rejected.type, error: {} });
    expect(state.queueError).toBe('errors.loadFailed');
    expect(state.queueLoaded).toBe(true);
  });

  it('setQueueScope points both lists at one plant and clears stale errors', () => {
    const state = reducer(
      { ...baseState, queueError: 'boom', completedTasksError: 'boom' },
      setQueueScope('plant-7'),
    );
    expect(state.queueScope).toBe('plant-7');
    expect(state.queueError).toBeNull();
    expect(state.completedTasksError).toBeNull();
  });

  describe('an answer to a scope the user has left is dropped', () => {
    // The race is not symmetric: the unscoped query is the slow branch, so the
    // older answer arriving last was the *likely* order, not the rare one.
    it('fetchTaskQueue.fulfilled keeps the current scope\'s rows', () => {
      const scoped = { ...baseState, queueScope: 'plant-B', queueLoading: true };
      const state = reducer(scoped, {
        type: fetchTaskQueue.fulfilled.type,
        payload: { scope: null, tasks: [{ key: 'whole-tenant' }] },
      });
      expect(state.taskQueue).toEqual([]);
      // The newer query owns the flag and is still running.
      expect(state.queueLoading).toBe(true);
    });

    it('fetchTaskQueue.rejected does not surface a stale failure', () => {
      const scoped = { ...baseState, queueScope: 'plant-B', queueLoading: true };
      const state = reducer(scoped, {
        type: fetchTaskQueue.rejected.type,
        payload: { scope: 'plant-A', message: 'errors.network' },
      });
      expect(state.queueError).toBeNull();
      expect(state.queueLoading).toBe(true);
    });

    it('fetchCompletedTasks.fulfilled keeps the current scope\'s rows', () => {
      const scoped = { ...baseState, queueScope: 'plant-B', completedTasksLoading: true };
      const state = reducer(scoped, {
        type: fetchCompletedTasks.fulfilled.type,
        payload: { scope: 'plant-A', tasks: [{ key: 'a-done' }] },
      });
      expect(state.completedTasks).toEqual([]);
      expect(state.completedTasksLoading).toBe(true);
    });
  });

  it('fetchCompletedTasks.rejected keeps the failure instead of showing an empty list', () => {
    const state = reducer(undefined, {
      type: fetchCompletedTasks.rejected.type,
      payload: { scope: null, message: 'errors.network' },
    });
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

  it('fetchTaskQueue reads the plant scope from the store, not from an argument', async () => {
    mocked.getTaskQueue.mockResolvedValue([{ key: 'task-q' }] as never);
    const store = makeTasksStore();
    store.dispatch(setQueueScope('pl1'));
    await store.dispatch(fetchTaskQueue());
    expect(mocked.getTaskQueue).toHaveBeenCalledWith('pl1');
    expect(store.getState().tasks.taskQueue).toEqual([{ key: 'task-q' }]);
    expect(store.getState().tasks.taskQueueScope).toBe('pl1');
  });

  it('fetchCompletedTasks scopes the query through entity_type/entity_key', async () => {
    mocked.listTasks.mockResolvedValue([{ key: 'done-1' }] as never);
    const store = makeTasksStore();
    store.dispatch(setQueueScope('pl1'));
    await store.dispatch(fetchCompletedTasks());
    expect(mocked.listTasks).toHaveBeenCalledWith(0, 100, {
      status: 'completed',
      entity_type: 'plant_instance',
      entity_key: 'pl1',
    });
    expect(store.getState().tasks.completedTasks).toEqual([{ key: 'done-1' }]);
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
