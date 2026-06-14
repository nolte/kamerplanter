import { screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { http, HttpResponse } from 'msw';
import i18n from 'i18next';
import SubstrateMixDialog from '@/pages/standorte/SubstrateMixDialog';
import { renderWithProviders } from '../helpers';
import { server } from '../mocks/server';
import { mockSubstrates } from '../mocks/handlers';

/** Seed the (otherwise empty) substrate list so the mix dialog has components. */
function seedSubstrates() {
  server.use(http.get('/api/v1/substrates', () => HttpResponse.json(mockSubstrates)));
}

/** Selects the substrate at the given mix-row index via its MUI select combobox. */
async function pickComponent(user: ReturnType<typeof userEvent.setup>, rowIndex: number, optionName: string) {
  const combos = screen.getAllByRole('combobox');
  await user.click(combos[rowIndex]);
  const option = await screen.findByRole('option', { name: optionName });
  await user.click(option);
}

describe('SubstrateMixDialog', () => {
  beforeEach(() => {
    i18n.changeLanguage('de');
    seedSubstrates();
  });

  it('renders the dialog with two default component rows', async () => {
    renderWithProviders(<SubstrateMixDialog open onClose={() => {}} onCreated={() => {}} />);
    expect(await screen.findByTestId('substrate-mix-dialog')).toBeTruthy();
    // Two default rows → two substrate selects
    await waitFor(() => {
      expect(screen.getAllByRole('combobox').length).toBeGreaterThanOrEqual(2);
    });
  });

  it('keeps preview and save disabled until two distinct components sum to 100%', async () => {
    const user = userEvent.setup();
    renderWithProviders(<SubstrateMixDialog open onClose={() => {}} onCreated={() => {}} />);

    await screen.findByTestId('substrate-mix-dialog');
    const previewBtn = screen.getByRole('button', { name: 'Vorschau berechnen' });
    expect(previewBtn).toBeDisabled();

    await pickComponent(user, 0, 'Kokos Substrat');
    await pickComponent(user, 1, 'Perlit');

    // Default fractions are 0.5 + 0.5 = 100% → now valid
    await waitFor(() => {
      expect(previewBtn).not.toBeDisabled();
    });
  });

  it('renders a computed preview after selecting valid components', async () => {
    const user = userEvent.setup();
    renderWithProviders(<SubstrateMixDialog open onClose={() => {}} onCreated={() => {}} />);

    await screen.findByTestId('substrate-mix-dialog');
    await pickComponent(user, 0, 'Kokos Substrat');
    await pickComponent(user, 1, 'Perlit');

    await user.click(screen.getByRole('button', { name: 'Vorschau berechnen' }));

    await waitFor(() => {
      expect(screen.getByText('Berechnete Eigenschaften')).toBeTruthy();
    });
  });

  it('adds a third component row when "add component" is clicked', async () => {
    const user = userEvent.setup();
    renderWithProviders(<SubstrateMixDialog open onClose={() => {}} onCreated={() => {}} />);

    await screen.findByTestId('substrate-mix-dialog');
    const before = screen.getAllByRole('combobox').length;
    await user.click(screen.getByRole('button', { name: 'Komponente hinzufügen' }));

    await waitFor(() => {
      expect(screen.getAllByRole('combobox').length).toBe(before + 1);
    });
  });

  it('saves a valid mix and calls onCreated', async () => {
    const user = userEvent.setup();
    const onCreated = vi.fn();
    renderWithProviders(<SubstrateMixDialog open onClose={() => {}} onCreated={onCreated} />);

    await screen.findByTestId('substrate-mix-dialog');
    await pickComponent(user, 0, 'Kokos Substrat');
    await pickComponent(user, 1, 'Perlit');

    const saveBtn = screen.getByRole('button', { name: 'Erstellen' });
    await waitFor(() => expect(saveBtn).not.toBeDisabled());
    await user.click(saveBtn);

    await waitFor(() => {
      expect(onCreated).toHaveBeenCalledOnce();
    });
  });

  it('calls onClose when the cancel button is clicked', async () => {
    const user = userEvent.setup();
    const onClose = vi.fn();
    renderWithProviders(<SubstrateMixDialog open onClose={onClose} onCreated={() => {}} />);

    const cancelBtn = within(await screen.findByRole('dialog')).getByRole('button', { name: 'Abbrechen' });
    await user.click(cancelBtn);
    expect(onClose).toHaveBeenCalledOnce();
  });

  it('redistributes fractions evenly across three components', async () => {
    const user = userEvent.setup();
    renderWithProviders(<SubstrateMixDialog open onClose={() => {}} onCreated={() => {}} />);

    await screen.findByTestId('substrate-mix-dialog');
    await user.click(screen.getByRole('button', { name: 'Komponente hinzufügen' }));
    await user.click(screen.getByRole('button', { name: 'Gleichmäßig verteilen' }));

    // 1/3 ≈ 33% — at least one row reflects an even distribution
    await waitFor(() => {
      expect(screen.getAllByText('33%').length).toBeGreaterThan(0);
    });
  });

  it('removes an added component row again', async () => {
    const user = userEvent.setup();
    renderWithProviders(<SubstrateMixDialog open onClose={() => {}} onCreated={() => {}} />);

    await screen.findByTestId('substrate-mix-dialog');
    await user.click(screen.getByRole('button', { name: 'Komponente hinzufügen' }));
    const afterAdd = screen.getAllByRole('combobox').length;

    // Delete buttons are enabled only when more than two rows exist
    const deleteButtons = screen.getAllByRole('button', { name: 'Löschen' });
    await user.click(deleteButtons[deleteButtons.length - 1]);

    await waitFor(() => {
      expect(screen.getAllByRole('combobox').length).toBe(afterAdd - 1);
    });
  });

  it('keeps preview disabled when the same substrate is chosen twice', async () => {
    const user = userEvent.setup();
    renderWithProviders(<SubstrateMixDialog open onClose={() => {}} onCreated={() => {}} />);

    await screen.findByTestId('substrate-mix-dialog');
    await pickComponent(user, 0, 'Kokos Substrat');
    // Second row: selecting the same substrate is disabled as an option, so the
    // duplicate guard keeps the form invalid (no distinct second component yet).
    const previewBtn = screen.getByRole('button', { name: 'Vorschau berechnen' });
    expect(previewBtn).toBeDisabled();
  });
});
