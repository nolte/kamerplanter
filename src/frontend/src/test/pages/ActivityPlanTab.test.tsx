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
});
