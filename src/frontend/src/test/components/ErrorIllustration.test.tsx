import { describe, it, expect } from 'vitest';
import { screen } from '@testing-library/react';
import ErrorIllustration from '@/components/common/ErrorIllustration';
import { renderWithProviders } from '../helpers';

/** #3023 (P-02) — the error illustration is resolved per status code on demand, with a reserved box meanwhile. */
describe('ErrorIllustration', () => {
  it('reserves the box first, then shows the illustration of the status code', async () => {
    renderWithProviders(<ErrorIllustration statusCode={404} />);

    expect(screen.getByTestId('error-illustration-placeholder')).toHaveAttribute('aria-hidden', 'true');
    const img = (await screen.findByTestId('error-illustration')) as HTMLImageElement;
    expect(img.getAttribute('src')).toMatch(/error-404/);
    expect(img).toHaveAttribute('alt', '');
    expect(screen.queryByTestId('error-illustration-placeholder')).not.toBeInTheDocument();
  });

  it('falls back to the 500 illustration for a status code without one', async () => {
    renderWithProviders(<ErrorIllustration statusCode={418} />);

    const img = await screen.findByTestId('error-illustration');
    expect(img.getAttribute('src')).toMatch(/error-500/);
  });
});
