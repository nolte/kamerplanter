import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import type { PayloadAction } from '@reduxjs/toolkit';
import type {
  TaskItem,
  TaskOrigin,
  TaskTemplate,
  WorkflowTemplate,
} from '@/api/types';
import { MACHINE_TASK_ORIGINS, PLANT_INSTANCE_ENTITY_TYPE } from '@/api/types';
import * as api from '@/api/endpoints/tasks';

/**
 * REQ-006: which tasks the user asked to see, by provenance. `machine` is a
 * *partition* over {@link MACHINE_TASK_ORIGINS} rather than one origin value —
 * see {@link originsFor}.
 */
export type OriginFilter = 'all' | 'machine' | 'user';

/**
 * What the task queue and the completed list are currently asking the server
 * for: which plant, which category, whose provenance — or the whole tenant.
 *
 * The scope lives in the store rather than travelling as a thunk argument, and
 * that is the point (#1484, #1503). Both lists are capped server-side — 200 rows
 * for the queue, 100 for the completed list — so narrowing them in the component
 * is not a filter but a guess about what the cap left behind. Reading the scope
 * from the state means a call site cannot pass the wrong one, or forget it:
 * there is no argument to get wrong, and a filter added to this object is asked
 * of the server by construction rather than by remembering to.
 */
export interface QueueScope {
  plantKey: string | null;
  category: string | null;
  origin: OriginFilter;
}

/** The whole tenant, every category, every origin. */
export const EMPTY_QUEUE_SCOPE: QueueScope = { plantKey: null, category: null, origin: 'all' };

/**
 * Structural comparison — the stamping below matches answers against the scope
 * they were fetched for, and a `!==` on an object would call every answer stale
 * because each patch produces a fresh object.
 */
export function sameQueueScope(a: QueueScope, b: QueueScope): boolean {
  return a.plantKey === b.plantKey && a.category === b.category && a.origin === b.origin;
}

/**
 * The wire form of {@link OriginFilter}: the repeated `origin` parameter, or
 * `undefined` for "every origin" (an *absent* predicate — a present but empty
 * list would mean "nothing matches").
 */
export function originsFor(origin: OriginFilter): readonly TaskOrigin[] | undefined {
  if (origin === 'user') return ['user'];
  if (origin === 'machine') return MACHINE_TASK_ORIGINS;
  return undefined;
}

/** A queue/completed answer, stamped with the scope it was fetched for. */
interface ScopedTasks {
  scope: QueueScope;
  tasks: TaskItem[];
}

/** A queue/completed failure, stamped the same way. */
interface ScopedFailure {
  scope: QueueScope;
  message: string;
}

/** The slice of the root state these thunks read their scope from. */
interface TasksRootState {
  tasks: TasksState;
}

function failureMessage(err: unknown): string {
  return err instanceof Error && err.message ? err.message : 'errors.loadFailed';
}

interface TasksState {
  workflows: WorkflowTemplate[];
  taskTemplates: TaskTemplate[];
  tasks: TaskItem[];
  currentTask: TaskItem | null;
  taskQueue: TaskItem[];
  overdueTasks: TaskItem[];
  completedTasks: TaskItem[];
  /** The scope both lists are asked for; see {@link QueueScope}. */
  queueScope: QueueScope;
  /** The scope the rows currently in `taskQueue` were fetched for. */
  taskQueueScope: QueueScope;
  /** The scope the rows currently in `completedTasks` were fetched for. */
  completedTasksScope: QueueScope;
  /**
   * Queue-only loading flag. `loading` is shared with the workflow and task
   * list thunks, so a page showing the queue could not tell whose request was
   * in flight — and the queue is the one list that now reloads on a filter pick.
   */
  queueLoading: boolean;
  queueError: string | null;
  /** True once a queue query has settled at least once, either way. */
  queueLoaded: boolean;
  completedTasksLoading: boolean;
  completedTasksError: string | null;
  loading: boolean;
  error: string | null;
}

