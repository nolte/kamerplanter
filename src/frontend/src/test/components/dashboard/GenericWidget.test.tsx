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

function render(widgetKey: string) {
  return renderWithProviders(<GenericWidget widgetKey={widgetKey} instanceId="inst-1" />);
}

beforeEach(() => {
  vi.clearAllMocks();
  payloadMock.useWidgetPayload.mockReturnValue({ payload: null, loading: false });
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
    render('vpd_gauge');
    // vpd_gauge maps to the 'vpd' glossary term -> HelpTooltip renders its icon.
    expect(screen.getByTestId('help-tooltip-icon-vpd')).toBeInTheDocument();
  });

  it('renders no glossary tooltip for widgets without a jargon term', () => {
    payloadMock.useWidgetPayload.mockReturnValue({ payload: null, loading: false });
    render('community_activity');
    expect(screen.queryByTestId(/^help-tooltip-icon-/)).not.toBeInTheDocument();
  });
});
