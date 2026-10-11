import { describe, it, expect, vi, beforeEach } from 'vitest';
import { screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import i18n from 'i18next';
import { ApiError } from '@/api/errors';
import type { Plan } from '@/api/types';
import AdminPlansPage from '@/pages/admin/AdminPlansPage';
import { authState, createTestStore, renderWithProviders } from '@/test/helpers';

/**
 * REQ-056 §7.6 / §15 (AK-45) — the plan catalogue page of the platform admin: a DataTable with the
 * default marker and the number of gardens, a form (react-hook-form + Zod, FormActions,
 * UnsavedChangesGuard) and a ConfirmDialog for deleting. An empty limit follows the instance setting,
 * `0` lifts it; the default plan and a plan in use cannot be deleted and the page says why.
 */

vi.mock('@/api/endpoints/adminPlans', () => ({
  listPlans: vi.fn(),
  createPlan: vi.fn(),
  updatePlan: vi.fn(),
  deletePlan: vi.fn(),
}));

const api = await import('@/api/endpoints/adminPlans');
const fn = (f: unknown) => f as ReturnType<typeof vi.fn>;

const STANDARD: Plan = {
  key: 'standard',
  name: 'Standard',
  description: null,
  limits: {
    members: null,
    service_accounts: null,
    storage_mb: null,
    photos_per_instance: null,
    ai_calls_per_user_day: null,
    ai_calls_per_tenant_day: null,
    ai_tokens_per_tenant_day: null,
  },
  unlimited: [],
  is_default: true,
  tenant_count: 4,
  created_at: null,
  updated_at: null,
};

const COMMUNITY: Plan = {
  ...STANDARD,
  key: 'community',
  name: 'Gemeinschaftsgarten',
  limits: { ...STANDARD.limits, members: 30, storage_mb: 0, ai_calls_per_tenant_day: 0 },
  unlimited: ['storage_mb', 'ai_calls_per_tenant_day'],
  is_default: false,
  tenant_count: 2,
};

const UNUSED: Plan = { ...COMMUNITY, key: 'trial', name: 'Probe', tenant_count: 0, limits: { ...STANDARD.limits } };

function apiError(status: number, code: string, details: { field: string; reason: string; code: string }[] = []): ApiError {
  return new ApiError(
    { error_id: 'e', error_code: code, message: 'English', details, timestamp: '', path: '/', method: 'POST' },
    status,
  );
}

async function renderPage(plans: Plan[] = [STANDARD, COMMUNITY, UNUSED]) {
  fn(api.listPlans).mockResolvedValue(plans);
  renderWithProviders(<AdminPlansPage />, { store: createTestStore(authState({ platformAdmin: true })) });
  await screen.findByRole('table', { name: 'Pläne' });
}

describe('AdminPlansPage (REQ-056 AK-45)', () => {
  beforeEach(async () => {
    vi.clearAllMocks();
    await i18n.changeLanguage('de');
  });

  it('lists every plan with the default marker, the number of gardens and readable limits', async () => {
    await renderPage();
    expect(screen.getByTestId('plan-default-standard')).toHaveTextContent('Standard');
    expect(screen.queryByTestId('plan-default-community')).toBeNull();
    expect(screen.getByTestId('plan-tenants-standard')).toHaveTextContent('4');
    // null = the instance setting, a number with its unit, 0 = unlimited / budget off — never "0".
    expect(screen.getByTestId('plan-limit-standard-members')).toHaveTextContent('wie Instanz-Einstellung');
    expect(screen.getByTestId('plan-limit-community-members')).toHaveTextContent('30 Mitglieder');
    expect(screen.getByTestId('plan-limit-community-storage_mb')).toHaveTextContent('unbegrenzt');
    expect(screen.getByTestId('plan-limit-community-ai_calls_per_tenant_day')).toHaveTextContent('Budget aus');
    expect(screen.getByTestId('plans-value-legend')).toBeInTheDocument();
  });

  it('blocks deleting the default plan and a plan in use, and says why', async () => {
    await renderPage();
    const defaultDelete = screen.getByTestId('plan-delete-standard');
    expect(defaultDelete).toBeDisabled();
    expect(defaultDelete).toHaveAccessibleName(/Standard-Plan lässt sich nicht löschen/);
    const inUseDelete = screen.getByTestId('plan-delete-community');
    expect(inUseDelete).toBeDisabled();
    expect(inUseDelete).toHaveAccessibleName(/2 Gärten nutzen diesen Plan/);
    expect(screen.getByTestId('plan-delete-trial')).toBeEnabled();
  });

  it('deletes an unused plan after the confirmation and reloads the list', async () => {
    await renderPage();
    fn(api.deletePlan).mockResolvedValue(undefined);
    await userEvent.click(screen.getByTestId('plan-delete-trial'));
    const dialog = await screen.findByTestId('confirm-dialog');
    expect(dialog).toHaveTextContent('Probe');
    await userEvent.click(within(dialog).getByTestId('confirm-dialog-confirm'));
    await waitFor(() => expect(api.deletePlan).toHaveBeenCalledWith('trial'));
    await waitFor(() => expect(api.listPlans).toHaveBeenCalledTimes(2));
  });

  it('creates a plan: an empty limit is left out (instance setting), a 0 is sent as 0 (unlimited)', async () => {
    await renderPage();
    fn(api.createPlan).mockImplementation(async (payload) => ({ ...UNUSED, ...payload }));
    await userEvent.click(screen.getByTestId('plan-add'));
    const dialog = await screen.findByTestId('plan-form-dialog');
    expect(within(dialog).getByTestId('plan-form-default-hint')).toBeInTheDocument();

    await userEvent.type(within(dialog).getByRole('textbox', { name: /Schlüssel/ }), 'verein');
    await userEvent.type(within(dialog).getByRole('textbox', { name: /^Name/ }), 'Verein');
    await userEvent.type(within(dialog).getByRole('spinbutton', { name: /^Mitglieder/ }), '25');
    const storage = within(dialog).getByRole('spinbutton', { name: /^Speicherplatz/ });
    await userEvent.type(storage, '0');
    // The field spells out what the value means before saving.
    expect(within(dialog).getByText(/Gilt als: unbegrenzt\./)).toBeInTheDocument();

    await userEvent.click(within(dialog).getByTestId('form-submit-button'));
    await waitFor(() =>
      expect(api.createPlan).toHaveBeenCalledWith({
        key: 'verein',
        name: 'Verein',
        description: null,
        limits: { members: 25, storage_mb: 0 },
      }),
    );
  });

  it('refuses an invalid key and a member limit below 1 before sending anything', async () => {
    await renderPage();
    await userEvent.click(screen.getByTestId('plan-add'));
    const dialog = await screen.findByTestId('plan-form-dialog');
    await userEvent.type(within(dialog).getByRole('textbox', { name: /Schlüssel/ }), 'Bad Key');
    await userEvent.type(within(dialog).getByRole('textbox', { name: /^Name/ }), 'X');
    await userEvent.type(within(dialog).getByRole('spinbutton', { name: /^Mitglieder/ }), '0');
    await userEvent.click(within(dialog).getByTestId('form-submit-button'));
    expect(await within(dialog).findByText(/beginnend mit einem Buchstaben/)).toBeInTheDocument();
    expect(within(dialog).getByText('Mindestens 1.')).toBeInTheDocument();
    expect(api.createPlan).not.toHaveBeenCalled();
  });

  it('shows a taken key (409 DUPLICATE_ENTRY) on the key field in German', async () => {
    await renderPage();
    fn(api.createPlan).mockRejectedValue(
      apiError(409, 'DUPLICATE_ENTRY', [{ field: 'key', reason: "Value 'community' is already taken.", code: 'DUPLICATE_ENTRY' }]),
    );
    await userEvent.click(screen.getByTestId('plan-add'));
    const dialog = await screen.findByTestId('plan-form-dialog');
    await userEvent.type(within(dialog).getByRole('textbox', { name: /Schlüssel/ }), 'community');
    await userEvent.type(within(dialog).getByRole('textbox', { name: /^Name/ }), 'Doppelt');
    await userEvent.click(within(dialog).getByTestId('form-submit-button'));
    expect(await within(dialog).findByText('Diesen Schlüssel hat schon ein anderer Plan.')).toBeInTheDocument();
  });

  it('edits only what changed: a cleared limit goes back to the instance setting (null)', async () => {
    await renderPage();
    fn(api.updatePlan).mockImplementation(async (_key, payload) => ({ ...COMMUNITY, ...payload }));
    await userEvent.click(screen.getByTestId('plan-edit-community'));
    const dialog = await screen.findByTestId('plan-form-dialog');
    expect(within(dialog).getByRole('textbox', { name: /Schlüssel/ })).toBeDisabled();

    await userEvent.clear(within(dialog).getByRole('spinbutton', { name: /^Mitglieder/ }));
    await userEvent.click(within(dialog).getByTestId('form-submit-button'));
    await waitFor(() => expect(api.updatePlan).toHaveBeenCalledWith('community', { limits: { members: null } }));
  });

  it('makes a plan the default from its form; the default plan offers no way to unset it', async () => {
    await renderPage();
    fn(api.updatePlan).mockImplementation(async (_key, payload) => ({ ...COMMUNITY, ...payload }));
    await userEvent.click(screen.getByTestId('plan-edit-community'));
    let dialog = await screen.findByTestId('plan-form-dialog');
    await userEvent.click(within(dialog).getByRole('switch', { name: /Als Standard-Plan festlegen/ }));
    await userEvent.click(within(dialog).getByTestId('form-submit-button'));
    await waitFor(() => expect(api.updatePlan).toHaveBeenCalledWith('community', { is_default: true }));

    await waitFor(() => expect(screen.queryByTestId('plan-form-dialog')).toBeNull());
    await userEvent.click(screen.getByTestId('plan-edit-standard'));
    dialog = await screen.findByTestId('plan-form-dialog');
    expect(within(dialog).getByTestId('plan-form-is-default')).toBeInTheDocument();
    expect(within(dialog).queryByRole('switch')).toBeNull();
  });
});
