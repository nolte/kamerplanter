import { describe, it, expect, afterEach } from 'vitest';
import { screen, cleanup } from '@testing-library/react';
import Typography from '@mui/material/Typography';
import AIResponse from '@/components/ai/AIResponse';
import { renderWithProviders, createStoreWithExpertise } from '@/test/helpers';
import type { AiSourceRef } from '@/api/types';

const SOURCES: AiSourceRef[] = [
  { source_key: 'umwelt/vpd', source_type: 'rag', title: 'VPD Grundlagen', score: 0.91, language: 'de' },
];

describe('AIResponse', () => {
  afterEach(() => cleanup());

  it('always renders the AI badge and disclaimer', () => {
    renderWithProviders(
      <AIResponse>
        <Typography>Antwort</Typography>
      </AIResponse>,
    );
    expect(screen.getByTestId('ai-badge')).toBeTruthy();
    expect(screen.getByText('Antwort')).toBeTruthy();
  });

  it('hides the "general information" badge for high confidence', () => {
    renderWithProviders(
      <AIResponse confidence="high">
        <span>x</span>
      </AIResponse>,
    );
    expect(screen.queryByTestId('ai-confidence-badge')).toBeNull();
  });

  it('shows the "general information" badge for low confidence', () => {
    renderWithProviders(
      <AIResponse confidence="low" cultivarHint="Meine Tomate" fallbackSpecies="Solanum sp.">
        <span>x</span>
      </AIResponse>,
    );
    expect(screen.getByTestId('ai-confidence-badge')).toBeTruthy();
  });

  it('hides the tenant-data indicator when usesTenantData is false', () => {
    renderWithProviders(
      <AIResponse usesTenantData={false}>
        <span>x</span>
      </AIResponse>,
    );
    expect(screen.queryByTestId('ai-tenant-data-indicator')).toBeNull();
  });

  it('shows the tenant-data indicator when usesTenantData is true', () => {
    renderWithProviders(
      <AIResponse usesTenantData>
        <span>x</span>
      </AIResponse>,
    );
    expect(screen.getByTestId('ai-tenant-data-indicator')).toBeTruthy();
  });

  it('shows the cloud indicator when usesCloudProvider is true', () => {
    renderWithProviders(
      <AIResponse usesCloudProvider providerType="anthropic">
        <span>x</span>
      </AIResponse>,
    );
    expect(screen.getByTestId('ai-cloud-indicator')).toBeTruthy();
  });

  it('renders the language mismatch hint when flagged', () => {
    renderWithProviders(
      <AIResponse languageMismatchWarning>
        <span>x</span>
      </AIResponse>,
    );
    expect(screen.getByTestId('ai-language-warning')).toBeTruthy();
  });

  it('renders the sources accordion with each source', () => {
    renderWithProviders(
      <AIResponse sources={SOURCES}>
        <span>x</span>
      </AIResponse>,
    );
    expect(screen.getByTestId('ai-sources')).toBeTruthy();
    expect(screen.getByText(/VPD Grundlagen/)).toBeTruthy();
  });

  it('expands sources by default for expert users', () => {
    renderWithProviders(
      <AIResponse sources={SOURCES}>
        <span>x</span>
      </AIResponse>,
      { store: createStoreWithExpertise('expert') },
    );
    // The source item is visible without expanding when default-expanded.
    expect(screen.getByTestId('ai-source-item')).toBeTruthy();
  });
});
