import { useState } from 'react';
import { screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, beforeEach } from 'vitest';
import i18n from 'i18next';
import SiteCreateDialog from '@/pages/standorte/SiteCreateDialog';
import SpeciesCreateDialog from '@/pages/stammdaten/SpeciesCreateDialog';
import { useExpertiseLevel } from '@/hooks/useExpertiseLevel';
import { renderWithProviders, createStoreWithExpertise } from '../helpers';

// #1900: "show all fields" is one global flag read by every expertise-gated
// form. A dialog that set it must hand it back however it closes -- including
// a SUCCESSFUL create, which closes through the parent (`onCreated` ->
// `setOpen(false)`) and never touches the dialog's own cancel handler.

function ExpertFieldProbe() {
  const { isFieldVisible } = useExpertiseLevel();
  return <div data-testid="probe">{isFieldVisible('expert') ? 'visible' : 'hidden'}</div>;
}

function SiteHost() {
  const [open, setOpen] = useState(true);
  return (
    <>
      <SiteCreateDialog open={open} onClose={() => setOpen(false)} onCreated={() => setOpen(false)} />
      <button type="button" data-testid="reopen" onClick={() => setOpen(true)}>
        reopen
      </button>
      <ExpertFieldProbe />
    </>
  );
}

function SpeciesHost() {
  const [open, setOpen] = useState(true);
  return (
    <>
      <SpeciesCreateDialog open={open} onClose={() => setOpen(false)} onCreated={() => setOpen(false)} />
      <ExpertFieldProbe />
    </>
  );
}

describe('show-all-fields override is scoped to the dialog that set it (#1900)', () => {
  beforeEach(() => {
    i18n.changeLanguage('de');
  });

  it('is reset after a successful site create', async () => {
    const user = userEvent.setup();
    const store = createStoreWithExpertise('beginner');
    renderWithProviders(<SiteHost />, { store });

    await user.click(await screen.findByTestId('show-all-fields-toggle'));
    expect(store.getState().ui.showAllFieldsOverride).toBe(true);
    expect(screen.getByTestId('probe').textContent).toBe('visible');

    await user.type(within(screen.getByTestId('form-field-name')).getByRole('textbox'), 'North Field');
    await user.click(screen.getByTestId('form-submit-button'));

    await waitFor(() => {
      expect(screen.queryByTestId('site-create-dialog')).toBeNull();
    });
    expect(store.getState().ui.showAllFieldsOverride).toBe(false);
    expect(screen.getByTestId('probe').textContent).toBe('hidden');
  });

  it('does not reopen the dialog already expanded', async () => {
    const user = userEvent.setup();
    const store = createStoreWithExpertise('beginner');
    renderWithProviders(<SiteHost />, { store });

    await user.click(await screen.findByTestId('show-all-fields-toggle'));
    await user.type(within(screen.getByTestId('form-field-name')).getByRole('textbox'), 'North Field');
    await user.click(screen.getByTestId('form-submit-button'));
    await waitFor(() => {
      expect(screen.queryByTestId('site-create-dialog')).toBeNull();
    });

    await user.click(screen.getByTestId('reopen'));
    const toggle = await screen.findByTestId('show-all-fields-toggle');
    expect(toggle.getAttribute('aria-expanded')).toBe('false');
    expect(screen.queryByTestId('form-field-timezone')).toBeNull();
  });

  it('is reset when the dialog is closed by the parent without a cancel', async () => {
    const user = userEvent.setup();
    const store = createStoreWithExpertise('beginner');
    renderWithProviders(<SpeciesHost />, { store });

    await user.click(await screen.findByTestId('show-all-fields-toggle'));
    expect(store.getState().ui.showAllFieldsOverride).toBe(true);

    await user.keyboard('{Escape}');
    await waitFor(() => {
      expect(screen.queryByTestId('species-create-dialog')).toBeNull();
    });
    expect(store.getState().ui.showAllFieldsOverride).toBe(false);
  });
});
