import { describe, it, expect, vi, beforeEach } from 'vitest';
import { screen, within, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import i18n from 'i18next';
import ChannelFertilizerDialog from '@/pages/duengung/ChannelFertilizerDialog';
import { renderWithProviders } from '../helpers';
import type { Fertilizer, FertilizerDosage } from '@/api/types';

/**
 * REQ-004 — ChannelFertilizerDialog renders one of two internal dialogs: an
 * edit dialog (single existing dosage) or an add dialog (multi-select draft
 * list). Both are pure and emit DosageEntry[] via onSave. These tests drive the
 * edit path (name resolution + fallback, dosage edit), and the add path
 * (multi-select, draft removal, availability filtering, count label).
 */

const t = (k: string) => i18n.t(k);

const fertilizers = [
  { key: 'f-calmag', product_name: 'CalMag', brand: 'BioBizz' },
  { key: 'f-grow', product_name: 'Grow A', brand: 'Canna' },
  { key: 'f-bloom', product_name: 'Bloom B', brand: 'Canna' },
] as unknown as Fertilizer[];

function dosage(overrides: Partial<FertilizerDosage> = {}): FertilizerDosage {
  return {
    fertilizer_key: 'f-calmag',
    ml_per_liter: 1.5,
    optional: false,
    mixing_order: 0,
    ...overrides,
  };
}

beforeEach(() => {
  i18n.changeLanguage('de');
});

describe('ChannelFertilizerDialog — edit mode', () => {
  it('resolves the fertilizer name, edits the dosage and saves a single entry', async () => {
    const user = userEvent.setup();
    const onSave = vi.fn();
    renderWithProviders(
      <ChannelFertilizerDialog
        open
        onClose={vi.fn()}
        onSave={onSave}
        fertilizers={fertilizers}
        existingFertilizerKeys={['f-calmag']}
        existingDosage={dosage()}
      />,
    );

    expect(screen.getByText(t('pages.nutrientPlans.editFertilizer'))).toBeInTheDocument();
    // Resolved fertilizer name shown in the disabled field.
    expect(screen.getByDisplayValue('CalMag (BioBizz)')).toBeInTheDocument();

    const mlField = within(
      screen.getByTestId('form-field-ml_per_liter'),
    ).getByRole('spinbutton');
    await user.clear(mlField);
    await user.type(mlField, '2.5');

    await user.click(screen.getByRole('button', { name: t('common.save') }));

    await waitFor(() => expect(onSave).toHaveBeenCalledTimes(1));
    expect(onSave.mock.calls[0][0]).toEqual([
      { fertilizer_key: 'f-calmag', ml_per_liter: 2.5, optional: false },
    ]);
  });

  it('falls back to the raw fertilizer key when it is unknown', () => {
    renderWithProviders(
      <ChannelFertilizerDialog
        open
        onClose={vi.fn()}
        onSave={vi.fn()}
        fertilizers={fertilizers}
        existingFertilizerKeys={[]}
        existingDosage={dosage({ fertilizer_key: 'ghost-key' })}
      />,
    );
    expect(screen.getByDisplayValue('ghost-key')).toBeInTheDocument();
  });
});

describe('ChannelFertilizerDialog — add mode', () => {
  it('selects fertilizers into the draft list, removes one and saves the rest', async () => {
    const user = userEvent.setup();
    const onSave = vi.fn();
    renderWithProviders(
      <ChannelFertilizerDialog
        open
        onClose={vi.fn()}
        onSave={onSave}
        fertilizers={fertilizers}
        // f-calmag already assigned → filtered out of the available options.
        existingFertilizerKeys={['f-calmag']}
      />,
    );

    expect(screen.getByText(t('pages.nutrientPlans.addFertilizer'))).toBeInTheDocument();

    // Save is disabled with an empty draft list.
    const saveButton = screen.getByRole('button', { name: t('common.save') });
    expect(saveButton).toBeDisabled();

    // Open the multi-select autocomplete and add the two available fertilizers.
    const combo = screen.getByRole('combobox');
    await user.click(combo);
    // f-calmag is excluded via existingFertilizerKeys.
    expect(screen.queryByRole('option', { name: /CalMag/ })).not.toBeInTheDocument();
    await user.click(await screen.findByRole('option', { name: /Grow A/ }));

    await user.click(combo);
    await user.click(await screen.findByRole('option', { name: /Bloom B/ }));

    // Two draft chips now present.
    expect(screen.getByText('Grow A (Canna)')).toBeInTheDocument();
    expect(screen.getByText('Bloom B (Canna)')).toBeInTheDocument();

    // Save label carries the count when more than one draft is queued.
    expect(
      screen.getByRole('button', { name: `${t('common.save')} (2)` }),
    ).toBeInTheDocument();

    // Remove the first draft via its delete icon-button.
    const growChip = screen.getByText('Grow A (Canna)').closest('div')!;
    const removeButton = within(growChip.parentElement as HTMLElement).getByRole('button', {
      name: t('common.delete'),
    });
    await user.click(removeButton);
    expect(screen.queryByText('Grow A (Canna)')).not.toBeInTheDocument();

    // Adjust the remaining draft's dose then save.
    const mlField = within(
      screen.getByTestId('form-field-drafts.0.ml_per_liter'),
    ).getByRole('spinbutton');
    await user.clear(mlField);
    await user.type(mlField, '3');

    await user.click(screen.getByRole('button', { name: t('common.save') }));
    await waitFor(() => expect(onSave).toHaveBeenCalledTimes(1));
    expect(onSave.mock.calls[0][0]).toEqual([
      { fertilizer_key: 'f-bloom', ml_per_liter: 3, optional: false },
    ]);
  });
});