const initialState: TasksState = {
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
  queueLoading: false,
  queueError: null,
  queueLoaded: false,
  completedTasksLoading: false,
  completedTasksError: null,
  loading: false,
  error: null,
};

// -- Workflow thunks --

export const fetchWorkflows = createAsyncThunk(
  'tasks/fetchWorkflows',
  async ({ offset, limit }: { offset?: number; limit?: number } = {}) => {
    return api.listWorkflows(offset, limit);
  },
);

export const fetchWorkflow = createAsyncThunk(
  'tasks/fetchWorkflow',
  async (key: string) => {
    return api.getWorkflow(key);
  },
);

export const deleteWorkflowThunk = createAsyncThunk(
  'tasks/deleteWorkflow',
  async (key: string) => {
    await api.deleteWorkflow(key);
    return key;
  },
);

// -- Task template thunks --

export const fetchTaskTemplates = createAsyncThunk(
  'tasks/fetchTaskTemplates',
  async (workflowKey: string) => {
    return api.listTaskTemplates(workflowKey);
  },
);

// -- Task thunks --

export const fetchTasks = createAsyncThunk(
  'tasks/fetchAll',
  async ({
    offset,
    limit,
    status,
    category,
    entityType,
    entityKey,
  }: {
    offset?: number;
    limit?: number;
    status?: string;
    category?: string;
    entityType?: string;
    entityKey?: string;
  } = {}) => {
    return api.listTasks(offset, limit, {
      status,
      category,
      entity_type: entityType,
      entity_key: entityKey,
    });
  },
);

export const fetchTask = createAsyncThunk(
  'tasks/fetchOne',
  async (key: string) => {
    return api.getTask(key);
  },
);

export const fetchTaskQueue = createAsyncThunk<
  ScopedTasks,
  void,
  { state: TasksRootState; rejectValue: ScopedFailure }
>('tasks/fetchQueue', async (_arg, { getState, rejectWithValue }) => {
  const scope = getState().tasks.queueScope;
  try {
    return {
      scope,
      tasks: await api.getTaskQueue({
        plantKey: scope.plantKey,
        category: scope.category,
        origin: originsFor(scope.origin),
      }),
    };
  } catch (err) {
    // The scope travels with the failure for the same reason it travels with
    // the answer: the reducer has to know which question this was an answer to.
    return rejectWithValue({ scope, message: failureMessage(err) });
  }
});

export const fetchOverdueTasks = createAsyncThunk(
  'tasks/fetchOverdue',
  async () => {
    return api.getOverdueTasks();
  },
);

export const fetchCompletedTasks = createAsyncThunk<
  ScopedTasks,
  void,
  { state: TasksRootState; rejectValue: ScopedFailure }
>('tasks/fetchCompleted', async (_arg, { getState, rejectWithValue }) => {
  const scope = getState().tasks.queueScope;
  try {
    // Every part of the scope belongs in the query, not in a filter over the
    // answer: past the 100-row cap the client had nothing left to filter (#1484,
    // #1503). A plant-scoped task is exactly the `entity_type`/`entity_key` pair
    // the list endpoint accepts; `category` and `origin` it accepts by name.
    const tasks = await api.listTasks(0, 100, {
      status: 'completed',
      ...(scope.category ? { category: scope.category } : {}),
      ...(originsFor(scope.origin) ? { origin: originsFor(scope.origin) } : {}),
      ...(scope.plantKey
        ? { entity_type: PLANT_INSTANCE_ENTITY_TYPE, entity_key: scope.plantKey }
        : {}),
    });
    return { scope, tasks };
  } catch (err) {
    return rejectWithValue({ scope, message: failureMessage(err) });
  }
});

