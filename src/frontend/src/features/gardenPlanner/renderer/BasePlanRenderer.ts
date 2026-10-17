import type { ReactNode } from 'react';
import type { PlanModel } from '../model/planModel';
import type { Point } from '../model/types';
import { hitTestAll } from './hitTest';
import type { PlanRenderer, RenderOptions, RenderSelection, Viewport } from './types';
import { toModel, toScreen } from './viewport';

interface Frame {
  model: PlanModel;
  viewport: Viewport;
}

/**
 * What every renderer shares: the remembered frame and the questions asked about it. A subclass
 * only decides what `draw` produces. Hit testing, `toScreen` and `toModel` come from the model
 * and viewport alone, so the SVG and the headless renderer cannot disagree about a click.
 */
export abstract class BasePlanRenderer implements PlanRenderer {
  private frame: Frame | null = null;

  render(
    model: PlanModel,
    viewport: Viewport,
    selection: RenderSelection,
    options: RenderOptions,
  ): ReactNode {
    this.frame = { model, viewport };
    return this.draw(model, viewport, selection, options);
  }

  protected abstract draw(
    model: PlanModel,
    viewport: Viewport,
    selection: RenderSelection,
    options: RenderOptions,
  ): ReactNode;

  abstract setDragOffset(key: string | null, dxPx?: number, dyPx?: number): void;

  hitTest(pointPx: Point): string | null {
    return this.hitTestAll(pointPx)[0] ?? null;
  }

  hitTestAll(pointPx: Point): string[] {
    const { model, viewport } = this.requireFrame();
    return hitTestAll(model, viewport, pointPx);
  }

  toScreen(pointM: Point): Point {
    return toScreen(this.requireFrame().viewport, pointM);
  }

  toModel(pointPx: Point): Point {
    return toModel(this.requireFrame().viewport, pointPx);
  }

  /** The viewport of the latest frame, for subclasses that convert pixel offsets. */
  protected get currentViewport(): Viewport | null {
    return this.frame?.viewport ?? null;
  }

  private requireFrame(): Frame {
    if (!this.frame)
      throw new Error('PlanRenderer: call render() before hit testing or projecting.');
    return this.frame;
  }
}
