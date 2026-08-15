import { screen, within, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { http, HttpResponse } from 'msw';
import i18n from 'i18next';
import CultivarCreateDialog from '@/pages/stammdaten/CultivarCreateDialog';
import { renderWithProviders } from '../helpers';
import { server } from '../mocks/server';

beforeEach(() => {
  i18n.changeLanguage('de');
});

describe('CultivarCreateDialog', () => {
  it('renders nothing while closed', () => {
    renderWithProviders(
      <CultivarCreateDialog speciesKey="sp-1" open={false} onClose={() => {}} onCreated={() => {}} />,
    );
    expect(screen.queryByTestId('cultivar-create-dialog')).toBeNull();
  });

  it('renders the identification and characteristics sections when open', () => {
    renderWithProviders(
      <CultivarCreateDialog speciesKey="sp-1" open onClose={() => {}} onCreated={() => {}} />,
    );
    expect(screen.getByTestId('cultivar-create-dialog')).toBeInTheDocument();
    expect(screen.getByText(i18n.t('pages.cultivars.sectionIdentification'))).toBeInTheDocument();
    // sectionCharacteristics shares its label with the traits field, so it is not unique.
    expect(screen.getAllByText(i18n.t('pages.cultivars.sectionCharacteristics')).length).toBeGreaterThan(0);
    expect(screen.getByLabelText(new RegExp(i18n.t('pages.cultivars.name')))).toBeInTheDocument();
  });

  it('invokes onClose from the cancel action', async () => {
    const onClose = vi.fn();
    renderWithProviders(
      <CultivarCreateDialog speciesKey="sp-1" open onClose={onClose} onCreated={() => {}} />,
    );
    await userEvent.click(screen.getByTestId('form-cancel-button'));
    expect(onClose).toHaveBeenCalled();
  });

  it('blocks submission and does not call onCreated when the name is empty', async () => {
    const onCreated = vi.fn();
    renderWithProviders(
      <CultivarCreateDialog speciesKey="sp-1" open onClose={() => {}} onCreated={onCreated} />,
    );
    await userEvent.click(screen.getByTestId('form-submit-button'));
    // zod min(1) rejects — the create callback never fires.
    await waitFor(() => expect(onCreated).not.toHaveBeenCalled());
  });

  it('creates the cultivar and calls onCreated on a valid submit', async () => {
    const onCreated = vi.fn();
    let payload: Record<string, unknown> | null = null;
    server.use(
      http.post('/api/v1/species/sp-1/cultivars', async ({ request }) => {
        payload = (await request.json()) as Record<string, unknown>;
        return HttpResponse.json({ key: 'cv-new', name: payload.name, species_key: 'sp-1' });
      }),
    );
    renderWithProviders(
      <CultivarCreateDialog speciesKey="sp-1" open onClose={() => {}} onCreated={onCreated} />,
    );

    const dialog = screen.getByTestId('cultivar-create-dialog');
    await userEvent.type(
      within(dialog).getByLabelText(new RegExp(i18n.t('pages.cultivars.name'))),
      'Marmande',
    );
    await userEvent.click(screen.getByTestId('form-submit-button'));

    await waitFor(() => expect(onCreated).toHaveBeenCalled());
    // #1114: the body no longer carries the parent species — the URL does, and it
    // is asserted by the handler path this test registers. Kept as an explicit
    // absence check rather than just dropping the key: silently shortening the
    // assertion would leave "does the client still smuggle it in?" unanswered.
    expect(payload).toMatchObject({ name: 'Marmande' });
    expect(payload).not.toHaveProperty('species_key');
  });

  it('keeps the dialog open and reports the error when creation fails', async () => {
    const onCreated = vi.fn();
    server.use(
      http.post('/api/v1/species/sp-1/cultivars', () =>
        HttpResponse.json({ message: 'boom' }, { status: 500 }),
      ),
    );
    renderWithProviders(
      <CultivarCreateDialog speciesKey="sp-1" open onClose={() => {}} onCreated={onCreated} />,
    );

    await userEvent.type(
      within(screen.getByTestId('cultivar-create-dialog')).getByLabelText(
        new RegExp(i18n.t('pages.cultivars.name')),
      ),
      'FehlerSorte',
    );
    await userEvent.click(screen.getByTestId('form-submit-button'));

    await waitFor(() => expect(onCreated).not.toHaveBeenCalled());
    // The submit button re-enables after the failed request settles.
    await waitFor(() => expect(screen.getByTestId('form-submit-button')).not.toBeDisabled());
  });
});
