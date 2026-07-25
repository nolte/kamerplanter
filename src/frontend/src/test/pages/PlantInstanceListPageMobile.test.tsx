import { cleanup, screen, within } from '@testing-library/react';
import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import i18n from 'i18next';
import { renderWithProviders } from '../helpers';

// Force the mobile breakpoint so DataTable uses the mobileCardRenderer branch.
vi.mock('@mui/material/useMediaQuery', () => ({ default: () => true }));

// Import after the mock so the mocked useMediaQuery is picked up.
import PlantInstanceListPage from '@/pages/pflanzen/PlantInstanceListPage';

describe('PlantInstanceListPage — mobile card hooks', () => {
  beforeEach(async () => {
    await i18n.changeLanguage('de');
  });

  afterEach(() => {
    cleanup();
  });

  it('keys the card title, phase chip and planting date of a plant card', async () => {
    renderWithProviders(<PlantInstanceListPage />);

    const cards = await screen.findByTestId('data-table-cards');
    const row = within(cards).getAllByTestId('data-table-row')[0];

    expect(within(row).getByTestId('card-title').textContent).toBe('Big Red');
    expect(within(row).getByTestId('card-subtitle').textContent).toBe('TOM-001');
    expect(within(row).getByTestId('card-chip-currentPhase').textContent).toBe('Vegetativ');
    expect(within(row).getByTestId('card-field-plantedOn')).toBeInTheDocument();
  });

  it('omits the hooks of the fields the plant has no data for', async () => {
    renderWithProviders(<PlantInstanceListPage />);

    const cards = await screen.findByTestId('data-table-cards');
    const row = within(cards).getAllByTestId('data-table-row')[0];

    // The seeded plant has neither a location nor a planting run. Reading the
    // first chip / first caption would have returned the phase chip and the
    // planting date here — the wrong value, silently. The keyed hooks report
    // absence instead.
    expect(within(row).queryByTestId('card-field-location')).toBeNull();
    expect(within(row).queryByTestId('card-chip-plantingRun')).toBeNull();
  });
});
