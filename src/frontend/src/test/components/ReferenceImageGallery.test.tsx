import { screen, waitFor } from '@testing-library/react';
import { describe, it, expect, beforeEach } from 'vitest';
import { http, HttpResponse } from 'msw';
import i18n from 'i18next';
import ReferenceImageGallery from '@/pages/stammdaten/ReferenceImageGallery';
import { renderWithProviders } from '../helpers';
import { server } from '../mocks/server';

describe('ReferenceImageGallery', () => {
  beforeEach(() => {
    i18n.changeLanguage('de');
  });

  it('shows a discreet empty hint when the gallery is empty (count 0)', async () => {
    server.use(
      http.get('/api/v1/species/sp-empty/reference-images', () =>
        HttpResponse.json({ species_key: 'sp-empty', count: 0, images: [] }),
      ),
    );
    renderWithProviders(<ReferenceImageGallery speciesKey="sp-empty" />);
    expect(await screen.findByTestId('reference-image-empty')).toBeTruthy();
    expect(screen.getByText('Noch keine Referenzbilder verfügbar.')).toBeTruthy();
  });

  it('treats a request failure as "no images" without surfacing an error', async () => {
    server.use(
      http.get('/api/v1/species/sp-error/reference-images', () =>
        HttpResponse.json({ detail: 'boom' }, { status: 500 }),
      ),
    );
    renderWithProviders(<ReferenceImageGallery speciesKey="sp-error" />);
    expect(await screen.findByTestId('reference-image-empty')).toBeTruthy();
  });

  it('renders images with attribution and license captions', async () => {
    server.use(
      http.get('/api/v1/species/sp-1/reference-images', () =>
        HttpResponse.json({
          species_key: 'sp-1',
          count: 2,
          images: [
            {
              source_url: 'https://example.org/leaf.jpg',
              license: 'CC-BY',
              attribution: 'Jane Doe',
              organ: 'leaf',
              source: 'gbif',
            },
            {
              source_url: 'https://example.org/flower.jpg',
              license: 'CC0',
              attribution: null,
              organ: 'flower',
              source: 'gbif',
            },
          ],
        }),
      ),
    );
    renderWithProviders(<ReferenceImageGallery speciesKey="sp-1" />);

    await waitFor(() => {
      expect(screen.getAllByTestId('reference-image-item').length).toBe(2);
    });
    // Legally-required attribution + license caption for the CC-BY image.
    expect(screen.getByText('© Jane Doe · CC-BY')).toBeTruthy();
    // CC0 image without attribution shows just the license.
    expect(screen.getByText('CC0')).toBeTruthy();
  });
});
