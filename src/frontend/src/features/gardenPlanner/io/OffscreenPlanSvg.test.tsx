/**
 * The off-screen drawing of the PNG export (REQ-053 GP-FR-144) reports exactly once: the SVG when it has one, a
 * failure when the drawing has none (so the export never hangs), and once even under StrictMode, whose mount effects
 * run twice. The renderer is replaced so a test can make it draw no SVG.
 */
import { StrictMode, type ReactNode } from 'react';
import { cleanup, render } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { smallPlan } from '@/test/gardenPlanFixtures';
import { TEST_LABELS } from '../renderer/rendererTestKit';
import OffscreenPlanSvg from './OffscreenPlanSvg';

const draws = vi.hoisted(() => ({ svg: true }));

vi.mock('../renderer/SvgPlanRenderer', () => ({
  SvgPlanRenderer: class {
    render(): ReactNode {
      return draws.svg ? <svg data-testid="garden-plan-svg" /> : <div />;
    }
  },
}));

const VIEWPORT = { originM: [0, 10] as [number, number], pxPerM: 10, widthPx: 100, heightPx: 100 };

afterEach(() => {
  cleanup();
  draws.svg = true;
});

function mount(strict: boolean) {
  const onReady = vi.fn();
  const onError = vi.fn();
  const element = (
    <OffscreenPlanSvg plan={smallPlan()} viewport={VIEWPORT} labels={TEST_LABELS} onReady={onReady} onError={onError} />
  );
  render(strict ? <StrictMode>{element}</StrictMode> : element);
  return { onReady, onError };
}

describe('OffscreenPlanSvg', () => {
  it('hands over its SVG once, from a container that is in the document but hidden', () => {
    const { onReady, onError } = mount(false);
    expect(onReady).toHaveBeenCalledTimes(1);
    expect(onError).not.toHaveBeenCalled();
    const svg = onReady.mock.calls[0][0] as SVGSVGElement;
    const container = svg.parentElement as HTMLElement;
    expect(document.body.contains(container)).toBe(true);
    expect(container.getAttribute('aria-hidden')).toBe('true');
    expect(container.hasAttribute('inert')).toBe(true);
  });

  it('reports once under StrictMode', () => {
    const { onReady, onError } = mount(true);
    expect(onReady).toHaveBeenCalledTimes(1);
    expect(onError).not.toHaveBeenCalled();
  });

  it('reports a failure when the drawing has no SVG', () => {
    draws.svg = false;
    const { onReady, onError } = mount(true);
    expect(onError).toHaveBeenCalledTimes(1);
    expect(onReady).not.toHaveBeenCalled();
  });
});
