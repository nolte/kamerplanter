import { describe, it, expect, vi, beforeEach } from 'vitest';
import { screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { renderWithProviders, createStoreWithExpertise } from '@/test/helpers';
import type { DiagnosisResult, DiagnosisSymptom } from '@/api/types';

const listSymptoms = vi.fn();
const analyzeDiagnosis = vi.fn();

vi.mock('@/api', () => ({
  diagnoseApi: {
    listSymptoms: (...args: unknown[]) => listSymptoms(...args),
    analyzeDiagnosis: (...args: unknown[]) => analyzeDiagnosis(...args),
  },
}));

import DiagnosisWizard from '@/components/diagnosis/DiagnosisWizard';

const SYMPTOMS: DiagnosisSymptom[] = [
  {
    slug: 'webbing_on_leaves',
    category: 'pest_visible',
    label: 'Fine webbing on the leaves',
    common_causes_hint: 'Spider mites.',
    applicable_phases: [],
  },
];

function makeResult(overrides: Partial<DiagnosisResult> = {}): DiagnosisResult {
  return {
    candidates: [
      {
        rank: 1,
        name: 'Spider mites',
        scientific_name: 'Tetranychus urticae',
        category: 'pest_visible',
        confidence: 0.85,
        confidence_level: 'high',
        explanation: 'Webbing present.',
        recommended_actions: ['Increase humidity'],
        matched_pest_key: 'pest-1',
        matched_pest_detail_url: '/pflanzenschutz/pests/pest-1',
        matched_disease_key: null,
        matched_disease_detail_url: null,
        matched_treatments: [],
      },
    ],
    answer_summary: 'Webbing present.',
    sources: [],
    language: 'de',
    uses_tenant_data: true,
    uses_cloud_provider: false,
    confidence: 'high',
    model_name: 'gemma3:12b',
    provider_type: 'ollama',
    status: 'ok',
    ...overrides,
  };
}

describe('DiagnosisWizard', () => {
  beforeEach(() => {
    listSymptoms.mockReset();
    analyzeDiagnosis.mockReset();
  });

  it('walks symptom → context → result on the happy path', async () => {
    listSymptoms.mockResolvedValue(SYMPTOMS);
    analyzeDiagnosis.mockResolvedValue(makeResult());
    const user = userEvent.setup();
    renderWithProviders(<DiagnosisWizard />, { store: createStoreWithExpertise('intermediate') });

    // Step 1 — symptoms load and the Next button is gated until one is picked.
    const symptom = await screen.findByTestId('symptom-webbing_on_leaves');
    expect((screen.getByTestId('diagnosis-next-context') as HTMLButtonElement).disabled).toBe(true);
    await user.click(symptom.querySelector('input')!);
    await user.click(screen.getByTestId('diagnosis-next-context'));

    // Step 2 — run the analysis.
    await user.click(screen.getByTestId('diagnosis-analyze'));

    // Step 3 — the results panel renders the top candidate.
    expect(await screen.findByTestId('diagnosis-results')).toBeTruthy();
    expect(screen.getByText('Spider mites')).toBeTruthy();
    await waitFor(() =>
      expect(analyzeDiagnosis).toHaveBeenCalledWith(
        expect.objectContaining({ symptom_slugs: ['webbing_on_leaves'], extra_notes: null }),
      ),
    );
  });

  it('forwards typed notes and can restart from the result step', async () => {
    listSymptoms.mockResolvedValue(SYMPTOMS);
    analyzeDiagnosis.mockResolvedValue(makeResult());
    const user = userEvent.setup();
    renderWithProviders(<DiagnosisWizard />, { store: createStoreWithExpertise('intermediate') });

    const symptom = await screen.findByTestId('symptom-webbing_on_leaves');
    await user.click(symptom.querySelector('input')!);
    await user.click(screen.getByTestId('diagnosis-next-context'));

    const notes = screen.getByTestId('diagnosis-notes').querySelector('textarea')!;
    await user.type(notes, 'looks bad');
    await user.click(screen.getByTestId('diagnosis-analyze'));

    await screen.findByTestId('diagnosis-results');
    await waitFor(() =>
      expect(analyzeDiagnosis).toHaveBeenCalledWith(expect.objectContaining({ extra_notes: 'looks bad' })),
    );

    // Restart returns to the first step.
    await user.click(screen.getByTestId('diagnosis-restart'));
    expect(screen.getByTestId('diagnosis-next-context')).toBeTruthy();
    expect(screen.queryByTestId('diagnosis-results')).toBeNull();
  });

  it('shows a warning when the knowledge service is unavailable', async () => {
    listSymptoms.mockResolvedValue(SYMPTOMS);
    analyzeDiagnosis.mockResolvedValue(makeResult({ status: 'knowledge_service_error', candidates: [] }));
    const user = userEvent.setup();
    renderWithProviders(<DiagnosisWizard />, { store: createStoreWithExpertise('beginner') });

    const symptom = await screen.findByTestId('symptom-webbing_on_leaves');
    await user.click(symptom.querySelector('input')!);
    await user.click(screen.getByTestId('diagnosis-next-context'));
    await user.click(screen.getByTestId('diagnosis-analyze'));

    expect(await screen.findByTestId('diagnosis-empty-result')).toBeTruthy();
  });

  it('surfaces an error alert when the analyse call fails', async () => {
    listSymptoms.mockResolvedValue(SYMPTOMS);
    analyzeDiagnosis.mockRejectedValue(new Error('boom'));
    const user = userEvent.setup();
    renderWithProviders(<DiagnosisWizard />, { store: createStoreWithExpertise('beginner') });

    const symptom = await screen.findByTestId('symptom-webbing_on_leaves');
    await user.click(symptom.querySelector('input')!);
    await user.click(screen.getByTestId('diagnosis-next-context'));
    await user.click(screen.getByTestId('diagnosis-analyze'));

    expect(await screen.findByTestId('diagnosis-analyze-error')).toBeTruthy();
  });

  it('degrades to a warning when the symptom catalogue fails to load', async () => {
    listSymptoms.mockRejectedValue(new Error('offline'));
    renderWithProviders(<DiagnosisWizard />, { store: createStoreWithExpertise('beginner') });

    await waitFor(() => expect(listSymptoms).toHaveBeenCalled());
    expect(await screen.findByTestId('diagnosis-load-error')).toBeTruthy();
  });
});
