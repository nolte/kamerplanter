import { describe, it, expect, vi, afterEach } from 'vitest';
import { render, screen, cleanup, fireEvent } from '@testing-library/react';
import ShowAllFieldsToggle from '@/components/common/ShowAllFieldsToggle';

/**
 * #1897 — the toggle is a disclosure button: it announces whether the hidden
 * fields are shown (WCAG 4.1.2), and that state is what the E2E harness reads
 * to know its click took effect instead of assuming it did.
 */
describe('ShowAllFieldsToggle', () => {
  afterEach(() => {
    cleanup();
  });

  it('reports collapsed while the extra fields are hidden', () => {
    render(<ShowAllFieldsToggle showAll={false} onToggle={() => {}} />);
    expect(screen.getByTestId('show-all-fields-toggle')).toHaveAttribute('aria-expanded', 'false');
  });

  it('reports expanded while every field is shown', () => {
    render(<ShowAllFieldsToggle showAll onToggle={() => {}} />);
    expect(screen.getByTestId('show-all-fields-toggle')).toHaveAttribute('aria-expanded', 'true');
  });

  it('calls onToggle on click', () => {
    const onToggle = vi.fn();
    render(<ShowAllFieldsToggle showAll={false} onToggle={onToggle} />);
    fireEvent.click(screen.getByTestId('show-all-fields-toggle'));
    expect(onToggle).toHaveBeenCalledOnce();
  });
});
