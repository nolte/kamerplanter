/**
 * #1628 acceptance: a failed catalogue load never renders as an empty picker.
 *
 * **The defect.** `useCatalogue` keeps pending / failed / empty apart, but
 * fourteen of its sixteen call sites rendered only `items` — so on a 500 the
 * picker showed an empty list, no message, no retry, and the user read it as
 * "there are no species". Four of them back a mandatory field.
 *
 * **What each row asserts.** The catalogue's endpoint answers 500; the site then
 * shows `CatalogueLoadError` for *that* catalogue (an announced alert with a
 * retry), and — where the catalogue feeds a picker — that picker is disabled, so
 * an empty, operable list cannot be mistaken for an empty catalogue. Against the
 * old code the element does not exist and the picker is enabled.
 *
 * The three detail pages (`SubstrateDetailPage`, `SpeciesDetailPage`,
 * `PlantInstanceDetailPage`) carry their row in their own suites, because they
 * need the route mocks those suites already set up.
 */
import type { ReactElement } from 'react';
import { cleanup, screen, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, beforeEach, describe, expect, it } from 'vitest';
import { http, HttpResponse } from 'msw';
import i18n from 'i18next';
import PropagationEventDialog from '@/pages/propagation/PropagationEventDialog';
import LineagePanel from '@/pages/propagation/LineagePanel';
import SuccessionPlanDialog from '@/pages/durchlaeufe/SuccessionPlanDialog';
import SuccessionPlanListPage from '@/pages/durchlaeufe/SuccessionPlanListPage';
import PlantingRunCreateDialog from '@/pages/durchlaeufe/PlantingRunCreateDialog';
import PlantInstanceCreateDialog from '@/pages/pflanzen/PlantInstanceCreateDialog';
import PlantInstanceListPage from '@/pages/pflanzen/PlantInstanceListPage';
import SpeciesCompanionTab from '@/pages/stammdaten/species-detail/SpeciesCompanionTab';
import CompanionPlantingPage from '@/pages/stammdaten/CompanionPlantingPage';
import { renderWithProviders } from '../helpers';
import { server } from '../mocks/server';
import { WAIT_BUDGET } from '../waitBudget';

const URLS = {
  species: '/api/v1/species',
  substrates: '/api/v1/substrates',
} as const;

type Catalogue = keyof typeof URLS;

interface CallSite {
  /** `file:line` of the `useCatalogue(` call, for the reader of a red run. */
  site: string;
  catalogue: Catalogue;
  render: () => ReactElement;
  /**
   * Returns the picker the catalogue feeds, or `null` for a lookup-only site.
   * Called after the failure element is on screen.
   */
  picker: (() => HTMLElement) | null;
  /** Steps a user takes before the picker exists (e.g. opening a dialog). */
  before?: (user: ReturnType<typeof userEvent.setup>) => Promise<void>;
}

/** The `<input>` inside a `form-field-<name>` wrapper. */
function fieldInput(name: string): HTMLElement {
  return within(screen.getByTestId(`form-field-${name}`)).getByRole('combobox');
}

const CALL_SITES: CallSite[] = [
  {
    site: 'propagation/PropagationEventDialog.tsx:74',
    catalogue: 'species',
    render: () => <PropagationEventDialog open onClose={() => {}} onCreated={() => {}} />,
    picker: () => fieldInput('species_key'),
  },
  {
    site: 'durchlaeufe/SuccessionPlanDialog.tsx:102',
    catalogue: 'species',
    render: () => <SuccessionPlanDialog open onClose={() => {}} onSaved={() => {}} />,
    picker: () => fieldInput('species_key'),
  },
  {
    site: 'durchlaeufe/PlantingRunCreateDialog.tsx:214',
    catalogue: 'species',
    render: () => <PlantingRunCreateDialog open onClose={() => {}} onCreated={() => {}} />,
    picker: () => fieldInput('entries.0.species_key'),
  },
  {
    site: 'pflanzen/PlantInstanceCreateDialog.tsx:122',
    catalogue: 'species',
    render: () => <PlantInstanceCreateDialog open onClose={() => {}} onCreated={() => {}} />,
    picker: () => fieldInput('species_key'),
  },
  {
    site: 'pflanzen/PlantInstanceCreateDialog.tsx:125',
    catalogue: 'substrates',
    render: () => <PlantInstanceCreateDialog open onClose={() => {}} onCreated={() => {}} />,
    picker: () => fieldInput('substrate_key'),
  },
  {
    site: 'durchlaeufe/SuccessionPlanListPage.tsx:81',
    catalogue: 'species',
    render: () => <SuccessionPlanListPage />,
    picker: null,
  },
  {
    site: 'pflanzen/PlantInstanceListPage.tsx:49',
    catalogue: 'species',
    render: () => <PlantInstanceListPage />,
    picker: null,
  },
  {
    site: 'propagation/LineagePanel.tsx:62',
    catalogue: 'species',
    render: () => <LineagePanel />,
    picker: null,
  },
  {
    site: 'stammdaten/CompanionPlantingPage.tsx:81',
    catalogue: 'species',
    render: () => <CompanionPlantingPage />,
    picker: () => within(screen.getByTestId('species-select')).getByRole('combobox'),
  },
  {
    site: 'stammdaten/species-detail/SpeciesCompanionTab.tsx:58',
    catalogue: 'species',
    render: () => (
      <SpeciesCompanionTab speciesKey="sp-1" speciesName="Tomate" fullScreen={false} />
    ),
    // The picker lives in the add-relation dialog, so the user opens it first.
    before: async (user) => {
      await user.click(await screen.findByTestId('add-compatible-button'));
    },
    picker: () => within(screen.getByTestId('target-species-select')).getByRole('combobox'),
  },
];

describe('a failed catalogue load is not an empty picker (#1628)', () => {
  beforeEach(() => {
    i18n.changeLanguage('de');
  });

  afterEach(() => {
    cleanup();
    i18n.changeLanguage('en');
  });

  it.each(CALL_SITES)('$site shows the $catalogue failure', async (callSite) => {
    server.use(http.get(URLS[callSite.catalogue], () => new HttpResponse(null, { status: 500 })));
    const user = userEvent.setup();
    renderWithProviders(callSite.render());
    await callSite.before?.(user);

    const element = await screen.findByTestId(
      `catalogue-load-error-${callSite.catalogue}`,
      {},
      { timeout: WAIT_BUDGET },
    );
    // Announced, and says what failed rather than that nothing exists.
    expect(within(element).getByRole('alert').textContent).toContain(
      i18n.t(`common.catalogue.names.${callSite.catalogue}`),
    );
    expect(
      within(element).getByTestId(`catalogue-load-error-${callSite.catalogue}-retry`),
    ).toBeTruthy();

    if (callSite.picker) {
      // An operable empty picker is the defect; a locked one next to the alert
      // is the repair.
      const picker = callSite.picker();
      const disabled =
        picker.hasAttribute('disabled') || picker.getAttribute('aria-disabled') === 'true';
      expect(disabled, `${callSite.site}: picker must be locked while failed`).toBe(true);
    }
  });
});
