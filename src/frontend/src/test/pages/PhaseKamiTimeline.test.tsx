import { screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import i18n from 'i18next';
import { renderWithProviders } from '../helpers';
import PhaseKamiTimeline from '@/pages/durchlaeufe/PhaseKamiTimeline';
import type { PhaseTimelineEntry } from '@/api/types';

const DAYS = i18n.t('common.days');
const daysRe = new RegExp(`\\b${DAYS}\\b`);

function makePhase(overrides: Partial<PhaseTimelineEntry> = {}): PhaseTimelineEntry {
  return {
    phase_key: 'pk-1',
    phase_name: 'vegetative',
    display_name: 'Vegetative',
    description: undefined,
    sequence_order: 1,
    typical_duration_days: 14,
    status: 'completed',
    actual_entered_at: null,
    actual_exited_at: null,
    actual_duration_days: null,
    projected_start: null,
    projected_end: null,
    ...overrides,
  };
}

describe('PhaseKamiTimeline', () => {
  it('renders nothing for an empty phase list', () => {
    const { container } = renderWithProviders(<PhaseKamiTimeline phases={[]} />);
    expect(container.querySelector('[role="list"]')).toBeNull();
  });

  it('renders completed, current and projected phases with translated labels', () => {
    const phases = [
      makePhase({ phase_key: 'p1', phase_name: 'germination', status: 'completed', actual_duration_days: 5 }),
      makePhase({ phase_key: 'p2', phase_name: 'vegetative', status: 'current', actual_duration_days: 14 }),
      makePhase({
        phase_key: 'p3',
        phase_name: 'flowering',
        status: 'projected',
        actual_duration_days: null,
        typical_duration_days: 0,
        projected_start: '2024-01-01T00:00:00Z',
        projected_end: '2024-01-11T00:00:00Z',
      }),
    ];
    const { container } = renderWithProviders(<PhaseKamiTimeline phases={phases} />);

    expect(screen.getByRole('list')).toBeInTheDocument();
    // Three semantic list items (one per phase).
    expect(screen.getAllByRole('listitem')).toHaveLength(3);
    // Translated phase labels (enums.phaseName.*).
    expect(screen.getByText(i18n.t('enums.phaseName.germination'))).toBeInTheDocument();
    expect(screen.getByText(i18n.t('enums.phaseName.vegetative'))).toBeInTheDocument();
    expect(screen.getByText(i18n.t('enums.phaseName.flowering'))).toBeInTheDocument();

    // Durations: actual (5, 14) and the projected span computed from start/end (10 days).
    const durationTexts = screen.getAllByText((c) => daysRe.test(c));
    const joined = durationTexts.map((n) => n.textContent).join('|');
    expect(joined).toMatch(/5/);
    expect(joined).toMatch(/14/);
    expect(joined).toMatch(/10/);

    // Known phases render their Kami illustration (decorative, empty-alt img).
    expect(container.querySelectorAll('img').length).toBe(3);
  });

  it('falls back to typical_duration_days when no actual or projected span exists', () => {
    renderWithProviders(
      <PhaseKamiTimeline phases={[makePhase({ typical_duration_days: 21 })]} />,
    );
    const durationTexts = screen.getAllByText((c) => daysRe.test(c));
    expect(durationTexts.map((n) => n.textContent).join('|')).toMatch(/21/);
  });

  it('hides the duration line when no duration is known', () => {
    const phase = makePhase({
      actual_duration_days: null,
      projected_start: null,
      projected_end: null,
      typical_duration_days: null as unknown as number,
    });
    renderWithProviders(<PhaseKamiTimeline phases={[phase]} />);
    // No element carries a numeric duration string.
    expect(screen.queryByText((c) => new RegExp(`\\d+.*${DAYS}`).test(c))).toBeNull();
  });

  it('adds a tooltip affordance (tabIndex) to phases that have a description', () => {
    renderWithProviders(
      <PhaseKamiTimeline phases={[makePhase({ phase_name: 'germination' })]} speciesName="Monstera deliciosa" />,
    );
    // germination has a generic enums.phaseDescription entry → label becomes focusable.
    const label = screen.getByText(i18n.t('enums.phaseName.germination'));
    expect(label.getAttribute('tabindex')).toBe('0');
  });

  it('renders an unknown phase with fallback label, no illustration and no tooltip affordance', () => {
    const phase = makePhase({
      phase_key: 'weird',
      phase_name: 'totally_unknown_phase',
      display_name: 'Custom Phase',
      status: 'projected',
    });
    const { container } = renderWithProviders(<PhaseKamiTimeline phases={[phase]} />);

    const label = screen.getByText('Custom Phase');
    expect(label).toBeInTheDocument();
    // No description → not focusable.
    expect(label.getAttribute('tabindex')).toBeNull();
    // No Kami illustration for an unknown phase.
    expect(container.querySelectorAll('img')).toHaveLength(0);
  });
});
