import { describe, it, expect, beforeEach, vi } from 'vitest';
import { screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { renderWithProviders } from '../../helpers';
import WidgetFrame from '@/components/dashboard/WidgetFrame';
import type { DashboardWidgetInstance } from '@/api/types';

// Replace the lazy widget lookup with a synchronous stub so the frame renders
// without Suspense boundaries getting in the way of the menu assertions.
const registryMock = vi.hoisted(() => ({
  getWidgetComponent: vi.fn(),
}));
vi.mock('@/components/dashboard/widgetRegistry', () => ({
  getWidgetComponent: registryMock.getWidgetComponent,
}));

const StubWidget = () => <div data-testid="stub-widget">widget body</div>;

const instance: DashboardWidgetInstance = {
  instance_id: 'inst-1',
  widget_key: 'tasks_today',
  config: {},
} as DashboardWidgetInstance;

function makeProps(over: Partial<React.ComponentProps<typeof WidgetFrame>> = {}) {
  return {
    instance,
    editMode: true,
    hasConfig: false,
    isFirst: false,
    isLast: false,
    onMoveUp: vi.fn(),
    onMoveDown: vi.fn(),
    onGrow: vi.fn(),
    onShrink: vi.fn(),
    onRemove: vi.fn(),
    onConfigure: vi.fn(),
    ...over,
  };
}

beforeEach(() => {
  vi.clearAllMocks();
  registryMock.getWidgetComponent.mockReturnValue(StubWidget);
});

describe('WidgetFrame', () => {
  it('renders the widget body and no menu when not in edit mode', () => {
    renderWithProviders(<WidgetFrame {...makeProps({ editMode: false })} />);
    expect(screen.getByTestId('widget-frame-tasks_today')).toBeInTheDocument();
    expect(screen.queryByTestId('widget-menu-tasks_today')).not.toBeInTheDocument();
  });

  it('exposes the edit kebab menu in edit mode', () => {
    renderWithProviders(<WidgetFrame {...makeProps()} />);
    expect(screen.getByTestId('widget-menu-tasks_today')).toBeInTheDocument();
  });

  it('gives the menu button an accessible name and haspopup (P3 affordance)', () => {
    renderWithProviders(<WidgetFrame {...makeProps()} />);
    const button = screen.getByTestId('widget-menu-tasks_today');
    // aria-label / data-testid must survive the visibility restyle.
    expect(button).toHaveAttribute('aria-label');
    expect(button.getAttribute('aria-label')).toBeTruthy();
    expect(button).toHaveAttribute('aria-haspopup', 'menu');
    expect(button).toHaveAttribute('aria-expanded', 'false');
    expect(button.tagName).toBe('BUTTON');
  });

  it('opens the menu via keyboard (Enter) — keyboard parity preserved', async () => {
    const user = userEvent.setup();
    renderWithProviders(<WidgetFrame {...makeProps()} />);
    const button = screen.getByTestId('widget-menu-tasks_today');
    button.focus();
    expect(button).toHaveFocus();
    await user.keyboard('{Enter}');
    expect(screen.getByTestId('widget-remove-tasks_today')).toBeInTheDocument();
    expect(button).toHaveAttribute('aria-expanded', 'true');
  });

  it('fires onMoveUp and closes the menu', async () => {
    const user = userEvent.setup();
    const props = makeProps();
    renderWithProviders(<WidgetFrame {...props} />);
    await user.click(screen.getByTestId('widget-menu-tasks_today'));
    await user.click(screen.getByTestId('widget-move-up-tasks_today'));
    expect(props.onMoveUp).toHaveBeenCalledTimes(1);
    expect(screen.queryByTestId('widget-move-up-tasks_today')).not.toBeInTheDocument();
  });

  it('disables move-up for the first and move-down for the last widget', async () => {
    const user = userEvent.setup();
    renderWithProviders(<WidgetFrame {...makeProps({ isFirst: true, isLast: true })} />);
    await user.click(screen.getByTestId('widget-menu-tasks_today'));
    expect(screen.getByTestId('widget-move-up-tasks_today')).toHaveAttribute('aria-disabled', 'true');
    expect(screen.getByTestId('widget-move-down-tasks_today')).toHaveAttribute('aria-disabled', 'true');
  });

  it('hides the configure item unless the widget has config', async () => {
    const user = userEvent.setup();
    renderWithProviders(<WidgetFrame {...makeProps({ hasConfig: false })} />);
    await user.click(screen.getByTestId('widget-menu-tasks_today'));
    expect(screen.queryByTestId('widget-configure-tasks_today')).not.toBeInTheDocument();
  });

  it('shows and fires the configure item when the widget has config', async () => {
    const user = userEvent.setup();
    const props = makeProps({ hasConfig: true });
    renderWithProviders(<WidgetFrame {...props} />);
    await user.click(screen.getByTestId('widget-menu-tasks_today'));
    await user.click(screen.getByTestId('widget-configure-tasks_today'));
    expect(props.onConfigure).toHaveBeenCalledTimes(1);
  });

  it('fires onRemove from the menu', async () => {
    const user = userEvent.setup();
    const props = makeProps();
    renderWithProviders(<WidgetFrame {...props} />);
    await user.click(screen.getByTestId('widget-menu-tasks_today'));
    await user.click(screen.getByTestId('widget-remove-tasks_today'));
    expect(props.onRemove).toHaveBeenCalledTimes(1);
  });

  it('still renders a frame when the widget key is unknown (null component)', () => {
    registryMock.getWidgetComponent.mockReturnValue(null);
    renderWithProviders(<WidgetFrame {...makeProps({ editMode: false })} />);
    expect(screen.getByTestId('widget-frame-tasks_today')).toBeInTheDocument();
    expect(screen.queryByTestId('stub-widget')).not.toBeInTheDocument();
  });
});
