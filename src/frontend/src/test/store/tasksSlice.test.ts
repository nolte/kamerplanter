import { describe, it, expect } from 'vitest';
import reducer, {
  clearCurrentTask,
  clearError,
  fetchWorkflows,
  deleteWorkflowThunk,
  fetchTaskTemplates,
  fetchTasks,
  fetchTask,
  fetchTaskQueue,
  fetchOverdueTasks,
} from '@/store/slices/tasksSlice';

const baseState = {
  workflows: [],
  taskTemplates: [],
  tasks: [],
  currentTask: null,
  taskQueue: [],
  overdueTasks: [],
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
    expect(state.error).toBe('Failed to load workflows');
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
    expect(state.error).toBe('Failed to load tasks');
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
    expect(state.error).toBe('Failed to load task queue');
  });

  it('fetchOverdueTasks.fulfilled stores overdue tasks', () => {
    const overdue = [{ key: 'task-2' }];
    const state = reducer(undefined, { type: fetchOverdueTasks.fulfilled.type, payload: overdue });
    expect(state.overdueTasks).toEqual(overdue);
  });
});
