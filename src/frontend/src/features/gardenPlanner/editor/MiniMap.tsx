/**
 * The mini-map (REQ-053 GP-UX-014): a 120 x 120 px overview at the bottom right of the plan - the beds and
 * garden objects as boxes, the boundary, and the rectangle of what the viewport shows. A click or tap jumps
 * the view there. It is a pointer shortcut only: the keyboard has the arrow keys and the list view, so it is
 * announced as an image and stays out of the tab order. It never takes the gestures of the plan beneath it.
 *
 * It is memoised on its props (the plan model, its extent, the viewport): the editor re-renders on every pointer
 * move of a drag, the mini-map does not, and a pan redraws only the viewport rectangle, not the boxes (#2536).
 */
import { memo, useMemo, type MouseEvent as ReactMouseEvent } from 'react';
import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import { useTheme } from '@mui/material/styles';
import { boundingBox } from '../model/geometry';
import type { PlanModel } from '../model/planModel';
import type { BoundingBox, Point } from '../model/types';
import type { Viewport } from '../renderer';
import {
  fromMiniMap,
  MINI_MAP_PX,
  miniMapScale,
  toMiniMap,
  viewportBox,
  type MiniMapScale,
} from './miniMap';

interface MiniMapProps {
  plan: PlanModel;
  /** The extent of the whole plan (`planContentBounds`). */
  extent: BoundingBox;
  viewport: Viewport;
  /** Pan the view by this many canvas pixels so that the clicked model point is centred. */
  onJump: (target: Point) => void;
}

const stop = (event: { stopPropagation: () => void }) => event.stopPropagation();

function boxRect(box: BoundingBox, extent: BoundingBox, fit: MiniMapScale) {
  const [x0, y1] = toMiniMap([box[0], box[1]], extent, fit);
  const [x1, y0] = toMiniMap([box[2], box[3]], extent, fit);
  return { x: x0, y: y0, width: Math.max(x1 - x0, 1), height: Math.max(y1 - y0, 1) };
}

function MiniMapView({ plan, extent, viewport, onJump }: MiniMapProps) {
  const { t } = useTranslation();
  const { palette } = useTheme();
  const fit = useMemo(() => miniMapScale(extent), [extent]);
  const boxFill = palette.success.main;
  const boundaryStroke = palette.text.secondary;
  // The boxes of the plan: drawn again only when the plan or its extent changes, never for a pan.
  const layer = useMemo(() => {
    const boundary = plan.settings?.boundary;
    const boxes: { key: string; box: BoundingBox }[] = [];
    for (const location of Object.values(plan.locations)) {
      if (location.geometry && location.bbox) boxes.push({ key: location.key, box: location.bbox });
    }
    for (const object of Object.values(plan.gardenObjects)) {
      if (object.bbox) boxes.push({ key: object.key, box: object.bbox });
    }
    return (
      <>
        {boundary && (
          <rect
            {...boxRect(boundingBox(boundary), extent, fit)}
            fill="none"
            stroke={boundaryStroke}
            strokeWidth={1}
            strokeDasharray="3 2"
          />
        )}
        {boxes.map(({ key, box }) => (
          <rect
            key={key}
            {...boxRect(box, extent, fit)}
            fill={boxFill}
            fillOpacity={0.55}
          />
        ))}
      </>
    );
  }, [boundaryStroke, boxFill, extent, fit, plan]);

  const onClick = (event: ReactMouseEvent<HTMLElement>) => {
    // The drawing starts inside the border: measure from the padding box, as the plan canvas does.
    const element = event.currentTarget;
    const box = element.getBoundingClientRect();
    onJump(
      fromMiniMap(
        [
          event.clientX - box.left - element.clientLeft,
          event.clientY - box.top - element.clientTop,
        ],
        extent,
        fit,
      ),
    );
  };

  const view = boxRect(viewportBox(viewport), extent, fit);
  return (
    <Box
      role="img"
      aria-label={t('pages.gardenPlan.editor.miniMap.label')}
      title={t('pages.gardenPlan.editor.miniMap.hint')}
      data-testid="garden-plan-minimap"
      onPointerDown={stop}
      onPointerMove={stop}
      onPointerUp={stop}
      onContextMenu={stop}
      onClick={(event) => {
        stop(event);
        onClick(event);
      }}
      sx={{
        position: 'absolute',
        right: 8,
        bottom: 8,
        // the 120 px drawing sits inside the border, not 2 px over it (the app's boxes are border-box)
        boxSizing: 'content-box',
        width: MINI_MAP_PX,
        height: MINI_MAP_PX,
        cursor: 'pointer',
        bgcolor: 'background.paper',
        border: 1,
        borderColor: 'divider',
        borderRadius: 1,
        opacity: 0.95,
        boxShadow: 1,
      }}
    >
      <svg width={MINI_MAP_PX} height={MINI_MAP_PX} aria-hidden style={{ display: 'block' }}>
        {layer}
        <rect
          {...view}
          fill={palette.primary.main}
          fillOpacity={0.12}
          stroke={palette.primary.main}
          strokeWidth={2}
          data-testid="garden-plan-minimap-viewport"
        />
      </svg>
    </Box>
  );
}

export const MiniMap = memo(MiniMapView);
