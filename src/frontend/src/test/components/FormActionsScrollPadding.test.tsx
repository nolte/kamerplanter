import { act, render, screen } from '@testing-library/react';
import { describe, it, expect, vi, afterEach } from 'vitest';
import { ThemeContextProvider } from '@/theme';
import '@/i18n';

// Force the compact breakpoint per test: below `sm` the action row is pinned,
// which is the only case that needs reserved scroll space.
const mediaQuery = vi.hoisted(() => ({ pinned: true }));
vi.mock('@mui/material/useMediaQuery', () => ({ default: () => mediaQuery.pinned }));

// Import after the mock so it is picked up.
import FormActions from '@/components/form/FormActions';

/**
 * jsdom has no layout engine: every rect is 0×0 and every scroll metric is 0.
 * These helpers feed the component the geometry a browser would measure, so the
 * reservation arithmetic can be asserted. What this cannot prove is the visual
 * outcome — see the module docblock of `useStickyBarScrollPadding`.
 */
function stubRect(element: HTMLElement, top: number, height: number): void {
  element.getBoundingClientRect = () =>
    ({
      top,
      bottom: top + height,
      left: 0,
      right: 0,
      width: 0,
      height,
      x: 0,
      y: top,
      toJSON: () => ({}),
    }) as DOMRect;
}

const patched: HTMLElement[] = [];

function stubScrollMetrics(element: HTMLElement, scrollHeight: number, clientHeight: number): void {
  Object.defineProperty(element, 'scrollHeight', { configurable: true, value: scrollHeight });
  Object.defineProperty(element, 'clientHeight', { configurable: true, value: clientHeight });
  patched.push(element);
}

function reserved(element: HTMLElement): number {
  return Number.parseFloat(element.style.scrollPaddingBottom);
}

function renderInScrollContainer() {
  const view = render(
    <ThemeContextProvider>
      {/* `overflow-y` is set inline because jsdom resolves MUI's emotion class
          for `DialogContent` unreliably; the shape mirrors the real DOM
          (scrolling container > form > action row). */}
      <div data-testid="scroll-container" style={{ overflowY: 'auto' }}>
        <form>
          <FormActions onCancel={vi.fn()} />
        </form>
      </div>
    </ThemeContextProvider>,
  );
  return { ...view, container: screen.getByTestId('scroll-container') };
}

afterEach(() => {
  mediaQuery.pinned = true;
  for (const element of patched) {
    Reflect.deleteProperty(element, 'scrollHeight');
    Reflect.deleteProperty(element, 'clientHeight');
  }
  patched.length = 0;
  document.documentElement.style.scrollPaddingBottom = '';
});

