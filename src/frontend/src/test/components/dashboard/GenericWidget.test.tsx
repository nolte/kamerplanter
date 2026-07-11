import { describe, it, expect, beforeEach, vi } from 'vitest';
import { screen, within } from '@testing-library/react';
import { renderWithProviders } from '../../helpers';
import GenericWidget from '@/components/dashboard/widgets/GenericWidget';

// GenericWidget pulls its data from the DashboardDataContext; mock the hook so
// each test drives one of the four mandatory REQ-009 render states directly.
const payloadMock = vi.hoisted(() => ({
  useWidgetPayload: vi.fn(() => ({ payload: null as unknown, loading: false })),
}));
vi.mock('@/components/dashboard/DashboardDataContext', () => ({
  useWidgetPayload: payloadMock.useWidgetPayload,
}));

// Deep-link gating (#461) is REQ-042 module-visibility driven; mock it so each
// test controls whether a target route is visible deterministically.
const moduleVisibilityMock = vi.hoisted(() => ({
  useModuleVisibility: vi.fn((): { isPathVisible: (path: string) => boolean } => ({
    isPathVisible: () => true,
  })),
}));
vi.mock('@/hooks/useModuleVisibility', () => ({
  useModuleVisibility: moduleVisibilityMock.useModuleVisibility,
}));

function render(widgetKey: string, editMode = false) {
  return renderWithProviders(<GenericWidget widgetKey={widgetKey} instanceId="inst-1" editMode={editMode} />);
}

beforeEach(() => {
  vi.clearAllMocks();
  payloadMock.useWidgetPayload.mockReturnValue({ payload: null, loading: false });
  moduleVisibilityMock.useModuleVisibility.mockReturnValue({ isPathVisible: () => true });
});

describe('GenericWidget', () => {
  it('renders the loading skeleton state', () => {
    payloadMock.useWidgetPayload.mockReturnValue({ payload: null, loading: true });
    render('tasks_today');
    expect(screen.getByTestId('widget-tasks_today-loading')).toBeInTheDocument();
  });

  it('renders numeric slices as stat tiles', () => {
    payloadMock.useWidgetPayload.mockReturnValue({ payload: { count: 7 }, loading: false });
    render('care_reminders');
    const group = screen.getByRole('group', { name: /7/ });
    expect(within(group).getByText('7')).toBeInTheDocument();
  });

  it('renders both the due-today and overdue tiles for tasks_today (Issue #438)', () => {
    payloadMock.useWidgetPayload.mockReturnValue({
      payload: { open_tasks_today: 0, overdue_tasks: 12, upcoming_tasks: [] },
      loading: false,
    });
    render('tasks_today');
    // Two distinct, honest counts surfaced side by side.
    const dueToday = screen.getByRole('group', { name: /: 0$/ });
    expect(within(dueToday).getByText('0')).toBeInTheDocument();
    const overdue = screen.getByRole('group', { name: /: 12$/ });
    expect(within(overdue).getByText('12')).toBeInTheDocument();
  });

  it('renders an event list for a populated upcoming_tasks slice', () => {
    payloadMock.useWidgetPayload.mockReturnValue({
      payload: { upcoming_tasks: [{ _key: 't1', name: 'Gießen', category: 'watering', due_date: '2026-07-10' }] },
      loading: false,
    });
    render('next_calendar_events');
    const list = screen.getByTestId('widget-next_calendar_events-events');
    expect(within(list).getByText('Gießen')).toBeInTheDocument();
  });

  it('renders the "nothing due" state for an empty upcoming_tasks array', () => {
    payloadMock.useWidgetPayload.mockReturnValue({ payload: { upcoming_tasks: [] }, loading: false });
    render('next_calendar_events');
    expect(screen.getByTestId('widget-next_calendar_events-events-empty')).toBeInTheDocument();
  });

  it('falls back to the empty "coming soon" state without a data slice', () => {
    payloadMock.useWidgetPayload.mockReturnValue({ payload: null, loading: false });
    render('community_activity');
    expect(screen.getByTestId('widget-community_activity-empty')).toBeInTheDocument();
  });

  it('shows a glossary tooltip for jargon-titled widgets', () => {
    payloadMock.useWidgetPayload.mockReturnValue({ payload: null, loading: false });
    render('ipm_alerts');
    // ipm_alerts maps to the 'ipm' glossary term -> HelpTooltip renders its icon.
    expect(screen.getByTestId('help-tooltip-icon-ipm')).toBeInTheDocument();
  });

  it('renders no glossary tooltip for widgets without a jargon term', () => {
    payloadMock.useWidgetPayload.mockReturnValue({ payload: null, loading: false });
    render('community_activity');
    expect(screen.queryByTestId(/^help-tooltip-icon-/)).not.toBeInTheDocument();
  });
});

