/**
 * The mini-map (REQ-053 GP-UX-014): a 120 x 120 px overview at the bottom right of the plan - the beds and
 * garden objects as boxes, the boundary, and the rectangle of what the viewport shows. A click or tap jumps
 * the view there. It is a pointer shortcut only: the keyboard has the arrow keys and the list view, so it is
 * announced as an image and stays out of the tab order. It never takes the gestures of the plan beneath it.
 */
import { useMemo, type MouseEvent as ReactMouseEvent } from 'react';
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

export function MiniMap({ plan, extent, viewport, onJump }: MiniMapProps) {
  const { t } = useTranslation();
  const { palette } = useTheme();
  const fit = useMemo(() => miniMapScale(extent), [extent]);
  const boxes = useMemo(() => {
    const out: { key: string; box: BoundingBox }[] = [];
    for (const location of Object.values(plan.locations)) {
      if (location.geometry && location.bbox) out.push({ key: location.key, box: location.bbox });
    }
    for (const object of Object.values(plan.gardenObjects)) {
      if (object.bbox) out.push({ key: object.key, box: object.bbox });
    }
    return out;
  }, [plan]);

  const rect = (box: BoundingBox) => {
    const [x0, y1] = toMiniMap([box[0], box[1]], extent, fit);
    const [x1, y0] = toMiniMap([box[2], box[3]], extent, fit);
    return { x: x0, y: y0, width: Math.max(x1 - x0, 1), height: Math.max(y1 - y0, 1) };
  };

  const onClick = (event: ReactMouseEvent<HTMLElement>) => {
    const box = event.currentTarget.getBoundingClientRect();
    onJump(fromMiniMap([event.clientX - box.left, event.clientY - box.top], extent, fit));
  };

  const view = rect(viewportBox(viewport));
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
      <svg width={MINI_MAP_PX} height={MINI_MAP_PX} aria-hidden>
        {plan.settings?.boundary && (
          <rect
            {...rect(boundingBox(plan.settings.boundary))}
            fill="none"
            stroke={palette.text.secondary}
            strokeWidth={1}
            strokeDasharray="3 2"
          />
        )}
        {boxes.map(({ key, box }) => (
          <rect key={key} {...rect(box)} fill={palette.success.main} fillOpacity={0.55} />
        ))}
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
