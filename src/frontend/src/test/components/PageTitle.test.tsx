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
});
