import { describe, it, expect, beforeEach, vi } from 'vitest';
import { screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import i18n from 'i18next';
import type { DashboardLayout, DashboardWidgetInstance } from '@/api/types';

/**
 * REQ-045 — DashboardPage edit-mode, config-dialog and empty-state coverage.
 * Complements DashboardPage.test.tsx (which covers the read-only default view).
 *
 * The real DashboardEditGrid is backed by react-grid-layout, which needs a
 * measured DOM and throws under jsdom. It is replaced with a lightweight
 * stand-in that still drives every `widgetProps` callback DashboardPage wires
 * up (move / grow / shrink / remove / configure) — the coverage target here is
 * DashboardPage's own logic, not the grid library.
 */

interface EditGridStub {
  layout: DashboardLayout;
  widgetProps: (instance: DashboardWidgetInstance) => {
    hasConfig: boolean;
    onMoveUp: () => void;
    onMoveDown: () => void;
    onGrow: () => void;
    onShrink: () => void;
    onRemove: () => void;
    onConfigure: () => void;
  };
}

vi.mock('@/components/dashboard/DashboardEditGrid', () => ({
  default: ({ layout, widgetProps }: EditGridStub) => (
    <div data-testid="edit-grid-stub">
      {layout.widgets.map((w) => {
        const p = widgetProps(w);
        return (
          <div key={w.instance_id} data-testid={`widget-frame-${w.widget_key}`}>
            <button data-testid={`mv-up-${w.widget_key}`} onClick={p.onMoveUp}>up</button>
            <button data-testid={`mv-down-${w.widget_key}`} onClick={p.onMoveDown}>down</button>
            <button data-testid={`grow-${w.widget_key}`} onClick={p.onGrow}>grow</button>
            <button data-testid={`shrink-${w.widget_key}`} onClick={p.onShrink}>shrink</button>
            <button data-testid={`remove-${w.widget_key}`} onClick={p.onRemove}>remove</button>
            {p.hasConfig && (
              <button data-testid={`config-${w.widget_key}`} onClick={p.onConfigure}>cfg</button>
            )}
          </div>
        );
      })}
    </div>
  ),
}));

import DashboardPage from '@/pages/DashboardPage';
import { renderWithProviders, createTestStore } from '@/test/helpers';

const LAYOUT: DashboardLayout = {
  schema_version: 2,
  widgets: [
    { instance_id: 'w-qa', widget_key: 'quick_actions', config: {} },
    { instance_id: 'w-wf', widget_key: 'weather_forecast', config: { location: 'Berlin' } },
  ],
  placements: {
    lg: [
      { instance_id: 'w-qa', x: 0, y: 0, w: 6, h: 4 },
      { instance_id: 'w-wf', x: 6, y: 0, w: 4, h: 3 },
    ],
  },
};

function storeWithLayout(layout: DashboardLayout | null) {
  return createTestStore({
    userPreferences: {
      preferences: {
        key: 'pref-1',
        user_key: 'user-1',
        experience_level: 'beginner',
        onboarding_completed: true,
        locale: 'de',
        theme: 'light',
        watering_can_liters: 5,
        smart_home_enabled: false,
        module_visibility: {},
        dashboard_layout: layout,
      },
      loading: false,
      error: null,
    },
  });
}

const EMPTY_LAYOUT: DashboardLayout = {
  schema_version: 2,
  widgets: [],
  placements: {},
};

beforeEach(() => {
  i18n.changeLanguage('de');
  // Note: the personalization coachmark (isPersonalizationHintDismissed) cannot
  // be exercised here — the jsdom test env ships a non-functional localStorage
  // stub whose getItem throws, so the hook takes its "storage unavailable →
  // don't nag" branch and the coachmark never renders.
});

describe('DashboardPage — empty state', () => {
  it('renders the empty state and offers a restore-default action', async () => {
    renderWithProviders(<DashboardPage />, { store: storeWithLayout(EMPTY_LAYOUT) });
    expect(await screen.findByTestId('dashboard-empty-state')).toBeInTheDocument();
    expect(screen.getByTestId('dashboard-empty-reset')).toBeInTheDocument();
  });

  it('restore-default dispatches a layout reset', async () => {
    const user = userEvent.setup();
    renderWithProviders(<DashboardPage />, { store: storeWithLayout(EMPTY_LAYOUT) });
    await user.click(await screen.findByTestId('dashboard-empty-reset'));
    // reset() → saveDashboardLayout(null) → the experience-level default layout
    // takes over, so the empty state gives way to the rendered dashboard.
    await waitFor(() =>
      expect(screen.queryByTestId('dashboard-empty-state')).not.toBeInTheDocument(),
    );
    expect(screen.getByTestId('dashboard-page')).toBeInTheDocument();
  });
});

describe('DashboardPage — edit mode', () => {
  it('enters edit mode, switches breakpoints and applies to all, then cancels', async () => {
    const user = userEvent.setup();
    renderWithProviders(<DashboardPage />, { store: storeWithLayout(LAYOUT) });

    await user.click(await screen.findByTestId('dashboard-edit-toggle'));

    // Breakpoint switcher becomes visible.
    const tablet = await screen.findByLabelText(i18n.t('dashboard.edit.tablet'));
    await user.click(tablet);
    await user.click(screen.getByLabelText(i18n.t('dashboard.edit.mobile')));

    // Apply-to-all copies the current breakpoint's placements everywhere.
    await user.click(screen.getByText(i18n.t('dashboard.edit.applyToAllShort')));

    // Cancel discards the working copy.
    await user.click(screen.getByTestId('dashboard-edit-cancel'));
    expect(screen.getByTestId('dashboard-edit-toggle')).toBeInTheDocument();
  });

  it('opens the widget config dialog from the edit grid and saves', async () => {
    const user = userEvent.setup();
    renderWithProviders(<DashboardPage />, { store: storeWithLayout(LAYOUT) });

    await user.click(await screen.findByTestId('dashboard-edit-toggle'));

    // weather_forecast has hasConfig=true → the stub renders a configure button.
    await user.click(await screen.findByTestId('config-weather_forecast'));

    const dialog = await screen.findByTestId('widget-config-dialog');
    const input = within(dialog).getByTestId('config-field-location') as HTMLInputElement;
    expect(input.value).toBe('Berlin');
    await user.clear(input);
    await user.type(input, 'München');
    await user.click(within(dialog).getByTestId('widget-config-save'));

    // Persist the whole layout edit.
    await user.click(screen.getByTestId('dashboard-edit-save'));
    await waitFor(() =>
      expect(screen.getByTestId('dashboard-edit-toggle')).toBeInTheDocument(),
    );
  });

  it('drives move / grow / shrink / remove through widgetProps', async () => {
    const user = userEvent.setup();
    renderWithProviders(<DashboardPage />, { store: storeWithLayout(LAYOUT) });

    await user.click(await screen.findByTestId('dashboard-edit-toggle'));

    await user.click(await screen.findByTestId('mv-up-weather_forecast'));
    await user.click(screen.getByTestId('mv-down-quick_actions'));
    await user.click(screen.getByTestId('grow-weather_forecast'));
    await user.click(screen.getByTestId('shrink-weather_forecast'));
    await user.click(screen.getByTestId('remove-weather_forecast'));

    await waitFor(() =>
      expect(screen.queryByTestId('widget-frame-weather_forecast')).not.toBeInTheDocument(),
    );
    // The other widget survives the removal.
    expect(screen.getByTestId('widget-frame-quick_actions')).toBeInTheDocument();
  });
});
