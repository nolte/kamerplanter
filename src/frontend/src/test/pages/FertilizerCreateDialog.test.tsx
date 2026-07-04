import { screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { http, HttpResponse } from 'msw';
import i18n from 'i18next';
import FertilizerCreateDialog from '@/pages/duengung/FertilizerCreateDialog';
import { renderWithProviders } from '../helpers';
import { server } from '../mocks/server';

describe('FertilizerCreateDialog — W-013 area-dosing fields', () => {
  beforeEach(() => {
    i18n.changeLanguage('de');
  });

  it('renders the area-dosing fields (g/m², L/m², dilution ratio, release speed)', async () => {
    renderWithProviders(<FertilizerCreateDialog open onClose={() => {}} onCreated={() => {}} />);
    await screen.findByTestId('fertilizer-create-dialog');
    expect(screen.getByTestId('form-field-application_rate_g_per_m2')).toBeTruthy();
    expect(screen.getByTestId('form-field-application_rate_l_per_m2')).toBeTruthy();
    expect(screen.getByTestId('form-field-dilution_ratio')).toBeTruthy();
    expect(screen.getByTestId('form-field-nutrient_release_speed')).toBeTruthy();
  });

  it('offers CalMag as a fertilizer type option', async () => {
    const user = userEvent.setup();
    renderWithProviders(<FertilizerCreateDialog open onClose={() => {}} onCreated={() => {}} />);
    await screen.findByTestId('fertilizer-create-dialog');
    const typeField = within(screen.getByTestId('form-field-fertilizer_type')).getByRole('combobox');
    await user.click(typeField);
    const option = await screen.findByRole('option', { name: /CalMag/i });
    expect(option).toBeTruthy();
  });

  it('sends the W-013 fields on submit and calls onCreated', async () => {
    let captured: Record<string, unknown> | null = null;
    server.use(
      http.post('/api/v1/t/:tenant/fertilizers', async ({ request }) => {
        captured = (await request.json()) as Record<string, unknown>;
        return HttpResponse.json({ key: 'f-1', product_name: 'Compost' }, { status: 201 });
      }),
    );
    const user = userEvent.setup();
    const onCreated = vi.fn();
    renderWithProviders(<FertilizerCreateDialog open onClose={() => {}} onCreated={onCreated} />);
    await screen.findByTestId('fertilizer-create-dialog');

    const nameField = within(screen.getByTestId('form-field-product_name')).getByRole('textbox');
    await user.type(nameField, 'Compost');

    const gPerM2 = within(screen.getByTestId('form-field-application_rate_g_per_m2')).getByRole('spinbutton');
    await user.type(gPerM2, '150');
    const dilution = within(screen.getByTestId('form-field-dilution_ratio')).getByRole('textbox');
    await user.type(dilution, '1:10');

    await user.click(screen.getByTestId('form-submit-button'));

    await waitFor(() => expect(onCreated).toHaveBeenCalledOnce());
    expect(captured).toMatchObject({
      application_rate_g_per_m2: 150,
      dilution_ratio: '1:10',
    });
  });

  it('rejects an invalid dilution ratio without submitting', async () => {
    const onCreated = vi.fn();
    const user = userEvent.setup();
    renderWithProviders(<FertilizerCreateDialog open onClose={() => {}} onCreated={onCreated} />);
    await screen.findByTestId('fertilizer-create-dialog');

    const nameField = within(screen.getByTestId('form-field-product_name')).getByRole('textbox');
    await user.type(nameField, 'Compost');
    const dilution = within(screen.getByTestId('form-field-dilution_ratio')).getByRole('textbox');
    await user.type(dilution, 'not-a-ratio');

    await user.click(screen.getByTestId('form-submit-button'));

    await waitFor(() => {
      expect(screen.getByTestId('form-submit-button')).not.toBeDisabled();
    });
    expect(onCreated).not.toHaveBeenCalled();
  });
});
