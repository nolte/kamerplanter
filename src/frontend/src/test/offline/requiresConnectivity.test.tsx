import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { act, screen, waitFor } from '@testing-library/react';
import { http, HttpResponse } from 'msw';
import i18n from 'i18next';
import ConnectivityIndicator from '@/components/layout/ConnectivityIndicator';
import FormActions from '@/components/form/FormActions';
import HarvestCreateDialog from '@/pages/ernte/HarvestCreateDialog';
import PhaseTransitionDialog from '@/pages/pflanzen/PhaseTransitionDialog';
import BatchPhaseTransitionDialog from '@/pages/durchlaeufe/BatchPhaseTransitionDialog';
import EnvironmentControlPage from '@/pages/environment/EnvironmentControlPage';
import { createStoreWithSmartHome, renderWithProviders } from '../helpers';
import { server } from '../mocks/server';

/**
 * #3025 N-39 — UI-NFR-012 outside the garden planner.
 *
 * - R-020a–R-020e: actions the server has to validate are disabled offline and say why ("Netzwerkverbindung
 *   erforderlich"): phase change (plant and run), harvest creation, harvest completion, actuator commands.
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

describe('connectivity-locked actions (UI-NFR-012 R-020a–R-020e)', () => {
  beforeEach(async () => {
    await i18n.changeLanguage('de');
    setOnline(true);
  });

  afterEach(() => {
    setOnline(true);
  });

  it('locks the harvest create button offline and names the reason (R-020b)', async () => {
    setOnline(false);
    renderWithProviders(<HarvestCreateDialog open onClose={vi.fn()} onCreated={vi.fn()} plantKey="plant-1" />);

    const submit = await screen.findByTestId('form-submit-button');
    expect(submit).toBeDisabled();
    const wrapper = screen.getByTestId('requires-connectivity');
    expect(wrapper).toContainElement(submit);
    expect(wrapper).toHaveAttribute('aria-label', HINT_DE);

    switchTo(true);
    await waitFor(() => expect(screen.getByTestId('form-submit-button')).toBeEnabled());
    expect(screen.queryByTestId('requires-connectivity')).toBeNull();
  });

  it('keeps an ordinary form save enabled offline', () => {
    setOnline(false);
    renderWithProviders(<FormActions onCancel={vi.fn()} />);
    expect(screen.getByTestId('form-submit-button')).toBeEnabled();
    expect(screen.queryByTestId('requires-connectivity')).toBeNull();
  });

  it('locks the plant phase change offline (R-020a)', async () => {
    setOnline(false);
    renderWithProviders(
      <PhaseTransitionDialog
        plantKey="plant-1"
        lifecycleKey={null}
        open
        onClose={vi.fn()}
        onTransitioned={vi.fn()}
      />,
    );
    const confirm = await screen.findByTestId('transition-confirm');
    expect(confirm).toBeDisabled();
    expect(screen.getByTestId('requires-connectivity')).toContainElement(confirm);

    switchTo(true);
    expect(screen.queryByTestId('requires-connectivity')).toBeNull();
  });

  it('locks the run phase change offline (R-020a)', async () => {
    setOnline(false);
    renderWithProviders(
      <BatchPhaseTransitionDialog
        open
        runKey="run-1"
        entries={[]}
        plants={[]}
        onClose={vi.fn()}
        onTransitioned={vi.fn()}
      />,
    );
    const confirm = await screen.findByTestId('batch-transition-confirm');
    expect(confirm).toBeDisabled();
    expect(screen.getByTestId('requires-connectivity')).toContainElement(confirm);
  });

  it('locks actuator commands and the emergency stop offline (R-020c)', async () => {
    server.use(
      http.get('/api/v1/t/:tenant/actuators', () =>
        HttpResponse.json([
          {
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
          },
        ]),
      ),
    );
    renderWithProviders(<EnvironmentControlPage />, { store: createStoreWithSmartHome() });

    const turnOn = await screen.findByTestId('turn-on-act1');
    expect(turnOn).toBeEnabled();
    expect(screen.getByTestId('emergency-stop-button')).toBeEnabled();

    switchTo(false);
    expect(screen.getByTestId('turn-on-act1')).toBeDisabled();
    expect(screen.getByTestId('turn-off-act1')).toBeDisabled();
    expect(screen.getByTestId('emergency-stop-button')).toBeDisabled();
    expect(screen.getAllByTestId('requires-connectivity')).toHaveLength(2);
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
    expect(screen.queryByText(/Du bist offline/)).toBeNull();

    switchTo(true);
    expect(await screen.findByText(/Wieder online/)).toBeInTheDocument();

    switchTo(false);
    expect(await screen.findByText(/Du bist offline/)).toBeInTheDocument();
  });
});
