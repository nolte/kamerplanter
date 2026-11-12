/**
 * Area doses and amendment materials in the bed care dialog (REQ-053 GP-FR-123/124, WP 8.9): the rate comes
 * from the product data sheet only, the live total follows the bed area, a bed without area disables the
 * per-m² units, a zero rate is refused, "≈ kg N/ha" is an approximation, liming shows a text-only hint.
 */
import { act, cleanup, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { http, HttpResponse } from 'msw';
import { afterEach, describe, expect, it, vi } from 'vitest';
import type { Fertilizer } from '@/api/types';
import i18n from '@/i18n/i18n';
import { expectNoA11yViolations } from '@/test/a11y/expectNoA11yViolations';
import { authState, createTestStore, renderWithProviders, tenantState } from '@/test/helpers';
import { server } from '@/test/mocks/server';
import CareCompletionDialog from './CareCompletionDialog';
import type { CompletionPayload } from './careTypes';

function fertilizer(key: string, overrides: Partial<Fertilizer>): Fertilizer {
  return {
    key,
    product_name: key,
    brand: '',
    fertilizer_type: 'organic',
    is_organic: true,
    tank_safe: false,
    recommended_application: 'any',
    npk_ratio: [0, 0, 0],
    ec_contribution_per_ml: 0,
    ec_contribution_uncertain: false,
    max_dose_ml_per_liter: null,
    mixing_priority: 50,
    ph_effect: 'neutral',
    bioavailability: 'slow_release',
    shelf_life_days: null,
    storage_temp_min: null,
    storage_temp_max: null,
    application_rate_g_per_m2: null,
    application_rate_l_per_m2: null,
    dilution_ratio: null,
    nutrient_release_speed: null,
    notes: null,
    created_at: null,
    updated_at: null,
    ...overrides,
  } as Fertilizer;
}

const CATALOGUE = [
  fertilizer('horn', {
    product_name: 'Horn shavings',
    application_rate_g_per_m2: 80,
    npk_ratio: [13, 0, 0],
  }),
  fertilizer('compost', { product_name: 'Green compost', application_rate_l_per_m2: 3 }),
  fertilizer('tea', { product_name: 'Nettle tea' }),
];

function useCatalogue() {
  server.use(http.get('/api/v1/t/:tenant/fertilizers', () => HttpResponse.json(CATALOGUE)));
}

function renderDialog(category: string, areaM2: number | null | undefined, onSubmit = vi.fn()) {
  const view = renderWithProviders(
    <CareCompletionDialog
      category={category}
      subject="Bed B03"
      saving={false}
      areaM2={areaM2}
      onSubmit={onSubmit}
      onClose={() => undefined}
    />,
    { store: createTestStore({ ...tenantState('grower'), ...authState() }) },
  );
  return { ...view, onSubmit };
}

async function pickProduct(user: ReturnType<typeof userEvent.setup>, name: string) {
  const input = screen.getByTestId('care-complete-product');
  await user.click(input);
  await user.type(input, name.slice(0, 4));
  await user.click(await screen.findByRole('option', { name }));
}

afterEach(() => cleanup());

describe('area dosing (GP-FR-123)', () => {
  it('pre-fills a fractional rate with the decimal comma in German (#2905)', async () => {
    server.use(
      http.get('/api/v1/t/:tenant/fertilizers', () =>
        HttpResponse.json([fertilizer('mulch', { product_name: 'Bark mulch', application_rate_l_per_m2: 0.5 })]),
      ),
    );
    const original = i18n.language;
    await act(() => i18n.changeLanguage('de'));
    try {
      const user = userEvent.setup();
      renderDialog('feeding', 3.6);
      await pickProduct(user, 'Bark mulch');
      expect(screen.getByTestId('care-complete-quantity')).toHaveValue('0,5');
    } finally {
      cleanup();
      await act(() => i18n.changeLanguage(original));
    }
  });

  it('pre-fills 80 g/m² from the data sheet, shows 288 g on 3.6 m² and sends rate and unit', async () => {
    useCatalogue();
    const user = userEvent.setup();
    const { onSubmit } = renderDialog('feeding', 3.6);

    await pickProduct(user, 'Horn shavings');

    expect(screen.getByTestId('care-complete-quantity')).toHaveValue('80');
    expect(screen.getByTestId('care-complete-unit')).toHaveValue('g_per_m2');
    expect(screen.getByTestId('care-complete-rate-source')).toHaveTextContent('data sheet');
    expect(screen.getByTestId('care-complete-total')).toHaveTextContent('Total for 3.6 m²: 288 g');

    await user.click(screen.getByTestId('care-complete-submit'));
    const payload: CompletionPayload = onSubmit.mock.calls[0][0];
    expect(payload).toEqual({
      product_ref: { kind: 'fertilizer', key: 'horn' },
      product_label: 'Horn shavings',
      quantity: 80,
      unit: 'g_per_m2',
    });
  });

  it('shows ≈ 104 kg N/ha for 80 g/m² at 13 % N, labelled as an approximation', async () => {
    useCatalogue();
    const user = userEvent.setup();
    renderDialog('feeding', 3.6);

    await pickProduct(user, 'Horn shavings');

    const nitrogen = screen.getByTestId('care-complete-nitrogen');
    expect(nitrogen).toHaveTextContent('≈ 104 kg N/ha (10.4 g N/m²)');
    expect(nitrogen).toHaveTextContent('Approximation');
    // No seasonal-sum warning: the threshold stays unset until R-004 is closed.
    expect(screen.queryByRole('alert')).toBeNull();
  });

  it('pre-fills 3 L/m² and shows 10.8 L with the layer in mm', async () => {
    useCatalogue();
    const user = userEvent.setup();
    renderDialog('feeding', 3.6);

    await pickProduct(user, 'Green compost');

    expect(screen.getByTestId('care-complete-quantity')).toHaveValue('3');
    expect(screen.getByTestId('care-complete-unit')).toHaveValue('l_per_m2');
    expect(screen.getByTestId('care-complete-total')).toHaveTextContent(
      'Total for 3.6 m²: 10.8 L (a 3 mm layer)',
    );
    expect(screen.queryByTestId('care-complete-nitrogen')).toBeNull();
  });

  it('never overwrites a quantity the user typed', async () => {
    useCatalogue();
    const user = userEvent.setup();
    renderDialog('feeding', 3.6);

    await user.type(screen.getByTestId('care-complete-quantity'), '50');
    await pickProduct(user, 'Horn shavings');

    expect(screen.getByTestId('care-complete-quantity')).toHaveValue('50');
    expect(screen.queryByTestId('care-complete-rate-source')).toBeNull();
  });

  it('another product replaces a pre-filled rate; one without a rate clears it', async () => {
    useCatalogue();
    const user = userEvent.setup();
    renderDialog('feeding', 3.6);

    await pickProduct(user, 'Horn shavings');
    await user.clear(screen.getByTestId('care-complete-product'));
    await pickProduct(user, 'Green compost');
    expect(screen.getByTestId('care-complete-quantity')).toHaveValue('3');
    expect(screen.getByTestId('care-complete-unit')).toHaveValue('l_per_m2');

    await user.clear(screen.getByTestId('care-complete-product'));
    await pickProduct(user, 'Nettle tea');
    expect(screen.getByTestId('care-complete-quantity')).toHaveValue('');
    expect(screen.queryByTestId('care-complete-total')).toBeNull();
  });

  it('a bed without area disables the per-m² units and takes no rate from the data sheet', async () => {
    useCatalogue();
    const user = userEvent.setup();
    renderDialog('feeding', 0);

    await pickProduct(user, 'Horn shavings');
    expect(screen.getByTestId('care-complete-quantity')).toHaveValue('');
    expect(screen.getByTestId('care-complete-unit')).toHaveValue('ml');
    expect(screen.getByText(/This bed has no area/)).toBeInTheDocument();

    await user.click(screen.getByRole('combobox', { name: 'Unit' }));
    const listbox = await screen.findByRole('listbox');
    expect(within(listbox).getByTestId('care-complete-unit-g_per_m2')).toHaveAttribute(
      'aria-disabled',
      'true',
    );
    expect(within(listbox).getByTestId('care-complete-unit-l_per_m2')).toHaveAttribute(
      'aria-disabled',
      'true',
    );
    expect(within(listbox).getByTestId('care-complete-unit-g')).not.toHaveAttribute(
      'aria-disabled',
    );
  });

  it('a soil amendment on a bed without area defaults to kilograms instead of g/m²', () => {
    useCatalogue();
    renderDialog('soil_amendment', null);
    expect(screen.getByTestId('care-complete-unit')).toHaveValue('kg');
  });

  it('refuses a rate of 0 per m² instead of sending a total of 0', async () => {
    useCatalogue();
    const user = userEvent.setup();
    const { onSubmit } = renderDialog('soil_amendment', 3.6);

    await user.type(screen.getByTestId('care-complete-quantity'), '0');
    await user.click(screen.getByTestId('care-complete-submit'));

    expect(onSubmit).not.toHaveBeenCalled();
    expect(screen.getByText('A rate per m² must be greater than 0.')).toBeInTheDocument();
    expect(screen.queryByTestId('care-complete-total')).toBeNull();
  });

  it('refuses a quantity that is no number', async () => {
    useCatalogue();
    const user = userEvent.setup();
    const { onSubmit } = renderDialog('feeding', 3.6);

    await user.type(screen.getByTestId('care-complete-quantity'), 'NaN');
    await user.click(screen.getByTestId('care-complete-submit'));

    expect(onSubmit).not.toHaveBeenCalled();
  });
});

describe('amendment materials (GP-FR-124)', () => {
  it('offers the GP-FR-124 materials translated, and free text stays possible', async () => {
    useCatalogue();
    const user = userEvent.setup();
    const { onSubmit } = renderDialog('soil_amendment', 3.6);

    await user.click(screen.getByTestId('care-complete-material'));
    const options = (await screen.findAllByRole('option')).map((option) => option.textContent);
    expect(options).toEqual(
      expect.arrayContaining(['Compost', 'Rock dust', 'Biochar', 'Wood ash', 'Lime', 'Other']),
    );

    await user.type(screen.getByTestId('care-complete-material'), 'Leaf mould');
    await user.keyboard('{Escape}');
    await user.click(screen.getByTestId('care-complete-submit'));
    expect(onSubmit.mock.calls[0][0]).toEqual({ material: 'Leaf mould' });
  });

  it('liming shows the text-only pH hint and computes no lime amount', async () => {
    useCatalogue();
    renderDialog('liming', 3.6);

    const hint = screen.getByTestId('care-complete-liming-hint');
    expect(hint).toHaveTextContent('above the target pH');
    expect(hint).toHaveTextContent('acid-loving plants');
    expect(screen.getByTestId('care-complete-quantity')).toHaveValue('');
  });

  it('a soil amendment shows the hint for wood ash, not for compost', async () => {
    useCatalogue();
    const user = userEvent.setup();
    renderDialog('soil_amendment', 3.6);

    expect(screen.queryByTestId('care-complete-liming-hint')).toBeNull();
    await user.click(screen.getByTestId('care-complete-material'));
    await user.click(await screen.findByRole('option', { name: 'Wood ash' }));
    await waitFor(() =>
      expect(screen.getByTestId('care-complete-liming-hint')).toBeInTheDocument(),
    );
  });
});

describe('accessibility', () => {
  it('the feeding dialog with total and N approximation has no critical axe violations', async () => {
    useCatalogue();
    const user = userEvent.setup();
    renderDialog('feeding', 3.6);
    await pickProduct(user, 'Horn shavings');
    await user.keyboard('{Escape}');
    await screen.findByTestId('care-complete-nitrogen');
    await expectNoA11yViolations(document.body, { minElements: 30 });
  });

  it('the liming dialog with its hint has no critical axe violations', async () => {
    useCatalogue();
    renderDialog('liming', 3.6);
    await screen.findByTestId('care-complete-liming-hint');
    await expectNoA11yViolations(document.body, { minElements: 20 });
  });
});
