import { describe, expect, it } from 'vitest';
import {
  GRID_STEPS_M,
  MAX_PX_PER_M,
  displayGridStep,
  formatArea,
  formatLength,
  gridStepLabel,
  nearestGridStep,
  pxPerMToPercent,
  scaleBarLabel,
  scaleBarLengthM,
  snapToStep,
  stepZoom,
  zoomAround,
} from './units';

describe('formatLength', () => {
  it('shows metres with two decimals and centimetres with at most one', () => {
    expect(formatLength(2.5, 'm', 'en')).toBe('2.50 m');
    expect(formatLength(2.5, 'm', 'de')).toBe('2,50 m');
    expect(formatLength(0.6, 'cm', 'en')).toBe('60 cm');
    expect(formatLength(0.0125, 'cm', 'en')).toBe('1.3 cm');
  });
  it('formats areas in square metres', () => {
    expect(formatArea(2.4, 'de')).toBe('2,40 m²');
  });
});

describe('grid steps (GP-FR-011)', () => {
  it('offers 1 cm, 5 cm, 10 cm, 25 cm, 50 cm and 1 m', () => {
    expect([...GRID_STEPS_M]).toEqual([0.01, 0.05, 0.1, 0.25, 0.5, 1]);
  });
  it('labels the steps in cm below one metre', () => {
    expect(GRID_STEPS_M.map((step) => gridStepLabel(step, 'en'))).toEqual([
      '1 cm',
      '5 cm',
      '10 cm',
      '25 cm',
      '50 cm',
      '1 m',
    ]);
  });
  it('maps a stored default to the nearest step, 10 cm without one', () => {
    expect(nearestGridStep(0.12)).toBe(0.1);
    expect(nearestGridStep(0.4)).toBe(0.5);
    expect(nearestGridStep(undefined)).toBe(0.1);
    expect(nearestGridStep(-1)).toBe(0.1);
  });
  it('draws lines only when they are at least 8 px apart, else the next coarser step', () => {
    expect(displayGridStep(0.1, 100)).toBe(0.1); // 10 px
    expect(displayGridStep(0.1, 80)).toBe(0.1); // exactly 8 px
    expect(displayGridStep(0.1, 79)).toBe(0.25); // 7.9 px
    expect(displayGridStep(0.01, 100)).toBe(0.1); // 1 cm = 1 px, 5 cm = 5 px, 10 cm = 10 px
    expect(displayGridStep(0.01, 800)).toBe(0.01);
    expect(displayGridStep(1, 4)).toBe(2);
    expect(displayGridStep(1, 1)).toBe(10); // 2 m = 2 px, 5 m = 5 px
    expect(displayGridStep(1, 0.5)).toBe(20);
  });
  it('snaps to a multiple of the step without float noise (GP-ACC-006)', () => {
    expect(snapToStep(0.23, 0.1)).toBe(0.2);
    expect(snapToStep(0.35, 0.1)).toBe(0.4);
    expect(snapToStep(1.2345, 0.01)).toBe(1.23);
    expect(snapToStep(-0.26, 0.25)).toBe(-0.25);
    expect(snapToStep(0.3, 0.1)).toBe(0.3);
  });
});

describe('zoom (GP-FR-009, GP-FR-150)', () => {
  it('100 percent is 100 px/m', () => {
    expect(pxPerMToPercent(100)).toBe(100);
    expect(pxPerMToPercent(25)).toBe(25);
  });
  it('the highest zoom shows 1 cm with 8 px', () => {
    expect(MAX_PX_PER_M * 0.01).toBe(8);
  });
  it('steps through 25, 50, 100, 200 and 400 percent', () => {
    expect(stepZoom(100, 1, 10)).toBe(200);
    expect(stepZoom(100, -1, 10)).toBe(50);
    expect(stepZoom(150, 1, 10)).toBe(200);
    expect(stepZoom(150, -1, 10)).toBe(100);
    expect(stepZoom(400, 1, 10)).toBe(MAX_PX_PER_M);
    expect(stepZoom(MAX_PX_PER_M, 1, 10)).toBe(MAX_PX_PER_M);
  });
  it('never goes below the fit zoom, so the small levels collapse on a large plan', () => {
    expect(stepZoom(100, -1, 60)).toBe(60);
    expect(stepZoom(60, -1, 60)).toBe(60);
    expect(stepZoom(130, -1, 130)).toBe(130);
  });
  it('zooms around an anchor that stays put on screen', () => {
    const view = { originM: [0, 10] as [number, number], pxPerM: 100 };
    const zoomed = zoomAround(view, 200, [300, 200], 10);
    // the model point under (300, 200) is (3, 8) before and after
    expect(zoomed.pxPerM).toBe(200);
    expect(zoomed.originM[0] + 300 / 200).toBeCloseTo(3, 9);
    expect(zoomed.originM[1] - 200 / 200).toBeCloseTo(8, 9);
  });
  it('clamps to the limits', () => {
    const view = { originM: [0, 10] as [number, number], pxPerM: 100 };
    expect(zoomAround(view, 99999, [0, 0], 10).pxPerM).toBe(MAX_PX_PER_M);
    expect(zoomAround(view, 1, [0, 0], 40).pxPerM).toBe(40);
  });
});

describe('scale bar', () => {
  it('uses 1 m, 5 m or 10 m depending on the zoom', () => {
    expect(scaleBarLengthM(100)).toBe(1); // 100 px; 5 m would be 500 px
    expect(scaleBarLengthM(40)).toBe(1); // 5 m = 200 px > 160
    expect(scaleBarLengthM(20)).toBe(5); // 100 px
    expect(scaleBarLengthM(10)).toBe(10); // 100 px
    expect(scaleBarLengthM(1)).toBe(100);
  });
  it('stays visible at extreme zoom', () => {
    expect(scaleBarLengthM(800)).toBe(0.1);
    expect(scaleBarLengthM(100000)).toBe(0.01);
    expect(scaleBarLengthM(0.001)).toBe(1000);
  });
  it('labels in cm below one metre', () => {
    expect(scaleBarLabel(0.5, 'en')).toBe('50 cm');
    expect(scaleBarLabel(5, 'en')).toBe('5 m');
  });
});