const tasksSlice = createSlice({
  name: 'tasks',
  initialState,
  reducers: {
    clearCurrentTask(state) {
      state.currentTask = null;
    },
    clearError(state) {
      state.error = null;
    },
    /**
     * Replace what both lists ask the server for. The querying effect keys on
     * these values; the answers are matched against them, so a scope change
     * invalidates whatever is still in flight.
     *
     * A scope identical to the current one is a no-op rather than a fresh
     * object, so re-selecting the value already active does not re-query.
     */
    setQueueScope(state, action: PayloadAction<QueueScope>) {
      if (sameQueueScope(state.queueScope, action.payload)) return;
      state.queueScope = action.payload;
      state.queueError = null;
      state.completedTasksError = null;
    },
  },
  extraReducers: (builder) => {
    builder
      // Workflows
      .addCase(fetchWorkflows.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchWorkflows.fulfilled, (state, action) => {
        state.loading = false;
        state.workflows = action.payload;
      })
      .addCase(fetchWorkflows.rejected, (state, action) => {
        state.loading = false;
        state.error = action.error.message ?? 'errors.loadFailed';
      })
      .addCase(deleteWorkflowThunk.fulfilled, (state, action) => {
        state.workflows = state.workflows.filter((w) => w.key !== action.payload);
      })
      // Task templates
      .addCase(fetchTaskTemplates.fulfilled, (state, action) => {
        state.taskTemplates = action.payload;
      })
      // Tasks
      .addCase(fetchTasks.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchTasks.fulfilled, (state, action) => {
        state.loading = false;
        state.tasks = action.payload;
      })
      .addCase(fetchTasks.rejected, (state, action) => {
        state.loading = false;
        state.error = action.error.message ?? 'errors.loadFailed';
      })
      // Single task
      .addCase(fetchTask.fulfilled, (state, action) => {
        state.currentTask = action.payload;
      })
      // Task queue
      .addCase(fetchTaskQueue.pending, (state) => {
        state.queueLoading = true;
        state.queueError = null;
      })
      .addCase(fetchTaskQueue.fulfilled, (state, action) => {
        // An answer to a scope the user has since left is dropped, not applied.
        // Letting it win by arriving last is a real race and not a symmetric
        // one: the unscoped query is the slow branch (the backend resolves
        // blocking tasks per row over up to 200 rows), so "whole tenant → one
        // plant" reliably ended with the tenant's rows under the plant's chip.
        // Leaving `queueLoading` alone here is deliberate: the newer query is
        // still running, and it owns the flag.
        if (!sameQueueScope(action.payload.scope, state.queueScope)) return;
        state.queueLoading = false;
        state.queueLoaded = true;
        state.taskQueue = action.payload.tasks;
        state.taskQueueScope = action.payload.scope;
      })
      .addCase(fetchTaskQueue.rejected, (state, action) => {
        // `payload` is absent only when the thunk threw outside its own catch,
        // in which case there is no scope to compare and the failure is current.
        if (action.payload && !sameQueueScope(action.payload.scope, state.queueScope)) return;
        state.queueLoading = false;
        state.queueLoaded = true;
        state.queueError = action.payload?.message ?? failureMessage(action.error);
      })
      // Overdue tasks
      .addCase(fetchOverdueTasks.fulfilled, (state, action) => {
        state.overdueTasks = action.payload;
      })
      // Completed tasks (separate loading flag so the queue skeleton is not
      // triggered when the "show completed" toggle lazily loads this list)
      .addCase(fetchCompletedTasks.pending, (state) => {
        state.completedTasksLoading = true;
        state.completedTasksError = null;
      })
      .addCase(fetchCompletedTasks.fulfilled, (state, action) => {
        if (!sameQueueScope(action.payload.scope, state.queueScope)) return;
        state.completedTasksLoading = false;
        state.completedTasks = action.payload.tasks;
        state.completedTasksScope = action.payload.scope;
      })
      .addCase(fetchCompletedTasks.rejected, (state, action) => {
        if (action.payload && !sameQueueScope(action.payload.scope, state.queueScope)) return;
        state.completedTasksLoading = false;
        // Dropping this message turned every failure into "no completed tasks".
        state.completedTasksError = action.payload?.message ?? failureMessage(action.error);
      });
  },
});

export const { clearCurrentTask, clearError, setQueueScope } = tasksSlice.actions;
export default tasksSlice.reducer;
