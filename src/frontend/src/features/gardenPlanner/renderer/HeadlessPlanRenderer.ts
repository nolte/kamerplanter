import type { ReactNode } from 'react';
import type { PlanModel } from '../model/planModel';
import { BasePlanRenderer } from './BasePlanRenderer';
import { buildScene, type Scene } from './scene';
import type { RenderOptions, RenderSelection, Viewport } from './types';

/**
 * Test double behind the {@link PlanRenderer} boundary (GP-NFR-009): no DOM, no React tree. It
 * computes what a real renderer would draw and keeps it for assertions, so editor logic
 * (tools, selection, keyboard) can be tested against hit testing and culling without jsdom layout.
 */
export class HeadlessPlanRenderer extends BasePlanRenderer {
  /** The scene of the latest `render()` call. */
  lastScene: Scene | null = null;
  /** The latest drag preview, or `null`. */
  dragPreview: { key: string; dxPx: number; dyPx: number } | null = null;

  protected draw(
    model: PlanModel,
    viewport: Viewport,
    selection: RenderSelection,
    options: RenderOptions,
  ): ReactNode {
    this.lastScene = buildScene(model, viewport, selection, options);
    return null;
  }

  setDragOffset(key: string | null, dxPx = 0, dyPx = 0): void {
    this.dragPreview = key === null ? null : { key, dxPx, dyPx };
  }
}
