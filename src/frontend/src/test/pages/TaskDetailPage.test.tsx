import { cleanup, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { http, HttpResponse } from 'msw';
import i18n from 'i18next';
import { renderWithProviders } from '../helpers';
import { server } from '../mocks/server';
import type { TaskItem, TaskComment, TaskAuditEntry } from '@/api/types';

const mockNavigate = vi.fn();
vi.mock('react-router-dom', async (orig) => {
  const actual = await orig<typeof import('react-router-dom')>();
  return { ...actual, useParams: () => ({ key: 'task-1' }), useNavigate: () => mockNavigate };
});

import TaskDetailPage from '@/pages/aufgaben/TaskDetailPage';

const TASK = '/api/v1/t/test-tenant/tasks';
const TASK_URL = `${TASK}/:key`;

function makeTask(overrides: Partial<TaskItem> = {}): TaskItem {
  return {
    key: 'task-1',
    name: 'Water plant',
    name_de: 'Pflanze giessen',
    instruction: 'Give 1L of water.',
    instruction_de: 'Gib 1L Wasser.',
    category: 'maintenance',
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

function makeComment(overrides: Partial<TaskComment> = {}): TaskComment {
  return {
    key: 'comment-1',
    task_key: 'task-1',
    comment_text: 'Looks healthy',
    created_by: 'demo',
    created_at: '2024-02-01T09:00:00Z',
    updated_at: null,
    ...overrides,
  };
}

function makeAudit(overrides: Partial<TaskAuditEntry> = {}): TaskAuditEntry {
  return {
    key: 'audit-1',
    task_key: 'task-1',
    changed_at: '2024-02-01T10:00:00Z',
    changed_by: 'demo',
    action: 'updated',
    field: 'priority',
    old_value: 'low',
    new_value: 'high',
    ...overrides,
  };
}

/** Records every mutation the page performs so tests can assert on the backend contract. */
interface TaskSpy {
  put?: Record<string, unknown>;
  deleted?: boolean;
  started?: boolean;
  completed?: Record<string, unknown>;
  skipped?: boolean;
  cloned?: boolean;
  reopened?: boolean;
  commentCreated?: string;
  commentUpdated?: string;
  commentDeleted?: string;
}

/**
 * Register the full task-detail endpoint surface with sensible defaults, wiring
 * every mutation into {@link spy}. Individual fields let a test seed the loaded
 * task, its comments and its history.
 */
function useTaskHandlers(
  spy: TaskSpy,
  {
    task = makeTask(),
    comments = [] as TaskComment[],
    history = [] as TaskAuditEntry[],
  }: { task?: TaskItem; comments?: TaskComment[]; history?: TaskAuditEntry[] } = {},
) {
  server.use(
    http.get(`${TASK_URL}/comments`, () => HttpResponse.json(comments)),
    http.get(`${TASK_URL}/history`, () => HttpResponse.json(history)),
    http.get(TASK_URL, () => HttpResponse.json(task)),
    http.put(`${TASK_URL}/comments/:ck`, async ({ request, params }) => {
      const body = (await request.json()) as { comment_text: string };
      spy.commentUpdated = body.comment_text;
      return HttpResponse.json(makeComment({ key: params.ck as string, comment_text: body.comment_text }));
    }),
    http.delete(`${TASK_URL}/comments/:ck`, () => {
      spy.commentDeleted = 'yes';
      return new HttpResponse(null, { status: 204 });
    }),
    http.post(`${TASK_URL}/comments`, async ({ request }) => {
      const body = (await request.json()) as { comment_text: string };
      spy.commentCreated = body.comment_text;
      return HttpResponse.json(makeComment({ key: 'comment-new', comment_text: body.comment_text }));
    }),
    http.put(TASK_URL, async ({ request }) => {
      spy.put = (await request.json()) as Record<string, unknown>;
      return HttpResponse.json({ ...task, ...spy.put });
    }),
    http.delete(TASK_URL, () => {
      spy.deleted = true;
      return new HttpResponse(null, { status: 204 });
    }),
    http.post(`${TASK_URL}/start`, () => {
      spy.started = true;
      return HttpResponse.json(makeTask({ ...task, status: 'in_progress', started_at: '2024-02-01T00:00:00Z' }));
    }),
    http.post(`${TASK_URL}/complete`, async ({ request }) => {
      spy.completed = (await request.json()) as Record<string, unknown>;
      return HttpResponse.json(makeTask({ ...task, status: 'completed' }));
    }),
    http.post(`${TASK_URL}/skip`, () => {
      spy.skipped = true;
      return HttpResponse.json(makeTask({ ...task, status: 'skipped' }));
    }),
    http.post(`${TASK_URL}/clone`, () => {
      spy.cloned = true;
      return HttpResponse.json(makeTask({ key: 'task-2' }));
    }),
    http.post(`${TASK_URL}/reopen`, () => {
      spy.reopened = true;
      return HttpResponse.json(makeTask({ ...task, status: 'pending' }));
    }),
  );
}

describe('TaskDetailPage — rendering & views', () => {
  let spy: TaskSpy;
  beforeEach(() => {
    i18n.changeLanguage('de');
    mockNavigate.mockClear();
    spy = {};
  });
  afterEach(() => {
    // Unmount before resetting the language: the file's afterEach runs before
    // testing-library's auto-cleanup (LIFO), so an i18n reset here would
    // otherwise re-render every still-mounted useTranslation() consumer
    // outside act(). Unmounting first makes the reset touch nothing.
    cleanup();
    i18n.changeLanguage('en');
  });

  it('shows a loading skeleton while the task is being fetched', () => {
    server.use(http.get(TASK_URL, () => new Promise(() => {})));
    renderWithProviders(<TaskDetailPage />, { route: '/aufgaben/task-1' });
    expect(screen.getByTestId('loading-skeleton')).toBeInTheDocument();
  });

  it('renders an error display when loading fails with a server error', async () => {
    server.use(http.get(TASK_URL, () => new HttpResponse(null, { status: 500 })));
    renderWithProviders(<TaskDetailPage />, { route: '/aufgaben/task-1' });
    expect(await screen.findByTestId('error-display')).toBeInTheDocument();
  });

  it('renders a rich detail tab with metadata, instruction, tags and checklist', async () => {
    useTaskHandlers(spy, {
      task: makeTask({
        entity_type: 'plant_instance',
        entity_key: 'plant-1',
        due_date: '2026-07-20T00:00:00Z',
        estimated_duration_minutes: 15,
        actual_duration_minutes: 12,
        assigned_to_user_key: 'user-9',
        recurrence_rule: 'FREQ=WEEKLY',
        started_at: '2026-07-01T08:00:00Z',
        completed_at: null,
        activity_key: 'act-1',
        tags: ['urgent'],
        checklist: [
          { text: 'Check soil moisture', done: false, order: 0 },
          { text: 'Refill can', done: true, order: 1 },
        ],
      }),
    });
    renderWithProviders(<TaskDetailPage />, { route: '/aufgaben/task-1' });

    expect(await screen.findByTestId('task-detail-page')).toBeInTheDocument();
    expect(screen.getByText('Pflanze giessen')).toBeInTheDocument();
    // Metadata + checklist + tag are all observable.
    expect(screen.getByText('urgent')).toBeInTheDocument();
    expect(screen.getByText('Check soil moisture')).toBeInTheDocument();
    // The instruction callout resolves the plain instruction text.
    expect(screen.getByText('Gib 1L Wasser.')).toBeInTheDocument();
    // The plant link resolves the plant display name once the plant loads.
    expect(await screen.findByTestId('plant-link')).toHaveTextContent('Big Red');
  });

  it('renders every tab in a scrollable tab bar so none is clipped on mobile', async () => {
    useTaskHandlers(spy);
    renderWithProviders(<TaskDetailPage />, { route: '/aufgaben/task-1' });
    await screen.findByTestId('task-detail-page');

    const tablist = screen.getByRole('tablist', { name: i18n.t('pages.tasks.title') });
    // All five tabs of an actionable task are present, including the trailing
    // ones that a fixed-width tab bar clipped out of the 393px viewport.
    expect(within(tablist).getAllByRole('tab')).toHaveLength(5);
    for (const label of [
      i18n.t('pages.tasks.tabDetails'),
      i18n.t('pages.tasks.tabComplete'),
      i18n.t('pages.tasks.tabComments'),
      i18n.t('pages.tasks.tabHistory'),
      i18n.t('common.edit'),
    ]) {
      expect(within(tablist).getByRole('tab', { name: label })).toBeInTheDocument();
    }
    // The bar scrolls horizontally instead of clipping — the regression guard
    // for the mobile reachability defect.
    const scroller = tablist.closest('.MuiTabs-root')?.querySelector('.MuiTabs-scroller');
    expect(scroller?.className).toContain('MuiTabs-scrollableX');
  });

  it('resolves a legacy care-instruction key to a readable label', async () => {
    useTaskHandlers(spy, {
      task: makeTask({ instruction: 'care:watering:5', instruction_de: '', category: 'care_reminder' }),
    });
    renderWithProviders(<TaskDetailPage />, { route: '/aufgaben/task-1' });
    await screen.findByTestId('task-detail-page');
    // The raw "care:<type>:<id>" key is never shown to the user; it is resolved
    // to a readable label instead.
    expect(screen.queryByText('care:watering:5')).toBeNull();
    // The care-reminder source label appears (both the category chip and the
    // source cell render it, hence getAllByText).
    expect(screen.getAllByText(i18n.t('pages.tasks.sourceCareReminder')).length).toBeGreaterThan(0);
  });

  it('shows the English title in the English locale', async () => {
    i18n.changeLanguage('en');
    useTaskHandlers(spy);
    renderWithProviders(<TaskDetailPage />, { route: '/aufgaben/task-1' });
    await screen.findByTestId('task-detail-page');
    expect(screen.getByText('Water plant')).toBeInTheDocument();
  });

  it('renders completion notes and ratings for a completed task', async () => {
    useTaskHandlers(spy, {
      task: makeTask({
        status: 'completed',
        completed_at: '2026-07-02T10:00:00Z',
        completion_notes: 'All done and watered.',
        difficulty_rating: 2,
        quality_rating: 5,
        actual_duration_minutes: 8,
      }),
    });
    renderWithProviders(<TaskDetailPage />, { route: '/aufgaben/task-1' });
    await screen.findByTestId('task-detail-page');

    expect(screen.getByText('All done and watered.')).toBeInTheDocument();
    expect(screen.getByText('2 / 5')).toBeInTheDocument();
    expect(screen.getByText('5 / 5')).toBeInTheDocument();
  });
});

describe('TaskDetailPage — status actions', () => {
  let spy: TaskSpy;
  beforeEach(() => {
    i18n.changeLanguage('de');
    mockNavigate.mockClear();
    spy = {};
  });
  afterEach(() => {
    cleanup();
    i18n.changeLanguage('en');
  });

  it('starts a pending task', async () => {
    useTaskHandlers(spy);
    const user = userEvent.setup();
    renderWithProviders(<TaskDetailPage />, { route: '/aufgaben/task-1' });
    await screen.findByTestId('task-detail-page');

    await user.click(screen.getByTestId('start-task-button'));
    await waitFor(() => expect(spy.started).toBe(true));
  });

  it('skips an actionable task', async () => {
    useTaskHandlers(spy);
    const user = userEvent.setup();
    renderWithProviders(<TaskDetailPage />, { route: '/aufgaben/task-1' });
    await screen.findByTestId('task-detail-page');

    await user.click(screen.getByTestId('skip-task-button'));
    await waitFor(() => expect(spy.skipped).toBe(true));
  });

  it('clones a task and navigates to the clone', async () => {
    useTaskHandlers(spy);
    const user = userEvent.setup();
    renderWithProviders(<TaskDetailPage />, { route: '/aufgaben/task-1' });
    await screen.findByTestId('task-detail-page');

    await user.click(screen.getByTestId('clone-task-button'));
    await waitFor(() => expect(spy.cloned).toBe(true));
    expect(mockNavigate).toHaveBeenCalledWith('/aufgaben/task-2');
  });

  it('reopens a completed task', async () => {
    useTaskHandlers(spy, { task: makeTask({ status: 'completed', completed_at: '2026-07-01T00:00:00Z' }) });
    const user = userEvent.setup();
    renderWithProviders(<TaskDetailPage />, { route: '/aufgaben/task-1' });
    await screen.findByTestId('task-detail-page');

    await user.click(screen.getByTestId('reopen-task-button'));
    await waitFor(() => expect(spy.reopened).toBe(true));
  });

  it('surfaces an error and stays put when an action fails', async () => {
    useTaskHandlers(spy);
    server.use(http.post(`${TASK_URL}/start`, () => new HttpResponse(null, { status: 500 })));
    const user = userEvent.setup();
    renderWithProviders(<TaskDetailPage />, { route: '/aufgaben/task-1' });
    await screen.findByTestId('task-detail-page');

    await user.click(screen.getByTestId('start-task-button'));
    expect(await screen.findByText(i18n.t('errors.server'))).toBeInTheDocument();
  });
});

describe('TaskDetailPage — checklist', () => {
  let spy: TaskSpy;
  beforeEach(() => {
    i18n.changeLanguage('de');
    mockNavigate.mockClear();
    spy = {};
  });
  afterEach(() => {
    cleanup();
    i18n.changeLanguage('en');
  });

  it('toggles a checklist item and persists the change', async () => {
    useTaskHandlers(spy, {
      task: makeTask({ checklist: [{ text: 'Check soil', done: false, order: 0 }] }),
    });
    const user = userEvent.setup();
    renderWithProviders(<TaskDetailPage />, { route: '/aufgaben/task-1' });
    await screen.findByTestId('task-detail-page');

    await user.click(screen.getByRole('checkbox'));
    await waitFor(() => expect(spy.put).toBeTruthy());
    expect((spy.put!.checklist as Array<{ done: boolean }>)[0].done).toBe(true);
  });

  it('adds a checklist item from the input field', async () => {
    useTaskHandlers(spy, { task: makeTask({ checklist: [] }) });
    const user = userEvent.setup();
    renderWithProviders(<TaskDetailPage />, { route: '/aufgaben/task-1' });
    await screen.findByTestId('task-detail-page');

    const input = screen.getByPlaceholderText(i18n.t('pages.tasks.addChecklistItem'));
    await user.type(input, 'Fertilize{Enter}');
    await waitFor(() => expect(spy.put).toBeTruthy());
    const checklist = spy.put!.checklist as Array<{ text: string }>;
    expect(checklist[checklist.length - 1].text).toBe('Fertilize');
  });
});

describe('TaskDetailPage — complete & edit tabs', () => {
  let spy: TaskSpy;
  beforeEach(() => {
    i18n.changeLanguage('de');
    mockNavigate.mockClear();
    spy = {};
  });
  afterEach(() => {
    cleanup();
    i18n.changeLanguage('en');
  });

  it('submits the completion form', async () => {
    useTaskHandlers(spy);
    const user = userEvent.setup();
    renderWithProviders(<TaskDetailPage />, { route: '/aufgaben/task-1#complete' });
    await screen.findByTestId('task-detail-page');

    await user.click(await screen.findByTestId('complete-task-submit'));
    await waitFor(() => expect(spy.completed).toBeTruthy());
  });

  it('disables the completion submit while a required photo is missing', async () => {
    useTaskHandlers(spy, { task: makeTask({ requires_photo: true, photo_refs: [] }) });
    renderWithProviders(<TaskDetailPage />, { route: '/aufgaben/task-1#complete' });
    await screen.findByTestId('task-detail-page');

    expect(screen.getByText(i18n.t('pages.tasks.photoRequired'))).toBeInTheDocument();
    expect(await screen.findByTestId('complete-task-submit')).toBeDisabled();
  });

  it('picks a difficulty and quality rating via the segmented selector and submits them', async () => {
    useTaskHandlers(spy);
    const user = userEvent.setup();
    renderWithProviders(<TaskDetailPage />, { route: '/aufgaben/task-1#complete' });
    await screen.findByTestId('task-detail-page');

    await user.click(screen.getByTestId('task-difficulty-rating-2'));
    await user.click(screen.getByTestId('task-quality-rating-5'));
    expect(screen.getByTestId('task-difficulty-rating-status')).toHaveTextContent(
      i18n.t('pages.tasks.ratingSelectedValue', { value: 2 }),
    );
    expect(screen.getByTestId('task-quality-rating-status')).toHaveTextContent(
      i18n.t('pages.tasks.ratingSelectedValue', { value: 5 }),
    );

    await user.click(screen.getByTestId('complete-task-submit'));
    await waitFor(() => expect(spy.completed).toBeTruthy());
    expect(spy.completed!.difficulty_rating).toBe(2);
    expect(spy.completed!.quality_rating).toBe(5);
  });

  it('clears a selected rating back to null via the reset action', async () => {
    useTaskHandlers(spy);
    const user = userEvent.setup();
    renderWithProviders(<TaskDetailPage />, { route: '/aufgaben/task-1#complete' });
    await screen.findByTestId('task-detail-page');

    await user.click(screen.getByTestId('task-difficulty-rating-3'));
    expect(screen.getByTestId('task-difficulty-rating-status')).toHaveTextContent(
      i18n.t('pages.tasks.ratingSelectedValue', { value: 3 }),
    );

    await user.click(screen.getByTestId('task-difficulty-rating-clear'));
    expect(screen.getByTestId('task-difficulty-rating-status')).toHaveTextContent(
      i18n.t('pages.tasks.ratingNotRated'),
    );

    await user.click(screen.getByTestId('complete-task-submit'));
    await waitFor(() => expect(spy.completed).toBeTruthy());
    expect(spy.completed!.difficulty_rating).toBeNull();
  });

  it('renders the zod error inline when a natively-constrained edit field is invalid', async () => {
    // Regression guard: the edit form must carry `noValidate`. Without it the
    // browser's constraint validation (the `required` name field) aborts the
    // submission before any `submit` event fires — zod never runs, no MUI
    // helper text renders, and the user is left with a transient native bubble
    // and a silently unsaved form. jsdom implements the same interactive
    // validation, so dropping `noValidate` makes this test fail.
    useTaskHandlers(spy);
    const user = userEvent.setup();
    renderWithProviders(<TaskDetailPage />, { route: '/aufgaben/task-1#edit' });
    await screen.findByTestId('task-detail-page');

    const nameField = await screen.findByTestId('form-field-name');
    await user.clear(await screen.findByDisplayValue('Water plant'));
    await user.click(screen.getByTestId('form-submit-button'));

    // zod rejected the empty name and the rejection is visible on the field.
    await waitFor(() =>
      expect(nameField.querySelector('.MuiFormHelperText-root.Mui-error')).not.toBeNull(),
    );
    expect(spy.put).toBeUndefined();
  });

  it('saves edits from the edit tab once the form is dirty', async () => {
    useTaskHandlers(spy);
    const user = userEvent.setup();
    renderWithProviders(<TaskDetailPage />, { route: '/aufgaben/task-1#edit' });
    await screen.findByTestId('task-detail-page');

    const nameField = await screen.findByDisplayValue('Water plant');
    await user.type(nameField, ' now');
    await user.click(screen.getByTestId('form-submit-button'));

    await waitFor(() => expect(spy.put).toBeTruthy());
    expect(spy.put!.name).toBe('Water plant now');
  });
});

describe('TaskDetailPage — comments & history tabs', () => {
  let spy: TaskSpy;
  beforeEach(() => {
    i18n.changeLanguage('de');
    mockNavigate.mockClear();
    spy = {};
  });
  afterEach(() => {
    cleanup();
    i18n.changeLanguage('en');
  });

  it('lists comments and adds a new one', async () => {
    useTaskHandlers(spy, { comments: [makeComment()] });
    const user = userEvent.setup();
    renderWithProviders(<TaskDetailPage />, { route: '/aufgaben/task-1#comments' });
    await screen.findByTestId('task-detail-page');

    expect(await screen.findByText('Looks healthy')).toBeInTheDocument();

    const input = screen.getByPlaceholderText(i18n.t('pages.tasks.addComment'));
    await user.type(input, 'Watered today');
    await user.click(screen.getByRole('button', { name: i18n.t('pages.tasks.send') }));
    await waitFor(() => expect(spy.commentCreated).toBe('Watered today'));
  });

  it('edits an existing comment', async () => {
    useTaskHandlers(spy, { comments: [makeComment()] });
    const user = userEvent.setup();
    renderWithProviders(<TaskDetailPage />, { route: '/aufgaben/task-1#comments' });
    await screen.findByText('Looks healthy');

    await user.click(screen.getByTestId('EditIcon').closest('button')!);
    const editField = screen.getByDisplayValue('Looks healthy');
    await user.clear(editField);
    await user.type(editField, 'Edited note');
    await user.click(screen.getByRole('button', { name: i18n.t('common.save') }));
    await waitFor(() => expect(spy.commentUpdated).toBe('Edited note'));
  });

  it('deletes a comment', async () => {
    useTaskHandlers(spy, { comments: [makeComment()] });
    const user = userEvent.setup();
    renderWithProviders(<TaskDetailPage />, { route: '/aufgaben/task-1#comments' });
    const commentPaper = (await screen.findByText('Looks healthy')).closest('.MuiPaper-root') as HTMLElement;

    await user.click(within(commentPaper).getByTestId('DeleteIcon').closest('button')!);
    await waitFor(() => expect(spy.commentDeleted).toBe('yes'));
  });

  it('renders the history tab entries', async () => {
    useTaskHandlers(spy, { history: [makeAudit()] });
    renderWithProviders(<TaskDetailPage />, { route: '/aufgaben/task-1#history' });
    await screen.findByTestId('task-detail-page');
    expect(await screen.findByText('updated')).toBeInTheDocument();
  });

  it('shows the empty state on the comments tab when there are none', async () => {
    useTaskHandlers(spy, { comments: [] });
    renderWithProviders(<TaskDetailPage />, { route: '/aufgaben/task-1#comments' });
    await screen.findByTestId('task-detail-page');
    expect(await screen.findByText(i18n.t('pages.tasks.noComments'))).toBeInTheDocument();
  });

  it('shows the empty state on the history tab when there are none', async () => {
    useTaskHandlers(spy, { history: [] });
    renderWithProviders(<TaskDetailPage />, { route: '/aufgaben/task-1#history' });
    await screen.findByTestId('task-detail-page');
    expect(await screen.findByText(i18n.t('pages.tasks.noHistory'))).toBeInTheDocument();
  });
});

describe('TaskDetailPage — delete flow', () => {
  let spy: TaskSpy;
  beforeEach(() => {
    i18n.changeLanguage('de');
    mockNavigate.mockClear();
    spy = {};
  });
  afterEach(() => {
    cleanup();
    i18n.changeLanguage('en');
  });

  it('deletes the task and navigates back to the queue', async () => {
    useTaskHandlers(spy);
    const user = userEvent.setup();
    renderWithProviders(<TaskDetailPage />, { route: '/aufgaben/task-1' });

    await screen.findByTestId('task-detail-page');
    await user.click(screen.getByRole('button', { name: i18n.t('common.delete') }));
    await user.click(await screen.findByTestId('confirm-dialog-confirm'));

    await waitFor(() => expect(spy.deleted).toBe(true));
    await waitFor(() => expect(mockNavigate).toHaveBeenCalledWith('/aufgaben/queue'));
  });

  it('shows the pending state on the confirm dialog while the delete is in flight', async () => {
    useTaskHandlers(spy);
    let release!: () => void;
    server.use(
      http.delete(TASK_URL, async () => {
        await new Promise<void>((res) => {
          release = res;
        });
        return new HttpResponse(null, { status: 204 });
      }),
    );
    const user = userEvent.setup();
    renderWithProviders(<TaskDetailPage />, { route: '/aufgaben/task-1' });

    await screen.findByTestId('task-detail-page');
    await user.click(screen.getByRole('button', { name: i18n.t('common.delete') }));
    await user.click(await screen.findByTestId('confirm-dialog-confirm'));

    await waitFor(() => expect(screen.getByTestId('confirm-dialog-confirm')).toBeDisabled());
    expect(screen.getByTestId('confirm-dialog-live-region')).toHaveTextContent(
      i18n.t('common.processing'),
    );

    release();
    await waitFor(() => expect(mockNavigate).toHaveBeenCalledWith('/aufgaben/queue'));
  });

  it('surfaces an error and does not navigate when the delete fails', async () => {
    useTaskHandlers(spy);
    server.use(http.delete(TASK_URL, () => new HttpResponse(null, { status: 500 })));
    const user = userEvent.setup();
    renderWithProviders(<TaskDetailPage />, { route: '/aufgaben/task-1' });

    await screen.findByTestId('task-detail-page');
    await user.click(screen.getByRole('button', { name: i18n.t('common.delete') }));
    await user.click(await screen.findByTestId('confirm-dialog-confirm'));

    expect(await screen.findByText(i18n.t('errors.server'))).toBeInTheDocument();
    expect(mockNavigate).not.toHaveBeenCalledWith('/aufgaben/queue');
  });
});

describe('TaskDetailPage — header action group', () => {
  let spy: TaskSpy;
  beforeEach(() => {
    i18n.changeLanguage('de');
    mockNavigate.mockClear();
    spy = {};
  });
  afterEach(() => {
    cleanup();
    i18n.changeLanguage('en');
  });

  it('keeps the action group shrinkable and wrapping so no action leaves the viewport', async () => {
    useTaskHandlers(spy);
    renderWithProviders(<TaskDetailPage />, { route: '/aufgaben/task-1' });
    await screen.findByTestId('task-detail-page');

    const startButton = screen.getByTestId('start-task-button');
    const group = startButton.parentElement as HTMLElement;

    // Every header action lives in this one group — including the destructive
    // one, which was the first to be pushed out of a 393px viewport.
    for (const testId of ['start-task-button', 'skip-task-button', 'clone-task-button', 'delete-task-button']) {
      expect(group).toContainElement(screen.getByTestId(testId));
    }

    // Regression guard: the group used to be `flexShrink: 0`, which sizes a flex
    // item to its max-content width — the four/five buttons then formed one
    // unbreakable row and the trailing ones rendered outside the viewport
    // (UI-NFR-001 R-005/R-006, UI-NFR-021 R-023).
    const groupStyle = window.getComputedStyle(group);
    expect(groupStyle.flexShrink).not.toBe('0');
    expect(groupStyle.flexWrap).toBe('wrap');
    // Stack's default margin-based spacing collapses once lines wrap, so the
    // group must use gap-based spacing.
    expect(groupStyle.gap).not.toBe('');
    expect(groupStyle.gap).not.toBe('normal');
  });

  it('exposes the reopen action inside the same wrapping group on a completed task', async () => {
    useTaskHandlers(spy, { task: makeTask({ status: 'completed' }) });
    renderWithProviders(<TaskDetailPage />, { route: '/aufgaben/task-1' });
    await screen.findByTestId('task-detail-page');

    const reopenButton = screen.getByTestId('reopen-task-button');
    const group = reopenButton.parentElement as HTMLElement;
    expect(group).toContainElement(screen.getByTestId('delete-task-button'));
    expect(window.getComputedStyle(group).flexWrap).toBe('wrap');
  });

  it('addresses the delete action by a stable test id, like its siblings', async () => {
    useTaskHandlers(spy);
    const user = userEvent.setup();
    renderWithProviders(<TaskDetailPage />, { route: '/aufgaben/task-1' });
    await screen.findByTestId('task-detail-page');

    // The delete action was the only header action without a test hook, which
    // forced consumers to select it by MUI class name plus translated label.
    const deleteButton = screen.getByTestId('delete-task-button');
    expect(deleteButton).toHaveAccessibleName(i18n.t('common.delete'));

    await user.click(deleteButton);
    expect(await screen.findByTestId('confirm-dialog-confirm')).toBeInTheDocument();
  });
});
