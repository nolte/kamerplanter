import { cleanup, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import i18n from 'i18next';
import { renderWithProviders } from '../helpers';
import PhaseTimelineView from '@/pages/kalender/PhaseTimelineView';
import type { CalendarEvent } from '@/api/types';

// PhaseTimelineView renders a per-plant phase Gantt from calendar events. Its only
// external is the router `navigate`, doubled here so run/plant links are observable.
const mockNavigate = vi.fn();
vi.mock('react-router-dom', async (orig) => {
  const actual = (await orig()) as Record<string, unknown>;
  return { ...actual, useNavigate: () => mockNavigate };
});

const NOW = new Date();
const Y = NOW.getFullYear();
const M = NOW.getMonth();
const DIM = new Date(Y, M + 1, 0).getDate();

const iso = (y: number, monthIndex: number, day: number) =>
  new Date(y, monthIndex, day, 12, 0).toISOString();
const at = (day: number) => iso(Y, M, day);

function ev(overrides: Partial<CalendarEvent> = {}): CalendarEvent {
  return {
    id: 'ev',
    title: 'Phase',
    description: '',
    category: 'phase_transition',
    source: 'phase_transition',
    color: '',
    start: at(3),
    end: at(10),
    all_day: false,
    plant_key: null,
    task_key: null,
    site_key: null,
    location_key: null,
    metadata: {},
    ...overrides,
  };
}

/** Events across a run group, standalone plants and the month boundaries. */
function richEvents(): CalendarEvent[] {
  return [
    // Run "Batch A" — plant p1, a mapped phase color, current status.
    ev({
      id: 'p1-veg',
      start: at(3),
      end: at(10),
      metadata: { run_key: 'run-1', run_name: 'Batch A', plant_instance_key: 'p1', plant_name: 'Tomato Plant', phase_name: 'vegetative', status: 'current' },
    }),
    // Run "Batch A" — plant p2, an UNMAPPED phase name (fallback color) + projected status.
    ev({
      id: 'p2-bloom',
      start: at(6),
      end: at(14),
      metadata: { run_key: 'run-1', run_name: 'Batch A', plant_instance_key: 'p2', plant_name: 'Basil Plant', phase_name: 'super_bloom', status: 'projected' },
    }),
    // Standalone plant p3 — phase starts in the PREVIOUS month (clamped to day 1).
    ev({
      id: 'p3-harvest',
      start: iso(Y, M - 1, 25),
      end: at(4),
      plant_key: 'p3',
      metadata: { plant_name: 'Solo Fern', phase_name: 'harvest', status: 'completed' },
    }),
    // Standalone plant p4 — phase runs INTO the next month (clamped, isOngoing).
    ev({
      id: 'p4-flower',
      start: at(Math.max(1, DIM - 2)),
      end: iso(Y, M + 1, 5),
      plant_key: 'p4',
      metadata: { plant_name: 'Ongoing Herb', phase_name: 'flowering', status: 'current' },
    }),
    // Non-phase event — filtered out entirely.
    ev({ id: 'task', category: 'custom', source: 'task', metadata: {} }),
    // Phase event without an end — filtered out (requires start && end).
    ev({ id: 'no-end', end: null, metadata: { phase_name: 'seedling' } }),
  ];
}

describe('PhaseTimelineView', () => {
  beforeEach(() => {
    i18n.changeLanguage('en');
    mockNavigate.mockClear();
  });
  afterEach(() => {
    // Unmount before resetting the language: the file's afterEach runs before
    // testing-library's auto-cleanup (LIFO), so an i18n reset here would
    // otherwise re-render every still-mounted useTranslation() consumer
    // outside act(). Unmounting first makes the reset touch nothing.
    cleanup();
    i18n.changeLanguage('en');
  });

  it('shows an empty state when no phase-transition events exist', () => {
    renderWithProviders(
      <PhaseTimelineView
        events={[ev({ id: 'task', category: 'custom', source: 'task' })]}
        year={Y}
        month={M}
      />,
    );
    expect(
      screen.getByText(i18n.t('pages.calendar.phaseTimeline.noData')),
    ).toBeInTheDocument();
  });

  it('renders the run header, plant rows and the phase legend', () => {
    renderWithProviders(<PhaseTimelineView events={richEvents()} year={Y} month={M} />);

    // Run header for the grouped run.
    expect(screen.getByText('Batch A')).toBeInTheDocument();
    // Plant rows — grouped and standalone.
    expect(screen.getByText('Tomato Plant')).toBeInTheDocument();
    expect(screen.getByText('Basil Plant')).toBeInTheDocument();
    expect(screen.getByText('Solo Fern')).toBeInTheDocument();
    expect(screen.getByText('Ongoing Herb')).toBeInTheDocument();

    // Legend lists the used phase names (mapped + fallback) and the today marker.
    expect(screen.getByText('vegetative')).toBeInTheDocument();
    expect(screen.getByText('super_bloom')).toBeInTheDocument();
    expect(screen.getByText(i18n.t('pages.calendar.phaseTimeline.today'))).toBeInTheDocument();
  });

  it('navigates to the planting run when the run header is clicked', async () => {
    const user = userEvent.setup();
    renderWithProviders(<PhaseTimelineView events={richEvents()} year={Y} month={M} />);

    await user.click(screen.getByText('Batch A'));
    expect(mockNavigate).toHaveBeenCalledWith('/durchlaeufe/planting-runs/run-1');
  });

  it('navigates to the plant instance when a plant row is clicked', async () => {
    const user = userEvent.setup();
    renderWithProviders(<PhaseTimelineView events={richEvents()} year={Y} month={M} />);

    await user.click(screen.getByText('Tomato Plant'));
    expect(mockNavigate).toHaveBeenCalledWith('/pflanzen/plant-instances/p1');
  });

  it('renders a timeline for a month that is not the current month (no today marker)', () => {
    // Use a fixed, non-current month so `todayDay` stays null. February is 0-based 1.
    const otherYear = Y - 1;
    const events: CalendarEvent[] = [
      ev({
        id: 'past-veg',
        start: iso(otherYear, 1, 3),
        end: iso(otherYear, 1, 12),
        metadata: { run_key: 'run-9', run_name: 'Past Run', plant_instance_key: 'px', plant_name: 'Past Plant', phase_name: 'vegetative', status: 'completed' },
      }),
    ];
    renderWithProviders(<PhaseTimelineView events={events} year={otherYear} month={1} />);

    expect(screen.getByText('Past Run')).toBeInTheDocument();
    expect(screen.getByText('Past Plant')).toBeInTheDocument();
    // Not the current month -> the "today" legend entry is absent.
    expect(screen.queryByText(i18n.t('pages.calendar.phaseTimeline.today'))).toBeNull();
  });
});
