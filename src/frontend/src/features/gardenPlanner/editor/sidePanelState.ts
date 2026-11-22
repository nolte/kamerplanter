/**
 * The state rule of the editor's side panel (REQ-053 §17.3, GP-UX-068, AC-5/AC-17), as pure transitions and the
 * hook that drives them.
 *
 * - A new selection opens the panel on "Eigenschaften" (properties).
 * - When the selection is cleared, the panel collapses only if the selection opened it.
 * - A panel the user opened stays open across selecting and deselecting.
 * - A panel the user closed stays closed until the user opens it or makes a new selection.
 * - Opened without a selection, the panel shows the tab the user used last; the first time "Ansicht" (view).
 *
 * The last used tab lives in component state only (no storage): it is a habit of this session, not a setting.
 */
import { useCallback, useMemo, useState } from 'react';

export const SIDE_PANEL_TABS = ['properties', 'view', 'layers', 'zones'] as const;
export type SidePanelTab = (typeof SIDE_PANEL_TABS)[number];

/** Who opened the panel: the selection (it collapses again with it) or the user (it stays). */
export type PanelOpener = 'selection' | 'user';

export interface SidePanelState {
  open: boolean;
  tab: SidePanelTab;
  /** `null` while the panel is collapsed. */
  openedBy: PanelOpener | null;
  /** The tab the user chose last; `null` until they chose one. */
  lastTab: SidePanelTab | null;
  /** The selection the state last saw (`''` = nothing selected): a different one is a new selection. */
  seenSelection: string;
}

/** The tab a panel opened without a selection shows first (GP-UX-068). */
export const FIRST_TAB: SidePanelTab = 'view';

export const INITIAL_SIDE_PANEL: SidePanelState = {
  open: false,
  tab: FIRST_TAB,
  openedBy: null,
  lastTab: null,
  seenSelection: '',
};

/** The selection changed to `selection` (a signature of the selected keys, `''` for none). */
export function withSelection(state: SidePanelState, selection: string): SidePanelState {
  if (selection === state.seenSelection) return state;
  if (selection === '') {
    const collapse = state.open && state.openedBy === 'selection';
    return collapse
      ? { ...state, open: false, openedBy: null, seenSelection: '' }
      : { ...state, seenSelection: '' };
  }
  // A new selection: open on the properties; a panel the user opened stays theirs (it survives the deselect).
  const keptByUser = state.open && state.openedBy === 'user';
  return {
    ...state,
    open: true,
    tab: 'properties',
    openedBy: keptByUser ? 'user' : 'selection',
    seenSelection: selection,
  };
}

/** The panel switch: closes an open panel, opens a closed one as the user's. */
export function toggled(state: SidePanelState): SidePanelState {
  if (state.open) return { ...state, open: false, openedBy: null };
  const tab = state.seenSelection !== '' ? 'properties' : (state.lastTab ?? FIRST_TAB);
  return { ...state, open: true, openedBy: 'user', tab };
}

/** The user closed the panel (its close button, or the close button of a tab's content). */
export function closed(state: SidePanelState): SidePanelState {
  return state.open ? { ...state, open: false, openedBy: null } : state;
}

/** The user chose `tab`: in the panel's tab list, or through an entry that opens the panel on it. */
export function withTab(state: SidePanelState, tab: SidePanelTab): SidePanelState {
  return {
    ...state,
    open: true,
    openedBy: state.open ? state.openedBy : 'user',
    tab,
    lastTab: tab,
  };
}

export interface SidePanel {
  open: boolean;
  tab: SidePanelTab;
  openedBy: PanelOpener | null;
  toggle: () => void;
  close: () => void;
  /** Show `tab`, opening the panel if needed. */
  showTab: (tab: SidePanelTab) => void;
}

/**
 * The side panel's state for the current selection. `selection` is a signature of what is selected (the keys,
 * joined), `''` while nothing is; the transition is applied in the render that sees the new value (the documented
 * "adjust state while rendering" pattern), so the panel opens in the same frame as the selection appears.
 */
export function useSidePanel(selection: string): SidePanel {
  const [state, setState] = useState<SidePanelState>(() =>
    withSelection(INITIAL_SIDE_PANEL, selection),
  );
  let current = state;
  if (state.seenSelection !== selection) {
    current = withSelection(state, selection);
    setState(current);
  }
  const toggle = useCallback(() => setState(toggled), []);
  const close = useCallback(() => setState(closed), []);
  const showTab = useCallback(
    (tab: SidePanelTab) => setState((previous) => withTab(previous, tab)),
    [],
  );
  const { open, tab, openedBy } = current;
  return useMemo(
    () => ({ open, tab, openedBy, toggle, close, showTab }),
    [open, tab, openedBy, toggle, close, showTab],
  );
}
