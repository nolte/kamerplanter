import { describe, it, expect, vi } from 'vitest';
import { screen } from '@testing-library/react';
import { renderWithProviders, createStoreWithExpertise } from '@/test/helpers';

const listSymptoms = vi.fn().mockResolvedValue([]);
const analyzeDiagnosis = vi.fn();

vi.mock('@/api', () => ({
  diagnoseApi: {
    listSymptoms: (...args: unknown[]) => listSymptoms(...args),
    analyzeDiagnosis: (...args: unknown[]) => analyzeDiagnosis(...args),
  },
}));

import DiagnosePage from '@/pages/ki-diagnose/DiagnosePage';

describe('DiagnosePage', () => {
  it('renders the page title and hosts the diagnosis wizard', () => {
    renderWithProviders(<DiagnosePage />, { store: createStoreWithExpertise('intermediate') });

    expect(screen.getByTestId('diagnose-page')).toBeTruthy();
    expect(screen.getByTestId('diagnosis-wizard')).toBeTruthy();
  });
});
