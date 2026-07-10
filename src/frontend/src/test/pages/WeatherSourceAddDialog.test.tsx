import { describe, it, expect, beforeEach, afterAll, vi } from 'vitest';
import { screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { http, HttpResponse } from 'msw';
import i18n from 'i18next';
import WeatherSourceAddDialog from '@/pages/standorte/WeatherSourceAddDialog';
import { renderWithProviders } from '../helpers';
import { server } from '../mocks/server';
import type {
  AvailableSourcesResponse,
  WeatherSourceEntryRequest,
} from '@/api/types';

/**
 * P7e — WeatherSourceAddDialog (REQ-046 §4.1). The two-way "add source" dialog,
 * rendered as a unit. Its `available` payload is passed as a prop; the HA
 * entity-discovery endpoints are doubled at the process boundary via msw.
 * Asserts observable output (rendered branch, hints, disabled confirm) and the
 * onSave / onClose callbacks.
 */

const AVAILABLE: AvailableSourcesResponse = {
  ha_token_set: true,
  sources: [
    { source_name: 'open-meteo', kind: 'public', requires_api_key: false },
    { source_name: 'dwd', kind: 'public', requires_api_key: false },
    { source_name: 'openweathermap', kind: 'public', requires_api_key: true },
    { source_name: 'ha_weather', kind: 'home_assistant', requires_api_key: false },
  ],
};

const WEATHER_ENTITIES = [
  { entity_id: 'weather.home', friendly_name: 'Home' },
  { entity_id: 'weather.roof', friendly_name: 'Roof' },
];
const SENSOR_ENTITIES = [
  { entity_id: 'sensor.outdoor_temp', friendly_name: 'Outdoor temperature' },
  { entity_id: 'sensor.rain', friendly_name: 'Rain' },
];

function registerHaHandlers(opts: { weather?: unknown[]; sensors?: unknown[]; fail?: boolean } = {}) {
  const { weather = WEATHER_ENTITIES, sensors = SENSOR_ENTITIES, fail } = opts;
  server.use(
    http.get('/api/v1/t/:tenant/ha/weather-entities', () =>
      fail ? HttpResponse.json({ message: 'x' }, { status: 500 }) : HttpResponse.json(weather),
    ),
    http.get('/api/v1/t/:tenant/ha/sensor-entities', () =>
      fail ? HttpResponse.json({ message: 'x' }, { status: 500 }) : HttpResponse.json(sensors),
    ),
  );
}

type MountProps = {
  open?: boolean;
  available?: AvailableSourcesResponse | null;
  existing?: WeatherSourceEntryRequest;
  existingApiKeySet?: boolean;
  onSave?: (entry: WeatherSourceEntryRequest) => void;
  onClose?: () => void;
};

function mount(props: MountProps = {}) {
  const onSave = (props.onSave ?? vi.fn()) as unknown as ReturnType<typeof vi.fn>;
  const onClose = (props.onClose ?? vi.fn()) as unknown as ReturnType<typeof vi.fn>;
  const utils = renderWithProviders(
    <WeatherSourceAddDialog
      open={props.open ?? true}
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      onClose={onClose as any}
      available={props.available ?? AVAILABLE}
      existing={props.existing}
      existingApiKeySet={props.existingApiKeySet}
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      onSave={onSave as any}
    />,
  );
  return { ...utils, onSave, onClose };
}

describe('WeatherSourceAddDialog', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    i18n.changeLanguage('de');
  });

  afterAll(() => {
    i18n.changeLanguage('en');
  });

  it('renders nothing when closed', () => {
    registerHaHandlers();
    mount({ open: false });
    expect(screen.queryByTestId('weather-source-add-dialog')).not.toBeInTheDocument();
  });

  it('opens on the public branch by default and shows the provider select', async () => {
    registerHaHandlers();
    mount();
    expect(await screen.findByTestId('weather-source-add-dialog')).toBeInTheDocument();
    expect(screen.getByTestId('weather-provider-select')).toBeInTheDocument();
    // Non-key provider: no API-key field.
    expect(screen.queryByTestId('weather-api-key-field')).not.toBeInTheDocument();
    // Confirm is enabled because the default provider is preselected.
    expect(screen.getByTestId('weather-source-add-confirm')).toBeEnabled();
  });

  it('saves a public source entry and closes', async () => {
    const user = userEvent.setup();
    registerHaHandlers();
    const { onSave, onClose } = mount();
    await screen.findByTestId('weather-source-add-dialog');
    await user.click(screen.getByTestId('weather-source-add-confirm'));
    expect(onSave).toHaveBeenCalledTimes(1);
    const entry = onSave.mock.calls[0][0] as WeatherSourceEntryRequest;
    expect(entry.kind).toBe('public');
    expect(entry.source_name).toBe('open-meteo');
    expect(onClose).toHaveBeenCalled();
  });

  it('reveals a masked API-key field with a visibility toggle for key-based providers', async () => {
    const user = userEvent.setup();
    registerHaHandlers();
    const { onSave } = mount();
    await screen.findByTestId('weather-source-add-dialog');
    const select = within(screen.getByTestId('weather-provider-select')).getByRole('combobox');
    await user.click(select);
    await user.click(await screen.findByRole('option', { name: 'OpenWeatherMap' }));

    const keyField = await screen.findByTestId('weather-api-key-field');
    const input = keyField.querySelector('input')!;
    expect(input.type).toBe('password');
    await user.type(input, 'secret-key');
    // Toggle visibility.
    await user.click(screen.getByTestId('weather-api-key-visibility-toggle'));
    expect(keyField.querySelector('input')!.type).toBe('text');

    await user.click(screen.getByTestId('weather-source-add-confirm'));
    const entry = onSave.mock.calls[0][0] as WeatherSourceEntryRequest;
    expect(entry.public_config?.api_key).toBe('secret-key');
  });

  it('disables the HA option with an explanatory hint when no HA token is set', async () => {
    registerHaHandlers();
    mount({ available: { ...AVAILABLE, ha_token_set: false } });
    await screen.findByTestId('weather-source-add-dialog');
    expect(screen.getByTestId('weather-kind-ha')).toBeDisabled();
    expect(screen.getByTestId('ha-token-missing-hint')).toBeInTheDocument();
  });

  it('switches to the Home Assistant weather-entity branch and saves the picked entity', async () => {
    const user = userEvent.setup();
    registerHaHandlers();
    const { onSave } = mount();
    await screen.findByTestId('weather-source-add-dialog');
    await user.click(screen.getByTestId('weather-kind-ha'));
    // Confirm is disabled until an entity is chosen.
    expect(screen.getByTestId('weather-source-add-confirm')).toBeDisabled();
    const autocomplete = await screen.findByTestId('ha-weather-entity-autocomplete');
    const combobox = within(autocomplete.closest('.MuiFormControl-root') as HTMLElement).getByRole('combobox');
    await user.click(combobox);
    await user.click(await screen.findByRole('option', { name: /Home \(weather\.home\)/ }));
    await waitFor(() =>
      expect(screen.getByTestId('weather-source-add-confirm')).toBeEnabled(),
    );
    await user.click(screen.getByTestId('weather-source-add-confirm'));
    const entry = onSave.mock.calls[0][0] as WeatherSourceEntryRequest;
    expect(entry.kind).toBe('home_assistant');
    expect(entry.ha_config?.mode).toBe('weather_entity');
    expect(entry.ha_config?.weather_entity_id).toBe('weather.home');
  });

  it('switches to the HA sensor-mapping branch and saves a mapped field', async () => {
    const user = userEvent.setup();
    registerHaHandlers();
    const { onSave } = mount();
    await screen.findByTestId('weather-source-add-dialog');
    await user.click(screen.getByTestId('weather-kind-ha'));
    await user.click(await screen.findByTestId('ha-mode-sensor-mapping'));
    // All eight per-field pickers are rendered.
    expect(await screen.findByTestId('ha-sensor-temp_min_entity')).toBeInTheDocument();
    expect(screen.getByTestId('ha-sensor-pressure_entity')).toBeInTheDocument();
    // Confirm disabled until at least one field is mapped.
    expect(screen.getByTestId('weather-source-add-confirm')).toBeDisabled();
    const field = screen.getByTestId('ha-sensor-temp_min_entity');
    const combobox = within(field.closest('.MuiFormControl-root') as HTMLElement).getByRole('combobox');
    await user.click(combobox);
    await user.click(await screen.findByRole('option', { name: /Outdoor temperature/ }));
    await waitFor(() =>
      expect(screen.getByTestId('weather-source-add-confirm')).toBeEnabled(),
    );
    await user.click(screen.getByTestId('weather-source-add-confirm'));
    const entry = onSave.mock.calls[0][0] as WeatherSourceEntryRequest;
    expect(entry.ha_config?.mode).toBe('sensor_mapping');
    expect(entry.ha_config?.sensor_mapping?.temp_min_entity).toBe('sensor.outdoor_temp');
  });

  it('shows an empty-state hint when HA exposes no weather entities', async () => {
    const user = userEvent.setup();
    registerHaHandlers({ weather: [], sensors: [] });
    mount();
    await screen.findByTestId('weather-source-add-dialog');
    await user.click(screen.getByTestId('weather-kind-ha'));
    expect(await screen.findByTestId('ha-no-weather-entities-hint')).toBeInTheDocument();
  });

  it('shows an empty-state hint in sensor-mapping mode when HA exposes no sensors', async () => {
    const user = userEvent.setup();
    registerHaHandlers({ weather: [], sensors: [] });
    mount();
    await screen.findByTestId('weather-source-add-dialog');
    await user.click(screen.getByTestId('weather-kind-ha'));
    await user.click(await screen.findByTestId('ha-mode-sensor-mapping'));
    expect(await screen.findByTestId('ha-no-sensor-entities-hint')).toBeInTheDocument();
  });

  it('tolerates an HA entity-discovery failure by rendering empty pickers', async () => {
    const user = userEvent.setup();
    registerHaHandlers({ fail: true });
    mount();
    await screen.findByTestId('weather-source-add-dialog');
    await user.click(screen.getByTestId('weather-kind-ha'));
    expect(await screen.findByTestId('ha-no-weather-entities-hint')).toBeInTheDocument();
  });

  it('renders the edit form with a locked kind switch and a Save label, and saves the existing public source', async () => {
    const user = userEvent.setup();
    registerHaHandlers();
    const existing: WeatherSourceEntryRequest = {
      source_name: 'openweathermap',
      kind: 'public',
      enabled: true,
      public_config: { api_key: null, units_hint: 'metric' },
    };
    const { onSave } = mount({ existing, existingApiKeySet: true });
    await screen.findByTestId('weather-source-add-dialog');
    expect(screen.getByText(i18n.t('pages.weatherSource.editSource'))).toBeInTheDocument();
    // The kind switch is locked while editing.
    expect(screen.getByTestId('weather-kind-public')).toBeDisabled();
    expect(screen.getByTestId('weather-edit-locked-hint')).toBeInTheDocument();
    // Confirm carries the Save label.
    const confirm = screen.getByTestId('weather-source-add-confirm');
    expect(confirm).toHaveTextContent(i18n.t('common.save'));
    // Masked placeholder for an already-stored key.
    const keyInput = screen.getByTestId('weather-api-key-field').querySelector('input')!;
    expect(keyInput.placeholder).toBe('••••');
    await user.click(confirm);
    const entry = onSave.mock.calls[0][0] as WeatherSourceEntryRequest;
    // Empty key means "unchanged" -> passes '' through and preserves units_hint.
    expect(entry.public_config?.api_key).toBe('');
    expect(entry.public_config?.units_hint).toBe('metric');
  });

  it('closes via the cancel button without saving', async () => {
    const user = userEvent.setup();
    registerHaHandlers();
    const { onSave, onClose } = mount();
    await screen.findByTestId('weather-source-add-dialog');
    await user.click(screen.getByRole('button', { name: i18n.t('common.cancel') }));
    expect(onClose).toHaveBeenCalled();
    expect(onSave).not.toHaveBeenCalled();
  });

  it('disables confirm when the provider list is empty (nothing selectable)', async () => {
    registerHaHandlers();
    mount({ available: { ha_token_set: false, sources: [] } });
    await screen.findByTestId('weather-source-add-dialog');
    expect(screen.getByTestId('weather-source-add-confirm')).toBeDisabled();
  });
});
