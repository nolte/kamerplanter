import { act, cleanup, fireEvent, screen, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { expectNoA11yViolations } from '@/test/a11y/expectNoA11yViolations';

/**
 * The companion-planting layer in the editor (REQ-053 GP-FR-134, WP 8.16): switched on in the view bar, it reads the
 * judged pairs of the beds at marker LOD, draws them, and a hover or a tap on a line shows reason and score.
 * It lives outside `editor/` because it composes the editor with the real `SvgPlanRenderer` (the pointer targets are
 * drawn DOM), which `editor/` may not import (GP-NFR-009).
 */
vi.mock('../api/companionEdges', () => ({ getCompanionEdges: vi.fn() }));

import * as api from '../api/companionEdges';
import type { CompanionEdgeWire, CompanionEdgesWire } from '../api/companionEdges';
import { SvgPlanRenderer } from '../renderer/SvgPlanRenderer';
import { openPanelTab, pointer, px, setupEditor } from '../editor/editorTestKit';

const getCompanionEdges = vi.mocked(api.getCompanionEdges);
const LAYERS_KEY = 'kp_garden_plan_layers';

/** Bed b1 of the test plan holds slots s1 (3.5, 3.5) and s2 (4.5, 4.5). */
const INCOMPATIBLE: CompanionEdgeWire = {
  slot_a: { slot_key: 's1', position: { x: 3.5, y: 3.5 }, species_keys: ['sp_tomato'] },
  slot_b: { slot_key: 's2', position: { x: 4.5, y: 4.5 }, species_keys: ['sp_fennel'] },
  status: 'incompatible',
  reason_code: 'companion.incompatible',
  reason: 'Fennel inhibits the growth of most neighbours.',
  score: null,
  deciding: {
    species_a_key: 'sp_tomato',
    species_a_name: 'Tomate',
    species_b_key: 'sp_fennel',
    species_b_name: 'Fenchel',
  },
  distance_cm: 141,
};
const COMPATIBLE: CompanionEdgeWire = {
  slot_a: { slot_key: 's2', position: { x: 4.5, y: 4.5 }, species_keys: ['sp_fennel'] },
  slot_b: { slot_key: 's9', position: { x: 4.5, y: 3.5 }, species_keys: ['sp_basil'] },
  status: 'compatible',
  reason_code: 'companion.compatible',
  reason: null,
  score: 0.85,
  deciding: { species_a_key: 'sp_fennel', species_a_name: null, species_b_key: 'sp_basil', species_b_name: 'Basilikum' },
  distance_cm: null,
};
const UNPLACED: CompanionEdgeWire = { ...COMPATIBLE, slot_a: { ...COMPATIBLE.slot_a, slot_key: 's7', position: null } };

function answer(bedKey: string): CompanionEdgesWire {
  return {
    location_key: bedKey,
    edges: bedKey === 'b1' ? [INCOMPATIBLE, COMPATIBLE, UNPLACED] : [],
    total: 3,
    truncated: false,
  };
}

beforeEach(() => {
  getCompanionEdges.mockReset();
  getCompanionEdges.mockImplementation((bedKey: string) => Promise.resolve(answer(bedKey)));
});
afterEach(() => {
  cleanup();
  window.localStorage.clear();
});

const lineOf = (id: string) =>
  document.querySelector(`[data-companion-edge="${id}"] line.gp-companion-hit`) as SVGLineElement | null;

async function setupOn() {
  window.localStorage.setItem(LAYERS_KEY, JSON.stringify({ companion: true }));
  const editor = setupEditor({ renderer: new SvgPlanRenderer() });
  await waitFor(() => expect(lineOf('b1:s1|s2')).not.toBeNull());
  return editor;
}

describe('companion layer in the editor', () => {
  it('is off by default: no toggle pressed, no read, no lines', async () => {
    setupEditor({ renderer: new SvgPlanRenderer() });
    openPanelTab('layers'); // the layer switches and the legend are in the side panel's tab "Ebenen" (WP 10.5)
    const toggle = screen.getByTestId('garden-plan-layer-companion');
    expect(toggle.getAttribute('aria-pressed')).toBe('false');
    await act(async () => undefined);
    expect(getCompanionEdges).not.toHaveBeenCalled();
    expect(document.querySelector('[data-testid="garden-plan-companion-layer"]')).toBeNull();
  });

  it('reads the beds at marker LOD once, draws their placed pairs and skips a pair without a position', async () => {
    await setupOn();
    expect(getCompanionEdges.mock.calls.map(([bedKey]) => bedKey)).toEqual(['b1']);
    expect([...document.querySelectorAll('[data-companion-edge]')].map((node) => node.getAttribute('data-companion-edge'))).toEqual([
      'b1:s1|s2',
      'b1:s2|s9',
    ]);
    openPanelTab('layers');
    expect(await screen.findByTestId('garden-plan-legend-companion')).toBeTruthy();
  });

  it('shows status, species, reason and distance on hover and hides the card when the pointer leaves', async () => {
    const { canvas } = await setupOn();
    fireEvent.pointerMove(lineOf('b1:s1|s2') as SVGLineElement, pointer({ ...px(4, 4), buttons: 0 }));
    const card = await screen.findByTestId('garden-plan-companion-info');
    expect(card.getAttribute('data-companion-status')).toBe('incompatible');
    expect(card.textContent).toContain('Bad neighbours');
    expect(card.textContent).toContain('Tomate and Fenchel');
    expect(card.textContent).toContain('Reason: Fennel inhibits the growth of most neighbours.');
    expect(card.textContent).toContain('Distance: 141 cm');
    // no score for an incompatibility, and no close button on a hover card
    expect(screen.queryByTestId('garden-plan-companion-info-score')).toBeNull();
    expect(screen.queryByTestId('garden-plan-companion-info-close')).toBeNull();
    fireEvent.pointerLeave(canvas());
    await waitFor(() => expect(screen.queryByTestId('garden-plan-companion-info')).toBeNull());
  });

  it('pins the card on a tap, with the score of a compatible pair, and closes it with the button', async () => {
    const { canvas, state } = await setupOn();
    const target = lineOf('b1:s2|s9') as SVGLineElement;
    fireEvent.pointerDown(target, pointer({ ...px(4.5, 4), pointerType: 'touch' }));
    fireEvent.pointerUp(target, pointer({ ...px(4.5, 4), pointerType: 'touch' }));
    fireEvent.click(target, px(4.5, 4));
    const card = await screen.findByTestId('garden-plan-companion-info');
    expect(card.textContent).toContain('Good neighbours');
    // a species the tenant may not read has no name: the card says so instead of showing a key
    expect(card.textContent).toContain('Unnamed species and Basilikum');
    expect(card.textContent).toContain('These species help each other as neighbours.');
    expect(screen.getByTestId('garden-plan-companion-info-score').textContent).toBe('Score: 0.85 of 1');
    // the press on the line started no gesture: the bed under it is not selected
    expect(state().selection).toEqual([]);
    await expectNoA11yViolations(card, { minImpact: 'serious' });
    fireEvent.click(screen.getByTestId('garden-plan-companion-info-close'));
    await waitFor(() => expect(screen.queryByTestId('garden-plan-companion-info')).toBeNull());
    // a tap elsewhere closes a pinned card too
    fireEvent.click(target, px(4.5, 4));
    await screen.findByTestId('garden-plan-companion-info');
    fireEvent.click(canvas(), px(15, 15));
    await waitFor(() => expect(screen.queryByTestId('garden-plan-companion-info')).toBeNull());
  });

  it('lets a finger that starts on a line pan the plan, and pins the card only on a tap that did not move', async () => {
    const { canvas, state, onPan } = await setupOn();
    const target = lineOf('b1:s1|s2') as SVGLineElement;
    const touch = { pointerType: 'touch', isPrimary: true, pointerId: 7 };
    fireEvent.pointerDown(target, pointer({ ...px(4, 4), ...touch }));
    fireEvent.pointerMove(canvas(), pointer({ ...px(4, 4), clientX: px(4, 4).clientX + 60, ...touch }));
    fireEvent.pointerUp(canvas(), pointer({ ...px(4, 4), clientX: px(4, 4).clientX + 60, ...touch }));
    expect(onPan).toHaveBeenCalled();
    expect(state().selection).toEqual([]);
    expect(screen.queryByTestId('garden-plan-companion-info')).toBeNull();
    // a tap pins the card on pointer-up, without waiting for the click
    onPan.mockClear();
    fireEvent.pointerDown(target, pointer({ ...px(4, 4), ...touch }));
    fireEvent.pointerUp(target, pointer({ ...px(4, 4), ...touch }));
    expect(await screen.findByTestId('garden-plan-companion-info-close')).toBeTruthy();
    expect(onPan).not.toHaveBeenCalled();
    expect(state().selection).toEqual([]);
  });

  it('lists the pairs in view as text, incompatible first, behind a disclosure button', async () => {
    await setupOn();
    openPanelTab('layers');
    const toggle = await screen.findByTestId('garden-plan-legend-companion-list-toggle');
    expect(toggle.getAttribute('aria-expanded')).toBe('false');
    expect(screen.queryByTestId('garden-plan-legend-companion-list')).toBeNull();
    fireEvent.click(toggle);
    expect(toggle.getAttribute('aria-expanded')).toBe('true');
    const list = await screen.findByTestId('garden-plan-legend-companion-list');
    const items = [...list.querySelectorAll('li')];
    expect(items.map((item) => item.getAttribute('data-legend-companion-pair'))).toEqual(['incompatible', 'compatible']);
    expect(items[0].textContent).toBe(
      'Bad neighbours: Tomate and Fenchel. Reason: Fennel inhibits the growth of most neighbours.',
    );
    expect(items[1].textContent).toContain('Good neighbours: Unnamed species and Basilikum.');
    expect(items[1].textContent).toContain('Score: 0.85 of 1');
    await expectNoA11yViolations(screen.getByTestId('garden-plan-legend-companion'), { minImpact: 'serious' });
  });

  it('says on the card that a slot held more species than were judged', async () => {
    getCompanionEdges.mockImplementation((bedKey: string) =>
      Promise.resolve({
        ...answer(bedKey),
        edges: bedKey === 'b1' ? [{ ...INCOMPATIBLE, slot_a: { ...INCOMPATIBLE.slot_a, species_truncated: true } }] : [],
      }),
    );
    await setupOn();
    fireEvent.pointerMove(lineOf('b1:s1|s2') as SVGLineElement, pointer({ ...px(4, 4), buttons: 0 }));
    const note = await screen.findByTestId('garden-plan-companion-info-truncated');
    expect(note.textContent).toBe('A slot holds more than 8 species; the verdict covers only the first 8.');
  });

  it('reads nothing below the marker LOD', async () => {
    window.localStorage.setItem(LAYERS_KEY, JSON.stringify({ companion: true }));
    // 5 px/m: the two slots of b1 are 7 px apart, below the 10 px marker spacing
    setupEditor({
      renderer: new SvgPlanRenderer(),
      viewport: { originM: [0, 20], pxPerM: 5, widthPx: 800, heightPx: 800 },
    });
    await act(async () => undefined);
    expect(getCompanionEdges).not.toHaveBeenCalled();
  });
});
