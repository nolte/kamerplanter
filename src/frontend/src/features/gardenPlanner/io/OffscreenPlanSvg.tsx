/**
 * The SVG the PNG export reads (REQ-053 GP-FR-144): the whole plan drawn by its own `SvgPlanRenderer` into a
 * container outside the visible page. It does not depend on what the editor shows - on a large plan the screen
 * may be a canvas renderer (D-01) with no SVG at all.
 *
 * The container is attached to `document.body` (a detached node has no computed styles) but placed off screen,
 * hidden from assistive technology and `inert`, so its focusable bed nodes never join the tab order. It is a portal,
 * so the drawing keeps the page's language; it lives only while one export runs.
 *
 * The drawing always uses the light theme, whatever the page shows: a PNG is shared and printed, and it must look
 * like the white preview and the server's PDF/SVG, not like a dark screen.
 */
import { useEffect, useMemo, useRef, useState } from 'react';
import { createPortal } from 'react-dom';
import { ThemeProvider } from '@mui/material/styles';
import { lightTheme } from '@/theme/theme';
import type { PlanModel } from '../model/planModel';
import { SvgPlanRenderer } from '../renderer/SvgPlanRenderer';
import type { RenderOptions, RendererLabels, Viewport } from '../renderer/types';

const NO_SELECTION = { selectedKeys: new Set<string>() };

interface OffscreenPlanSvgProps {
  plan: PlanModel;
  viewport: Viewport;
  labels: RendererLabels;
  /** View options besides the labels (the plan's own site-condition layers); never interaction or field mode. */
  options?: Omit<RenderOptions, 'labels'>;
  /** Called once with the drawn SVG after it is in the document; the caller unmounts this component when done. */
  onReady: (svg: SVGSVGElement) => void;
  /** Called once instead of `onReady` when the drawing produced no SVG, so the export always ends. */
  onError: () => void;
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
    // Text inherits from here, not from a dark page body.
    color: lightTheme.palette.text.primary,
    fontFamily: String(lightTheme.typography.fontFamily),
  });
  return container;
}

export default function OffscreenPlanSvg({
  plan,
  viewport,
  labels,
  options,
  onReady,
  onError,
}: OffscreenPlanSvgProps) {
  const [container] = useState(createContainer);
  const renderer = useMemo(() => new SvgPlanRenderer(), []);
  // StrictMode runs mount effects twice: one export must report once, or it downloads twice.
  const reported = useRef(false);
  const drawing = useMemo(
    () => renderer.render(plan, viewport, NO_SELECTION, { ...options, labels, fieldMode: false }),
    [renderer, plan, viewport, labels, options],
  );

  useEffect(() => {
    document.body.appendChild(container);
    return () => {
      container.remove();
    };
  }, [container]);

  useEffect(() => {
    if (reported.current) return;
    reported.current = true;
    const svg = container.querySelector('svg');
    if (svg) onReady(svg);
    else onError();
    // Once per mount: the export reads the first complete drawing.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [container]);

  return createPortal(<ThemeProvider theme={lightTheme}>{drawing}</ThemeProvider>, container);
}
