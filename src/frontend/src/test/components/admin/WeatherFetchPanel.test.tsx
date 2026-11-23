import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { act, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { renderWithProviders } from '../../helpers';
import WeatherFetchPanel from '@/components/admin/WeatherFetchPanel';
import { WEATHER_FETCH_MAX_POLLS, WEATHER_FETCH_POLL_INTERVAL_MS } from '@/hooks/useWeatherFetch';
import { ApiError } from '@/api/errors';
import type { WeatherFetchRun, WeatherFetchStatusResponse } from '@/api/types';

/**
 * F-14 (#2934, REQ-046 §3.6a) — the weather fetch status and "fetch now" of the
 * installation's weather card.
 *
 * acceptance-2 is the sprint's value-verifying criterion: "fetch now" shows its
 * progress and then the result, and a refused fetch says when a new one is
 * possible. acceptance-3: the card shows the last successful and the next
 * scheduled fetch.
 */

vi.mock('@/api/endpoints/adminWeatherProviders', () => ({
  getWeatherFetchStatus: vi.fn(),
  triggerWeatherFetch: vi.fn(),
}));

import { getWeatherFetchStatus, triggerWeatherFetch } from '@/api/endpoints/adminWeatherProviders';

const mockStatus = vi.mocked(getWeatherFetchStatus);
const mockTrigger = vi.mocked(triggerWeatherFetch);

const OLD_RUN: WeatherFetchRun = {
  trigger: 'scheduled',
  started_at: '2026-11-23T06:00:02Z',
  finished_at: '2026-11-23T06:00:41Z',
  success: true,
  sites: 3,
  sites_written: 3,
  sites_failed: 0,
  sites_skipped: 0,
  forecasts_written: 21,
  error_type: null,
};

const NEW_RUN: WeatherFetchRun = {
  trigger: 'manual',
  started_at: '2026-11-23T09:17:02Z',
  finished_at: '2026-11-23T09:17:41Z',
  success: true,
  sites: 3,
  sites_written: 2,
  sites_failed: 1,
  sites_skipped: 0,
  forecasts_written: 14,
  error_type: null,
};

function status(overrides: Partial<WeatherFetchStatusResponse> = {}): WeatherFetchStatusResponse {
  return {
    interval_hours: 6,
    last_run: OLD_RUN,
    last_success: OLD_RUN,
    next_scheduled_at: '2026-11-23T12:00:00Z',
    running: false,
    manual_fetch_available_in_s: 0,
    ...overrides,
  };
}

function apiError(statusCode: number, errorCode: string, retryAfterSeconds: number | null = null): ApiError {
  return new ApiError(
    {
      error_id: 'err_1',
      error_code: errorCode,
      message: 'refused',
      details: [],
      timestamp: '2026-11-23T09:00:00Z',
      path: '/api/v1/admin/weather-providers/fetch',
      method: 'POST',
    },
    statusCode,
    retryAfterSeconds,
  );
}

/** Click "fetch now" once the mount status read has enabled it (it starts disabled). */
async function clickFetchNow(user: ReturnType<typeof userEvent.setup>) {
  const button = await screen.findByTestId('weather-fetch-now-button');
  await waitFor(() => expect(button).toBeEnabled());
  await user.click(button);
}

/** Advance the poll timer by one interval and let the status read settle. */
async function nextPoll() {
  await act(async () => {
    await vi.advanceTimersByTimeAsync(WEATHER_FETCH_POLL_INTERVAL_MS);
  });
}

describe('WeatherFetchPanel', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.useFakeTimers({ shouldAdvanceTime: true });
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  function setup() {
    const user = userEvent.setup({ advanceTimers: vi.advanceTimersByTime });
    return { user, ...renderWithProviders(<WeatherFetchPanel />) };
  }

  // ── acceptance-3 ─────────────────────────────────────────────────────

  it('acceptance-3: shows the last successful and the next scheduled fetch', async () => {
    mockStatus.mockResolvedValue(status());
    setup();

    const last = await screen.findByTestId('weather-fetch-last-success');
    // Date and time of the run plus how many sites it updated.
    expect(last).toHaveTextContent(/23\.11\.2026|11\/23\/2026/);
    expect(last).toHaveTextContent(/3 von 3|3 of 3/);
    expect(screen.getByTestId('weather-fetch-next-scheduled')).toHaveTextContent(/23\.11\.2026|11\/23\/2026/);
    expect(screen.getByTestId('weather-fetch-interval-effective')).toHaveTextContent('6');
    expect(screen.getByTestId('weather-fetch-now-button')).toBeEnabled();
  });

  it('acceptance-3: says so when there was no successful fetch yet', async () => {
    mockStatus.mockResolvedValue(status({ last_run: null, last_success: null }));
    setup();

    expect(await screen.findByTestId('weather-fetch-last-success')).toHaveTextContent(
      /noch kein erfolgreicher|no successful fetch yet/i,
    );
  });

  it('acceptance-3: names a failed newest run beside the last success', async () => {
    const failed: WeatherFetchRun = { ...NEW_RUN, success: false, sites_written: 0, sites_failed: 3 };
    mockStatus.mockResolvedValue(status({ last_run: failed }));
    setup();

    expect(await screen.findByTestId('weather-fetch-last-failed')).toHaveTextContent(/3 von 3|3 of 3/);
  });

  it('acceptance-3: shows no next fetch and disables the button while weather is switched off', async () => {
    mockStatus.mockResolvedValue(status({ next_scheduled_at: null }));
    setup();

    expect(await screen.findByTestId('weather-fetch-next-scheduled')).toHaveTextContent(
      /ausgeschaltet|switched off/i,
    );
    expect(screen.getByTestId('weather-fetch-now-button')).toBeDisabled();
  });

  it('shows a retry when the status cannot be loaded, and keeps the button disabled', async () => {
    mockStatus.mockRejectedValueOnce(new Error('Network Error')).mockResolvedValueOnce(status());
    const { user } = setup();

    expect(await screen.findByTestId('weather-fetch-status-error')).toBeInTheDocument();
    expect(screen.getByTestId('weather-fetch-now-button')).toBeDisabled();

    await user.click(screen.getByRole('button', { name: /erneut|retry/i }));
    expect(await screen.findByTestId('weather-fetch-last-success')).toBeInTheDocument();
    expect(screen.getByTestId('weather-fetch-now-button')).toBeEnabled();
  });

  // ── acceptance-2: progress and result ────────────────────────────────

  it('acceptance-2: shows the progress of an accepted fetch, then its result', async () => {
    mockStatus
      .mockResolvedValueOnce(status()) // mount
      .mockResolvedValueOnce(status({ running: true, manual_fetch_available_in_s: 590 })) // poll 1
      .mockResolvedValueOnce(
        status({ last_run: NEW_RUN, last_success: NEW_RUN, manual_fetch_available_in_s: 560 }),
      ); // poll 2
    mockTrigger.mockResolvedValue({ status: 'queued', task_id: 'task-1' });
    const { user } = setup();

    await clickFetchNow(user);

    // Progress, and no second fetch can be started meanwhile.
    expect(await screen.findByTestId('weather-fetch-progress')).toBeInTheDocument();
    expect(screen.getByTestId('weather-fetch-now-button')).toBeDisabled();

    await nextPoll();
    expect(screen.getByTestId('weather-fetch-progress')).toBeInTheDocument();
    expect(screen.queryByTestId('weather-fetch-result')).not.toBeInTheDocument();

    await nextPoll();
    const result = await screen.findByTestId('weather-fetch-result');
    expect(result).toHaveTextContent(/abgeschlossen|finished/i);
    expect(result).toHaveTextContent(/2 von 3|2 of 3/);
    expect(result).toHaveTextContent(/14/);
    // The site with an error is named, not hidden in the success.
    expect(result).toHaveTextContent(/fehler: 1|error: 1/i);
    expect(screen.queryByTestId('weather-fetch-progress')).not.toBeInTheDocument();
    // The status line moved to the new run.
    expect(screen.getByTestId('weather-fetch-last-success')).toHaveTextContent(/manuell|manual/i);
    expect(mockStatus).toHaveBeenCalledTimes(3);
  });

  it('acceptance-2: shows a failed run as a failure', async () => {
    const failed: WeatherFetchRun = { ...NEW_RUN, success: false, sites_written: 0, sites_failed: 3 };
    mockStatus
      .mockResolvedValueOnce(status())
      .mockResolvedValueOnce(status({ last_run: failed, manual_fetch_available_in_s: 580 }));
    mockTrigger.mockResolvedValue({ status: 'queued', task_id: 'task-1' });
    const { user } = setup();

    await clickFetchNow(user);
    await nextPoll();

    const result = await screen.findByTestId('weather-fetch-result');
    expect(result).toHaveTextContent(/fehlgeschlagen|failed/i);
    expect(result).toHaveTextContent(/3 von 3|3 of 3/);
  });

  it('acceptance-2: follows a fetch that is already running (409 WEATHER_FETCH_RUNNING)', async () => {
    mockStatus
      .mockResolvedValueOnce(status())
      .mockResolvedValueOnce(status({ last_run: NEW_RUN, last_success: NEW_RUN }));
    mockTrigger.mockRejectedValue(apiError(409, 'WEATHER_FETCH_RUNNING'));
    const { user } = setup();

    await clickFetchNow(user);
    expect(await screen.findByTestId('weather-fetch-progress')).toBeInTheDocument();
    expect(screen.queryByTestId('weather-fetch-refusal')).not.toBeInTheDocument();

    await nextPoll();
    expect(await screen.findByTestId('weather-fetch-result')).toBeInTheDocument();
  });

  // ── acceptance-2: refusals ───────────────────────────────────────────

  it('acceptance-2: a 429 says from when a new fetch is possible (Retry-After)', async () => {
    vi.setSystemTime(new Date('2026-11-23T09:20:00Z'));
    mockStatus.mockResolvedValue(status());
    mockTrigger.mockRejectedValue(apiError(429, 'WEATHER_FETCH_COOLDOWN', 420));
    const { user } = setup();

    await clickFetchNow(user);

    const refusal = await screen.findByTestId('weather-fetch-refusal');
    expect(refusal).toHaveAttribute('data-refusal', 'cooldown');
    // 09:20 + 420 s = 09:27 UTC; rendered in the local zone, so the minutes are what is fixed.
    expect(refusal).toHaveTextContent(/:27/);
    expect(refusal).toHaveTextContent(/10 minuten|10 minutes/i);
    expect(screen.getByTestId('weather-fetch-now-button')).toBeDisabled();
    expect(screen.queryByTestId('weather-fetch-progress')).not.toBeInTheDocument();
  });

  it('acceptance-2: a 429 without a readable Retry-After falls back to the status', async () => {
    vi.setSystemTime(new Date('2026-11-23T09:20:00Z'));
    mockStatus
      .mockResolvedValueOnce(status())
      .mockResolvedValueOnce(status({ manual_fetch_available_in_s: 300 }));
    mockTrigger.mockRejectedValue(apiError(429, 'WEATHER_FETCH_COOLDOWN', null));
    const { user } = setup();

    await clickFetchNow(user);

    const refusal = await screen.findByTestId('weather-fetch-refusal');
    expect(refusal).toHaveTextContent(/:25/);
    expect(mockStatus).toHaveBeenCalledTimes(2);
  });

  it('acceptance-2: the button becomes available again when the cooldown ends', async () => {
    mockStatus.mockResolvedValue(status());
    mockTrigger.mockRejectedValue(apiError(429, 'WEATHER_FETCH_COOLDOWN', 60));
    const { user } = setup();

    await clickFetchNow(user);
    expect(await screen.findByTestId('weather-fetch-refusal')).toBeInTheDocument();
    expect(screen.getByTestId('weather-fetch-now-button')).toBeDisabled();

    await act(async () => {
      await vi.advanceTimersByTimeAsync(61_000);
    });
    expect(screen.getByTestId('weather-fetch-now-button')).toBeEnabled();
    expect(screen.queryByTestId('weather-fetch-refusal')).not.toBeInTheDocument();
  });

  it('acceptance-2: a cooldown known from the status disables the button and names the time', async () => {
    vi.setSystemTime(new Date('2026-11-23T09:20:00Z'));
    mockStatus.mockResolvedValue(status({ manual_fetch_available_in_s: 540 }));
    setup();

    const button = await screen.findByTestId('weather-fetch-now-button');
    await waitFor(() => expect(button).toBeDisabled());
    // The helper the button is described by names the instant (09:29 UTC).
    const helper = document.getElementById(button.getAttribute('aria-describedby')!);
    expect(helper).toHaveTextContent(/:29/);
  });

  it('acceptance-2: a 409 WEATHER_FETCH_DISABLED explains that weather is switched off', async () => {
    mockStatus.mockResolvedValue(status());
    mockTrigger.mockRejectedValue(apiError(409, 'WEATHER_FETCH_DISABLED'));
    const { user } = setup();

    await clickFetchNow(user);

    const refusal = await screen.findByTestId('weather-fetch-refusal');
    expect(refusal).toHaveAttribute('data-refusal', 'disabled');
    expect(refusal).toHaveTextContent(/WEATHER_ENABLED/);
  });

  it('acceptance-2: a 503 asks to try again later', async () => {
    mockStatus.mockResolvedValue(status());
    mockTrigger.mockRejectedValue(apiError(503, 'WEATHER_FETCH_UNAVAILABLE'));
    const { user } = setup();

    await clickFetchNow(user);

    const refusal = await screen.findByTestId('weather-fetch-refusal');
    expect(refusal).toHaveAttribute('data-refusal', 'unavailable');
    expect(refusal).toHaveTextContent(/in ein paar minuten erneut|try again in a few minutes/i);
    // A 503 takes no cooldown: the button stays usable.
    expect(screen.getByTestId('weather-fetch-now-button')).toBeEnabled();
  });

  it('disables the button while the lock store cannot be checked (running unknown)', async () => {
    mockStatus.mockResolvedValue(status({ running: null, manual_fetch_available_in_s: null }));
    setup();

    const button = await screen.findByTestId('weather-fetch-now-button');
    await waitFor(() => expect(button).toBeDisabled());
  });

  // ── polling bounds ───────────────────────────────────────────────────

  it('stops polling when the card is unmounted mid-fetch', async () => {
    mockStatus.mockResolvedValueOnce(status()).mockResolvedValue(status({ running: true }));
    mockTrigger.mockResolvedValue({ status: 'queued', task_id: 'task-1' });
    const { user, unmount } = setup();

    await clickFetchNow(user);
    await screen.findByTestId('weather-fetch-progress');
    await nextPoll();
    const callsAtUnmount = mockStatus.mock.calls.length;
    unmount();

    await act(async () => {
      await vi.advanceTimersByTimeAsync(WEATHER_FETCH_POLL_INTERVAL_MS * 5);
    });
    expect(mockStatus).toHaveBeenCalledTimes(callsAtUnmount);
  });

  it('gives up after the poll budget and says the result will appear in the status', async () => {
    mockStatus.mockResolvedValueOnce(status()).mockResolvedValue(status({ running: true }));
    mockTrigger.mockResolvedValue({ status: 'queued', task_id: 'task-1' });
    const { user } = setup();

    await clickFetchNow(user);
    // The poll loop is armed once the progress shows; step it one interval at a time.
    await screen.findByTestId('weather-fetch-progress');
    for (let i = 0; i < WEATHER_FETCH_MAX_POLLS + 5; i += 1) {
      await nextPoll();
    }

    expect(await screen.findByTestId('weather-fetch-timed-out')).toBeInTheDocument();
    expect(screen.queryByTestId('weather-fetch-progress')).not.toBeInTheDocument();
    // One mount read plus exactly the budget.
    expect(mockStatus).toHaveBeenCalledTimes(1 + WEATHER_FETCH_MAX_POLLS);
  });
});
