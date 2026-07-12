import { describe, it, expect } from 'vitest';
import { screen } from '@testing-library/react';
import { renderWithProviders, createStoreWithExpertise } from '@/test/helpers';
import DiagnosisResultsPanel from '@/components/diagnosis/DiagnosisResultsPanel';
import type { DiagnosisResult } from '@/api/types';

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
        explanation: 'Fine webbing on the leaves indicates spider mites.',
        recommended_actions: ['Increase humidity', 'Isolate the plant'],
        matched_pest_key: 'pest-1',
        matched_pest_detail_url: '/pflanzenschutz/pests/pest-1',
        matched_disease_key: null,
        matched_disease_detail_url: null,
        matched_treatments: [
          {
            key: 't-2',
            name: 'Pyrethrin',
            name_de: 'Pyrethrin',
            treatment_type: 'chemical',
            safety_interval_days: 3,
            has_karenz: true,
            detail_url: '/pflanzenschutz/treatments/t-2',
          },
        ],
      },
    ],
    answer_summary: 'Fine webbing on the leaves indicates spider mites.',
    sources: [{ source_key: 's1', source_type: 'rag', title: 'Spider mite care', score: 0.9, language: 'de' }],
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

describe('DiagnosisResultsPanel', () => {
  it('renders the top candidate inside the AIResponse shell', () => {
    renderWithProviders(<DiagnosisResultsPanel result={makeResult()} />, {
      store: createStoreWithExpertise('intermediate'),
    });

    expect(screen.getByTestId('diagnosis-results')).toBeTruthy();
    // Mandatory KI labeling from the shell.
    expect(screen.getByTestId('ai-badge')).toBeTruthy();
    expect(screen.getByTestId('diagnosis-candidate-1')).toBeTruthy();
    expect(screen.getByText('Spider mites')).toBeTruthy();
    expect(screen.getByTestId('diagnosis-confidence-1').textContent).toContain('85');
  });

  it('deep-links the matched pest and treatment', () => {
    renderWithProviders(<DiagnosisResultsPanel result={makeResult()} />, {
      store: createStoreWithExpertise('intermediate'),
    });

    const pestLink = screen.getByTestId('diagnosis-pest-link-1') as HTMLAnchorElement;
    expect(pestLink.getAttribute('href')).toBe('/pflanzenschutz/pests/pest-1');
    const treatment = screen.getByTestId('diagnosis-treatment-t-2') as HTMLAnchorElement;
    expect(treatment.getAttribute('href')).toBe('/pflanzenschutz/treatments/t-2');
    // Karenz treatments carry the waiting-period hint in their label.
    expect(treatment.textContent).toContain('3');
  });

  it('lists the recommended actions', () => {
    renderWithProviders(<DiagnosisResultsPanel result={makeResult()} />, {
      store: createStoreWithExpertise('beginner'),
    });
    expect(screen.getByText('Increase humidity')).toBeTruthy();
    expect(screen.getByText('Isolate the plant')).toBeTruthy();
  });
});
