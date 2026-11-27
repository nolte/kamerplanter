import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { act, fireEvent, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { http, HttpResponse } from 'msw';
import i18n from 'i18next';
import ConnectivityIndicator from '@/components/layout/ConnectivityIndicator';
import ConfirmDialog from '@/components/common/ConfirmDialog';
import FormActions from '@/components/form/FormActions';
import HarvestCreateDialog from '@/pages/ernte/HarvestCreateDialog';
import PhaseTransitionDialog from '@/pages/pflanzen/PhaseTransitionDialog';
import BatchPhaseTransitionDialog from '@/pages/durchlaeufe/BatchPhaseTransitionDialog';
import EnvironmentControlPage from '@/pages/environment/EnvironmentControlPage';
import { createStoreWithSmartHome, renderWithProviders } from '../helpers';
import { server } from '../mocks/server';
import { setActiveTenantSlug } from '@/api/client';

/**
 * #3025 N-39 — UI-NFR-012 outside the garden planner.
 *
 * - R-020a–R-020e: actions the server has to validate are locked offline and say why ("Netzwerkverbindung
 *   erforderlich"): phase change (plant and run), harvest creation, harvest completion (opener and confirm),
 *   actuator on/off. The button stays focusable (`aria-disabled`), keeps its name and is described by the reason.
 * - REQ-018: the emergency stop is never locked by connectivity; offline it warns and still sends.
 * - R-036/R-037: a snackbar when the connection drops and when it returns — on the change, not at mount.
 *
 * Each case renders the production component and drives `navigator.onLine` plus the browser event, the same
 * signal `useOnlineStatus` listens to.
 */

function setOnline(value: boolean) {
  Object.defineProperty(navigator, 'onLine', { configurable: true, get: () => value });
}

function switchTo(online: boolean) {
  act(() => {
    setOnline(online);
    window.dispatchEvent(new Event(online ? 'online' : 'offline'));
  });
}

const HINT_DE = 'Netzwerkverbindung erforderlich';

/** Locked the accessible way: focusable, named after the action, described by the reason. */
function expectLocked(button: HTMLElement, name: RegExp | string) {
  expect(button).toBeEnabled();
  expect(button).toHaveAttribute('aria-disabled', 'true');
  expect(button).toHaveAccessibleName(name);
  expect(button).toHaveAccessibleDescription(HINT_DE);
}

function expectUnlocked(button: HTMLElement) {
  expect(button).not.toHaveAttribute('aria-disabled', 'true');
  expect(button).not.toHaveAccessibleDescription(HINT_DE);
}

const ACTUATOR = {
  key: 'act1',
  tenant_key: 't1',
  location_key: 'loc1',
  name: 'Hauptlicht Zelt 1',
  actuator_type: 'light',
  protocol: 'manual',
  ha_entity_id: null,
  mqtt_command_topic: null,
  mqtt_state_topic: null,
  capabilities: ['on_off'],
  min_value: null,
  max_value: null,
  unit: null,
  current_state: 'off',
  current_value: null,
  last_state_change: null,
  is_online: true,
  last_seen: null,
  power_watts: null,
  fail_safe_state: 'last',
  fail_safe_value: null,
  conflict_group: null,
  installed_on: null,
  notes: null,
};

describe('connectivity-locked actions (UI-NFR-012 R-020a–R-020e)', () => {
  beforeEach(async () => {
    await i18n.changeLanguage('de');
    setOnline(true);
  });

  afterEach(() => {
    setOnline(true);
  });

  it('locks the harvest create button offline, keeps it focusable and blocks the submit (R-020b)', async () => {
    const created = vi.fn();
    server.use(
      http.post('/api/v1/t/:tenant/harvest/plants/:plantKey/batches', () => {
        created();
        return HttpResponse.json({});
      }),
    );
    setOnline(false);
    renderWithProviders(<HarvestCreateDialog open onClose={vi.fn()} onCreated={vi.fn()} plantKey="plant-1" />);

    const submit = await screen.findByTestId('form-submit-button');
    expectLocked(submit, /anlegen|erstellen/i);
    // A tap on a tablet shows no tooltip: the reason is visible as well.
    expect(screen.getByTestId('requires-connectivity-reason')).toBeVisible();
    expect(screen.getByTestId('requires-connectivity-reason')).toHaveTextContent(HINT_DE);
    submit.focus();
    expect(submit).toHaveFocus();
    fireEvent.click(submit);
    await new Promise((resolve) => setTimeout(resolve, 20));
    expect(created).not.toHaveBeenCalled();

    // Same element after the change: no remount, focus stays.
    switchTo(true);
    expect(screen.getByTestId('form-submit-button')).toBe(submit);
    expect(submit).toHaveFocus();
    expectUnlocked(submit);
    expect(screen.getByTestId('requires-connectivity-reason')).toHaveTextContent('');

    // Positive control: the same form, online, does create — so "nothing sent" above is the guard's doing.
    fireEvent.click(submit);
    await waitFor(() => expect(created).toHaveBeenCalledTimes(1));
  });

  it('does not submit the harvest form on Enter in a text field while offline (R-020b)', async () => {
    const created = vi.fn();
    server.use(
      http.post('/api/v1/t/:tenant/harvest/plants/:plantKey/batches', () => {
        created();
        return HttpResponse.json({});
      }),
    );
    setOnline(false);
    renderWithProviders(<HarvestCreateDialog open onClose={vi.fn()} onCreated={vi.fn()} plantKey="plant-1" />);
    await screen.findByTestId('form-submit-button');
    const user = userEvent.setup();
    const batchInput = within(screen.getByTestId('form-field-batch_id')).getByRole('textbox');
    await user.type(batchInput, 'HB-OFFLINE{Enter}');
    await new Promise((resolve) => setTimeout(resolve, 50));
    expect(created).not.toHaveBeenCalled();

    // Control: the same keystroke online submits.
    switchTo(true);
    await user.type(batchInput, '{Enter}');
    await waitFor(() => expect(created).toHaveBeenCalledTimes(1));
  });

  it('keeps an ordinary form save unlocked offline', () => {
    setOnline(false);
    renderWithProviders(<FormActions onCancel={vi.fn()} />);
    const submit = screen.getByTestId('form-submit-button');
    expect(submit).toBeEnabled();
    expectUnlocked(submit);
    // No wrapper, tooltip or reason element for a form that did not ask for the lock.
    expect(screen.queryByTestId('requires-connectivity')).toBeNull();
  });

  it('locks the plant phase change offline with a target chosen (R-020a)', async () => {
    const transitions = vi.fn();
    server.use(
      http.get('/api/v1/growth-phases', () =>
        HttpResponse.json([
          {
            key: 'ph-veg',
            name: 'vegetative',
            display_name: 'Vegetativ',
            description: '',
            lifecycle_key: 'lc-1',
            typical_duration_days: 30,
            sequence_order: 2,
            is_terminal: false,
            allows_harvest: false,
            stress_tolerance: 'medium',
            watering_interval_days: null,
            created_at: null,
            updated_at: null,
          },
        ]),
      ),
      http.post('/api/v1/plant-instances/:key/phases/transition', () => {
        transitions();
        return HttpResponse.json({ key: 'plant-1' });
      }),
    );
    renderWithProviders(
      <PhaseTransitionDialog plantKey="plant-1" lifecycleKey="lc-1" open onClose={vi.fn()} onTransitioned={vi.fn()} />,
    );
    // Choose a target, so the button is not natively disabled and the guard itself is what is tested.
    const select = within(screen.getByTestId('target-phase-select')).getByRole('combobox');
    await waitFor(() => expect(select).not.toHaveAttribute('aria-disabled', 'true'));
    fireEvent.mouseDown(select);
    fireEvent.click(await screen.findByRole('option', { name: /Vegetativ/ }));
    const confirm = screen.getByTestId('transition-confirm');
    expect(confirm).toBeEnabled();

    switchTo(false);
    expectLocked(confirm, /bestätigen/i);
    expect(screen.getByTestId('requires-connectivity-reason')).toHaveTextContent(HINT_DE);
    fireEvent.click(confirm);
    await new Promise((resolve) => setTimeout(resolve, 20));
    expect(transitions).not.toHaveBeenCalled();

    switchTo(true);
    expectUnlocked(confirm);
    fireEvent.click(confirm);
    await waitFor(() => expect(transitions).toHaveBeenCalledTimes(1));
  });

  it('locks the run phase change offline with a target chosen (R-020a)', async () => {
    setActiveTenantSlug('t1');
    const transitions = vi.fn();
    server.use(
      http.get('/api/v1/species/:key/phase-sequence', () =>
        HttpResponse.json({
          key: 'seq-1',
          entries: [
            {
              key: 'e-flower',
              phase_definition: { name: 'flowering', display_name: 'Blüte', typical_duration_days: 50 },
              override_duration_days: null,
              sequence_order: 2,
              is_terminal: false,
              allows_harvest: false,
              created_at: null,
              updated_at: null,
            },
          ],
        }),
      ),
      http.post('/api/v1/t/:tenant/planting-runs/:key/transition', () => {
        transitions();
        return HttpResponse.json({ transitioned_count: 0, skipped_count: 0, failed_count: 0, results: [] });
      }),
    );
    renderWithProviders(
      <BatchPhaseTransitionDialog
        open
        runKey="run-1"
        entries={[{ key: 'en-1', species_key: 'sp-1' }] as never}
        plants={[]}
        onClose={vi.fn()}
        onTransitioned={vi.fn()}
      />,
    );
    const dialog = await screen.findByRole('dialog');
    // The select appears once the phases are loaded.
    fireEvent.mouseDown(await within(dialog).findByRole('combobox'));
    fireEvent.click(await screen.findByRole('option', { name: /Blüte/ }));
    const confirm = screen.getByTestId('batch-transition-confirm');
    expect(confirm).toBeEnabled();

    switchTo(false);
    expectLocked(confirm, /bestätigen/i);
    fireEvent.click(confirm);
    await new Promise((resolve) => setTimeout(resolve, 20));
    expect(transitions).not.toHaveBeenCalled();

    switchTo(true);
    fireEvent.click(confirm);
    await waitFor(() => expect(transitions).toHaveBeenCalledTimes(1));
  });

  it('locks the confirm of an already open dialog when the connection drops', () => {
    const onConfirm = vi.fn();
    renderWithProviders(
      <ConfirmDialog
        open
        title="Ernte abschließen"
        message="Wirklich?"
        confirmLabel="Ernte abschließen"
        requiresConnectivity
        onConfirm={onConfirm}
        onCancel={vi.fn()}
      />,
    );
    const confirm = screen.getByTestId('confirm-dialog-confirm');
    expectUnlocked(confirm);

    switchTo(false);
    expect(screen.getByTestId('confirm-dialog-confirm')).toBe(confirm);
    expectLocked(confirm, 'Ernte abschließen');
    expect(screen.getByTestId('confirm-dialog-offline')).toHaveTextContent(HINT_DE);
    fireEvent.click(confirm);
    expect(onConfirm).not.toHaveBeenCalled();

    switchTo(true);
    fireEvent.click(confirm);
    expect(onConfirm).toHaveBeenCalledTimes(1);
  });

  it('leaves a confirm dialog without the flag untouched offline', () => {
    const onConfirm = vi.fn();
    setOnline(false);
    renderWithProviders(
      <ConfirmDialog open title="Löschen" message="Wirklich?" onConfirm={onConfirm} onCancel={vi.fn()} />,
    );
    fireEvent.click(screen.getByTestId('confirm-dialog-confirm'));
    expect(onConfirm).toHaveBeenCalledTimes(1);
    expect(screen.queryByTestId('requires-connectivity')).toBeNull();
  });

  it('locks actuator on/off offline but keeps the emergency stop usable and sends it (R-020c, REQ-018)', async () => {
    const stops: unknown[] = [];
    const commands = vi.fn();
    server.use(
      http.get('/api/v1/t/:tenant/actuators', () => HttpResponse.json([ACTUATOR])),
      http.post('/api/v1/t/:tenant/actuators/:key/command', () => {
        commands();
        return HttpResponse.json({});
      }),
      http.post('/api/v1/t/:tenant/emergency-stop', async ({ request }) => {
        stops.push(await request.json());
        return HttpResponse.json({ stopped: ['act1'], failed: [] });
      }),
    );
    renderWithProviders(<EnvironmentControlPage />, { store: createStoreWithSmartHome() });

    const turnOn = await screen.findByTestId('turn-on-act1');
    expectUnlocked(turnOn);
    expect(screen.queryByTestId('environment-offline-warning')).toBeNull();

    switchTo(false);
    expectLocked(screen.getByTestId('turn-on-act1'), /einschalten/i);
    expectLocked(screen.getByTestId('turn-off-act1'), /ausschalten/i);
    fireEvent.click(screen.getByTestId('turn-on-act1'));
    expect(commands).not.toHaveBeenCalled();

    // The stop: enabled, warned about, and the request goes out.
    expect(screen.getByTestId('environment-offline-warning')).toBeInTheDocument();
    const stop = screen.getByTestId('emergency-stop-button');
    expect(stop).toBeEnabled();
    expect(stop).not.toHaveAttribute('aria-disabled', 'true');
    fireEvent.click(stop);
    fireEvent.click(await screen.findByTestId('confirm-dialog-confirm'));
    await waitFor(() => expect(stops).toHaveLength(1));
  });
});

describe('emergency stop with an unknown actuator list (REQ-018)', () => {
  beforeEach(async () => {
    await i18n.changeLanguage('de');
    setOnline(true);
  });

  afterEach(() => {
    setOnline(true);
  });

  it('stays clickable and sends when the page opened offline and the list failed to load', async () => {
    const stops: unknown[] = [];
    server.use(
      http.get('/api/v1/t/:tenant/actuators', () => HttpResponse.error()),
      http.post('/api/v1/t/:tenant/emergency-stop', async ({ request }) => {
        stops.push(await request.json());
        return HttpResponse.json({ stopped: [], failed: [] });
      }),
    );
    setOnline(false);
    renderWithProviders(<EnvironmentControlPage />, { store: createStoreWithSmartHome() });

    const stop = await screen.findByTestId('emergency-stop-button');
    await waitFor(() => expect(screen.queryByTestId('loading-skeleton')).toBeNull());
    expect(stop).toBeEnabled();
    fireEvent.click(stop);
    fireEvent.click(await screen.findByTestId('confirm-dialog-confirm'));
    await waitFor(() => expect(stops).toHaveLength(1));
  });

  it('stays disabled when the list was read and is really empty', async () => {
    server.use(http.get('/api/v1/t/:tenant/actuators', () => HttpResponse.json([])));
    renderWithProviders(<EnvironmentControlPage />, { store: createStoreWithSmartHome() });
    await waitFor(() => expect(screen.getByTestId('emergency-stop-button')).toBeDisabled());
  });
});

describe('connectivity snackbars (UI-NFR-012 R-036/R-037)', () => {
  beforeEach(async () => {
    await i18n.changeLanguage('de');
    setOnline(true);
  });

  afterEach(() => {
    setOnline(true);
  });

  it('announces going offline and coming back, but not the state at mount', async () => {
    setOnline(false);
    renderWithProviders(<ConnectivityIndicator />);
    // The notices are a lazy chunk of the indicator; let it mount before the connection changes.
    await act(async () => {
      await import('@/components/layout/ConnectivityNotices');
      await new Promise((resolve) => setTimeout(resolve, 0));
    });
    // Opened offline: the indicator shows it; no toast for a state the user did not just enter.
    expect(screen.queryByText(/^Offline – /)).toBeNull();

    switchTo(true);
    expect(await screen.findByText(/^Online – Synchronisation startet/)).toBeInTheDocument();

    switchTo(false);
    expect(await screen.findByText(/^Offline – /)).toBeInTheDocument();
  });
});
