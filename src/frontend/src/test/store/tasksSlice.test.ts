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
  fetchOverdueTasks,
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
  completedTasksLoading: false,
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

  it('fetchTaskQueue.pending sets loading and clears prior error', () => {
    const state = reducer({ ...baseState, error: 'old' }, { type: fetchTaskQueue.pending.type });
    expect(state.loading).toBe(true);
    expect(state.error).toBeNull();
  });

  it('fetchTaskQueue.fulfilled stores the task queue', () => {
    const queue = [{ key: 'task-1' }];
    const state = reducer(undefined, { type: fetchTaskQueue.fulfilled.type, payload: queue });
    expect(state.taskQueue).toEqual(queue);
  });

  it('fetchTaskQueue.rejected falls back to a default message', () => {
    const state = reducer(undefined, { type: fetchTaskQueue.rejected.type, error: {} });
    expect(state.error).toBe('errors.loadFailed');
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

  it('fetchTaskQueue forwards the plant key and stores the queue', async () => {
    mocked.getTaskQueue.mockResolvedValue([{ key: 'task-q' }] as never);
    const store = makeTasksStore();
    await store.dispatch(fetchTaskQueue('pl1'));
    expect(mocked.getTaskQueue).toHaveBeenCalledWith('pl1');
    expect(store.getState().tasks.taskQueue).toEqual([{ key: 'task-q' }]);
  });

  it('fetchOverdueTasks stores overdue tasks', async () => {
    mocked.getOverdueTasks.mockResolvedValue([{ key: 'task-od' }] as never);
    const store = makeTasksStore();
    await store.dispatch(fetchOverdueTasks());
    expect(store.getState().tasks.overdueTasks).toEqual([{ key: 'task-od' }]);
  });
});
