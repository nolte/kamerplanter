import { describe, it, expect, beforeEach, vi } from 'vitest';
import { screen, within, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import i18n from 'i18next';
import { renderWithProviders } from '@/test/helpers';
import type { ActivityPlanResponse, TaskItem, TaskTemplateResponse } from '@/api/types';

/**
 * REQ-006 — ActivityPlanTab. Two mutually-exclusive views: the assigned-tasks
 * view (when a run/plant already has tasks) and the plan-generation fallback.
 * The endpoint modules are mocked so both flows resolve deterministically.
 */

const activityPlanApi = vi.hoisted(() => ({
  generatePlan: vi.fn(),
  applyPlan: vi.fn(),
  updateTaskTemplate: vi.fn(),
  deleteTaskTemplate: vi.fn(),
}));
vi.mock('@/api/endpoints/activityPlans', () => activityPlanApi);

const taskApi = vi.hoisted(() => ({
  listTasks: vi.fn(),
}));
vi.mock('@/api/endpoints/tasks', () => taskApi);

import ActivityPlanTab from '@/pages/durchlaeufe/ActivityPlanTab';

// ── Fixtures ────────────────────────────────────────────────────────

function template(overrides: Partial<TaskTemplateResponse> = {}): TaskTemplateResponse {
  return {
    key: 'tt-1',
    name: 'Topping',
    name_de: 'Entspitzen',
    instruction: 'Cut the top',
    instruction_de: 'Spitze kappen',
    trigger_phase: 'vegetative',
    phase_display_name: 'Vegetativ',
    phase_duration_days: 28,
    phase_stress_tolerance: 'medium',
    days_offset: 5,
    rationale: 'Promotes bushing',
    rationale_de: 'Fördert Verzweigung',
    category: 'training_hst',
    stress_level: 'low',
    skill_level: 'intermediate',
    estimated_duration_minutes: 15,
    tools_required: [],
    recovery_days: 3,
    is_optional: false,
    enabled: true,
    activity_key: null,
    description: '',
    description_de: '',
    ...overrides,
  };
}

function plan(overrides: Partial<ActivityPlanResponse> = {}): ActivityPlanResponse {
  return {
    workflow_template_key: 'wf-1',
    name: 'Cannabis Trainingsplan',
    species_name: 'Cannabis',
    species_key: 'sp-1',
    auto_generated: true,
    growth_system: null,
    skill_level_filter: null,
    total_activities: 2,
    total_duration_days: 60,
    // Default: already the caller's own plan. The shared-template case gets its
    // own describe block below, because it behaves differently on write (#1003).
    is_shared_template: false,
    templates: [
      template({ key: 'tt-veg', trigger_phase: 'vegetative', phase_display_name: 'Vegetativ' }),
      template({
        key: 'tt-flower',
        name: 'Defoliation',
        name_de: 'Entlauben',
        trigger_phase: 'flowering',
        phase_display_name: 'Blüte',
        phase_stress_tolerance: 'low',
        stress_level: 'high', // exceeds tolerance → stress warning branch
        is_optional: true,
        tools_required: ['scissors'],
        description: 'Remove fan leaves',
        description_de: 'Große Blätter entfernen',
      }),
    ],
    ...overrides,
  };
}

function task(overrides: Partial<TaskItem> = {}): TaskItem {
  return {
    key: 'task-1',
    name: 'Topping',
    name_de: 'Entspitzen',
    instruction: 'Cut the top',
    instruction_de: 'Spitze kappen',
    category: 'training_hst',
    entity_key: 'run-1',
    entity_type: 'planting_run',
    due_date: null,
    scheduled_time: null,
    status: 'completed',
    priority: 'normal',
    skill_level: 'intermediate',
    stress_level: 'low',
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
    origin: 'user',
    source: '',
    source_run_ref: null,
    external_ref: null,
    parent_recurring_task_key: null,
    trigger_phase: 'vegetative',
    trigger_phase_override: null,
    reopened_at: null,
    reopened_from_status: null,
    started_at: null,
    completed_at: null,
    activity_key: null,
    template_key: 'tt-veg',
    workflow_execution_key: null,
    watering_event_key: null,
    created_at: null,
    updated_at: null,
    ...overrides,
  };
}

beforeEach(() => {
  vi.clearAllMocks();
  i18n.changeLanguage('de');
  taskApi.listTasks.mockResolvedValue([]);
});

// ── Plan-generation fallback ────────────────────────────────────────

describe('ActivityPlanTab — plan generation fallback', () => {
  it('shows the generate prompt when there are no assigned tasks', async () => {
    renderWithProviders(<ActivityPlanTab speciesKey="sp-1" />);
    expect(
      await screen.findByTestId('generate-activity-plan-button'),
    ).toBeInTheDocument();
    expect(screen.getByText(i18n.t('pages.activityPlan.noAssignedTasks'))).toBeInTheDocument();
  });

  it('generates a plan and renders phase tables, then toggles / edits / removes templates', async () => {
    activityPlanApi.generatePlan.mockResolvedValue(plan());
    activityPlanApi.updateTaskTemplate.mockImplementation((key: string, body: { enabled?: boolean; days_offset?: number }) => {
      const base = template({ key });
      return Promise.resolve({ ...base, ...body });
    });
    activityPlanApi.deleteTaskTemplate.mockResolvedValue(undefined);

    const user = userEvent.setup();
    renderWithProviders(<ActivityPlanTab speciesKey="sp-1" runKey="run-1" />);

    await user.click(await screen.findByTestId('generate-activity-plan-button'));

    // Plan header + both phase accordions.
    expect(await screen.findByText('Cannabis Trainingsplan')).toBeInTheDocument();
    expect(screen.getByText('Vegetativ')).toBeInTheDocument();
    expect(screen.getByText('Blüte')).toBeInTheDocument();
    expect(activityPlanApi.generatePlan).toHaveBeenCalledWith(
      expect.objectContaining({ species_key: 'sp-1', force_regenerate: false }),
    );

    // Toggle a template's enabled switch.
    const vegRow = screen.getByText('Entspitzen').closest('tr') as HTMLElement;
    await user.click(within(vegRow).getByRole('switch'));
    await waitFor(() => expect(activityPlanApi.updateTaskTemplate).toHaveBeenCalled());

    // Edit the day offset.
    const offsetInput = within(vegRow).getByRole('spinbutton') as HTMLInputElement;
    await user.clear(offsetInput);
    await user.type(offsetInput, '9');
    await waitFor(() =>
      expect(
        activityPlanApi.updateTaskTemplate.mock.calls.some(
          (c) => c[1] && typeof c[1].days_offset === 'number',
        ),
      ).toBe(true),
    );

    // Remove a template.
    await user.click(
      within(vegRow).getByRole('button', { name: i18n.t('pages.activityPlan.removeActivity') }),
    );
    await waitFor(() => expect(activityPlanApi.deleteTaskTemplate).toHaveBeenCalledWith('tt-veg'));
  });

  it('applies the plan and shows the success notification', async () => {
    activityPlanApi.generatePlan.mockResolvedValue(plan());
    activityPlanApi.applyPlan.mockResolvedValue({ total_tasks: 4, created_count: 4 });

    const user = userEvent.setup();
    renderWithProviders(<ActivityPlanTab speciesKey="sp-1" runKey="run-1" />);

    await user.click(await screen.findByTestId('generate-activity-plan-button'));
    await screen.findByText('Cannabis Trainingsplan');

    // The apply button carries the run label (runKey present).
    await user.click(screen.getByRole('button', { name: i18n.t('pages.activityPlan.applyToRun') }));

    await waitFor(() =>
      expect(activityPlanApi.applyPlan).toHaveBeenCalledWith(
        expect.objectContaining({ workflow_template_key: 'wf-1', run_key: 'run-1' }),
      ),
    );
    // Success snackbar with the interpolated count.
    expect(
      await screen.findByText(i18n.t('pages.activityPlan.successMessage', { count: 4 })),
    ).toBeInTheDocument();
  });

  it('falls back to the generate prompt when task loading fails', async () => {
    taskApi.listTasks.mockRejectedValue(new Error('boom'));
    renderWithProviders(<ActivityPlanTab speciesKey="sp-1" plantKey="plant-1" />);
    expect(
      await screen.findByTestId('generate-activity-plan-button'),
    ).toBeInTheDocument();
  });

  it('surfaces the apply label for a single plant when only plantKey is set', async () => {
    activityPlanApi.generatePlan.mockResolvedValue(plan());
    const user = userEvent.setup();
    renderWithProviders(<ActivityPlanTab speciesKey="sp-1" plantKey="plant-1" />);
    await user.click(await screen.findByTestId('generate-activity-plan-button'));
    expect(
      await screen.findByRole('button', { name: i18n.t('pages.activityPlan.applyToPlant') }),
    ).toBeInTheDocument();
  });
});

// ── Shared generated plan (#1003) ───────────────────────────────────

/**
 * A generated plan is one object shared by every tenant growing that species
 * until one of them edits it; the backend then forks it into a private copy
 * with fresh document keys. Two consequences the tab has to carry:
 *
 * - say so *before* the first edit, because nothing else distinguishes a shared
 *   plan from a private one (#1003 §3);
 * - reload after that edit rather than merging the response by key, because the
 *   keys it holds — including the workflow key "Anwenden" posts — now address
 *   the plan the user just stopped editing.
 */
describe('ActivityPlanTab — a plan that is still the shared template', () => {
  const sharedPlan = () => plan({ is_shared_template: true });

  it('says the plan is shared before anything is edited', async () => {
    activityPlanApi.generatePlan.mockResolvedValue(sharedPlan());
    const user = userEvent.setup();
    renderWithProviders(<ActivityPlanTab speciesKey="sp-1" runKey="run-1" />);

    await user.click(await screen.findByTestId('generate-activity-plan-button'));

    const notice = await screen.findByTestId('shared-plan-notice');
    expect(within(notice).getByText(i18n.t('pages.activityPlan.sharedPlanTitle'))).toBeInTheDocument();
  });

  it('says nothing of the sort once the plan belongs to the tenant', async () => {
    activityPlanApi.generatePlan.mockResolvedValue(plan());
    const user = userEvent.setup();
    renderWithProviders(<ActivityPlanTab speciesKey="sp-1" runKey="run-1" />);

    await user.click(await screen.findByTestId('generate-activity-plan-button'));
    await screen.findByText('Cannabis Trainingsplan');

    expect(screen.queryByTestId('shared-plan-notice')).toBeNull();
  });

  it('reloads the plan after the first edit and tells the user a copy was made', async () => {
    activityPlanApi.generatePlan
      .mockResolvedValueOnce(sharedPlan())
      .mockResolvedValue(plan({ workflow_template_key: 'wf-copy' }));
    activityPlanApi.updateTaskTemplate.mockResolvedValue(template({ key: 'tt-copy-1', enabled: false }));

    const user = userEvent.setup();
    renderWithProviders(<ActivityPlanTab speciesKey="sp-1" runKey="run-1" />);

    await user.click(await screen.findByTestId('generate-activity-plan-button'));
    const vegRow = (await screen.findByText('Entspitzen')).closest('tr') as HTMLElement;
    await user.click(within(vegRow).getByRole('switch'));

    await waitFor(() => expect(activityPlanApi.generatePlan).toHaveBeenCalledTimes(2));
    expect(
      await screen.findByText(i18n.t('pages.activityPlan.privateCopyCreated')),
    ).toBeInTheDocument();
    await waitFor(() => expect(screen.queryByTestId('shared-plan-notice')).toBeNull());
  });

  it('reloads after a removal too, so the plan is not left holding stale keys', async () => {
    activityPlanApi.generatePlan
      .mockResolvedValueOnce(sharedPlan())
      .mockResolvedValue(plan({ workflow_template_key: 'wf-copy' }));
    activityPlanApi.deleteTaskTemplate.mockResolvedValue(undefined);

    const user = userEvent.setup();
    renderWithProviders(<ActivityPlanTab speciesKey="sp-1" runKey="run-1" />);

    await user.click(await screen.findByTestId('generate-activity-plan-button'));
    const vegRow = (await screen.findByText('Entspitzen')).closest('tr') as HTMLElement;
    await user.click(
      within(vegRow).getByRole('button', { name: i18n.t('pages.activityPlan.removeActivity') }),
    );

    await waitFor(() => expect(activityPlanApi.deleteTaskTemplate).toHaveBeenCalledWith('tt-veg'));
    await waitFor(() => expect(activityPlanApi.generatePlan).toHaveBeenCalledTimes(2));
  });

  it('does not reload after an edit on a plan the tenant already owns', async () => {
    activityPlanApi.generatePlan.mockResolvedValue(plan());
    activityPlanApi.updateTaskTemplate.mockResolvedValue(template({ key: 'tt-veg', enabled: false }));

    const user = userEvent.setup();
    renderWithProviders(<ActivityPlanTab speciesKey="sp-1" runKey="run-1" />);

    await user.click(await screen.findByTestId('generate-activity-plan-button'));
    const vegRow = (await screen.findByText('Entspitzen')).closest('tr') as HTMLElement;
    await user.click(within(vegRow).getByRole('switch'));

    await waitFor(() => expect(activityPlanApi.updateTaskTemplate).toHaveBeenCalled());
    expect(activityPlanApi.generatePlan).toHaveBeenCalledTimes(1);
  });
});

// ── Assigned-tasks view ─────────────────────────────────────────────

describe('ActivityPlanTab — assigned tasks view', () => {
  it('renders grouped assigned tasks with a completion chip and workflow origin link', async () => {
    taskApi.listTasks.mockResolvedValue([
      task({ key: 't-done', status: 'completed', workflow_execution_key: 'wfx-1' }),
      task({
        key: 't-progress',
        template_key: 'tt-water',
        name: 'Watering',
        name_de: 'Gießen',
        status: 'in_progress',
        stress_level: 'none',
        category: 'general',
      }),
    ]);

    renderWithProviders(
      <ActivityPlanTab speciesKey="sp-1" runKey="run-1" currentPhaseName="vegetative" />,
    );

    expect(await screen.findByText(i18n.t('pages.activityPlan.assignedTasks'))).toBeInTheDocument();
    // German display names surface (de language).
    expect(screen.getByText('Entspitzen')).toBeInTheDocument();
    expect(screen.getByText('Gießen')).toBeInTheDocument();
    // The workflow-origin chip links out to the workflows page.
    expect(screen.getByTestId('workflow-origin-chip')).toBeInTheDocument();
    // Current-phase highlight chip.
    expect(screen.getByText(i18n.t('pages.activityPlan.currentPhase'))).toBeInTheDocument();
  });

  it('groups tasks without a trigger phase under the "no phase" bucket', async () => {
    taskApi.listTasks.mockResolvedValue([
      task({ key: 't-nophase', trigger_phase: null, template_key: 'tt-x', name_de: 'Kontrolle' }),
    ]);
    renderWithProviders(<ActivityPlanTab speciesKey="sp-1" plantKey="plant-1" />);
    expect(await screen.findByText(i18n.t('pages.activityPlan.noPhase'))).toBeInTheDocument();
  });

  it('renders English display names and instructions when the locale is en', async () => {
    i18n.changeLanguage('en');
    taskApi.listTasks.mockResolvedValue([
      task({
        key: 't-en',
        status: 'completed',
        name: 'Topping',
        instruction: 'Cut the top',
        category: 'unknown_category',
        stress_level: 'unknown_stress',
      }),
    ]);
    renderWithProviders(<ActivityPlanTab speciesKey="sp-1" runKey="run-1" />);

    // English name is shown (not the German name_de) and the component renders
    // its category/stress chips using the '?? default' colour fallback.
    expect(await screen.findByText('Topping')).toBeInTheDocument();
    expect(screen.getByText('Cut the top')).toBeInTheDocument();
  });

  it('marks overdue open tasks (error completion colour path)', async () => {
    taskApi.listTasks.mockResolvedValue([
      task({
        key: 't-overdue',
        status: 'pending',
        due_date: '2000-01-01T00:00:00Z',
        name_de: 'Überfällig',
      }),
    ]);
    renderWithProviders(<ActivityPlanTab speciesKey="sp-1" runKey="run-1" />);
    // The task renders in the assigned view without throwing on the overdue branch.
    expect(await screen.findByText('Überfällig')).toBeInTheDocument();
  });

  // #548 — a recurring care reminder that is satisfied and only due in the future
  // must read as "Geplant" (scheduled), never as an open "0 von 1 erledigt" task,
  // so the activity plan agrees with the task queue's due-date bucketing.
  it('shows a future-due recurring reminder as scheduled, not "0 von 1 erledigt"', async () => {
    taskApi.listTasks.mockResolvedValue([
      task({
        key: 't-water',
        template_key: null,
        category: 'care_reminder',
        name: 'Watering',
        name_de: 'Gießen',
        status: 'pending',
        due_date: '2099-07-14T00:00:00Z',
        trigger_phase: 'vegetative',
      }),
    ]);

    renderWithProviders(
      <ActivityPlanTab speciesKey="sp-1" plantKey="plant-1" currentPhaseName="vegetative" />,
    );

    expect(await screen.findByText('Gießen')).toBeInTheDocument();
    // At least the group/phase/top chip present the "scheduled" state...
    expect(screen.getAllByTestId('activity-scheduled-chip').length).toBeGreaterThan(0);
    // ...and the misleading "0 von 1 erledigt" wording is gone entirely.
    expect(
      screen.queryByText(i18n.t('pages.activityPlan.completedOf', { completed: 0, total: 1 })),
    ).not.toBeInTheDocument();
  });

  it('counts a done cycle as 1/1 and flags the queued next cycle as scheduled', async () => {
    taskApi.listTasks.mockResolvedValue([
      task({
        key: 't-water-done',
        template_key: null,
        category: 'care_reminder',
        name: 'Watering',
        name_de: 'Gießen',
        status: 'completed',
        due_date: '2000-07-07T00:00:00Z',
        trigger_phase: 'vegetative',
      }),
      task({
        key: 't-water-next',
        template_key: null,
        category: 'care_reminder',
        name: 'Watering',
        name_de: 'Gießen',
        status: 'pending',
        due_date: '2099-07-14T00:00:00Z',
        trigger_phase: 'vegetative',
      }),
    ]);

    renderWithProviders(
      <ActivityPlanTab speciesKey="sp-1" plantKey="plant-1" currentPhaseName="vegetative" />,
    );

    // The finished cycle counts as done (scheduled next cycle excluded from ratio)...
    expect(
      await screen.findAllByText(i18n.t('pages.activityPlan.completedOf', { completed: 1, total: 1 })),
    ).not.toHaveLength(0);
    // ...and the future occurrence is surfaced as "scheduled", not as unfinished.
    expect(screen.getAllByTestId('activity-scheduled-count-chip').length).toBeGreaterThan(0);
  });
});
