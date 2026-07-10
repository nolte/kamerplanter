import { screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { http, HttpResponse } from 'msw';
import i18n from 'i18next';
import { renderWithProviders } from '../helpers';
import { server } from '../mocks/server';
import type { PlantInstance, Fertilizer } from '@/api/types';
import WateringLogCreateDialog, {
  type ChannelPreset,
} from '@/pages/giessprotokoll/WateringLogCreateDialog';

const PLANTS_URL = '/api/v1/t/test-tenant/plant-instances';
const FERTILIZERS_URL = '/api/v1/t/test-tenant/fertilizers';
const CREATE_URL = '/api/v1/t/test-tenant/watering-logs';

function makePlant(overrides: Partial<PlantInstance> = {}): PlantInstance {
  return {
    key: 'plant-1',
    instance_id: 'BSL-1',
    species_key: 'sp-1',
    cultivar_key: null,
    site_key: null,
    location_key: null,
    slot_key: null,
    substrate_batch_key: null,
    substrate_key: null,
    plant_name: 'Basil One',
    planted_on: '2024-03-01',
    removed_on: null,
    termination_type: null,
    termination_cause: null,
    current_phase: 'vegetative',
    current_phase_key: null,
    current_phase_started_at: null,
    container_volume_liters: null,
    substrate_type_override: null,
    species: null,
    cultivar: null,
    mother_key: null,
    created_at: '2024-03-01T00:00:00Z',
    updated_at: null,
    ...overrides,
  };
}

function makeFertilizer(overrides: Partial<Fertilizer> = {}): Fertilizer {
  return {
    key: 'fert-1',
    product_name: 'Base A',
    brand: 'Acme',
    fertilizer_type: 'mineral',
    is_organic: false,
    tank_safe: true,
    recommended_application: 'fertigation',
    npk_ratio: [5, 5, 5],
    ec_contribution_per_ml: 0.1,
    ec_contribution_uncertain: false,
    max_dose_ml_per_liter: null,
    mixing_priority: 1,
    ph_effect: 'neutral',
    bioavailability: 'high',
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

interface Seed {
  plants?: PlantInstance[];
  fertilizers?: Fertilizer[];
  plantsError?: boolean;
  createStatus?: number;
  onPost?: (body: Record<string, unknown>) => void;
}

function seed(state: Seed = {}) {
  const {
    plants = [makePlant()],
    fertilizers = [makeFertilizer()],
    plantsError = false,
    createStatus = 201,
    onPost,
  } = state;

  server.use(
    http.get(PLANTS_URL, () =>
      plantsError
        ? HttpResponse.json({ error_id: 'e', error_code: 'X', message: 'boom', details: [] }, { status: 500 })
        : HttpResponse.json(plants),
    ),
    http.get(FERTILIZERS_URL, () => HttpResponse.json(fertilizers)),
    http.post(CREATE_URL, async ({ request }) => {
      const body = (await request.json()) as Record<string, unknown>;
      onPost?.(body);
      return createStatus < 400
        ? HttpResponse.json({ key: 'wl-new', ...body }, { status: createStatus })
        : HttpResponse.json({ error_id: 'e', error_code: 'INTERNAL_ERROR', message: 'boom', details: [] }, { status: createStatus });
    }),
  );
}

function renderDialog(props: {
  open?: boolean;
  onClose?: () => void;
  onCreated?: () => void;
  plantKeys?: string[];
  slotKeys?: string[];
  channelPreset?: ChannelPreset;
  availableFertilizers?: Fertilizer[];
} = {}) {
  const onClose = props.onClose ?? vi.fn();
  const onCreated = props.onCreated ?? vi.fn();
  renderWithProviders(
    <WateringLogCreateDialog
      open={props.open ?? true}
      onClose={onClose}
      onCreated={onCreated}
      plantKeys={props.plantKeys}
      slotKeys={props.slotKeys}
      channelPreset={props.channelPreset}
      availableFertilizers={props.availableFertilizers}
    />,
  );
  return { onClose, onCreated };
}

describe('WateringLogCreateDialog', () => {
  beforeEach(() => {
    i18n.changeLanguage('en');
  });
  afterEach(() => {
    i18n.changeLanguage('en');
  });

  it('does not render dialog content while closed', () => {
    seed();
    renderDialog({ open: false });
    expect(screen.queryByTestId('watering-log-create-dialog')).not.toBeInTheDocument();
  });

  it('creates a log with the default values and a selected plant', async () => {
    let body: Record<string, unknown> | null = null;
    seed({ onPost: (b) => (body = b) });
    const user = userEvent.setup();
    const { onCreated } = renderDialog();

    expect(await screen.findByTestId('watering-log-create-dialog')).toBeInTheDocument();

    // Multi-select the standalone plant through the autocomplete.
    const plantsInput = within(screen.getByTestId('plant-keys-autocomplete')).getByRole('combobox');
    await user.click(plantsInput);
    await user.click(await screen.findByRole('option', { name: /Basil One/ }));

    await user.click(screen.getByTestId('form-submit-button'));

    await waitFor(() => expect(onCreated).toHaveBeenCalled());
    expect(body!.plant_keys).toEqual(['plant-1']);
    expect(body!.application_method).toBe('drench');
    expect(body!.volume_liters).toBe(1);
  });

  it('renders the channel-preset alert and submits preset-derived fields', async () => {
    let body: Record<string, unknown> | null = null;
    const channelPreset: ChannelPreset = {
      channelId: 'chan-1',
      channelLabel: 'Channel 1',
      nutrientPlanKey: 'np-7',
      applicationMethod: 'fertigation',
      targetEcMs: 1.8,
      targetPh: 6.1,
      fertilizers: [{ fertilizer_key: 'fert-1', ml_per_liter: 2 }],
      volumeLiters: 5,
    };
    seed({ onPost: (b) => (body = b) });
    const user = userEvent.setup();
    const { onCreated } = renderDialog({ channelPreset });

    await screen.findByTestId('watering-log-create-dialog');
    // Preset alert shows the channel label plus EC and pH hints.
    expect(
      screen.getByText(
        i18n.t('pages.wateringLogs.channelPresetInfo', { channel: 'Channel 1' }),
        { exact: false },
      ),
    ).toBeInTheDocument();

    await user.click(screen.getByTestId('form-submit-button'));
    await waitFor(() => expect(onCreated).toHaveBeenCalled());

    expect(body!.application_method).toBe('fertigation');
    expect(body!.volume_liters).toBe(5);
    expect(body!.nutrient_plan_key).toBe('np-7');
    expect(body!.channel_id).toBe('chan-1');
    expect(body!.ph_before).toBe(6.1);
    expect(body!.fertilizers_used).toEqual([{ fertilizer_key: 'fert-1', ml_per_liter: 2 }]);
  });

  it('appends a fertilizer row, blocks submit on invalid input, then removes it and submits', async () => {
    let posted = false;
    seed({ onPost: () => (posted = true) });
    const user = userEvent.setup();
    const { onCreated } = renderDialog();

    await screen.findByTestId('watering-log-create-dialog');

    // Append an empty fertilizer line -> zod validation fails on submit.
    await user.click(screen.getByTestId('add-fertilizer-button'));
    await user.click(screen.getByTestId('form-submit-button'));
    // No POST because the fertilizer_key is empty.
    await waitFor(() => expect(posted).toBe(false));
    expect(onCreated).not.toHaveBeenCalled();

    // Remove the invalid row and submit successfully.
    await user.click(screen.getByTestId('remove-fertilizer-0'));
    await user.click(screen.getByTestId('form-submit-button'));
    await waitFor(() => expect(onCreated).toHaveBeenCalled());
    expect(posted).toBe(true);
  });

  it('passes initial plant keys and slot keys, hiding the slot text field', async () => {
    let body: Record<string, unknown> | null = null;
    seed({ onPost: (b) => (body = b) });
    const user = userEvent.setup();
    const { onCreated } = renderDialog({
      plantKeys: ['plant-1'],
      slotKeys: ['slot-a', 'slot-b'],
    });

    await screen.findByTestId('watering-log-create-dialog');
    // The free-text slot field is hidden when slotKeys are provided.
    expect(screen.queryByLabelText(i18n.t('pages.wateringLogs.slotKeys'), { exact: false })).not.toBeInTheDocument();

    await user.click(screen.getByTestId('form-submit-button'));
    await waitFor(() => expect(onCreated).toHaveBeenCalled());
    expect(body!.plant_keys).toEqual(['plant-1']);
    expect(body!.slot_keys).toEqual(['slot-a', 'slot-b']);
  });

  it('surfaces an error and keeps the dialog when creation fails', async () => {
    seed({ createStatus: 500 });
    const user = userEvent.setup();
    const { onCreated } = renderDialog();

    await screen.findByTestId('watering-log-create-dialog');
    await user.click(screen.getByTestId('form-submit-button'));

    expect(await screen.findByText(i18n.t('errors.server'))).toBeInTheDocument();
    expect(onCreated).not.toHaveBeenCalled();
    expect(screen.getByTestId('watering-log-create-dialog')).toBeInTheDocument();
  });

  it('uses pre-loaded fertilizers and tolerates a plant-load failure', async () => {
    let body: Record<string, unknown> | null = null;
    // plantsError -> listPlantInstances rejects -> caught -> empty plant options.
    seed({ plantsError: true, onPost: (b) => (body = b) });
    const user = userEvent.setup();
    const { onCreated } = renderDialog({
      availableFertilizers: [makeFertilizer({ key: 'fert-9', product_name: 'Cal-Mag' })],
    });

    await screen.findByTestId('watering-log-create-dialog');
    // No plant options loaded -> opening the autocomplete shows the no-options text.
    const plantsInput = within(screen.getByTestId('plant-keys-autocomplete')).getByRole('combobox');
    await user.click(plantsInput);

    await user.click(screen.getByTestId('form-submit-button'));
    await waitFor(() => expect(onCreated).toHaveBeenCalled());
    // No plants were selectable -> plant_keys omitted from the payload.
    expect(body!.plant_keys).toBeUndefined();
  });

  it('closes via the cancel action', async () => {
    seed();
    const user = userEvent.setup();
    const { onClose } = renderDialog();

    await screen.findByTestId('watering-log-create-dialog');
    await user.click(screen.getByTestId('form-cancel-button'));
    expect(onClose).toHaveBeenCalled();
  });
});
