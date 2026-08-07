import { describe, it, expect, beforeEach, vi } from 'vitest';
import { screen, within } from '@testing-library/react';
import i18n from 'i18next';
import { renderWithProviders } from '@/test/helpers';
import type { PlantDiaryEntry } from '@/api/types';
import DiaryEntryCard from '@/components/diary/DiaryEntryCard';

/**
 * REQ-013 §2.3a — the stored environment snapshot on a diary entry.
 *
 * The single property worth defending here is the *separation*: a reader has to
 * be able to tell, at a glance and a year later, what a machine reported and
 * what the grower typed. One merged list would destroy that, and it is exactly
 * the shape the obvious implementation would have produced.
 */

function entry(overrides: Partial<PlantDiaryEntry> = {}): PlantDiaryEntry {
  return {
    key: 'e1',
    plant_key: 'plant-1',
    entry_type: 'problem',
    title: 'Braune Flecken unten',
    text: 'Untere Blätter hängen.',
    photo_refs: [],
    tags: [],
    measurements: null,
    created_by: 'u1',
    created_at: '2026-08-03T18:22:11Z',
    updated_at: '2026-08-03T18:22:11Z',
    environment: [],
    environment_captured_at: null,
    environment_status: 'not_attempted',
    analysis_state: 'none',
    analysis_requested_at: null,
    analysis_requested_by: null,
    analysis_claimed_at: null,
    analysis_claimed_by: null,
    analysis_lease_expires_at: null,
    analysis: null,
    analysis_error: null,
    can_request_analysis: true,
    ...overrides,
  };
}

const READINGS: PlantDiaryEntry['environment'] = [
  {
    metric_type: 'temperature_celsius',
    value: 31.2,
    unit: '°C',
    source: 'ha_auto',
    measured_at: '2026-08-03T18:21:44Z',
    sensor_key: 's-temp',
    origin: 'location',
  },
  {
    metric_type: 'humidity_percent',
    value: 28,
    unit: '%',
    source: 'dwd',
    measured_at: '2026-08-03T18:10:00Z',
    sensor_key: null,
    origin: 'weather',
  },
];

describe('DiaryEntryCard — environment snapshot', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    i18n.changeLanguage('de');
  });

  it('shows the captured conditions with their provenance', () => {
    renderWithProviders(
      <DiaryEntryCard
        entry={entry({ environment: READINGS, environment_status: 'captured' })}
      />,
    );

    const block = screen.getByTestId('diary-entry-environment');
    expect(block).toHaveTextContent('31.2 °C');
    expect(block).toHaveTextContent('28 %');
    expect(
      within(block).getByTestId('diary-entry-environment-origin-temperature_celsius'),
    ).toHaveTextContent('Standort');
    expect(
      within(block).getByTestId('diary-entry-environment-origin-humidity_percent'),
    ).toHaveTextContent('Wetterdienst');
    // The measurement instant, not the entry's: a stale reading must be
    // recognisable as one rather than passing for "now".
    expect(block).toHaveTextContent('dwd');
  });

  it('keeps the automatic values out of the grower measurements block', () => {
    renderWithProviders(
      <DiaryEntryCard
        entry={entry({
          environment: READINGS,
          environment_status: 'captured',
          measurements: { height_cm: 84 },
        })}
      />,
    );

    const measurements = screen.getByTestId('diary-entry-measurements');
    expect(measurements).toHaveTextContent('height_cm: 84');
    // Two blocks, two meanings. A single merged list would tell the reader that
    // a machine and a human said the same kind of thing.
    expect(measurements).not.toHaveTextContent('31.2');
    expect(screen.getByTestId('diary-entry-environment')).not.toHaveTextContent('height_cm');
  });

  it('flags a partial snapshot so the gaps are not read as facts', () => {
    renderWithProviders(
      <DiaryEntryCard
        entry={entry({ environment: [READINGS[0]], environment_status: 'unavailable' })}
      />,
    );

    expect(screen.getByTestId('diary-entry-environment-partial')).toHaveTextContent(
      /Nicht alle Sensoren/i,
    );
  });

  it('renders nothing for an entry written before the feature existed', () => {
    renderWithProviders(<DiaryEntryCard entry={entry()} />);

    // ``not_attempted`` is not a statement about the garden, so there is nothing
    // honest to display — an empty "Umgebung" heading would imply there was one.
    expect(screen.queryByTestId('diary-entry-environment')).toBeNull();
  });

  it('renders nothing when the author opted out', () => {
    renderWithProviders(
      <DiaryEntryCard entry={entry({ environment: [], environment_status: 'opted_out' })} />,
    );

    expect(screen.queryByTestId('diary-entry-environment')).toBeNull();
  });
});
