/** The sun window chips, the summer sun hours and the leaf-shade switch (REQ-053 GP-FR-158/159, WP 7.20). */
import { cleanup, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { useState } from 'react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { expectNoA11yViolations } from '@/test/a11y/expectNoA11yViolations';
import { renderWithProviders } from '@/test/helpers';
import SunWindowFields, { SUN_WINDOW_VALUES, parseSunHours } from './SunWindowFields';
import type { SunProfile, SunProfilePatch } from './types';

afterEach(() => cleanup());

function Harness({
  initial = {},
  spy,
  touchTarget,
}: {
  initial?: SunProfile;
  spy?: (patch: SunProfilePatch) => void;
  touchTarget?: number;
}) {
  const [value, setValue] = useState<SunProfile>(initial);
  return (
    <SunWindowFields
      value={value}
      touchTarget={touchTarget}
      onChange={(patch) => {
        spy?.(patch);
        setValue((previous) => ({ ...previous, ...patch }));
      }}
    />
  );
}

describe('SunWindowFields', () => {
  it('offers the times of day as chips, "not known" last and checked by default', () => {
    renderWithProviders(<Harness />);

    const radios = screen.getAllByRole('radio');
    expect(radios.map((radio) => (radio as HTMLInputElement).value)).toEqual([...SUN_WINDOW_VALUES]);
    expect(screen.getByRole('radio', { name: 'Morning' })).toBeInTheDocument();
    expect(screen.getByRole('radio', { name: 'All day' })).toBeInTheDocument();
    expect(screen.getByRole('radio', { name: 'Not known' })).toBeChecked();
  });

  it('reports only the chosen window and does not report the one already chosen', async () => {
    const spy = vi.fn();
    const user = userEvent.setup();
    renderWithProviders(<Harness initial={{ sun_window: 'midday' }} spy={spy} />);

    await user.click(screen.getByRole('radio', { name: 'Midday' }));
    expect(spy).not.toHaveBeenCalled();
    await user.click(screen.getByRole('radio', { name: 'Afternoon' }));

    expect(spy).toHaveBeenCalledExactlyOnceWith({ sun_window: 'afternoon' });
    expect(screen.getByRole('radio', { name: 'Afternoon' })).toBeChecked();
  });

  it('takes the hours as optional text, commits on blur and clears with an empty field', async () => {
    const spy = vi.fn();
    const user = userEvent.setup();
    renderWithProviders(<Harness initial={{ direct_sun_hours_summer: 4 }} spy={spy} />);
    const hours = screen.getByRole('textbox', { name: 'Hours of direct sun in summer (optional)' });

    expect(hours).toHaveValue('4');
    await user.clear(hours);
    await user.type(hours, '6,5{Enter}');
    expect(spy).toHaveBeenLastCalledWith({ direct_sun_hours_summer: 6.5 });

    await user.clear(hours);
    await user.tab();
    expect(spy).toHaveBeenLastCalledWith({ direct_sun_hours_summer: null });
  });

  it('refuses hours outside 0 to 24 in words and sends nothing', async () => {
    const spy = vi.fn();
    const user = userEvent.setup();
    renderWithProviders(<Harness spy={spy} />);
    const hours = screen.getByRole('textbox', { name: 'Hours of direct sun in summer (optional)' });

    await user.type(hours, '30');
    await user.tab();

    expect(spy).not.toHaveBeenCalled();
    expect(hours).toBeInvalid();
    expect(screen.getByText('Enter a number between 0 and 24, or leave the field empty.')).toBeVisible();
  });

  it('parses the hours strictly', () => {
    expect(parseSunHours('')).toBeNull();
    expect(parseSunHours(' 0 ')).toBe(0);
    expect(parseSunHours('24')).toBe(24);
    expect(parseSunHours('7.25')).toBe(7.25);
    expect(parseSunHours('24.5')).toBeUndefined();
    expect(parseSunHours('-1')).toBeUndefined();
    expect(parseSunHours('abc')).toBeUndefined();
  });

  it('toggles leaf shade and says it is a note only (operator decision #2466 item 10)', async () => {
    const spy = vi.fn();
    const user = userEvent.setup();
    renderWithProviders(<Harness spy={spy} />);
    const toggle = screen.getByRole('switch', { name: 'Leaf shade in summer' });

    expect(toggle).not.toBeChecked();
    expect(toggle).toHaveAccessibleDescription(/This is a note only/);
    await user.click(toggle);

    expect(spy).toHaveBeenCalledExactlyOnceWith({ foliage_shade_in_summer: true });
    expect(toggle).toBeChecked();
  });

  it('takes no input while disabled', () => {
    renderWithProviders(
      <SunWindowFields value={{ sun_window: 'morning' }} onChange={vi.fn()} disabled />,
    );

    for (const radio of screen.getAllByRole('radio')) expect(radio).toBeDisabled();
    expect(screen.getByRole('switch')).toBeDisabled();
    expect(screen.getByRole('textbox')).toBeDisabled();
  });

  it('keeps every control at the touch target it was given (64 px in field mode)', () => {
    renderWithProviders(<Harness touchTarget={64} />);

    for (const option of SUN_WINDOW_VALUES) {
      expect(screen.getByTestId(`bed-view-sun-profile-window-${option}`)).toHaveStyle({
        minHeight: '64px',
        minWidth: '64px',
      });
    }
    expect(screen.getByTestId('bed-view-sun-profile-hours').closest('.MuiInputBase-root')).toHaveStyle({
      minHeight: '64px',
    });
  });

  it('has no accessibility violations', async () => {
    const { container } = renderWithProviders(
      <Harness initial={{ sun_window: 'morning', direct_sun_hours_summer: 5, foliage_shade_in_summer: true }} />,
    );

    await expectNoA11yViolations(container);
  });
});
