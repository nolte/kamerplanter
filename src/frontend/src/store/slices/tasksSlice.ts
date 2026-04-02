import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import type {
  TaskItem,
  TaskTemplate,
  WorkflowTemplate,
} from '@/api/types';
import * as api from '@/api/endpoints/tasks';

interface TasksState {
  workflows: WorkflowTemplate[];
  taskTemplates: TaskTemplate[];
  tasks: TaskItem[];
  currentTask: TaskItem | null;
  taskQueue: TaskItem[];
  overdueTasks: TaskItem[];
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

export const fetchTaskQueue = createAsyncThunk(
  'tasks/fetchQueue',
  async (plantKey?: string) => {
    return api.getTaskQueue(plantKey);
  },
);

export const fetchOverdueTasks = createAsyncThunk(
  'tasks/fetchOverdue',
  async () => {
    return api.getOverdueTasks();
  },
);

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
        state.error = action.error.message ?? 'Failed to load workflows';
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
        state.error = action.error.message ?? 'Failed to load tasks';
      })
      // Single task
      .addCase(fetchTask.fulfilled, (state, action) => {
        state.currentTask = action.payload;
      })
      // Task queue
      .addCase(fetchTaskQueue.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchTaskQueue.fulfilled, (state, action) => {
        state.loading = false;
        state.taskQueue = action.payload;
      })
      .addCase(fetchTaskQueue.rejected, (state, action) => {
        state.loading = false;
        state.error = action.error.message ?? 'Failed to load task queue';
      })
      // Overdue tasks
      .addCase(fetchOverdueTasks.fulfilled, (state, action) => {
        state.overdueTasks = action.payload;
      });
  },
});

export const { clearCurrentTask, clearError } = tasksSlice.actions;
export default tasksSlice.reducer;
