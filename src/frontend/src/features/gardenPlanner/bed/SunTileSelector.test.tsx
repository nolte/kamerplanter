/** The sun tiles (REQ-053 GP-FR-157): five tiles, definitions as help text, keyboard, a11y. */
import { cleanup, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { useState } from 'react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { renderWithProviders } from '@/test/helpers';
import { expectNoA11yViolations } from '@/test/a11y/expectNoA11yViolations';
import SunTileSelector, { SUN_TILE_VALUES } from './SunTileSelector';
import type { SunExposure } from '../model/types';

afterEach(() => cleanup());

function Harness({ initial, spy }: { initial: SunExposure | null; spy?: (v: SunExposure) => void }) {
  const [value, setValue] = useState<SunExposure | null>(initial);
  return (
    <SunTileSelector
      value={value}
      onChange={(next) => {
        spy?.(next);
        setValue(next);
      }}
    />
  );
}

describe('SunTileSelector', () => {
  it('offers the five classes with icon and text, unknown last (TC-053-036)', () => {
    renderWithProviders(<Harness initial="unknown" />);

    const radios = screen.getAllByRole('radio');
    expect(radios).toHaveLength(5);
    expect(SUN_TILE_VALUES).toEqual(['full_sun', 'partial_shade', 'shade', 'deep_shade', 'unknown']);
    expect(radios.map((radio) => (radio as HTMLInputElement).value)).toEqual([...SUN_TILE_VALUES]);
    expect(screen.getByRole('radio', { name: 'Full sun' })).toBeInTheDocument();
    expect(screen.getByRole('radio', { name: 'Deep shade' })).toBeInTheDocument();
    expect(screen.getByRole('radio', { name: 'Unknown' })).toBeChecked();
  });

  it('shows the definition of every class as help text (GP-FR-157)', () => {
    renderWithProviders(<Harness initial={null} />);

    expect(screen.getByText('More than 6 hours of direct sunlight on a summer day')).toBeVisible();
    expect(screen.getByText('3–6 hours of direct sunlight')).toBeVisible();
    expect(screen.getByText('2–3 hours of direct sunlight')).toBeVisible();
    expect(screen.getByText('Less than 2 hours of direct sunlight')).toBeVisible();
    expect(screen.getByText('Not recorded yet')).toBeVisible();
    expect(screen.getByRole('radio', { name: 'Full sun' })).toHaveAccessibleDescription(
      'More than 6 hours of direct sunlight on a summer day',
    );
  });

  it('shows no selection for a null value and reports the chosen class', async () => {
    const spy = vi.fn();
    const user = userEvent.setup();
    renderWithProviders(<Harness initial={null} spy={spy} />);

    for (const radio of screen.getAllByRole('radio')) expect(radio).not.toBeChecked();
    await user.click(screen.getByRole('radio', { name: 'Partial shade' }));

    expect(spy).toHaveBeenCalledWith('partial_shade');
    expect(screen.getByRole('radio', { name: 'Partial shade' })).toBeChecked();
  });

  it('moves with the arrow keys', async () => {
    const spy = vi.fn();
    const user = userEvent.setup();
    renderWithProviders(<Harness initial="full_sun" spy={spy} />);

    screen.getByRole('radio', { name: 'Full sun' }).focus();
    await user.keyboard('{ArrowRight}');

    expect(spy).toHaveBeenCalledWith('partial_shade');
  });

  it('takes no input when disabled', async () => {
    const spy = vi.fn();
    const user = userEvent.setup();
    renderWithProviders(<SunTileSelector value="shade" onChange={spy} disabled />);

    await user.click(screen.getByRole('radio', { name: 'Full sun' }));

    expect(spy).not.toHaveBeenCalled();
    expect(screen.getByRole('radio', { name: 'Shade' })).toBeDisabled();
  });

  it('has no critical accessibility violations', async () => {
    const { container } = renderWithProviders(<Harness initial="partial_shade" />);

    await expectNoA11yViolations(container, { minImpact: 'serious' });
  });
});
