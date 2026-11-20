/**
 * The side panel's form from the width actually available (#3034, operator decision): docked beside the canvas where
 * the canvas keeps `MIN_CANVAS_WIDTH_PX`, a drawer over it where it would not, the bottom sheet below md.
 *
 * The widths are the ones of the app at a given window (the app sidebar of 240 px from md, the page padding of
 * 2 x 16 px, the 112 px rail and its 8 px gap): canvas room = window - 240 - 32 - 112 - 8. At 820 px that is 428 px -
 * the issue measured the docked canvas there at 76 px = 428 - 344 - 8.
 */
import { describe, expect, it } from 'vitest';
import {
  DRAWER_TOP_PX,
  MIN_CANVAS_WIDTH_PX,
  PANEL_GAP_PX,
  PANEL_WIDTH_PX,
  ZOOM_OVERLAY_INSET_PX,
  drawerCoverPx,
  sidePanelVariant,
} from './layout';

const roomAt = (windowPx: number) => windowPx - 240 - 32 - 112 - PANEL_GAP_PX;

describe('sidePanelVariant (#3034)', () => {
  it('opens the panel as a drawer at 820 px, where docking left the canvas 76 px (TC-053-102)', () => {
    expect(roomAt(820) - PANEL_WIDTH_PX - PANEL_GAP_PX).toBe(76);
    expect(sidePanelVariant(false, roomAt(820), false)).toBe('drawer');
  });

  it('opens a drawer at 1024 px as well: docked, the canvas would keep 280 px, less than the minimum', () => {
    expect(roomAt(1024) - PANEL_WIDTH_PX - PANEL_GAP_PX).toBe(280);
    expect(sidePanelVariant(false, roomAt(1024), false)).toBe('drawer');
  });

  it('docks the panel where the canvas keeps at least the minimum width beside it', () => {
    expect(sidePanelVariant(false, roomAt(1280), false)).toBe('docked');
    expect(sidePanelVariant(false, roomAt(1366), false)).toBe('docked');
    expect(sidePanelVariant(false, roomAt(1920), false)).toBe('docked');
  });

  it('decides at the minimum canvas width exactly: equal docks, one pixel less is a drawer', () => {
    const threshold = MIN_CANVAS_WIDTH_PX + PANEL_WIDTH_PX + PANEL_GAP_PX;
    expect(sidePanelVariant(false, threshold, false)).toBe('docked');
    expect(sidePanelVariant(false, threshold - 1, false)).toBe('drawer');
  });

  it('keeps the bottom sheet below md, whatever the width', () => {
    expect(sidePanelVariant(true, roomAt(390), false)).toBe('sheet');
    expect(sidePanelVariant(true, 5000, false)).toBe('sheet');
    expect(sidePanelVariant(true, null, false)).toBe('sheet');
    expect(sidePanelVariant(true, 5000, true)).toBe('sheet');
  });

  it('docks while nothing is measured yet (first render, jsdom)', () => {
    expect(sidePanelVariant(false, null, false)).toBe('docked');
  });

  it('always docks in the list view: the list wraps into any width and nothing pans it out from under a drawer', () => {
    // The room the list view measures is the whole row (no rail); at 548 px a drawer would cover the move buttons.
    expect(sidePanelVariant(false, 548, true)).toBe('docked');
    expect(sidePanelVariant(false, 1, true)).toBe('docked');
    expect(sidePanelVariant(false, null, true)).toBe('docked');
  });
});

describe('drawerCoverPx (#3034)', () => {
  it('is the panel width only while the open drawer lies over the plan', () => {
    expect(drawerCoverPx('drawer', true, true)).toBe(PANEL_WIDTH_PX);
    expect(drawerCoverPx('drawer', false, true)).toBe(0);
    expect(drawerCoverPx('drawer', true, false)).toBe(0);
    expect(drawerCoverPx('docked', true, true)).toBe(0);
    expect(drawerCoverPx('sheet', true, true)).toBe(0);
  });
});

describe('minimum canvas and drawer top', () => {

  it('never lets the minimum canvas be narrower than the zoom overlay with its insets', () => {
    // The zoom overlay is about 260 px wide in German ("−", "100 %", "+", "Einpassen").
    expect(MIN_CANVAS_WIDTH_PX).toBeGreaterThanOrEqual(260 + 2 * ZOOM_OVERLAY_INSET_PX);
    // The drawer starts below the zoom overlay's 48 px row and its insets.
    expect(DRAWER_TOP_PX).toBe(48 + 2 * ZOOM_OVERLAY_INSET_PX);
  });
});
