import { describe, it, expect, vi, beforeEach } from 'vitest';
import { screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import i18n from 'i18next';
import WidgetConfigDialog from '@/components/dashboard/WidgetConfigDialog';
import { renderWithProviders } from '@/test/helpers';

/**
 * REQ-045 — per-widget configuration dialog. Covers the schema-driven field
 * rendering (text vs number, none), the draft state, and the save/cancel paths.
 */

beforeEach(() => {
  i18n.changeLanguage('de');
});

describe('WidgetConfigDialog', () => {
  it('renders a text field pre-filled from config and saves the edited draft', async () => {
    const onSave = vi.fn();
    const onClose = vi.fn();
    const user = userEvent.setup();
    renderWithProviders(
      <WidgetConfigDialog
        open
        widgetKey="weather_forecast"
        config={{ location: 'Berlin' }}
        onSave={onSave}
        onClose={onClose}
      />,
    );

    const input = screen.getByTestId('config-field-location') as HTMLInputElement;
    expect(input.value).toBe('Berlin');

    await user.clear(input);
    await user.type(input, 'Hamburg');
    await user.click(screen.getByTestId('widget-config-save'));

    expect(onSave).toHaveBeenCalledWith({ location: 'Hamburg' });
    expect(onClose).toHaveBeenCalledTimes(1);
  });

  it('coerces a numeric field to a number on save', async () => {
    const onSave = vi.fn();
    const user = userEvent.setup();
    renderWithProviders(
      <WidgetConfigDialog
        open
        widgetKey="harvest_forecast"
        config={{}}
        onSave={onSave}
        onClose={vi.fn()}
      />,
    );

    const input = screen.getByTestId('config-field-timeframe_days') as HTMLInputElement;
    expect(input.type).toBe('number');
    await user.type(input, '14');
    await user.click(screen.getByTestId('widget-config-save'));

    expect(onSave).toHaveBeenCalledWith({ timeframe_days: 14 });
  });

  it('shows a disabled "no options" field for widgets without a config schema', async () => {
    const onSave = vi.fn();
    const onClose = vi.fn();
    const user = userEvent.setup();
    renderWithProviders(
      <WidgetConfigDialog
        open
        widgetKey="quick_actions"
        config={{}}
        onSave={onSave}
        onClose={onClose}
      />,
    );

    expect(
      screen.getByLabelText(i18n.t('dashboard.config.noOptions')),
    ).toBeInTheDocument();
    expect(screen.queryByTestId('config-field-location')).not.toBeInTheDocument();

    // Saving an unconfigurable widget passes the untouched config back through.
    await user.click(screen.getByTestId('widget-config-save'));
    expect(onSave).toHaveBeenCalledWith({});
    expect(onClose).toHaveBeenCalledTimes(1);
  });

  it('cancel closes without saving', async () => {
    const onSave = vi.fn();
    const onClose = vi.fn();
    const user = userEvent.setup();
    renderWithProviders(
      <WidgetConfigDialog
        open
        widgetKey="weather_forecast"
        config={{ location: 'Berlin' }}
        onSave={onSave}
        onClose={onClose}
      />,
    );

    await user.click(screen.getByRole('button', { name: i18n.t('common.cancel') }));
    expect(onClose).toHaveBeenCalledTimes(1);
    expect(onSave).not.toHaveBeenCalled();
  });
});
