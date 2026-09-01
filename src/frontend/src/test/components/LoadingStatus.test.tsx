import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import i18n from 'i18next';
import LoadingStatus from '@/components/common/LoadingStatus';

/**
 * #1324 — the announcement half of every loading placeholder. Each assertion
 * here guards one of the three properties that were measured in Chrome's
 * accessibility tree and that a well-meaning simplification would remove.
 */
describe('LoadingStatus', () => {
  it('announces with the translated wording by default', () => {
    render(<LoadingStatus />);
    const status = screen.getByRole('status');
    expect(i18n.t('common.loading')).not.toBe('common.loading');
    expect(status).toHaveAccessibleName(i18n.t('common.loading'));
    expect(status).toHaveTextContent(i18n.t('common.loading'));
  });

  it('lets a region override the generic wording', () => {
    render(<LoadingStatus label="Lade Bilder" />);
    expect(screen.getByRole('status')).toHaveAccessibleName('Lade Bilder');
    expect(screen.getByRole('status')).toHaveTextContent('Lade Bilder');
  });

  it('carries both a name and content, because they do different work', () => {
    // `status` takes its name from the author only, never from content, so
    // dropping `aria-label` leaves the region nameless; a live region announces
    // its content, not its name, so dropping the text leaves it silent.
    render(<LoadingStatus label="Lade" />);
    const status = screen.getByRole('status');
    expect(status).toHaveAttribute('aria-label', 'Lade');
    expect(status.textContent).toBe('Lade');
  });

  it('is a polite live region and is not itself marked busy', () => {
    render(<LoadingStatus />);
    const status = screen.getByRole('status');
    expect(status).toHaveAttribute('aria-live', 'polite');
    expect(status).not.toHaveAttribute('aria-busy');
  });

  it('is visually hidden but not hidden from assistive technology', () => {
    render(<LoadingStatus />);
    const status = screen.getByRole('status');
    expect(status).not.toHaveAttribute('aria-hidden');
    // `visuallyHidden` clips the element rather than using display:none, which
    // would take it out of the accessibility tree along with the announcement.
    expect(getComputedStyle(status).position).toBe('absolute');
  });

  it('accepts a test id for callers that need to address it', () => {
    render(<LoadingStatus data-testid="widget-loading-status" />);
    expect(screen.getByTestId('widget-loading-status')).toHaveAttribute('role', 'status');
  });
});
