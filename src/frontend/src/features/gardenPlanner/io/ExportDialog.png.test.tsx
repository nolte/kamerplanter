/**
 * The PNG of the export dialog (REQ-053 GP-FR-144): drawn in the browser from the loaded plan, never from the
 * drawing on screen - the screen here is a canvas-only renderer with no SVG at all (D-01, WP 9.7). Resolution
 * 1×/2×/4× with the canvas cap and its hint, the watermark off unless chosen, no request to the server.
 */
import type { ReactNode } from 'react';
import { cleanup, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { http, HttpResponse } from 'msw';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { authState, createTestStore, renderWithProviders, tenantState } from '@/test/helpers';
import { smallPlan } from '@/test/gardenPlanFixtures';
import { server } from '@/test/mocks/server';
import { BasePlanRenderer } from '../renderer/BasePlanRenderer';
import { TEST_LABELS } from '../renderer/rendererTestKit';
import type { PlanModel } from '../model/planModel';
import type { GardenPlanState } from '../state/gardenPlanSlice';
import ExportDialog from './ExportDialog';

const loaded = vi.hoisted(() => ({ state: null as unknown }));

vi.mock('../state/gardenPlanSlice', async (importOriginal) => {
  const original = await importOriginal<typeof import('../state/gardenPlanSlice')>();
  return { ...original, selectGardenPlanState: () => loaded.state as GardenPlanState };
});

const saved = vi.hoisted(() => ({ calls: [] as { blob: Blob; filename: string }[] }));
vi.mock('./ioApi', async (importOriginal) => {
  const original = await importOriginal<typeof import('./ioApi')>();
  return {
    ...original,
    saveBlob: (blob: Blob, filename: string) => saved.calls.push({ blob, filename }),
  };
});

/** What a canvas renderer (Konva, WP 9.7) puts on screen: a bitmap, no SVG to read. */
class CanvasOnlyRenderer extends BasePlanRenderer {
  protected draw(): ReactNode {
    return <canvas data-testid="onscreen-canvas" />;
  }

  setDragOffset(): void {}
}

function OnScreenPlan({ plan }: { plan: PlanModel }) {
  const renderer = new CanvasOnlyRenderer();
  return (
    <>
      {renderer.render(plan, { originM: [0, 100], pxPerM: 10, widthPx: 1000, heightPx: 1000 }, { selectedKeys: new Set() }, { labels: TEST_LABELS })}
    </>
  );
}

let svgTexts: string[];
let fillTexts: string[];
let canvasSizes: [number, number][];
let serverRequests: number;

beforeEach(() => {
  svgTexts = [];
  fillTexts = [];
  canvasSizes = [];
  serverRequests = 0;
  saved.calls = [];
  const plan = smallPlan();
  loaded.state = { plan } as unknown as GardenPlanState;
  server.use(
    http.get('/api/v1/t/:tenant/*', () => {
      serverRequests += 1;
      return new HttpResponse('<svg xmlns="http://www.w3.org/2000/svg"/>', { headers: { 'content-type': 'image/svg+xml' } });
    }),
  );
  vi.spyOn(URL, 'createObjectURL').mockImplementation((object: Blob | MediaSource) => {
    if (object instanceof Blob && object.type.startsWith('image/svg+xml')) {
      void object.text().then((text) => svgTexts.push(text));
      return 'blob:plan-svg';
    }
    return 'blob:other';
  });
  vi.spyOn(URL, 'revokeObjectURL').mockImplementation(() => undefined);
  // jsdom decodes no images: an <img> "loads" as soon as it has a source.
  vi.spyOn(HTMLImageElement.prototype, 'src', 'set').mockImplementation(function (this: HTMLImageElement) {
    setTimeout(() => this.onload?.(new Event('load')), 0);
  });
  vi.spyOn(HTMLCanvasElement.prototype, 'getContext').mockImplementation(function (this: HTMLCanvasElement) {
    canvasSizes.push([this.width, this.height]);
    return {
      fillRect: () => undefined,
      drawImage: () => undefined,
      measureText: (text: string) => ({ width: text.length * 8 }),
      fillText: (text: string) => fillTexts.push(text),
    } as unknown as CanvasRenderingContext2D;
  } as never);
  vi.spyOn(HTMLCanvasElement.prototype, 'toBlob').mockImplementation((callback: BlobCallback, type?: string) =>
    callback(new Blob(['png'], { type })),
  );
});

afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
});

function renderDialog(onClose = vi.fn()) {
  const store = createTestStore({ ...tenantState('viewer'), ...authState() });
  renderWithProviders(
    <>
      <OnScreenPlan plan={(loaded.state as GardenPlanState).plan as PlanModel} />
      <ExportDialog open siteKey="s1" onClose={onClose} />
    </>,
    { store },
  );
  return onClose;
}

