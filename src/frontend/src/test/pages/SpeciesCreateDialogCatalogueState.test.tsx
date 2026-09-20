/**
 * #1568 acceptance: the "Familie" dropdown reports a failed family load instead
 * of swallowing it.
 *
 * **The defect.** The dialog loaded its catalogue with
 * `listAllBotanicalFamilies().then(setFamilies).catch(() => {})`. On a failure
 * the mandatory field rendered its placeholder and nothing else — no message, no
 * spinner, no retry — so the user's only reading was "this species has no
 * family to choose", and the species was created without one. There was no
 * in-flight state and no ignore guard either, so closing and reopening the
 * dialog started a second sequence whose late answer could land on top of the
 * live one.
 *
 * **What makes this a falsification and not a neighbouring claim.** The rule is
 * "a failed catalogue load is visible and retryable at this field". The
 * assertions below read that field's own region, which against the old code was
 * an enabled select with one placeholder option and no sibling — the exact state
 * the repair changes.
 */
import { cleanup, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import { http, HttpResponse } from 'msw';
import i18n from 'i18next';
import SpeciesCreateDialog from '@/pages/stammdaten/SpeciesCreateDialog';
import { renderWithProviders, createStoreWithExpertise } from '../helpers';
import { server } from '../mocks/server';
import { WAIT_BUDGET } from '../waitBudget';

const FAMILIES_URL = '/api/v1/botanical-families';

function makeFamily(index: number) {
  return {
    key: `fam-${index}`,
    name: `Familie ${String(index).padStart(2, '0')}`,
    typical_nutrient_demand: 'medium',
    common_pests: [],
    rotation_category: 'fruit',
    created_at: '2024-01-01T00:00:00Z',
    updated_at: null,
  };
}

function renderDialog() {
  return renderWithProviders(
    <SpeciesCreateDialog open onClose={() => {}} onCreated={() => {}} />,
    { store: createStoreWithExpertise('expert') },
  );
}

describe('SpeciesCreateDialog — the family catalogue has three states (#1568)', () => {
  beforeEach(() => {
    i18n.changeLanguage('de');
  });

  afterEach(() => {
    cleanup();
    i18n.changeLanguage('en');
  });

  it('shows a retryable failure at the family field instead of an empty dropdown', async () => {
    server.use(http.get(FAMILIES_URL, () => new HttpResponse(null, { status: 500 })));
    renderDialog();

    await waitFor(
      () => {
        expect(screen.getByTestId('family-catalogue-error')).toBeTruthy();
      },
      { timeout: WAIT_BUDGET },
    );
    expect(screen.getByTestId('error-retry-button')).toBeTruthy();

    // Against the old code the field was enabled and silently offered only the
    // "—" placeholder, which reads as a deliberate "no family". It must not.
    expect(screen.queryByTestId('family-catalogue-empty')).toBeNull();
  });

  it('recovers through the retry control', async () => {
    let attempts = 0;
    server.use(
      http.get(FAMILIES_URL, () => {
        attempts += 1;
        if (attempts === 1) return new HttpResponse(null, { status: 500 });
        return HttpResponse.json([makeFamily(0)]);
      }),
    );
    const user = userEvent.setup();
    renderDialog();

    await waitFor(
      () => {
        expect(screen.getByTestId('error-retry-button')).toBeTruthy();
      },
      { timeout: WAIT_BUDGET },
    );
    await user.click(screen.getByTestId('error-retry-button'));

    await waitFor(
      () => {
        expect(screen.queryByTestId('family-catalogue-error')).toBeNull();
      },
      { timeout: WAIT_BUDGET },
    );

    // The recovered catalogue, read the way a user reaches it: MUI renders the
    // options into a popover only once the select is open, so asserting the
    // option without opening would assert nothing.
    const combobox = within(screen.getByTestId('form-field-family_key')).getByRole('combobox');
    await user.click(combobox);
    const listbox = await screen.findByRole('listbox');
    expect(within(listbox).getByText(makeFamily(0).name)).toBeTruthy();
    // Pins the recovery to a second request rather than to a re-render.
    expect(attempts).toBeGreaterThan(1);
  });

  it('says the catalogue is empty only when it arrived empty', async () => {
    server.use(http.get(FAMILIES_URL, () => HttpResponse.json([])));
    renderDialog();

    await waitFor(
      () => {
        expect(screen.getByTestId('family-catalogue-empty')).toBeTruthy();
      },
      { timeout: WAIT_BUDGET },
    );
    expect(screen.queryByTestId('family-catalogue-error')).toBeNull();
    expect(
      screen.getByText(i18n.t('pages.species.familyCatalogueEmpty')),
    ).toBeTruthy();
  });
});
