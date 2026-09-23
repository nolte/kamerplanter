import { screen, waitFor } from '@testing-library/react';
import { describe, it, expect, beforeEach } from 'vitest';
import { http, HttpResponse } from 'msw';
import i18n from 'i18next';
import PlantingRunCreateDialog from '@/pages/durchlaeufe/PlantingRunCreateDialog';
import { renderWithProviders } from '../helpers';
import { server } from '../mocks/server';

describe('PlantingRunCreateDialog', () => {
  beforeEach(() => {
    i18n.changeLanguage('de');
  });

  /**
   * #1628 UI review: every entry row's species picker was disabled while the
   * catalogue loaded with no visible reason, indistinguishable from a field
   * the form itself decided to lock. Follows the loading helper text already
   * shown by `PropagationEventDialog`'s species field (same shared
   * `SpeciesAutocompleteField`) instead of leaving the disablement unexplained.
   */
  it('shows a loading helper text on the first entry row species field while the catalogue is in flight', async () => {
    let resolveSpecies!: () => void;
    const pending = new Promise<void>((resolve) => {
      resolveSpecies = resolve;
    });
    server.use(
      http.get('/api/v1/species', async () => {
        await pending;
        return HttpResponse.json({ items: [], total: 0, offset: 0, limit: 200 });
      }),
    );

    renderWithProviders(
      <PlantingRunCreateDialog open onClose={() => {}} onCreated={() => {}} />,
    );

    const field = await screen.findByTestId('form-field-entries.0.species_key');
    expect(field.querySelector('input')?.disabled).toBe(true);
    expect(field.textContent).toContain(i18n.t('common.loading'));

    resolveSpecies();

    await waitFor(() => {
      expect(field.querySelector('input')?.disabled).toBe(false);
    });
    expect(field.textContent).not.toContain(i18n.t('common.loading'));
  });
});
