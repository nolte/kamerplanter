import type { ReactNode } from 'react';
import Skeleton from '@mui/material/Skeleton';
import type { PlanModel } from '../model/planModel';
import { BasePlanRenderer } from './BasePlanRenderer';
import type { RenderOptions, RenderSelection, Viewport } from './types';

/**
 * Stands in for the Konva renderer while its chunk loads (D-01, WP 9.7): a plan large enough for Konva is not first
 * drawn in full by SVG only to be thrown away. It draws a skeleton of the plan's size; hit testing and projection are
 * the model's (`BasePlanRenderer`), so a click in the gap still resolves. The list view stays usable meanwhile.
 */
export class PlaceholderPlanRenderer extends BasePlanRenderer {
  protected draw(_model: PlanModel, viewport: Viewport, _selection: RenderSelection, options: RenderOptions): ReactNode {
    return (
      <Skeleton
        variant="rectangular"
        animation="wave"
        width={viewport.widthPx}
        height={viewport.heightPx}
        role="img"
        aria-label={options.labels.canvas}
        aria-busy="true"
        data-testid="garden-plan-renderer-loading"
      />
    );
  }

  setDragOffset(): void {
    // Nothing is drawn that could move.
  }
}
