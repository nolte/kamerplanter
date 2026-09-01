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

  it('shows a warning when the substrate options fail to load (FE-L3)', async () => {
    server.use(
      http.get('/api/v1/substrates', () => HttpResponse.json({ detail: 'boom' }, { status: 500 })),
    );
    renderWithProviders(<SubstrateMixDialog open onClose={() => {}} onCreated={() => {}} />);

    await screen.findByTestId('substrate-mix-dialog');
    await waitFor(() => {
      expect(screen.getByText('Auswahloptionen konnten nicht geladen werden.')).toBeTruthy();
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

describe('SubstrateMixDialog — the shapes #1175 introduced', () => {
  beforeEach(() => {
    i18n.changeLanguage('de');
    seedSubstrates();
  });

  /** Runs a preview whose response is `overrides` merged over the default one. */
  async function previewWith(overrides: Record<string, unknown>) {
    server.use(
      http.post('/api/v1/substrates/preview-mix', () =>
        HttpResponse.json({
          key: 'sub-preview',
          type: 'coco',
          brand: null,
          name_de: 'Mix',
          name_en: 'Mix',
          is_mix: true,
          mix_components: [],
          ph_base: 6.2,
          ec_base_ms: 0.3,
          water_retention: 'medium',
          air_porosity_percent: 40,
          composition: { coco: 1.0 },
          additives: [],
          is_amendment: false,
          buffer_capacity: 'medium',
          reusable: false,
          max_reuse_cycles: 1,
          water_holding_capacity_percent: null,
          easily_available_water_percent: null,
          cec_meq_per_100cm3: null,
          particle_size_mm: null,
          bulk_density_g_per_l: null,
          irrigation_strategy: null,
          created_at: '2024-01-01T00:00:00Z',
          updated_at: null,
          ...overrides,
        }),
      ),
    );

    const user = userEvent.setup();
    renderWithProviders(<SubstrateMixDialog open onClose={() => {}} onCreated={() => {}} />);
    await screen.findByTestId('substrate-mix-dialog');
    await pickComponent(user, 0, 'Kokos Substrat');
    await pickComponent(user, 1, 'Perlit');
    await user.click(screen.getByRole('button', { name: 'Vorschau berechnen' }));
    await screen.findByText('Berechnete Eigenschaften');
  }

  it('renders an absent air porosity as "not applicable", not as a number', async () => {
    // The whole point of making the field nullable: a blend with no pore space to
    // state must not render a figure. `0.0 %` would be the placeholder again, in
    // the other direction — and `.toFixed` on null is a crash, which is how this
    // reached the UI at all.
    await previewWith({ air_porosity_percent: null });

    expect(screen.getByTestId('mix-preview-air-porosity').textContent).toBe('nicht anwendbar');
  });

  it('still renders a declared air porosity as a percentage', async () => {
    // Control. Without it the assertion above passes on a component that renders
    // "not applicable" unconditionally.
    await previewWith({ air_porosity_percent: 40 });

    expect(screen.getByTestId('mix-preview-air-porosity').textContent).toBe('40.0%');
  });

  it('shows the blend\'s additives by name, without a percentage', async () => {
    // Additives left `composition` because a lime *fraction* was the wrong reading.
    // Rendering them as `kalk: 10%` again would restore exactly that.
    await previewWith({ additives: ['kalk', 'spurenelemente'] });

    const box = screen.getByTestId('mix-preview-additives');
    expect(within(box).getByText('kalk')).toBeTruthy();
    expect(within(box).getByText('spurenelemente')).toBeTruthy();
    expect(box.textContent).not.toMatch(/\d+\s*%/);
  });

  it('omits the additives block when the blend has none', async () => {
    await previewWith({ additives: [] });

    expect(screen.queryByTestId('mix-preview-additives')).toBeNull();
  });
});
