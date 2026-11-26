import { describe, expect, it } from 'vitest';
import { screen } from '@testing-library/react';
import i18n from '@/i18n/i18n';
import TaskTemplateDialog from '@/pages/aufgaben/TaskTemplateDialog';
import type { TaskTemplate } from '@/api/types';
import { renderWithProviders } from '../helpers';

/**
 * #3025 M14 review — the option lists of the task-template dialog are the backend's
 * `TimeOfDay` (`morning/afternoon/evening/lights_off`) and `SkillLevel`
 * (`beginner/intermediate/advanced`). The dialog offered `night` and `expert`, which the
 * backend refuses, and a stored `lights_off` / `advanced` rendered an empty select.
 * The value lists themselves are pinned against `app.common.enums` by
 * `src/backend/tests/contracts/test_plant_property_enum_sync.py`.
 */
function template(overrides: Partial<TaskTemplate>): TaskTemplate {
  return {
    key: 'tt-1',
    name: 'Ausgeizen',
    instruction: '',
    category: 'pruning',
    trigger_type: 'manual',
    trigger_phase: null,
    workflow_phase_key: null,
    days_offset: 0,
    stress_level: 'none',
    skill_level: 'beginner',
    optimal_time_of_day: null,
    estimated_duration_minutes: null,
    requires_photo: false,
    sequence_order: 0,
    tools_required: [],
    timer_duration_seconds: null,
    timer_label: null,
    ...overrides,
  } as TaskTemplate;
}

describe('TaskTemplateDialog offers the backend enum values (#3025)', () => {
  it('shows a stored lights_off time of day and an advanced skill level', async () => {
    renderWithProviders(
      <TaskTemplateDialog
        open
        onClose={() => {}}
        workflowKey="wf-1"
        template={template({ optimal_time_of_day: 'lights_off', skill_level: 'advanced' })}
        phases={[]}
        onSaved={() => {}}
      />,
    );

    expect(await screen.findByText(i18n.t('enums.timeOfDay.lights_off'))).toBeInTheDocument();
    expect(screen.getByText(i18n.t('enums.skillLevel.advanced'))).toBeInTheDocument();
  });
});
