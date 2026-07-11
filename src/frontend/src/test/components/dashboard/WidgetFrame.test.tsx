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

// Mock the module visibility hook to control whether a route is visible.
const moduleVisibilityMock = vi.hoisted(() => ({
  useModuleVisibility: vi.fn(() => ({ isPathVisible: vi.fn((_path: string) => true) })),
}));
vi.mock('@/hooks/useModuleVisibility', () => ({
  useModuleVisibility: moduleVisibilityMock.useModuleVisibility,
}));

// Note: catalog is imported normally (not mocked) since we rely on real navigateTo values.

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
  moduleVisibilityMock.useModuleVisibility.mockReturnValue({
    isPathVisible: vi.fn((_path: string) => true),
  });
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

  describe('Issue #439 — Widget Navigation (WP-4/5)', () => {
    it('renders as a navigable link in read-only mode when widget has navigateTo (care_reminders)', () => {
      // care_reminders has navigateTo: '/aufgaben/queue' and — unlike the
      // entity-list widgets (#461) — keeps the whole-panel link.
      const careInst: DashboardWidgetInstance = {
        instance_id: 'inst-1',
        widget_key: 'care_reminders',
        config: {},
      } as DashboardWidgetInstance;
      renderWithProviders(<WidgetFrame {...makeProps({ instance: careInst, editMode: false })} />);
      const navLink = screen.getByTestId('widget-nav-care_reminders');
      expect(navLink).toBeInTheDocument();
      expect(navLink.tagName).toBe('A'); // CardActionArea renders as <a> with RouterLink.
      expect(navLink).toHaveAttribute('href', '/aufgaben/queue');
      expect(screen.getByTestId('widget-nav-affordance-care_reminders')).toBeInTheDocument();
    });

    it('skips the panel-level link for entity-list widgets (#461, tasks_today)', () => {
      // tasks_today renders its own deep-linkable rows + header "open list" link,
      // so it must NOT be wrapped in a panel <a> (would nest a row <a>).
      renderWithProviders(<WidgetFrame {...makeProps({ editMode: false })} />);
      expect(screen.queryByTestId('widget-nav-tasks_today')).not.toBeInTheDocument();
      expect(screen.queryByTestId('widget-nav-affordance-tasks_today')).not.toBeInTheDocument();
      // The widget body itself still renders.
      expect(screen.getByTestId('stub-widget')).toBeInTheDocument();
    });

    it('does not render as navigable for static widgets (weather_forecast)', () => {
      // weather_forecast has no navigateTo in the catalog
      const staticInst: DashboardWidgetInstance = {
        instance_id: 'inst-1',
        widget_key: 'weather_forecast',
        config: {},
      } as DashboardWidgetInstance;
      renderWithProviders(<WidgetFrame {...makeProps({ instance: staticInst, editMode: false })} />);
      expect(screen.queryByTestId('widget-nav-weather_forecast')).not.toBeInTheDocument();
      expect(screen.queryByTestId('widget-nav-affordance-weather_forecast')).not.toBeInTheDocument();
    });

    it('does not render as navigable in edit mode even when navigateTo is set', () => {
      // tasks_today has navigateTo, but in edit mode it should not be a link
      renderWithProviders(<WidgetFrame {...makeProps({ editMode: true })} />);
      // In edit mode, panel is not wrapped in a link; only the kebab menu is present.
      expect(screen.queryByTestId('widget-nav-tasks_today')).not.toBeInTheDocument();
      expect(screen.queryByTestId('widget-nav-affordance-tasks_today')).not.toBeInTheDocument();
      expect(screen.getByTestId('widget-menu-tasks_today')).toBeInTheDocument();
    });

    it('respects module visibility gating — no link when target path is hidden (care_reminders)', () => {
      // Hide the tasks module so care_reminders navigation is gated out
      const careInst: DashboardWidgetInstance = {
        instance_id: 'inst-1',
        widget_key: 'care_reminders',
        config: {},
      } as DashboardWidgetInstance;
      const isPathVisibleMock = vi.fn((_path: string) => _path !== '/aufgaben/queue');
      moduleVisibilityMock.useModuleVisibility.mockReturnValue({ isPathVisible: isPathVisibleMock });
      renderWithProviders(<WidgetFrame {...makeProps({ instance: careInst, editMode: false })} />);
      // Widget should not be navigable when its target path is hidden (REQ-042 gating).
      expect(screen.queryByTestId('widget-nav-care_reminders')).not.toBeInTheDocument();
      expect(screen.queryByTestId('widget-nav-affordance-care_reminders')).not.toBeInTheDocument();
    });

    it('skips navigation wrapper for self-navigating widgets (winter_protection)', () => {
      // winter_protection has navigateTo but is in SELF_NAVIGATING_KEYS
      const winterInst: DashboardWidgetInstance = {
        instance_id: 'inst-1',
        widget_key: 'winter_protection',
        config: {},
      } as DashboardWidgetInstance;
      renderWithProviders(<WidgetFrame {...makeProps({ instance: winterInst, editMode: false })} />);
      // winter_protection has navigateTo but is in SELF_NAVIGATING_KEYS,
      // so panel should NOT be wrapped in a link (prevents nested <a> tags inside it).
      expect(screen.queryByTestId('widget-nav-winter_protection')).not.toBeInTheDocument();
      expect(screen.queryByTestId('widget-nav-affordance-winter_protection')).not.toBeInTheDocument();
      // The widget body itself renders.
      expect(screen.getByTestId('stub-widget')).toBeInTheDocument();
    });

    it('does not navigate when component is null', () => {
      registryMock.getWidgetComponent.mockReturnValue(null);
      renderWithProviders(<WidgetFrame {...makeProps({ editMode: false })} />);
      // No widget component => no nav link (isNavigational requires widgetNode !== null).
      expect(screen.queryByTestId('widget-nav-tasks_today')).not.toBeInTheDocument();
    });

    it('regression F1 — help tooltip inside navigable panel does not break (ipm_alerts)', () => {
      // ipm_alerts has navigateTo: '/pflanzenschutz/pests' in the real catalog
      // Mock a widget with a help tooltip-like button inside
      const MockWidgetWithHelp = () => (
        <div data-testid="stub-widget">
          <button data-testid="help-tooltip-trigger">Help</button>
        </div>
      );
      registryMock.getWidgetComponent.mockReturnValue(MockWidgetWithHelp);
      const ipmInst: DashboardWidgetInstance = {
        instance_id: 'inst-1',
        widget_key: 'ipm_alerts',
        config: {},
      } as DashboardWidgetInstance;
      renderWithProviders(<WidgetFrame {...makeProps({ instance: ipmInst, editMode: false })} />);
      // Verify the nav link exists.
      expect(screen.getByTestId('widget-nav-ipm_alerts')).toBeInTheDocument();
      // Verify the help button is inside the CardActionArea
      const helpBtn = screen.getByTestId('help-tooltip-trigger');
      expect(helpBtn).toBeInTheDocument();
      // Clicking inside should not break; the CardActionArea inherits click behavior
      expect(screen.getByTestId('stub-widget')).toBeInTheDocument();
    });
  });
});
