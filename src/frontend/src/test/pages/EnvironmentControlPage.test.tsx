import { screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { http, HttpResponse } from 'msw';
import i18n from 'i18next';
import EnvironmentControlPage from '@/pages/environment/EnvironmentControlPage';
import { renderWithProviders } from '../helpers';
import { server } from '../mocks/server';

const T = '/api/v1/t/:tenant';

const ACTUATOR = {
  key: 'act1',
  tenant_key: 't1',
  location_key: 'loc1',
  name: 'Hauptlicht Zelt 1',
  actuator_type: 'light',
  protocol: 'home_assistant',
  ha_entity_id: 'light.growzelt_1',
  mqtt_command_topic: null,
  mqtt_state_topic: null,
  capabilities: ['on_off', 'dimmable'],
  min_value: 0,
  max_value: 100,
  unit: '%',
  current_state: 'off',
  current_value: null,
  last_state_change: null,
  is_online: true,
  last_seen: null,
  power_watts: 480,
  fail_safe_state: 'last',
  fail_safe_value: null,
  conflict_group: null,
  installed_on: null,
  notes: null,
};

function mockActuators(actuators: unknown[]) {
  server.use(http.get(`${T}/actuators`, () => HttpResponse.json(actuators)));
}

function field(scope: HTMLElement, name: string): HTMLInputElement {
  const input = within(scope).getByTestId(`form-field-${name}`).querySelector('input');
  if (!input) throw new Error(`input for ${name} not found`);
  return input as HTMLInputElement;
}

describe('EnvironmentControlPage', () => {
  beforeEach(() => {
    i18n.changeLanguage('de');
    mockActuators([]);
  });

  it('renders the title, intro and create button', async () => {
    renderWithProviders(<EnvironmentControlPage />);
    await waitFor(() =>
      expect(screen.getByTestId('create-actuator-button')).toBeInTheDocument(),
    );
    expect(screen.getByTestId('page-title')).toHaveTextContent('Umgebungssteuerung');
    expect(screen.getByText(/Aktoren/)).toBeInTheDocument();
  });

  it('shows the empty state with no actuators', async () => {
    renderWithProviders(<EnvironmentControlPage />);
    await waitFor(() =>
      expect(screen.getByText(/Noch kein Aktor angelegt/)).toBeInTheDocument(),
    );
    // The emergency-stop button is disabled while there are no actuators.
    expect(screen.getByTestId('emergency-stop-button')).toBeDisabled();
  });

  it('lists actuators with type, protocol and online chips', async () => {
    mockActuators([ACTUATOR]);
    renderWithProviders(<EnvironmentControlPage />);
    await waitFor(() =>
      expect(screen.getByTestId('actuator-card-act1')).toBeInTheDocument(),
    );
    const card = screen.getByTestId('actuator-card-act1');
    expect(within(card).getByText('Hauptlicht Zelt 1')).toBeInTheDocument();
    expect(within(card).getByText('Licht')).toBeInTheDocument();
    expect(within(card).getByText('Home Assistant')).toBeInTheDocument();
    expect(within(card).getByText('Online')).toBeInTheDocument();
    expect(within(card).getByText(/480 W/)).toBeInTheDocument();
  });

  it('sends a turn-on command', async () => {
    const user = userEvent.setup();
    mockActuators([ACTUATOR]);
    const commanded = vi.fn();
    server.use(
      http.post(`${T}/actuators/:key/command`, async ({ request }) => {
        commanded(await request.json());
        return HttpResponse.json({ key: 'ev1', success: true, new_state: 'on' });
      }),
    );
    renderWithProviders(<EnvironmentControlPage />);
    await waitFor(() => expect(screen.getByTestId('turn-on-act1')).toBeInTheDocument());
    await user.click(screen.getByTestId('turn-on-act1'));
    await waitFor(() => expect(commanded).toHaveBeenCalled());
    expect(commanded.mock.calls[0][0]).toMatchObject({ command: 'turn_on' });
  });

  it('runs an emergency stop after confirmation', async () => {
    const user = userEvent.setup();
    mockActuators([ACTUATOR]);
    const stopped = vi.fn();
    server.use(
      http.post(`${T}/emergency-stop`, async ({ request }) => {
        stopped(await request.json());
        return HttpResponse.json({ scenario: 'fire_alarm', stopped: ['act1'], forced_on: [] });
      }),
    );
    renderWithProviders(<EnvironmentControlPage />);
    await waitFor(() =>
      expect(screen.getByTestId('emergency-stop-button')).toBeEnabled(),
    );
    await user.click(screen.getByTestId('emergency-stop-button'));
    await user.click(await screen.findByTestId('confirm-dialog-confirm'));
    await waitFor(() => expect(stopped).toHaveBeenCalled());
    expect(stopped.mock.calls[0][0]).toMatchObject({ scenario: 'fire_alarm' });
  });

  it('renders an offline actuator and sends a turn-off command', async () => {
    const user = userEvent.setup();
    mockActuators([
      { ...ACTUATOR, key: 'act2', name: 'Abluft', is_online: false, current_state: 'on', power_watts: null },
    ]);
    const commanded = vi.fn();
    server.use(
      http.post(`${T}/actuators/:key/command`, async ({ request }) => {
        commanded(await request.json());
        return HttpResponse.json({ key: 'ev2', success: true, new_state: 'off' });
      }),
    );
    renderWithProviders(<EnvironmentControlPage />);
    await waitFor(() => expect(screen.getByTestId('actuator-card-act2')).toBeInTheDocument());
    const card = screen.getByTestId('actuator-card-act2');
    expect(within(card).getByText('Offline')).toBeInTheDocument();
    await user.click(screen.getByTestId('turn-off-act2'));
    await waitFor(() => expect(commanded).toHaveBeenCalled());
    expect(commanded.mock.calls[0][0]).toMatchObject({ command: 'turn_off' });
  });

  it('shows the MQTT topic field for the mqtt protocol', async () => {
    const user = userEvent.setup();
    mockActuators([]);
    server.use(http.get(`${T}/sites`, () => HttpResponse.json([{ key: 'site1', name: 'Growroom' }])));
    renderWithProviders(<EnvironmentControlPage />);
    await user.click(await screen.findByTestId('create-actuator-button'));
    const dialog = await screen.findByRole('dialog');

    const protocolSelect = within(dialog).getByTestId('form-field-protocol');
    await user.click(within(protocolSelect).getByRole('combobox'));
    await user.click(await screen.findByRole('option', { name: 'MQTT' }));
    await waitFor(() =>
      expect(within(dialog).getByTestId('form-field-mqtt_command_topic')).toBeInTheDocument(),
    );
    // The HA entity field is hidden for non-HA protocols.
    expect(within(dialog).queryByTestId('form-field-ha_entity_id')).toBeNull();
  });

  it('creates an actuator through the dialog', async () => {
    const user = userEvent.setup();
    mockActuators([]);
    const created = vi.fn();
    server.use(
      http.get(`${T}/sites`, () => HttpResponse.json([{ key: 'site1', name: 'Growroom' }])),
      http.get(`${T}/locations`, () =>
        HttpResponse.json([{ key: 'loc1', name: 'Zelt 1' }]),
      ),
      http.post(`${T}/locations/:key/actuators`, async ({ request }) => {
        created(await request.json());
        return HttpResponse.json({ ...ACTUATOR, key: 'new1' }, { status: 201 });
      }),
    );
    renderWithProviders(<EnvironmentControlPage />);
    await waitFor(() =>
      expect(screen.getByTestId('create-actuator-button')).toBeInTheDocument(),
    );
    await user.click(screen.getByTestId('create-actuator-button'));
    const dialog = await screen.findByRole('dialog');

    // Pick site -> location.
    const siteSelect = within(dialog).getByTestId('form-field-site_key');
    await user.click(within(siteSelect).getByRole('combobox'));
    await user.click(await screen.findByRole('option', { name: 'Growroom' }));
    await waitFor(() =>
      expect(within(dialog).getByTestId('form-field-location_key')).toBeInTheDocument(),
    );
    const locSelect = within(dialog).getByTestId('form-field-location_key');
    await user.click(within(locSelect).getByRole('combobox'));
    await user.click(await screen.findByRole('option', { name: 'Zelt 1' }));

    await user.type(field(dialog, 'name'), 'Neues Licht');
    await user.type(field(dialog, 'ha_entity_id'), 'light.new');

    await user.click(within(dialog).getByTestId('form-submit-button'));
    await waitFor(() => expect(created).toHaveBeenCalled());
    expect(created.mock.calls[0][0]).toMatchObject({
      name: 'Neues Licht',
      actuator_type: 'light',
      protocol: 'home_assistant',
    });
  });
});
