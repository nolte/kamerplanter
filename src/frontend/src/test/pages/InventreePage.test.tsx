import { screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { http, HttpResponse } from 'msw';
import i18n from 'i18next';
import InventreePage from '@/pages/inventree/InventreePage';
import { renderWithProviders } from '../helpers';
import { server } from '../mocks/server';

const T = '/api/v1/t/:tenant';

function field(scope: HTMLElement, name: string): HTMLInputElement {
  const input = within(scope).getByTestId(`form-field-${name}`).querySelector('input');
  if (!input) throw new Error(`input for ${name} not found`);
  return input as HTMLInputElement;
}

const EQUIPMENT = {
  key: 'eq1',
  name: 'Bluelab pH Pen',
  equipment_type: 'sensor',
  status: 'active',
  inventree_part_id: 1247,
};

function mockEquipment(items: unknown[]) {
  server.use(http.get(`${T}/equipment`, () => HttpResponse.json(items)));
}

function mockConnections(items: unknown[]) {
  server.use(http.get(`${T}/inventree/connections`, () => HttpResponse.json(items)));
}

describe('InventreePage', () => {
  beforeEach(() => {
    i18n.changeLanguage('de');
    mockEquipment([]);
    mockConnections([]);
  });

  it('renders the title, intro and create button', async () => {
    renderWithProviders(<InventreePage />);
    await waitFor(() =>
      expect(screen.getByTestId('create-equipment-button')).toBeInTheDocument(),
    );
    expect(screen.getByTestId('page-title')).toHaveTextContent('Betriebsmittel');
    expect(screen.getAllByText(/InvenTree/).length).toBeGreaterThan(0);
  });

  it('shows the "no connection" banner when none is configured', async () => {
    renderWithProviders(<InventreePage />);
    await waitFor(() =>
      expect(screen.getByTestId('inventree-connection-status')).toHaveTextContent(
        /Keine InvenTree-Verbindung/,
      ),
    );
  });

  it('shows an active-connection banner when one exists', async () => {
    mockConnections([{ key: 'c1', name: 'Haupt-Inventar', is_active: true, last_health_check_ok: true }]);
    renderWithProviders(<InventreePage />);
    await waitFor(() =>
      expect(screen.getByTestId('inventree-connection-status')).toHaveTextContent(
        /Haupt-Inventar/,
      ),
    );
  });

  it('shows the empty state when there is no equipment', async () => {
    renderWithProviders(<InventreePage />);
    await waitFor(() =>
      expect(screen.getByText(/Noch kein Betriebsmittel angelegt/)).toBeInTheDocument(),
    );
  });

  it('lists equipment rows', async () => {
    mockEquipment([EQUIPMENT]);
    renderWithProviders(<InventreePage />);
    await waitFor(() => expect(screen.getByText('Bluelab pH Pen')).toBeInTheDocument());
    expect(screen.getByText('#1247')).toBeInTheDocument();
  });

  it('creates equipment through the dialog', async () => {
    const user = userEvent.setup();
    const created = vi.fn();
    server.use(
      http.post(`${T}/equipment`, async ({ request }) => {
        created(await request.json());
        return HttpResponse.json({ ...EQUIPMENT, key: 'new1' }, { status: 201 });
      }),
    );
    renderWithProviders(<InventreePage />);
    await user.click(await screen.findByTestId('create-equipment-button'));
    const dialog = await screen.findByRole('dialog');

    await user.type(field(dialog, 'name'), 'Umwälzpumpe');
    const typeField = within(dialog).getByTestId('form-field-equipment_type');
    await user.click(within(typeField).getByRole('combobox'));
    await user.click(await screen.findByRole('option', { name: /Pumpe/ }));
    await user.click(within(dialog).getByTestId('form-submit-button'));

    await waitFor(() => expect(created).toHaveBeenCalled());
    expect(created.mock.calls[0][0]).toMatchObject({
      name: 'Umwälzpumpe',
      equipment_type: 'pump',
    });
  });

  it('edits an existing equipment item through the dialog', async () => {
    const user = userEvent.setup();
    const updated = vi.fn();
    mockEquipment([EQUIPMENT]);
    server.use(
      http.put(`${T}/equipment/:key`, async ({ request }) => {
        updated(await request.json());
        return HttpResponse.json({ ...EQUIPMENT, status: 'maintenance' });
      }),
    );
    renderWithProviders(<InventreePage />);
    await waitFor(() => expect(screen.getByText('Bluelab pH Pen')).toBeInTheDocument());

    await user.click(screen.getByTestId('edit-equipment-eq1'));
    const dialog = await screen.findByRole('dialog');
    // The name is pre-filled from the existing item (edit mode).
    expect(field(dialog, 'name')).toHaveValue('Bluelab pH Pen');

    const statusField = within(dialog).getByTestId('form-field-status');
    await user.click(within(statusField).getByRole('combobox'));
    await user.click(await screen.findByRole('option', { name: /In Wartung/ }));
    await user.click(within(dialog).getByTestId('form-submit-button'));

    await waitFor(() => expect(updated).toHaveBeenCalled());
    expect(updated.mock.calls[0][0]).toMatchObject({ status: 'maintenance' });
  });

  it('deletes equipment after confirmation', async () => {
    const user = userEvent.setup();
    const deleted = vi.fn();
    mockEquipment([EQUIPMENT]);
    server.use(
      http.delete(`${T}/equipment/:key`, () => {
        deleted();
        return new HttpResponse(null, { status: 204 });
      }),
    );
    renderWithProviders(<InventreePage />);
    await waitFor(() => expect(screen.getByText('Bluelab pH Pen')).toBeInTheDocument());

    await user.click(screen.getByTestId('delete-equipment-eq1'));
    const dialog = await screen.findByTestId('confirm-dialog');
    await user.click(within(dialog).getByTestId('confirm-dialog-confirm'));

    await waitFor(() => expect(deleted).toHaveBeenCalled());
  });
});
