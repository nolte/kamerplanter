import { screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import i18n from 'i18next';
import type { UseFormSetValue } from 'react-hook-form';
import GpsDetectButton from '@/pages/standorte/GpsDetectButton';
import type { SiteFormData } from '@/pages/standorte/siteForm';
import { renderWithProviders } from '../helpers';

const originalGeolocation = Object.getOwnPropertyDescriptor(navigator, 'geolocation');
const originalSecureContext = Object.getOwnPropertyDescriptor(window, 'isSecureContext');

function setSecureContext(value: boolean) {
  Object.defineProperty(window, 'isSecureContext', { value, configurable: true });
}

function setGeolocation(value: unknown) {
  Object.defineProperty(navigator, 'geolocation', { value, configurable: true });
}

function makeSetValue() {
  return vi.fn() as unknown as UseFormSetValue<SiteFormData> & ReturnType<typeof vi.fn>;
}

describe('GpsDetectButton', () => {
  beforeEach(() => {
    i18n.changeLanguage('de');
    setSecureContext(true);
  });

  afterEach(() => {
    if (originalGeolocation) Object.defineProperty(navigator, 'geolocation', originalGeolocation);
    if (originalSecureContext) Object.defineProperty(window, 'isSecureContext', originalSecureContext);
    vi.restoreAllMocks();
  });

  it('fills the coordinate fields on a successful position fix', async () => {
    const getCurrentPosition = vi.fn((success: PositionCallback) =>
      success({ coords: { latitude: 52.5200081, longitude: 13.404954 } } as GeolocationPosition),
    );
    setGeolocation({ getCurrentPosition });

    const setValue = makeSetValue();
    const user = userEvent.setup();
    renderWithProviders(<GpsDetectButton setValue={setValue} />);

    await user.click(await screen.findByTestId('gps-detect-button'));

    expect(getCurrentPosition).toHaveBeenCalledOnce();
    // Rounded to 6 decimals, with validation + dirty flags so superRefine runs.
    expect(setValue).toHaveBeenCalledWith('gps_lat', 52.520008, { shouldValidate: true, shouldDirty: true });
    expect(setValue).toHaveBeenCalledWith('gps_lon', 13.404954, { shouldValidate: true, shouldDirty: true });
  });

  it('shows the denied message and keeps the fields untouched when permission is refused', async () => {
    const getCurrentPosition = vi.fn((_success: PositionCallback, error: PositionErrorCallback) =>
      error({ code: 1 } as GeolocationPositionError),
    );
    setGeolocation({ getCurrentPosition });

    const setValue = makeSetValue();
    const user = userEvent.setup();
    renderWithProviders(<GpsDetectButton setValue={setValue} />);

    await user.click(await screen.findByTestId('gps-detect-button'));

    expect(await screen.findByText('Standortfreigabe im Browser verweigert.')).toBeTruthy();
    expect(setValue).not.toHaveBeenCalled();
  });

  it('shows the unavailable message on POSITION_UNAVAILABLE and keeps the fields untouched', async () => {
    const getCurrentPosition = vi.fn((_success: PositionCallback, error: PositionErrorCallback) =>
      error({ code: 2 } as GeolocationPositionError),
    );
    setGeolocation({ getCurrentPosition });

    const setValue = makeSetValue();
    const user = userEvent.setup();
    renderWithProviders(<GpsDetectButton setValue={setValue} />);

    await user.click(await screen.findByTestId('gps-detect-button'));

    expect(await screen.findByText('Standort konnte nicht ermittelt werden.')).toBeTruthy();
    expect(setValue).not.toHaveBeenCalled();
  });

  it('shows the timeout message on TIMEOUT and keeps the fields untouched', async () => {
    const getCurrentPosition = vi.fn((_success: PositionCallback, error: PositionErrorCallback) =>
      error({ code: 3 } as GeolocationPositionError),
    );
    setGeolocation({ getCurrentPosition });

    const setValue = makeSetValue();
    const user = userEvent.setup();
    renderWithProviders(<GpsDetectButton setValue={setValue} />);

    await user.click(await screen.findByTestId('gps-detect-button'));

    expect(await screen.findByText('Standortermittlung hat zu lange gedauert.')).toBeTruthy();
    expect(setValue).not.toHaveBeenCalled();
  });

  it('renders nothing when the browser has no Geolocation API (feature detect)', () => {
    setGeolocation(undefined);

    const setValue = makeSetValue();
    renderWithProviders(<GpsDetectButton setValue={setValue} />);

    expect(screen.queryByTestId('gps-detect-button')).toBeNull();
  });

  it('renders a disabled button outside a secure context', async () => {
    setGeolocation({ getCurrentPosition: vi.fn() });
    setSecureContext(false);

    const setValue = makeSetValue();
    renderWithProviders(<GpsDetectButton setValue={setValue} />);

    const button = await screen.findByTestId('gps-detect-button');
    expect(button).toBeDisabled();
  });
});
