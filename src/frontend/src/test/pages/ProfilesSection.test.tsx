import { screen, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import i18n from 'i18next';
import { renderWithProviders } from '../helpers';
import ProfilesSection from '@/pages/pflanzen/ProfilesSection';
import type { NutrientProfile, RequirementProfile } from '@/api/types';

// ProfilesSection loads its data via the phases API on mount. Mock the module so
// each test controls exactly which nutrient profile the E7/E8 guidance renders.
vi.mock('@/api/endpoints/phases', () => ({
  getRequirementProfile: vi.fn(),
  getNutrientProfile: vi.fn(),
  generateDefaultProfiles: vi.fn(),
}));

import {
  getRequirementProfile,
  getNutrientProfile,
} from '@/api/endpoints/phases';

const mockGetReq = vi.mocked(getRequirementProfile);
const mockGetNut = vi.mocked(getNutrientProfile);

/** Minimal but type-complete NutrientProfile with overridable guidance fields. */
function makeNutrientProfile(overrides: Partial<NutrientProfile> = {}): NutrientProfile {
  return {
    key: 'nut-1',
    phase_key: 'phase-flowering',
    npk_ratio: [1, 3, 2],
    target_ec_ms: 1.6,
    target_ph: 6.2,
    calcium_ppm: null,
    magnesium_ppm: null,
    micro_nutrients: {},
    feed: true,
    micros_available: true,
    ph_note: undefined,
    created_at: null,
    updated_at: null,
    ...overrides,
  };
}

describe('ProfilesSection — E7/E8 nutrient guidance', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    // No requirement profile: keeps the render focused on the nutrient card while
    // still yielding hasProfiles === true so the card is shown.
    mockGetReq.mockRejectedValue(new Error('no requirement profile'));
  });

  it('renders the pH-lockout warning alert with the ph_note when micros are unavailable', async () => {
    const phNote = 'pH 6.5 liegt oberhalb des Zielbereichs — Eisen wird blockiert.';
    mockGetNut.mockResolvedValue(
      makeNutrientProfile({ micros_available: false, ph_note: phNote }),
    );

    renderWithProviders(
      <ProfilesSection phaseKey="phase-flowering" phaseName="Blüte" />,
    );

    // The MUI Alert severity="warning" exposes role="alert".
    const alert = await screen.findByRole('alert');
    expect(alert).toHaveTextContent(i18n.t('pages.profiles.microLockoutTitle'));
    expect(alert).toHaveTextContent(i18n.t('pages.profiles.microLockoutIntro'));
    expect(alert).toHaveTextContent(phNote);
  });

  it('omits the pH-lockout warning when micros are available', async () => {
    mockGetNut.mockResolvedValue(
      makeNutrientProfile({ micros_available: true }),
    );

    renderWithProviders(
      <ProfilesSection phaseKey="phase-flowering" phaseName="Blüte" />,
    );

    // Wait for the nutrient card to finish loading (npk_ratio row is always shown).
    await screen.findByText(i18n.t('pages.profiles.npkRatio'));

    expect(screen.queryByRole('alert')).not.toBeInTheDocument();
    expect(
      screen.queryByText(i18n.t('pages.profiles.microLockoutTitle')),
    ).not.toBeInTheDocument();
  });

  it('renders the no-feed chip when the phase is not fed (feed === false)', async () => {
    mockGetNut.mockResolvedValue(
      makeNutrientProfile({ feed: false }),
    );

    renderWithProviders(
      <ProfilesSection phaseKey="phase-flush" phaseName="Flush" />,
    );

    expect(
      await screen.findByText(i18n.t('pages.profiles.noFeed')),
    ).toBeInTheDocument();
  });

  it('omits the no-feed chip when the phase is fed (feed === true)', async () => {
    mockGetNut.mockResolvedValue(
      makeNutrientProfile({ feed: true }),
    );

    renderWithProviders(
      <ProfilesSection phaseKey="phase-veg" phaseName="Vegetativ" />,
    );

    await screen.findByText(i18n.t('pages.profiles.npkRatio'));

    await waitFor(() => {
      expect(
        screen.queryByText(i18n.t('pages.profiles.noFeed')),
      ).not.toBeInTheDocument();
    });
  });
});

