/**
 * The way from the plan to the care tab (REQ-053 GP-FR-089): a press on the task badge of a bed and the
 * "Care" button of the properties panel both open the bed's care tab; a bed without open tasks offers neither.
 */
import { cleanup, fireEvent, screen } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { setupEditor } from './editorTestKit';

afterEach(() => cleanup());

describe('care button of the properties panel', () => {
  it('names the open and overdue tasks of the selected bed and opens its care tab', () => {
    const onOpenCare = vi.fn<(locationKey: string) => void>();
    const t = setupEditor({ onOpenCare });
    t.click(4, 4);
    expect(t.selected()).toEqual(['b1']);
    const button = screen.getByTestId('garden-plan-panel-care');
    expect(button).toHaveTextContent('Care: 3 open, 0 overdue');
    fireEvent.click(button);
    expect(onOpenCare).toHaveBeenCalledWith('b1');
  });

  it('is not offered for a bed without open tasks, nor without a care tab', () => {
    const onOpenCare = vi.fn<(locationKey: string) => void>();
    const t = setupEditor({ onOpenCare });
    t.click(7, 4);
    expect(t.selected()).toEqual(['b2']);
    expect(screen.queryByTestId('garden-plan-panel-care')).toBeNull();
    cleanup();
    const without = setupEditor();
    without.click(4, 4);
    expect(screen.queryByTestId('garden-plan-panel-care')).toBeNull();
  });
});

describe('task badge on the canvas', () => {
  /** The headless renderer draws no DOM, so the badge node of the SVG renderer is stood in for. */
  function badgeNode(canvas: HTMLElement, key: string): SVGGElement {
    const node = document.createElementNS('http://www.w3.org/2000/svg', 'g');
    node.setAttribute('data-plan-badge', key);
    canvas.appendChild(node);
    return node;
  }
  const PRESS = { button: 0, pointerId: 1, pointerType: 'mouse', isPrimary: true };

  it('opens the care tab on the click, and the press that lands on it starts no gesture', () => {
    const onOpenCare = vi.fn<(locationKey: string) => void>();
    const t = setupEditor({ onOpenCare });
    const badge = badgeNode(t.canvas(), 'b1');
    fireEvent.pointerDown(badge, PRESS);
    // Only the click opens it: a drag that starts on the badge (pan, pinch) never produces one.
    expect(onOpenCare).not.toHaveBeenCalled();
    expect(t.selected()).toEqual([]);
    fireEvent.pointerUp(badge, PRESS);
    fireEvent.click(badge);
    expect(onOpenCare).toHaveBeenCalledExactlyOnceWith('b1');
    expect(t.selected()).toEqual([]);
  });

  it('is ignored with another tool, where the press belongs to the tool', () => {
    const onOpenCare = vi.fn<(locationKey: string) => void>();
    const t = setupEditor({ onOpenCare });
    fireEvent.click(screen.getByRole('button', { name: /Pan/ }));
    expect(t.state().tool).toBe('pan');
    const badge = badgeNode(t.canvas(), 'b1');
    fireEvent.pointerDown(badge, PRESS);
    fireEvent.click(badge);
    expect(onOpenCare).not.toHaveBeenCalled();
  });
});
