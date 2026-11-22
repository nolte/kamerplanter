import { useSyncExternalStore, type ReactNode } from 'react';
import { moveSnapMark, selectOverlay } from './tools/selectMachine';
import type { Overlay } from './tools/machineTypes';
import type { SnapMark } from './tools/snap';
import type { LiveMoveStore } from './tools/useEditorTools';
import type { DimensionItem } from './DimensionLabels';
import type { HandleSet } from './tools/handles';
import type { Point } from '../model/types';

export interface LiveMoveView {
  overlay: Overlay;
  dimensionItems: DimensionItem[];
  snapMark: SnapMark | null;
  /** The selection's handles; hidden while a move runs, like the committed state does for a move. */
  handles: HandleSet | null;
  handlesPx: Point[] | undefined;
}

interface LiveMoveLayerProps extends LiveMoveView {
  liveMove: LiveMoveStore;
  children: (view: LiveMoveView) => ReactNode;
}

/**
 * The part of the editor that follows a move gesture pointer move by pointer move (GP-NFR-011, GP-NFR-033): the ghost
 * outline, its size labels and the move's snap marker. It subscribes to the tools' live move state, so a pointer move
 * re-renders this layer - and not the editor with its toolbar, panels and lists. Between moves (and for every other
 * gesture) it shows what the editor passed in.
 */
export function LiveMoveLayer({
  liveMove,
  overlay,
  dimensionItems,
  snapMark,
  handles,
  handlesPx,
  children,
}: LiveMoveLayerProps) {
  const live = useSyncExternalStore(liveMove.subscribe, liveMove.get, liveMove.get);
  if (live === null) return <>{children({ overlay, dimensionItems, snapMark, handles, handlesPx })}</>;
  const liveOverlay = selectOverlay(live);
  return (
    <>
      {children({
        overlay: liveOverlay,
        dimensionItems: liveOverlay.shapes.map(({ key, shape }) => ({ key, shape })),
        snapMark: moveSnapMark(live),
        handles: null,
        handlesPx: undefined,
      })}
    </>
  );
}
