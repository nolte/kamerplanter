import { useState } from 'react';
import { cleanup, screen, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import i18n from 'i18next';
import { renderWithProviders } from '../helpers';
import PlantFilterTree from '@/pages/kalender/PlantFilterTree';
import type { CalendarEvent } from '@/api/types';

// PlantFilterTree is a controlled tree: the parent owns the checked/expanded sets.
// A small stateful harness supplies that ownership so the resulting checkbox and
// button states are observable after each interaction.

function ev(overrides: Partial<CalendarEvent> = {}): CalendarEvent {
  return {
    id: 'ev',
    title: 'E',
    description: '',
    category: 'phase_transition',
    source: 'phase_transition',
    color: '',
    start: null,
    end: null,
    all_day: false,
    plant_key: null,
    task_key: null,
    site_key: null,
    location_key: null,
    metadata: {},
    ...overrides,
  };
}

/** Events building two runs, a standalone plant and a run/standalone overlap. */
function treeEvents(): CalendarEvent[] {
  return [
    ev({ id: 'e1', metadata: { run_key: 'run-1', run_name: 'Batch A', plant_instance_key: 'p1', plant_name: 'Tomato' } }),
    ev({ id: 'e2', metadata: { run_key: 'run-1', run_name: 'Batch A', plant_instance_key: 'p2', plant_name: 'Basil' } }),
    ev({ id: 'e3', metadata: { run_key: 'run-2', run_name: 'Batch B', plant_instance_key: 'p3', plant_name: 'Chili' } }),
    // Standalone plant (no run_key).
    ev({ id: 'e4', plant_key: 'p4', metadata: { plant_name: 'Mint' } }),
    // p5 belongs to run-1 AND appears standalone -> must be excluded from standalone.
    ev({ id: 'e5', metadata: { run_key: 'run-1', run_name: 'Batch A', plant_instance_key: 'p5', plant_name: 'Sage' } }),
    ev({ id: 'e6', plant_key: 'p5', metadata: {} }),
    // Event with no plant association -> skipped entirely.
    ev({ id: 'e7', metadata: {} }),
  ];
}

const ALL_KEYS = ['p1', 'p2', 'p3', 'p4', 'p5'];

function Harness({
  events,
  initialChecked,
  initialExpanded = new Set<string>(),
}: {
  events: CalendarEvent[];
  initialChecked: Set<string>;
  initialExpanded?: Set<string>;
}) {
  const [checked, setChecked] = useState<Set<string>>(initialChecked);
  const [expanded, setExpanded] = useState<Set<string>>(initialExpanded);
  return (
    <PlantFilterTree
      events={events}
      checkedPlantKeys={checked}
      onCheckedChange={setChecked}
      expandedRuns={expanded}
      onExpandedChange={setExpanded}
    />
  );
}

/** The <input> inside a MUI checkbox rendered under a given data-testid. */
function checkbox(testId: string): HTMLInputElement {
  return within(screen.getByTestId(testId)).getByRole('checkbox') as HTMLInputElement;
}

describe('PlantFilterTree', () => {
  beforeEach(() => {
    i18n.changeLanguage('en');
  });
  afterEach(() => {
    // Unmount before resetting the language: the file's afterEach runs before
    // testing-library's auto-cleanup (LIFO), so an i18n reset here would
    // otherwise re-render every still-mounted useTranslation() consumer
    // outside act(). Unmounting first makes the reset touch nothing.
    cleanup();
    i18n.changeLanguage('en');
  });

  it('renders nothing when no events carry a plant association', () => {
    renderWithProviders(
      <Harness events={[ev({ id: 'x', metadata: {} })]} initialChecked={new Set()} />,
    );
    expect(screen.queryByText(i18n.t('pages.calendar.plantFilter.title'))).toBeNull();
  });

  it('builds run and standalone nodes and reflects the fully-checked state', () => {
    renderWithProviders(
      <Harness
        events={treeEvents()}
        initialChecked={new Set(ALL_KEYS)}
        initialExpanded={new Set(['run-1', 'run-2', '_standalone'])}
      />,
    );

    expect(screen.getByText(i18n.t('pages.calendar.plantFilter.title'))).toBeInTheDocument();
    expect(screen.getByText('Batch A')).toBeInTheDocument();
    expect(screen.getByText('Batch B')).toBeInTheDocument();
    // Standalone group uses the "no run" label.
    expect(screen.getByText(i18n.t('pages.calendar.phaseTimeline.noRun'))).toBeInTheDocument();
    // p5 is assigned to run-1, so it is NOT listed under the standalone group; only
    // Mint remains standalone.
    expect(screen.getByText('Mint')).toBeInTheDocument();

    // Everything checked -> the top "all" checkbox is checked, not partial.
    expect(checkbox('plant-filter-select-all')).toBeChecked();
    expect(checkbox('plant-filter-run-run-1')).toBeChecked();
    // No filtering active -> the "show all" shortcut is hidden.
    expect(screen.queryByTestId('plant-filter-clear')).toBeNull();
  });

  it('unchecking a single plant drives the partial (indeterminate) states', async () => {
    const user = userEvent.setup();
    renderWithProviders(
      <Harness
        events={treeEvents()}
        initialChecked={new Set(ALL_KEYS)}
        initialExpanded={new Set(['run-1'])}
      />,
    );

    await user.click(checkbox('plant-filter-plant-p1'));

    // The run and the top-level checkbox both go indeterminate.
    expect(checkbox('plant-filter-run-run-1')).toBePartiallyChecked();
    expect(checkbox('plant-filter-select-all')).toBePartiallyChecked();
    // Filtering is now active -> the "show all" shortcut appears.
    expect(screen.getByTestId('plant-filter-clear')).toBeInTheDocument();

    // "Show all" re-checks every plant and hides the shortcut again.
    await user.click(screen.getByTestId('plant-filter-clear'));
    expect(checkbox('plant-filter-select-all')).toBeChecked();
    expect(screen.queryByTestId('plant-filter-clear')).toBeNull();
  });

  it('toggles a whole run on and off', async () => {
    const user = userEvent.setup();
    renderWithProviders(
      <Harness
        events={treeEvents()}
        initialChecked={new Set(ALL_KEYS)}
        initialExpanded={new Set(['run-2'])}
      />,
    );

    // Run B (single plant p3) starts fully checked -> unchecking clears its plant.
    await user.click(checkbox('plant-filter-run-run-2'));
    expect(checkbox('plant-filter-plant-p3')).not.toBeChecked();
    expect(screen.getByTestId('plant-filter-clear')).toBeInTheDocument();

    // Toggling the run again re-checks it.
    await user.click(checkbox('plant-filter-run-run-2'));
    expect(checkbox('plant-filter-plant-p3')).toBeChecked();
  });

  it('checks everything from the empty state via the top-level checkbox', async () => {
    const user = userEvent.setup();
    renderWithProviders(
      <Harness events={treeEvents()} initialChecked={new Set()} initialExpanded={new Set(['run-1'])} />,
    );

    // Nothing checked -> not partial, and no "show all" shortcut.
    expect(checkbox('plant-filter-select-all')).not.toBeChecked();
    expect(checkbox('plant-filter-select-all')).not.toBePartiallyChecked();
    expect(screen.queryByTestId('plant-filter-clear')).toBeNull();

    await user.click(checkbox('plant-filter-select-all'));
    expect(checkbox('plant-filter-select-all')).toBeChecked();
    expect(checkbox('plant-filter-run-run-1')).toBeChecked();
  });

  it('expands and collapses a run node', async () => {
    const user = userEvent.setup();
    renderWithProviders(
      <Harness events={treeEvents()} initialChecked={new Set(ALL_KEYS)} initialExpanded={new Set()} />,
    );

    // The expand control toggles the run open and then closed again without error;
    // both branches of handleToggleExpand run.
    const expandBtn = screen.getByTestId('plant-filter-expand-run-1');
    await user.click(expandBtn);
    expect(checkbox('plant-filter-plant-p1')).toBeChecked();
    await user.click(expandBtn);
    // The run node itself remains rendered after collapsing.
    expect(screen.getByText('Batch A')).toBeInTheDocument();
  });
});
