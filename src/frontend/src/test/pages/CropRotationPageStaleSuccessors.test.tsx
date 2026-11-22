/**
 * #3014 (audit 2026-11, A-04): switching the selected family while the previous
 * family's successors are still in flight. When the older answer arrives last it
 * must neither replace the current successors nor leave the skeleton up for good
 * (`loadedKey` pointing at the old family kept `successorsPending` true).
 */
import { act, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, beforeEach } from 'vitest';
import { http, HttpResponse } from 'msw';
import i18n from 'i18next';
import CropRotationPage from '@/pages/stammdaten/CropRotationPage';
import { createPlatformAdminStore, renderWithProviders } from '../helpers';
import { server } from '../mocks/server';

const FAMILIES = [
  { key: 'fam-solanaceae', name: 'Solanaceae', nitrogen_fixing: false, frost_tolerance: 'sensitive', typical_nutrient_demand: 'heavy_feeder' },
  { key: 'fam-brassicaceae', name: 'Brassicaceae', nitrogen_fixing: false, frost_tolerance: 'hardy', typical_nutrient_demand: 'light_feeder' },
];

/** The one successor each selected family answers with, named after that family. */
function successorOf(familyKey: string) {
  const label = familyKey === 'fam-solanaceae' ? 'Successor of Solanaceae' : 'Successor of Brassicaceae';
  return {
    family_key: `succ-${familyKey}`,
    name: label,
    common_name_de: label,
    common_name_en: label,
    rotation_category: 'legume',
    wait_years: 3,
    benefit_score: 0.8,
    benefit_reason: '',
  };
}

const TIMEOUT = { timeout: 5000 } as const;

describe('CropRotationPage — out-of-order successor answers (#3014)', () => {
  const releases = new Map<string, () => void>();
  const requested: string[] = [];

  beforeEach(async () => {
    await i18n.changeLanguage('en');
    releases.clear();
    requested.length = 0;
    server.use(
      http.get('/api/v1/botanical-families', () => HttpResponse.json(FAMILIES)),
      http.get('/api/v1/crop-rotation/counts', () => HttpResponse.json({ 'fam-solanaceae': 1, 'fam-brassicaceae': 1 })),
      http.get('/api/v1/crop-rotation/families/:key/successors', async ({ params }) => {
        const key = String(params.key);
        requested.push(key);
        await new Promise<void>((resolve) => releases.set(key, resolve));
        return HttpResponse.json([successorOf(key)]);
      }),
      http.get('/api/v1/favorites', () => HttpResponse.json([])),
      http.get('/api/v1/t/:tenant/favorites', () => HttpResponse.json([])),
    );
  });

  async function selectFamily(familyKey: string) {
    const combobox = within(await screen.findByTestId('from-family-select')).getByRole('combobox');
    await userEvent.click(combobox);
    await userEvent.click(await screen.findByTestId(`family-option-${familyKey}`, {}, TIMEOUT));
    await waitFor(() => expect(requested).toContain(familyKey), TIMEOUT);
  }

  it('shows the current family and drops the skeleton when the older answer lands last', async () => {
    renderWithProviders(<CropRotationPage />, { store: createPlatformAdminStore() });

    await selectFamily('fam-solanaceae');
    await selectFamily('fam-brassicaceae');

    await act(async () => releases.get('fam-brassicaceae')!());
    await screen.findByText('Successor of Brassicaceae', {}, TIMEOUT);

    await act(async () => {
      releases.get('fam-solanaceae')!();
      await new Promise((resolve) => setTimeout(resolve, 150));
    });

    expect(screen.queryByTestId('loading-skeleton')).toBeNull();
    expect(screen.getByText('Successor of Brassicaceae')).toBeTruthy();
    expect(screen.queryByText('Successor of Solanaceae')).toBeNull();
  });
});
