/**
 * REQ-053 GP-FR-016 (#2894): the compass shows today's sunrise and sunset directions when the site has a GPS
 * position - two marks on the ring, turned with geographic north, and a caption with time, direction and azimuth -
 * and nothing without one. The azimuths come from the plan read model (`sun_directions`, server-side
 * `sun_calculator`); the compass does no astronomy. No shading (§29).
 */
import { cleanup, render, screen } from '@testing-library/react';
import { afterEach, describe, expect, it } from 'vitest';
import { ThemeContextProvider } from '@/theme';
import { expectNoA11yViolations } from '@/test/a11y/expectNoA11yViolations';
import type { PlanSunDirections } from '../model/types';
import { Compass } from './Compass';

const SUN: PlanSunDirections = {
  day: '2026-03-20',
  sunrise: { azimuth_deg: 90, time: '06:12' },
  sunset: { azimuth_deg: 270.4, time: '18:24' },
};
/** `DIAL_PX / 2` and `SUN_RADIUS` of the component. */
const CENTER = 28;
const RADIUS = 25;

function renderCompass(props: { angleDeg?: number; sunDirections?: PlanSunDirections | null }) {
  return render(
    <ThemeContextProvider>
      <Compass angleDeg={props.angleDeg ?? 0} onChange={() => undefined} sunDirections={props.sunDirections} />
    </ThemeContextProvider>,
  );
}

function position(testId: string): [number, number] {
  const mark = screen.getByTestId(testId);
  return [Number(mark.getAttribute('cx')), Number(mark.getAttribute('cy'))];
}

afterEach(() => {
  cleanup();
});

describe('sunrise and sunset in the compass (GP-FR-016)', () => {
  it('shows nothing without a GPS position', () => {
    renderCompass({ sunDirections: null });

    expect(screen.queryByTestId('garden-plan-compass-sunrise')).not.toBeInTheDocument();
    expect(screen.queryByTestId('garden-plan-compass-sunset')).not.toBeInTheDocument();
    expect(screen.queryByTestId('garden-plan-compass-sun')).not.toBeInTheDocument();
  });

  it('shows nothing when the prop is absent', () => {
    renderCompass({});

    expect(screen.queryByTestId('garden-plan-compass-sun')).not.toBeInTheDocument();
  });

  it('marks both directions on the ring and names time, direction and azimuth', () => {
    renderCompass({ sunDirections: SUN });

    const [riseX, riseY] = position('garden-plan-compass-sunrise');
    expect(riseX).toBeCloseTo(CENTER + RADIUS, 6); // east lies right when north is up
    expect(riseY).toBeCloseTo(CENTER, 6);
    const [setX] = position('garden-plan-compass-sunset');
    expect(setX).toBeLessThan(CENTER - RADIUS + 0.5); // west lies left
    expect(screen.getByTestId('garden-plan-compass-sun')).toHaveTextContent(
      'Today: sunrise 06:12, direction East (90°), sunset 18:24, direction West (270.4°).',
    );
  });

  it('turns the marks with geographic north', () => {
    renderCompass({ angleDeg: 90, sunDirections: SUN }); // north points right: east points down

    const [riseX, riseY] = position('garden-plan-compass-sunrise');
    expect(riseX).toBeCloseTo(CENTER, 6);
    expect(riseY).toBeCloseTo(CENTER + RADIUS, 6);
  });

  it('has no accessibility violations with the marks', async () => {
    const view = renderCompass({ sunDirections: SUN });

    await expectNoA11yViolations(view.container);
  });
});