describe('ExportDialog PNG', () => {
  it('draws the plan off screen although the screen shows no SVG, and downloads a PNG at the chosen factor', async () => {
    const user = userEvent.setup();
    const onClose = renderDialog();
    expect(screen.getByTestId('onscreen-canvas')).toBeInTheDocument();
    expect(document.querySelector('[data-testid="garden-plan-svg"]')).toBeNull();

    await user.click(screen.getByTestId('plan-export-format-png'));
    const requestsBefore = serverRequests;
    // 2x is the default: the 100 m plan fits 1200 px at 1x.
    expect(screen.getByTestId('plan-export-png-summary')).toHaveTextContent('2400 × 2400 pixels');
    await user.click(screen.getByTestId('plan-export-download'));

    await waitFor(() => expect(onClose).toHaveBeenCalled());
    expect(saved.calls).toHaveLength(1);
    expect(saved.calls[0].filename).toMatch(/^garden-plan-s1-\d{8}\.png$/);
    expect(saved.calls[0].blob.type).toBe('image/png');
    expect(canvasSizes).toEqual([[2400, 2400]]);
    // The image came from the export's own SVG of the loaded plan, sized by the factor (the PDF preview fetched
    // before PNG was chosen is an SVG blob too, but carries no plan keys).
    await waitFor(() => expect(svgTexts.filter((text) => text.includes('data-plan-key'))).toHaveLength(1));
    const exported = svgTexts.find((text) => text.includes('data-plan-key')) ?? '';
    expect(exported).toContain('data-plan-key="loc_a"');
    expect(exported).toMatch(/<svg[^>]* width="2400"/);
    // Gone after the export; nothing was asked of the server for the PNG.
    expect(screen.queryByTestId('plan-png-offscreen')).not.toBeInTheDocument();
    expect(serverRequests).toBe(requestsBefore);
  });

  it('caps 4x at the canvas limit, says so and exports the reduced size', async () => {
    const user = userEvent.setup();
    renderDialog();
    await user.click(screen.getByTestId('plan-export-format-png'));
    expect(screen.queryByTestId('plan-export-png-capped')).not.toBeInTheDocument();

    await user.click(screen.getByTestId('plan-export-png-resolution-4'));
    const hint = screen.getByTestId('plan-export-png-capped');
    expect(hint).toHaveTextContent('4×');
    expect(hint).toHaveTextContent('3.41×');
    expect(screen.getByTestId('plan-export-png-summary')).toHaveTextContent('4092 × 4092 pixels');
    await user.click(screen.getByTestId('plan-export-download'));

    await waitFor(() => expect(saved.calls).toHaveLength(1));
    expect(canvasSizes).toEqual([[4092, 4092]]);
  });

  it('draws the watermark only when it is chosen', async () => {
    const user = userEvent.setup();
    renderDialog();
    await user.click(screen.getByTestId('plan-export-format-png'));
    expect(screen.getByTestId('plan-export-png-watermark')).not.toBeChecked();
    await user.click(screen.getByTestId('plan-export-download'));
    await waitFor(() => expect(saved.calls).toHaveLength(1));
    expect(fillTexts).toEqual([]);

    cleanup();
    renderDialog();
    await user.click(screen.getByTestId('plan-export-format-png'));
    await user.click(screen.getByTestId('plan-export-png-watermark'));
    await user.click(screen.getByTestId('plan-export-download'));
    await waitFor(() => expect(saved.calls).toHaveLength(2));
    expect(fillTexts).toHaveLength(1);
    expect(fillTexts[0]).toMatch(/^Kamerplanter · /);
  });

  it('says why when the plan has nothing to draw, and does not download', async () => {
    loaded.state = { plan: { ...smallPlan(), settings: null, locations: {}, gardenObjects: {} } } as unknown as GardenPlanState;
    const user = userEvent.setup();
    renderDialog();
    await user.click(screen.getByTestId('plan-export-format-png'));
    expect(screen.getByTestId('plan-export-png-summary')).toHaveTextContent('The plan is still empty');
    expect(screen.getByTestId('plan-export-download')).toBeDisabled();
  });

  it('reports a failed drawing and keeps the dialog open', async () => {
    vi.spyOn(HTMLCanvasElement.prototype, 'getContext').mockReturnValue(null);
    const user = userEvent.setup();
    const onClose = renderDialog();
    await user.click(screen.getByTestId('plan-export-format-png'));
    await user.click(screen.getByTestId('plan-export-download'));
    expect(await screen.findByTestId('plan-export-error')).toHaveTextContent('The image could not be created');
    expect(onClose).not.toHaveBeenCalled();
    expect(saved.calls).toHaveLength(0);
  });
});