describe('GenericWidget — entity deep links (#461)', () => {
  const TASK = { _key: 't1', name: 'Gießen', category: 'watering', due_date: '2026-07-10' };
  const PLANTS = [
    { _key: 'p1', plant_name: 'Basilikum', species_key: 'ocimum-basilicum' },
    { _key: 'p2', plant_name: null, species_key: 'solanum-lycopersicum' },
  ];

  it('deep-links each next_calendar_events row to its task detail — no nested <a>', () => {
    payloadMock.useWidgetPayload.mockReturnValue({ payload: { upcoming_tasks: [TASK] }, loading: false });
    render('next_calendar_events');
    const row = screen.getByTestId('widget-next_calendar_events-row-t1');
    expect(row.tagName).toBe('A');
    expect(row).toHaveAttribute('href', '/aufgaben/tasks/t1');
    // Valid, accessible markup: the row anchor is NOT nested inside another anchor.
    expect(row.parentElement?.closest('a')).toBeNull();
  });

  it('shows both the counts and deep-linked task rows for tasks_today', () => {
    payloadMock.useWidgetPayload.mockReturnValue({
      payload: { open_tasks_today: 2, overdue_tasks: 1, upcoming_tasks: [TASK] },
      loading: false,
    });
    render('tasks_today');
    // Counts still present (Issue #438 contract preserved).
    expect(screen.getByRole('group', { name: /: 2$/ })).toBeInTheDocument();
    // Task row is a deep link.
    const row = screen.getByTestId('widget-tasks_today-row-t1');
    expect(row.tagName).toBe('A');
    expect(row).toHaveAttribute('href', '/aufgaben/tasks/t1');
  });

  it('renders task rows as plain (non-link) rows in edit mode', () => {
    payloadMock.useWidgetPayload.mockReturnValue({ payload: { upcoming_tasks: [TASK] }, loading: false });
    render('next_calendar_events', true);
    expect(screen.queryByTestId('widget-next_calendar_events-row-t1')).not.toBeInTheDocument();
    // The task name is still shown, just not as a link.
    expect(screen.getByText('Gießen')).toBeInTheDocument();
    expect(screen.queryByTestId('widget-next_calendar_events-open-list')).not.toBeInTheDocument();
  });

  it('does not deep-link rows when the target module is hidden (REQ-042)', () => {
    moduleVisibilityMock.useModuleVisibility.mockReturnValue({
      isPathVisible: (path: string) => path !== '/aufgaben/tasks',
    });
    payloadMock.useWidgetPayload.mockReturnValue({ payload: { upcoming_tasks: [TASK] }, loading: false });
    render('next_calendar_events');
    expect(screen.queryByTestId('widget-next_calendar_events-row-t1')).not.toBeInTheDocument();
    expect(screen.getByText('Gießen')).toBeInTheDocument();
  });

  it('renders a header "open list" link for entity widgets in read-only mode', () => {
    payloadMock.useWidgetPayload.mockReturnValue({ payload: { upcoming_tasks: [TASK] }, loading: false });
    render('next_calendar_events');
    const listLink = screen.getByTestId('widget-next_calendar_events-open-list');
    expect(listLink.tagName).toBe('A');
    // next_calendar_events navigateTo is '/kalender' in the catalog.
    expect(listLink).toHaveAttribute('href', '/kalender');
  });

  it('deep-links each plant_grid tile to its plant detail — no nested <a>', () => {
    payloadMock.useWidgetPayload.mockReturnValue({ payload: { plants: PLANTS }, loading: false });
    render('plant_grid');
    const tile = screen.getByTestId('widget-plant_grid-tile-p1');
    expect(tile.tagName).toBe('A');
    expect(tile).toHaveAttribute('href', '/pflanzen/plant-instances/p1');
    expect(tile.parentElement?.closest('a')).toBeNull();
    // A plant without a name falls back to its species key label.
    expect(screen.getByTestId('widget-plant_grid-tile-p2')).toHaveTextContent('solanum-lycopersicum');
  });

  it('renders the empty state when plant_grid has no active plants', () => {
    payloadMock.useWidgetPayload.mockReturnValue({ payload: { plants: [] }, loading: false });
    render('plant_grid');
    expect(screen.getByTestId('widget-plant_grid-tiles-empty')).toBeInTheDocument();
  });
});
