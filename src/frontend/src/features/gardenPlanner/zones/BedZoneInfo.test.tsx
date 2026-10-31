/**
 * The water info of a bed (GP-UX-006): it names the zone by the same number the legend and the hatching use.
 */
import { cleanup, screen } from '@testing-library/react';
import { afterEach, describe, expect, it } from 'vitest';
import { renderWithProviders } from '@/test/helpers';
import { BedZoneInfo } from './BedZoneInfo';
import { ZoneLegend } from './ZoneLegend';
import { zone } from './zonesTestKit';

afterEach(() => cleanup());

const ZONES = [
  zone('z1', { name: 'Front', irrigation_type: 'drip', location_keys: ['loc_a'] }),
  zone('z2', { name: 'Back', irrigation_type: 'drip', location_keys: ['loc_b'] }),
];

describe('BedZoneInfo', () => {
  it('names the zone with the number the legend gives it', () => {
    renderWithProviders(
      <>
        <ZoneLegend zones={ZONES} showZones showLastWatered={false} />
        <BedZoneInfo bedKey="loc_b" zones={ZONES} lastWateredAt={null} nowMs={Date.now()} />
      </>,
    );
    expect(screen.getByTestId('garden-plan-legend-zones')).toHaveTextContent('2. Back, Drip irrigation');
    expect(screen.getByTestId('garden-plan-panel-zone')).toHaveTextContent('Irrigation zone: 2. Back');
  });

  it('names no zone for a bed outside every zone', () => {
    renderWithProviders(<BedZoneInfo bedKey="loc_c" zones={ZONES} lastWateredAt={null} nowMs={Date.now()} />);
    expect(screen.queryByTestId('garden-plan-panel-zone')).toBeNull();
    expect(screen.getByTestId('garden-plan-panel-last-watered')).toHaveTextContent('No watering recorded.');
  });
});
