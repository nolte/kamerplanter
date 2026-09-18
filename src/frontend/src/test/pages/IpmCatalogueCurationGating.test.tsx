import type { ReactElement } from 'react';
import { screen } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import i18n from 'i18next';
import PestListPage from '@/pages/pflanzenschutz/PestListPage';
import DiseaseListPage from '@/pages/pflanzenschutz/DiseaseListPage';
import TreatmentListPage from '@/pages/pflanzenschutz/TreatmentListPage';
import {
  createPlatformAdminStore,
  createTestStore,
  renderWithProviders,
} from '../helpers';

/**
 * #1501 — the three IPM catalogue list pages offer their create control to a
 * platform admin only.
 *
 * `Pest`, `Disease` and `Treatment` are **installation-wide** reference data —
 * `app/api/v1/ipm/tenant_router.py` states it in its own module docstring, and the
 * models bear it out: none of the three carries a `tenant_key`. Their nine write
 * routes used to resolve `get_current_user` and nothing else, so any member of any
 * tenant could add to, edit or delete the catalogue everybody else reads. They now
 * carry `require_platform_admin`, which makes an unbound create button a control
 * that can only ever answer 403 — the mirror defect #1467 is about.
 *
 * `origin: 'tenant'` on a created row is what made these creates *look* local. It
 * is a provenance marker (hand-curated vs. seeded) and never an ownership stamp;
 * nothing has ever scoped an IPM read by it.
 *
 * ## Why the empty-state action is asserted too
 *
 * Each page offers the same create in two places: the header button and
 * `DataTable`'s empty-state action. Binding one and not the other is exactly the
 * "sibling nobody bound" class that produced #948 and #1467, so both are checked,
 * and the empty case is driven with an empty catalogue so the second control is
 * really on screen.
 */

// The pages dispatch their fetch thunks on mount; stub them so state comes purely
// from the preloaded store and no network is involved.
vi.mock('@/store/slices/ipmSlice', async (importOriginal) => {
  const actual = await importOriginal<typeof import('@/store/slices/ipmSlice')>();
  return {
    ...actual,
    fetchPests: () => ({ type: 'ipm/fetchPests/mock' }),
    fetchDiseases: () => ({ type: 'ipm/fetchDiseases/mock' }),
    fetchTreatments: () => ({ type: 'ipm/fetchTreatments/mock' }),
  };
});
vi.mock('@/store/slices/pestDetectionSlice', async (importOriginal) => {
  const actual = await importOriginal<typeof import('@/store/slices/pestDetectionSlice')>();
  return {
    ...actual,
    fetchPestDetectionStatus: () => ({ type: 'pestDetection/fetchStatus/mock' }),
  };
});

/** An `ipm` slice with every catalogue empty, so the empty-state action renders. */
const EMPTY_IPM = {
  ipm: {
    pests: [],
    diseases: [],
    treatments: [],
    inspections: [],
    applications: [],
    loading: false,
    error: null,
  },
};

const PAGES: ReadonlyArray<readonly [string, () => ReactElement, string, string]> = [
  ['pests', () => <PestListPage />, 'pages.ipm.createPest', 'pest-list-page'],
  ['diseases', () => <DiseaseListPage />, 'pages.ipm.createDisease', 'disease-list-page'],
  ['treatments', () => <TreatmentListPage />, 'pages.ipm.createTreatment', 'treatment-list-page'],
];

describe('#1501 — IPM catalogue creation is offered to a platform admin only', () => {
  it.each(PAGES)('%s: a platform admin is offered the create control', (_name, page) => {
    renderWithProviders(page(), { store: createPlatformAdminStore(EMPTY_IPM) });

    expect(screen.getByTestId('create-button')).toBeInTheDocument();
  });

  it.each(PAGES)(
    '%s: a non-admin sees the catalogue and neither create control',
    (_name, page, label, pageTestId) => {
      renderWithProviders(page(), { store: createTestStore(EMPTY_IPM) });

      // The read is not gated — the page itself still renders for every member.
      // Asserted on the page marker, not on a table: with the catalogue empty,
      // `DataTable` renders its empty state instead of a table, and asserting the
      // table would have made this pass only for the reason the create control is
      // hidden — i.e. for no reason at all.
      expect(screen.getByTestId(pageTestId)).toBeInTheDocument();

      expect(screen.queryByTestId('create-button')).not.toBeInTheDocument();
      // …and the empty-state action, which is the same create wearing another hat.
      expect(
        screen.queryByRole('button', { name: i18n.t(label) }),
      ).not.toBeInTheDocument();
    },
  );
});
