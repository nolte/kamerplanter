import { screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { http, HttpResponse } from 'msw';
import i18n from 'i18next';
import type { ReactElement } from 'react';
import SiteCreateDialog from '@/pages/standorte/SiteCreateDialog';
import PlantInstanceCreateDialog from '@/pages/pflanzen/PlantInstanceCreateDialog';
import FertilizerCreateDialog from '@/pages/duengung/FertilizerCreateDialog';
import { renderWithProviders, createStoreWithExpertise } from '../helpers';
import { server } from '../mocks/server';

/**
 * #3019 (UI-NFR-008) — three representative create dialogs migrated to
 * `FormDialog`: input typed into them is not thrown away by Escape, a
 * backdrop click or the cancel button without a confirmation.
 */

interface Case {
  name: string;
  testId: string;
  field: string;
  render: (onClose: () => void) => ReactElement;
}

const CASES: Case[] = [
  {
    name: 'SiteCreateDialog',
    testId: 'site-create-dialog',
    field: 'name',
    render: (onClose) => <SiteCreateDialog open onClose={onClose} onCreated={() => {}} />,
  },
  {
    name: 'PlantInstanceCreateDialog',
    testId: 'plant-instance-create-dialog',
    field: 'instance_id',
    render: (onClose) => <PlantInstanceCreateDialog open onClose={onClose} onCreated={() => {}} />,
  },
  {
    name: 'FertilizerCreateDialog',
    testId: 'fertilizer-create-dialog',
    field: 'product_name',
    render: (onClose) => <FertilizerCreateDialog open onClose={onClose} onCreated={() => {}} />,
  },
];

async function typeInto(field: string, text: string) {
  const user = userEvent.setup();
  const input = within(await screen.findByTestId(`form-field-${field}`)).getByRole('textbox');
  await user.type(input, text);
  return { user, input: input as HTMLInputElement };
}

describe.each(CASES)('$name — dirty close (#3019)', ({ testId, field, render }) => {
  beforeEach(() => {
    i18n.changeLanguage('de');
  });

  it('asks before Escape discards typed input, and keeps it on "cancel"', async () => {
    const onClose = vi.fn();
    renderWithProviders(render(onClose), { store: createStoreWithExpertise('expert') });
    await screen.findByTestId(testId);
    const { user, input } = await typeInto(field, 'XYZ');

    await user.keyboard('{Escape}');

    const prompt = await screen.findByTestId('confirm-dialog');
    expect(within(prompt).getByText(i18n.t('common.discardChangesTitle'))).toBeInTheDocument();
    expect(onClose).not.toHaveBeenCalled();

    await user.click(within(prompt).getByTestId('confirm-dialog-cancel'));
    await waitFor(() => expect(screen.queryByTestId('confirm-dialog')).not.toBeInTheDocument());
    expect(onClose).not.toHaveBeenCalled();
    expect(input.value).toContain('XYZ');
  });

  it('closes after the user confirms the discard from the cancel button', async () => {
    const onClose = vi.fn();
    renderWithProviders(render(onClose), { store: createStoreWithExpertise('expert') });
    await screen.findByTestId(testId);
    const { user } = await typeInto(field, 'XYZ');

    await user.click(screen.getByTestId('form-cancel-button'));
    expect(onClose).not.toHaveBeenCalled();

    await user.click(await screen.findByTestId('confirm-dialog-confirm'));
    expect(onClose).toHaveBeenCalledOnce();
  });
});

describe('SiteCreateDialog — 422 field mapping (#3019)', () => {
  beforeEach(() => {
    i18n.changeLanguage('de');
  });

  it('marks the field a 422 violation names, in German', async () => {
    const reason = 'String should have at most 200 characters';
    const envelope = {
      error_id: 'e',
      error_code: 'VALIDATION_ERROR',
      message: 'Request validation failed',
      details: [{ field: 'body.name', reason, code: 'string_too_long' }],
      timestamp: '',
      path: '',
      method: 'POST',
    };
    server.use(
      http.post('/api/v1/sites', () => HttpResponse.json(envelope, { status: 422 })),
      http.post('/api/v1/t/:tenant/sites', () => HttpResponse.json(envelope, { status: 422 })),
    );
    const onCreated = vi.fn();
    renderWithProviders(<SiteCreateDialog open onClose={() => {}} onCreated={onCreated} />, {
      store: createStoreWithExpertise('expert'),
    });
    const { user } = await typeInto('name', 'North Field');

    await user.click(screen.getByTestId('form-submit-button'));

    const nameField = screen.getByTestId('form-field-name');
    expect(await within(nameField).findByText(i18n.t('validation.invalid'))).toBeInTheDocument();
    expect(screen.queryByText(reason)).not.toBeInTheDocument();
    expect(onCreated).not.toHaveBeenCalled();
  });
});
