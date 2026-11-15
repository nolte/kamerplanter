import { describe, it, expect, afterEach } from 'vitest';
import { cleanup, screen } from '@testing-library/react';
import i18n from 'i18next';
import { renderWithProviders } from '@/test/helpers';
import PestFindingsResult from '@/components/pests/PestFindingsResult';
import type { PestDetectionResult, PestFinding } from '@/api/types';

// #2955 — a finding is named in the UI language; without a name for it, the stored one.

const FINDING: PestFinding = {
  label: 'spider_mite',
  category: 'pest',
  common_name: 'Gemeine Spinnmilbe',
  common_names_i18n: { de: ['Gemeine Spinnmilbe'], en: ['Two-spotted spider mite'] },
  confidence: 0.72,
  mode: 'symptom',
  bounding_box: null,
  matched_pest_key: null,
  matched_beneficial_key: null,
};

function resultWith(finding: PestFinding): PestDetectionResult {
  return {
    key: 'd1',
    plant_instance_key: null,
    source: 'local',
    adapter_key: 'local',
    is_confident: true,
    trigger: 'manual',
    findings: [finding],
    tiles_processed: 1,
    suggested_next_step: 'none',
    image_hash: 'h',
    disclaimer: 'x',
    created_at: null,
  };
}

function render(finding: PestFinding) {
  return renderWithProviders(
    <PestFindingsResult result={resultWith(finding)} level="expert" onFeedback={() => {}} onViewPest={() => {}} />,
  );
}

describe('PestFindingsResult names', () => {
  afterEach(async () => {
    cleanup();
    await i18n.changeLanguage('de');
  });

  it('names a finding in the English UI by its English name', async () => {
    await i18n.changeLanguage('en');
    render(FINDING);

    expect(screen.getByText('Two-spotted spider mite')).toBeInTheDocument();
    expect(screen.queryByText('Gemeine Spinnmilbe')).not.toBeInTheDocument();
  });

  it('names a finding in the German UI by its German name', () => {
    render(FINDING);

    expect(screen.getByText('Gemeine Spinnmilbe')).toBeInTheDocument();
  });

  it('shows the stored name of a finding stored before the map existed', async () => {
    await i18n.changeLanguage('en');
    render({ ...FINDING, common_names_i18n: undefined });

    expect(screen.getByText('Gemeine Spinnmilbe')).toBeInTheDocument();
  });
});
