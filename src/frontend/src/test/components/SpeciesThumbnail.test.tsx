import { screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, beforeEach } from 'vitest';
import i18n from 'i18next';
import SpeciesThumbnail from '@/pages/stammdaten/SpeciesThumbnail';
import { renderWithProviders } from '../helpers';

describe('SpeciesThumbnail', () => {
  beforeEach(() => {
    i18n.changeLanguage('de');
  });

  it('renders the external image when a URL is provided', () => {
    renderWithProviders(
      <SpeciesThumbnail
        imageUrl="https://example.org/leaf.jpg"
        attribution="Jane Doe"
        license="CC-BY"
        alt="Monstera deliciosa"
      />,
    );
    const img = screen.getByRole('img', { name: 'Monstera deliciosa' }) as HTMLImageElement;
    expect(img.getAttribute('src')).toBe('https://example.org/leaf.jpg');
    expect(img.getAttribute('referrerpolicy')).toBe('no-referrer');
    expect(img.getAttribute('loading')).toBe('lazy');
  });

  it('shows the icon fallback when no URL is provided', () => {
    renderWithProviders(<SpeciesThumbnail imageUrl={null} alt="Ocimum basilicum" />);
    expect(screen.queryByRole('img')).toBeNull();
    expect(screen.getByTestId('species-thumbnail')).toBeTruthy();
  });

  it('falls back to the icon when the external image fails to load', () => {
    renderWithProviders(
      <SpeciesThumbnail imageUrl="https://example.org/broken.jpg" alt="Broken" />,
    );
    const img = screen.getByRole('img', { name: 'Broken' });
    fireEvent.error(img);
    expect(screen.queryByRole('img')).toBeNull();
    expect(screen.getByTestId('species-thumbnail')).toBeTruthy();
  });
});