/** #2857: the light hours are shown with where they came from, in words. */
describe('ProfilesSection — origin of the light hours', () => {
  function makeRequirementProfile(overrides: Partial<RequirementProfile> = {}): RequirementProfile {
    return {
      key: 'req-1',
      phase_key: 'phase-flowering',
      light_ppfd_target: 600,
      photoperiod_hours: 12,
      light_spectrum: {},
      temperature_day_c: 26,
      temperature_night_c: 20,
      humidity_day_percent: 50,
      humidity_night_percent: 55,
      vpd_target_kpa: 1.2,
      co2_ppm: null,
      irrigation_frequency_days: 1,
      irrigation_volume_ml_per_plant: 250,
      created_at: null,
      updated_at: null,
      ...overrides,
    };
  }

  beforeEach(() => {
    vi.clearAllMocks();
    mockGetNut.mockRejectedValue(new Error('no nutrient profile'));
  });

  it.each([
    ['sourced', 'enums.photoperiodSource.sourced'],
    ['generated', 'enums.photoperiodSource.generated'],
    ['default', 'enums.photoperiodSource.default'],
  ] as const)('names the origin %s next to the hours', async (source, key) => {
    mockGetReq.mockResolvedValue(makeRequirementProfile({ photoperiod_source: source }));

    renderWithProviders(<ProfilesSection phaseKey="phase-flowering" phaseName="Blüte" />);

    const detail = await screen.findByTestId('profile-photoperiod-source');
    expect(detail).toHaveTextContent(i18n.t(key));
    expect(i18n.t(key)).not.toBe(key);
    expect(screen.getByText('12 h')).toBeInTheDocument();
  });

  it.each([null, undefined])('says the origin is unknown for a profile from before the provenance (%s)', async (source) => {
    mockGetReq.mockResolvedValue(makeRequirementProfile({ photoperiod_source: source }));

    renderWithProviders(<ProfilesSection phaseKey="phase-flowering" phaseName="Blüte" />);

    expect(await screen.findByTestId('profile-photoperiod-source')).toHaveTextContent(
      i18n.t('pages.profiles.photoperiodSourceUnknown'),
    );
  });

  it.each(['generated', 'default', null] as const)('says what to do while the hours are not entered (%s)', async (source) => {
    mockGetReq.mockResolvedValue(makeRequirementProfile({ photoperiod_source: source }));

    renderWithProviders(<ProfilesSection phaseKey="phase-flowering" phaseName="Blüte" />);

    expect(await screen.findByTestId('profile-photoperiod-source-todo')).toHaveTextContent(
      i18n.t('pages.profiles.photoperiodSourceTodo'),
    );
  });

  it('asks for nothing once the hours are entered, nor from a reader who cannot edit', async () => {
    mockGetReq.mockResolvedValue(makeRequirementProfile({ photoperiod_source: 'sourced' }));
    const { unmount } = renderWithProviders(<ProfilesSection phaseKey="phase-flowering" phaseName="Blüte" />);
    await screen.findByTestId('profile-photoperiod-source');
    expect(screen.queryByTestId('profile-photoperiod-source-todo')).not.toBeInTheDocument();
    unmount();

    mockGetReq.mockResolvedValue(makeRequirementProfile({ photoperiod_source: 'generated' }));
    renderWithProviders(<ProfilesSection phaseKey="phase-flowering" phaseName="Blüte" readOnly />);
    await screen.findByTestId('profile-photoperiod-source');
    expect(screen.queryByTestId('profile-photoperiod-source-todo')).not.toBeInTheDocument();
  });
});
