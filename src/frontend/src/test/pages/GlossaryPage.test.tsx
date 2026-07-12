import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { screen, waitFor, cleanup } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { renderWithProviders } from '@/test/helpers';
import type { GlossaryTermAnswer, GlossaryTermSummary } from '@/api/types';

vi.mock('@/api', () => ({
  glossaryApi: {
    listTerms: vi.fn(),
    getTerm: vi.fn(),
  },
}));

import { glossaryApi } from '@/api';
import GlossaryPage from '@/pages/glossar/GlossaryPage';
import { clearGlossaryCache } from '@/hooks/useGlossaryTerm';

const listTerms = vi.mocked(glossaryApi.listTerms);
const getTerm = vi.mocked(glossaryApi.getTerm);

const TERMS: GlossaryTermSummary[] = [
  { slug: 'vpd', label: 'VPD', category: 'umwelt' },
  { slug: 'ec', label: 'EC', category: 'duengung' },
];

function answer(overrides: Partial<GlossaryTermAnswer> = {}): GlossaryTermAnswer {
  return {
    slug: 'vpd',
    label: 'VPD',
    long_label: 'Vapor Pressure Deficit',
    category: 'umwelt',
    answer_text: 'VPD describes how thirsty the air is.',
    expertise_level: 'beginner',
    language: 'de',
    language_mismatch_warning: false,
    sources: [],
    related_terms: [],
    is_fallback: false,
    model_name: 'gemma3:12b',
    provider_type: 'ollama',
    uses_tenant_data: false,
    uses_cloud_provider: false,
    ...overrides,
  };
}

describe('GlossaryPage', () => {
  beforeEach(() => {
    clearGlossaryCache();
    listTerms.mockReset();
    getTerm.mockReset();
  });
  afterEach(() => cleanup());

  it('renders the title and lists terms grouped by category', async () => {
    listTerms.mockResolvedValue(TERMS);
    renderWithProviders(<GlossaryPage />, { route: '/glossar' });

    expect(await screen.findByText('Terminology glossary')).toBeTruthy();
    expect(await screen.findByTestId('glossary-term-vpd')).toBeTruthy();
    expect(screen.getByTestId('glossary-term-ec')).toBeTruthy();
    expect(screen.getByTestId('glossary-category-umwelt')).toBeTruthy();
  });

  it('opens the detail view for a selected term and returns via back', async () => {
    listTerms.mockResolvedValue(TERMS);
    getTerm.mockResolvedValue(answer());
    const user = userEvent.setup();
    renderWithProviders(<GlossaryPage />, { route: '/glossar' });

    await user.click(await screen.findByTestId('glossary-term-vpd'));

    await waitFor(() => expect(getTerm).toHaveBeenCalledWith('vpd', 'beginner', 'en'));
    expect(await screen.findByTestId('glossary-detail')).toBeTruthy();
    expect(screen.getByText(/thirsty the air/)).toBeTruthy();
    expect(screen.getByTestId('ai-badge')).toBeTruthy();

    await user.click(screen.getByTestId('glossary-detail-back'));
    expect(await screen.findByTestId('glossary-term-vpd')).toBeTruthy();
  });

  it('shows the empty state when there are no terms', async () => {
    listTerms.mockResolvedValue([]);
    renderWithProviders(<GlossaryPage />, { route: '/glossar' });

    expect(await screen.findByText('No terms are available yet.')).toBeTruthy();
  });

  it('shows a load-error state when the list fails', async () => {
    listTerms.mockRejectedValue(new Error('down'));
    renderWithProviders(<GlossaryPage />, { route: '/glossar' });

    expect(
      await screen.findByText('The term list could not be loaded. Please try again later.'),
    ).toBeTruthy();
  });
});
