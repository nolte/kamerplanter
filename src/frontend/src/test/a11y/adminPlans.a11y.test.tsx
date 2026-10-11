/**
 * Axe pass for the plan catalogue page and its form (REQ-056 AK-45, #1094).
 *
 * Scanned in the states a platform admin reaches: the populated list (with a disabled, explained
 * delete), the create form and the delete confirmation. Dialogs render into a portal, so the
 * container is `document.body`; the element floor stops a scan of an empty portal from counting.
 */

import { screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, beforeEach, vi } from 'vitest';
import i18n from 'i18next';
import type { Plan } from '@/api/types';
import AdminPlansPage from '@/pages/admin/AdminPlansPage';
import { createTestStore, authState, renderWithProviders } from '@/test/helpers';
import { expectNoA11yViolations } from './expectNoA11yViolations';

vi.mock('@/api/endpoints/adminPlans', () => ({
  listPlans: vi.fn(),
  createPlan: vi.fn(),
  updatePlan: vi.fn(),
  deletePlan: vi.fn(),
}));

const api = await import('@/api/endpoints/adminPlans');

const STANDARD: Plan = {
  key: 'standard',
  name: 'Standard',
  description: null,
  limits: {},
  unlimited: [],
  is_default: true,
  tenant_count: 3,
  created_at: null,
  updated_at: null,
};
const TRIAL: Plan = { ...STANDARD, key: 'trial', name: 'Probe', is_default: false, tenant_count: 0, limits: { storage_mb: 0 } };

async function renderPage() {
  (api.listPlans as ReturnType<typeof vi.fn>).mockResolvedValue([STANDARD, TRIAL]);
  renderWithProviders(<AdminPlansPage />, { store: createTestStore(authState({ platformAdmin: true })) });
  await screen.findByRole('table', { name: 'Pläne' });
}

describe('plan catalogue page a11y', () => {
  beforeEach(() => i18n.changeLanguage('de'));

  it('the populated list has no critical axe violations', async () => {
    await renderPage();
    await expectNoA11yViolations(document.body, { minElements: 40 });
  });

  it('the create form has no critical axe violations', async () => {
    await renderPage();
    await userEvent.click(screen.getByTestId('plan-add'));
    await screen.findByTestId('plan-form-dialog');
    await expectNoA11yViolations(document.body, { minElements: 60 });
  });

  it('the delete confirmation has no critical axe violations', async () => {
    await renderPage();
    await userEvent.click(screen.getByTestId('plan-delete-trial'));
    await screen.findByTestId('confirm-dialog');
    await expectNoA11yViolations(document.body, { minElements: 30 });
  });
});
