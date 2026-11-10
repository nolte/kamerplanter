/**
 * The state rule of the side panel (REQ-053 GP-UX-068, AC-17) as pure transitions: every one of the four sentences
 * of the rule, plus the tab a panel opened without a selection shows.
 */
import { describe, expect, it } from 'vitest';
import {
  FIRST_TAB,
  INITIAL_SIDE_PANEL,
  closed,
  toggled,
  withSelection,
  withTab,
  type SidePanelState,
} from './sidePanelState';

const A = 'location:a';
const B = 'location:b';

describe('side panel state rule (GP-UX-068, AC-17)', () => {
  it('a new selection opens the panel on the properties', () => {
    const next = withSelection(INITIAL_SIDE_PANEL, A);
    expect(next).toMatchObject({ open: true, tab: 'properties', openedBy: 'selection' });
  });

  it('the deselect collapses the panel only when the selection opened it', () => {
    const bySelection = withSelection(INITIAL_SIDE_PANEL, A);
    expect(withSelection(bySelection, '')).toMatchObject({ open: false, openedBy: null });
  });

  it('a panel the user opened stays open across selecting and deselecting', () => {
    const userOpened = toggled(INITIAL_SIDE_PANEL);
    const selected = withSelection(userOpened, A);
    expect(selected).toMatchObject({ open: true, tab: 'properties', openedBy: 'user' });
    const deselected = withSelection(selected, '');
    expect(deselected).toMatchObject({ open: true, openedBy: 'user' });
    // ... and over the next selection too.
    expect(withSelection(deselected, B)).toMatchObject({ open: true, tab: 'properties', openedBy: 'user' });
  });

  it('a panel the user closed stays closed until the user opens it or a new selection is made', () => {
    const selected = withSelection(INITIAL_SIDE_PANEL, A);
    const userClosed = closed(selected);
    expect(userClosed).toMatchObject({ open: false, openedBy: null });
    // The same selection (another render, a move of the selected bed) does not open it again.
    expect(withSelection(userClosed, A)).toBe(userClosed);
    // A deselect leaves it closed.
    const deselected = withSelection(userClosed, '');
    expect(deselected.open).toBe(false);
    // A new selection opens it again, as the selection's.
    expect(withSelection(deselected, B)).toMatchObject({ open: true, tab: 'properties', openedBy: 'selection' });
    // So does the user.
    expect(toggled(userClosed)).toMatchObject({ open: true, openedBy: 'user', tab: 'properties' });
  });

  it('a different selection while open is a new selection: back to the properties', () => {
    const onLayers = withTab(withSelection(INITIAL_SIDE_PANEL, A), 'layers');
    expect(onLayers).toMatchObject({ open: true, tab: 'layers', openedBy: 'selection' });
    expect(withSelection(onLayers, `${A}|${B}`)).toMatchObject({ tab: 'properties', openedBy: 'selection' });
  });

  it('opened without a selection it shows "Ansicht" first, afterwards the tab used last', () => {
    expect(FIRST_TAB).toBe('view');
    const first = toggled(INITIAL_SIDE_PANEL);
    expect(first).toMatchObject({ open: true, tab: 'view', openedBy: 'user' });
    const zones = withTab(first, 'zones');
    const reopened = toggled(toggled(zones));
    expect(reopened).toMatchObject({ open: true, tab: 'zones' });
    // A selection in between does not change what "last used" means.
    const viaSelection = withSelection(withSelection(closed(reopened), A), '');
    expect(toggled(viaSelection).tab).toBe('zones');
  });

  it('a tab chosen while collapsed opens the panel as the user\'s', () => {
    const state: SidePanelState = withTab(INITIAL_SIDE_PANEL, 'zones');
    expect(state).toMatchObject({ open: true, tab: 'zones', openedBy: 'user', lastTab: 'zones' });
    // Choosing a tab keeps who opened an open panel.
    expect(withTab(withSelection(INITIAL_SIDE_PANEL, A), 'view').openedBy).toBe('selection');
  });
});