describe('FormActions — reserved space below the pinned row (#768)', () => {
  it('reserves at least the row height plus the container tail on the scrolling ancestor', () => {
    const { container } = renderInScrollContainer();
    const actions = screen.getByTestId('form-actions');

    // 60px row resting 40px above the scrollport edge — the tail a sticky box
    // cannot cross because its containing block (the `<form>`) ends there, i.e.
    // `DialogContent`'s bottom padding in the real dialog.
    stubRect(container, 0, 600);
    stubRect(actions, 900, 60);
    stubScrollMetrics(container, 1000, 600);
    act(() => {
      window.dispatchEvent(new Event('resize'));
    });

    // Without a reservation the browser parks a scrolled-to field flush against
    // the scrollport edge, i.e. behind the row (issue #768: a click on an
    // Autocomplete input at y=803 of an 852px viewport hit the submit button).
    expect(container.style.scrollPaddingBottom).not.toBe('');
    expect(reserved(container)).toBeGreaterThanOrEqual(100);
    // Never a runaway value: `scroll-padding` beyond half the scrollport would
    // make every scroll-into-view on this container jump.
    expect(reserved(container)).toBeLessThanOrEqual(300);
  });

  it('reserves on the root element when the document itself scrolls', () => {
    render(
      <ThemeContextProvider>
        <form>
          <FormActions onCancel={vi.fn()} />
        </form>
      </ThemeContextProvider>,
    );
    const actions = screen.getByTestId('form-actions');

    // In-page edit form (task detail and the migrated detail pages): no ancestor
    // scrolls, so the reservation has to land on the element whose value
    // propagates to the viewport.
    stubRect(actions, 1900, 60);
    stubScrollMetrics(document.documentElement, 2000, 800);
    act(() => {
      window.dispatchEvent(new Event('resize'));
    });

    expect(reserved(document.documentElement)).toBeGreaterThanOrEqual(100);
  });

  it('ignores a tail the row has already scrolled past', () => {
    const { container } = renderInScrollContainer();
    const actions = screen.getByTestId('form-actions');

    // A form followed by a lot more content: at maximum scroll the row is long
    // gone from the viewport, so its containing block's distance to the content
    // end must not be reserved — only the row's own height (plus the gap).
    stubRect(container, 0, 600);
    stubRect(actions, 900, 60);
    stubScrollMetrics(container, 5000, 600);
    act(() => {
      window.dispatchEvent(new Event('resize'));
    });

    expect(reserved(container)).toBeGreaterThanOrEqual(60);
    expect(reserved(container)).toBeLessThan(100);
  });

  it('reserves nothing on a viewport where the row is not pinned', () => {
    mediaQuery.pinned = false;
    const { container } = renderInScrollContainer();
    const actions = screen.getByTestId('form-actions');

    stubRect(container, 0, 600);
    stubRect(actions, 900, 60);
    stubScrollMetrics(container, 1000, 600);
    act(() => {
      window.dispatchEvent(new Event('resize'));
    });

    expect(container.style.scrollPaddingBottom).toBe('');
  });

  it('follows the row height instead of a fixed value when it changes', () => {
    // jsdom ships no ResizeObserver. The stub captures the instance so the test
    // can synthesise the notification a browser sends when the row grows (a
    // wrapped label, a spinner) — the reservation must follow, which is why it
    // is measured rather than derived from a pixel constant.
    const observers: { callback: ResizeObserverCallback; targets: Element[] }[] = [];
    class ResizeObserverStub {
      targets: Element[] = [];
      constructor(public callback: ResizeObserverCallback) {
        observers.push(this);
      }
      observe(target: Element) {
        this.targets.push(target);
      }
      unobserve() {}
      disconnect() {}
    }
    const original = globalThis.ResizeObserver;
    globalThis.ResizeObserver = ResizeObserverStub as unknown as typeof ResizeObserver;

    try {
      const { container } = renderInScrollContainer();
      const actions = screen.getByTestId('form-actions');
      stubRect(container, 0, 600);
      stubScrollMetrics(container, 1000, 600);

      stubRect(actions, 900, 60);
      act(() => {
        window.dispatchEvent(new Event('resize'));
      });
      const before = reserved(container);

      // The row grows by 40px; the container observes it, not the other way round.
      stubRect(actions, 860, 100);
      act(() => {
        for (const observer of observers) {
          observer.callback(
            observer.targets.map((target) => ({ target }) as ResizeObserverEntry),
            observer as unknown as ResizeObserver,
          );
        }
      });

      expect(observers.length).toBeGreaterThan(0);
      expect(reserved(container)).toBeGreaterThanOrEqual(before + 40);
    } finally {
      globalThis.ResizeObserver = original;
    }
  });

  it('restores the container on unmount', () => {
    const { container, unmount } = renderInScrollContainer();
    const actions = screen.getByTestId('form-actions');

    stubRect(container, 0, 600);
    stubRect(actions, 900, 60);
    stubScrollMetrics(container, 1000, 600);
    act(() => {
      window.dispatchEvent(new Event('resize'));
    });
    expect(container.style.scrollPaddingBottom).not.toBe('');

    unmount();

    // The node survives in the test, but a closed dialog's `DialogContent` is
    // reused by MUI — a leftover reservation would silently shift every later
    // scroll-into-view inside it.
    expect(container.style.scrollPaddingBottom).toBe('');
  });
});
