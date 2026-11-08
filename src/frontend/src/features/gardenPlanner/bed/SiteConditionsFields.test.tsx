/** Microclimate, wind, slope, aspect and access sides of a bed (REQ-053 GP-FR-162/163/168, WP 8.22). */
import { cleanup, screen, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { useState } from 'react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { expectNoA11yViolations } from '@/test/a11y/expectNoA11yViolations';
import { renderWithProviders } from '@/test/helpers';
import SiteConditionsFields, { parseDegrees } from './SiteConditionsFields';
import { appliedSitePatch, changedSitePatch, mergeSitePatch } from './siteConditionsPatch';
import type { SiteConditionsPatch, SiteConditionsSlice } from './types';

afterEach(() => cleanup());

function Harness({
  initial = {},
  spy,
  touchTarget,
}: {
  initial?: SiteConditionsSlice;
  spy?: (patch: SiteConditionsPatch) => void;
  touchTarget?: number;
}) {
  const [patch, setPatch] = useState<SiteConditionsPatch>({});
  return (
    <SiteConditionsFields
      value={appliedSitePatch(initial, patch)}
      touchTarget={touchTarget}
      onChange={(next) => {
        spy?.(next);
        setPatch((previous) => mergeSitePatch(previous, next));
      }}
    />
  );
}

describe('SiteConditionsFields', () => {
  it('checks "Unknown" by default in every chip group', () => {
    renderWithProviders(<Harness />);
    for (const group of ['frost', 'heat', 'wind']) {
      const radios = within(screen.getByTestId(`bed-view-site-conditions-${group}`)).getAllByRole('radio');
      expect(radios[radios.length - 1]).toBeChecked();
    }
    expect(screen.getAllByRole('checkbox', { name: /North|East|South|West/ }).every((box) => !(box as HTMLInputElement).checked)).toBe(true);
  });

  it('reports one microclimate key per tap', async () => {
    const spy = vi.fn();
    const user = userEvent.setup();
    renderWithProviders(<Harness spy={spy} />);

    await user.click(within(screen.getByTestId('bed-view-site-conditions-frost')).getByRole('radio', { name: 'High' }));
    await user.click(screen.getByRole('switch', { name: 'Cold-air pocket' }));
    await user.click(within(screen.getByTestId('bed-view-site-conditions-heat')).getByRole('radio', { name: 'Wall' }));

    expect(spy.mock.calls.map(([patch]) => patch)).toEqual([
      { microclimate: { frost_risk: 'high' } },
      { microclimate: { cold_air_pocket: true } },
      { microclimate: { heat_retention: 'wall' } },
    ]);
  });

  it('reports the wind and does not report the chip that is already chosen', async () => {
    const spy = vi.fn();
    const user = userEvent.setup();
    renderWithProviders(<Harness initial={{ wind_exposure: 'normal' }} spy={spy} />);

    await user.click(screen.getByRole('radio', { name: 'Normal', checked: true }));
    expect(spy).not.toHaveBeenCalled();
    await user.click(screen.getByRole('radio', { name: 'Exposed' }));
    expect(spy).toHaveBeenCalledWith({ wind_exposure: 'exposed' });
  });

  it('toggles access sides and reports the whole list', async () => {
    const spy = vi.fn();
    const user = userEvent.setup();
    renderWithProviders(<Harness initial={{ access_sides: ['S'] }} spy={spy} />);

    await user.click(screen.getByRole('checkbox', { name: 'North' }));
    await user.click(screen.getByRole('checkbox', { name: 'South' }));

    expect(spy.mock.calls.map(([patch]) => patch)).toEqual([
      { access_sides: ['S', 'N'] },
      { access_sides: ['N'] },
    ]);
  });

  it('toggles the competition flags and reports the whole list (GP-FR-165)', async () => {
    const spy = vi.fn();
    const user = userEvent.setup();
    renderWithProviders(<Harness initial={{ flags: ['allelopathy_risk'] }} spy={spy} />);

    const group = screen.getByRole('group', { name: 'Competition at the site' });
    expect(within(group).getByRole('checkbox', { name: 'Allelopathy risk' })).toBeChecked();
    expect(within(group).getByRole('checkbox', { name: 'Root competition' })).not.toBeChecked();
    await user.click(within(group).getByRole('checkbox', { name: 'Root competition' }));
    await user.click(within(group).getByRole('checkbox', { name: 'Allelopathy risk' }));

    expect(spy.mock.calls.map(([patch]) => patch)).toEqual([
      { flags: ['allelopathy_risk', 'root_competition'] },
      { flags: ['root_competition'] },
    ]);
  });

  it('commits slope and aspect on Enter, clears with an empty entry and flags an unreadable one', async () => {
    const spy = vi.fn();
    const user = userEvent.setup();
    renderWithProviders(<Harness initial={{ slope_deg: 5 }} spy={spy} />);

    const slope = screen.getByRole('textbox', { name: 'Slope (degrees)' });
    expect(slope).toHaveValue('5');
    await user.clear(slope);
    await user.type(slope, '12,5{Enter}');
    expect(spy).toHaveBeenLastCalledWith({ slope_deg: 12.5 });

    await user.clear(slope);
    await user.type(slope, '120{Enter}');
    expect(await screen.findByText('Enter a number from 0 to 90.')).toBeInTheDocument();
    expect(spy).toHaveBeenCalledTimes(1);

    await user.clear(slope);
    await user.keyboard('{Enter}');
    expect(spy).toHaveBeenLastCalledWith({ slope_deg: null });

    await user.type(screen.getByRole('textbox', { name: 'Aspect (degrees)' }), '360{Enter}');
    expect(await screen.findByText('Enter a number from 0 to under 360.')).toBeInTheDocument();
  });

  it('does not rewrite a stored value that is only shown rounded when the field is left untouched', async () => {
    const spy = vi.fn();
    const user = userEvent.setup();
    renderWithProviders(<Harness initial={{ slope_deg: 12.345 }} spy={spy} />);

    const slope = screen.getByRole('textbox', { name: 'Slope (degrees)' });
    expect(slope).toHaveValue('12.3');
    await user.click(slope);
    await user.tab();
    expect(spy).not.toHaveBeenCalled();
  });

  it('keeps every chip at the touch target it was given', () => {
    renderWithProviders(<Harness touchTarget={64} />);
    expect(screen.getByTestId('bed-view-site-conditions-wind-exposed')).toHaveStyle({ minHeight: '64px' });
  });

  it('has no accessibility violations', async () => {
    const { container } = renderWithProviders(
      <Harness initial={{ wind_exposure: 'exposed', flags: ['root_competition'] }} />,
    );
    await expectNoA11yViolations(container, { minElements: 10 });
  });
});

describe('parseDegrees', () => {
  it.each([
    ['', 90, true, null],
    ['0', 90, true, 0],
    ['90', 90, true, 90],
    ['90,5', 90, true, undefined],
    ['359.9', 360, false, 359.9],
    ['360', 360, false, undefined],
    ['abc', 90, true, undefined],
    ['-1', 90, true, undefined],
  ])('%j (max %d, inclusive %s) -> %j', (text, max, inclusive, expected) => {
    expect(parseDegrees(text, max, inclusive)).toBe(expected);
  });
});

describe('the patch helpers', () => {
  const stored: SiteConditionsSlice = {
    microclimate: { frost_risk: 'high', cold_air_pocket: false },
    wind_exposure: 'exposed',
    access_sides: ['N', 'S'],
  };

  it('drops keys that were set back to what is stored and keeps the others', () => {
    const patch: SiteConditionsPatch = {
      microclimate: { frost_risk: 'high', heat_retention: 'wall', cold_air_pocket: false },
      wind_exposure: 'normal',
      access_sides: ['S', 'N'],
      slope_deg: null,
    };
    expect(changedSitePatch(stored, patch)).toEqual({
      microclimate: { heat_retention: 'wall' },
      wind_exposure: 'normal',
    });
  });

  it('compares with the defaults a missing stored value stands for', () => {
    expect(changedSitePatch(null, { microclimate: { frost_risk: 'unknown', cold_air_pocket: false }, wind_exposure: 'unknown' })).toEqual({});
    expect(changedSitePatch(undefined, { slope_deg: 0 })).toEqual({ slope_deg: 0 });
  });

  it('never sends the legacy frost_exposed field (the server keeps it in step, #2512)', () => {
    const out = changedSitePatch(stored, { microclimate: { frost_risk: 'low' } });
    expect(out).toEqual({ microclimate: { frost_risk: 'low' } });
    expect(JSON.stringify(out)).not.toContain('frost_exposed');
  });

  it('sends the flags only when the set differs from what is stored, whatever the order', () => {
    const flagged: SiteConditionsSlice = { flags: ['root_competition', 'allelopathy_risk'] };
    expect(changedSitePatch(flagged, { flags: ['allelopathy_risk', 'root_competition'] })).toEqual({});
    expect(changedSitePatch(flagged, { flags: ['root_competition'] })).toEqual({ flags: ['root_competition'] });
    expect(changedSitePatch(flagged, { flags: [] })).toEqual({ flags: [] });
    expect(changedSitePatch(null, { flags: [] })).toEqual({});
    expect(changedSitePatch(undefined, { flags: ['allelopathy_risk'] })).toEqual({ flags: ['allelopathy_risk'] });
  });

  it('replaces the flags as a whole when patches are merged', () => {
    expect(mergeSitePatch({ flags: ['root_competition'] }, { flags: ['allelopathy_risk'] })).toEqual({
      flags: ['allelopathy_risk'],
    });
  });

  it('merges microclimate keys across patches', () => {
    expect(mergeSitePatch({ microclimate: { frost_risk: 'low' } }, { microclimate: { cold_air_pocket: true } })).toEqual({
      microclimate: { frost_risk: 'low', cold_air_pocket: true },
    });
  });
});
