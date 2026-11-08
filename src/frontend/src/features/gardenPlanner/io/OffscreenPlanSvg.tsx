/**
 * The SVG the PNG export reads (REQ-053 GP-FR-144): the whole plan drawn by its own `SvgPlanRenderer` into a
 * container outside the visible page. It does not depend on what the editor shows - on a large plan the screen
 * may be a canvas renderer (D-01) with no SVG at all.
 *
 * The container is attached to `document.body` (a detached node has no computed styles) but placed off screen,
 * hidden from assistive technology and `inert`, so its focusable bed nodes never join the tab order. It is a portal,
 * so the drawing keeps the page's theme and language; it lives only while one export runs.
 */
import { useEffect, useMemo, useState } from 'react';
import { createPortal } from 'react-dom';
import type { PlanModel } from '../model/planModel';
import { SvgPlanRenderer } from '../renderer/SvgPlanRenderer';
import type { RendererLabels, Viewport } from '../renderer/types';

const NO_SELECTION = { selectedKeys: new Set<string>() };

interface OffscreenPlanSvgProps {
  plan: PlanModel;
  viewport: Viewport;
  labels: RendererLabels;
  /** Called once with the drawn SVG after it is in the document; the caller unmounts this component when done. */
  onReady: (svg: SVGSVGElement) => void;
}

function createContainer(): HTMLDivElement {
  const container = document.createElement('div');
  container.setAttribute('aria-hidden', 'true');
  container.setAttribute('inert', '');
  container.setAttribute('data-testid', 'plan-png-offscreen');
  // Off screen, not `visibility: hidden` or `display: none`: both would be computed into the inlined styles.
  Object.assign(container.style, {
    position: 'fixed',
    left: '-100000px',
    top: '0',
    pointerEvents: 'none',
  });
  return container;
}

export default function OffscreenPlanSvg({ plan, viewport, labels, onReady }: OffscreenPlanSvgProps) {
  const [container] = useState(createContainer);
  const renderer = useMemo(() => new SvgPlanRenderer(), []);
  const drawing = useMemo(
    () => renderer.render(plan, viewport, NO_SELECTION, { labels }),
    [renderer, plan, viewport, labels],
  );

  useEffect(() => {
    document.body.appendChild(container);
    return () => {
      container.remove();
    };
  }, [container]);

  useEffect(() => {
    const svg = container.querySelector('svg');
    if (svg) onReady(svg);
    // Once per mount: the export reads the first complete drawing.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [container]);

  return createPortal(drawing, container);
}
