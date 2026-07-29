import { render, screen } from '@testing-library/react';
import { describe, it, expect, afterEach } from 'vitest';
import PageTitle from '@/components/layout/PageTitle';

describe('PageTitle', () => {
  afterEach(() => {
    document.title = '';
  });

  it('renders the title as h1', () => {
    render(<PageTitle title="My Page" />);
    const heading = screen.getByRole('heading', { level: 1 });
    expect(heading).toBeTruthy();
    expect(heading.textContent).toBe('My Page');
  });

  it('sets document.title', () => {
    render(<PageTitle title="Test" />);
    expect(document.title).toBe('Test — Kamerplanter');
  });

  it('resets document.title on unmount', () => {
    const { unmount } = render(<PageTitle title="Test" />);
    expect(document.title).toBe('Test — Kamerplanter');
    unmount();
    expect(document.title).toBe('Kamerplanter');
  });

  it('keeps the action slot shrinkable and wrapping so headers cannot overflow mobile', () => {
    render(
      <PageTitle
        title="My Page"
        action={
          <button type="button" data-testid="header-action">
            Do it
          </button>
        }
      />,
    );

    const slot = screen.getByTestId('page-title-actions');
    expect(slot).toContainElement(screen.getByTestId('header-action'));

    const style = window.getComputedStyle(slot);
    // Regression guard: the slot used to be `flexShrink: 0`, which sizes a flex
    // item to max-content. Every action group therefore ignored its own
    // `flexWrap` and pushed the document past the viewport width
    // (UI-NFR-001 R-005/R-006).
    expect(style.flexShrink).not.toBe('0');
    // The slot itself wraps, so an action group passed as a fragment or as a
    // non-wrapping flex box still breaks onto a second line (UI-NFR-021 R-023).
    expect(style.display).toBe('flex');
    expect(style.flexWrap).toBe('wrap');
  });
});
