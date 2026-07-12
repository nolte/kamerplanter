import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { screen, waitFor, cleanup } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { renderWithProviders } from '@/test/helpers';
import type { GlossaryTermAnswer } from '@/api/types';

vi.mock('@/api', () => ({
  glossaryApi: {
    getTerm: vi.fn(),
    listTerms: vi.fn(),
  },
}));

import { glossaryApi } from '@/api';
import TermTooltip from '@/components/glossary/TermTooltip';
import { clearGlossaryCache } from '@/hooks/useGlossaryTerm';

const getTerm = vi.mocked(glossaryApi.getTerm);

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

describe('TermTooltip', () => {
  beforeEach(() => {
    clearGlossaryCache();
    getTerm.mockReset();
  });
  afterEach(() => cleanup());

  it('renders the trigger with its label', () => {
    renderWithProviders(<TermTooltip slug="vpd">VPD</TermTooltip>);
    expect(screen.getByTestId('term-tooltip-trigger-vpd')).toBeTruthy();
  });

  it('opens the popover and loads the explanation on click', async () => {
    getTerm.mockResolvedValue(answer());
    const user = userEvent.setup();
    renderWithProviders(<TermTooltip slug="vpd">VPD</TermTooltip>);

    await user.click(screen.getByTestId('term-tooltip-trigger-vpd'));

    await waitFor(() => expect(getTerm).toHaveBeenCalledWith('vpd', 'beginner', 'en'));
    expect(await screen.findByText(/thirsty the air/)).toBeTruthy();
    // Rendered through the mandatory AIResponse shell.
    expect(screen.getByTestId('ai-badge')).toBeTruthy();
  });

  it('shows the fallback hint for an editorial fallback answer', async () => {
    getTerm.mockResolvedValue(answer({ is_fallback: true }));
    const user = userEvent.setup();
    renderWithProviders(<TermTooltip slug="vpd">VPD</TermTooltip>);

    await user.click(screen.getByTestId('term-tooltip-trigger-vpd'));
    expect(await screen.findByTestId('term-tooltip-fallback-hint')).toBeTruthy();
  });

  it('navigates to a related term and back via the stack', async () => {
    getTerm.mockImplementation(async (slug: string) =>
      slug === 'vpd'
        ? answer({ related_terms: [{ slug: 'transpiration', label: 'Transpiration' }] })
        : answer({ slug: 'transpiration', label: 'Transpiration', long_label: 'Transpiration', answer_text: 'Water loss.' }),
    );
    const user = userEvent.setup();
    renderWithProviders(<TermTooltip slug="vpd">VPD</TermTooltip>);

    await user.click(screen.getByTestId('term-tooltip-trigger-vpd'));
    const relatedChip = await screen.findByTestId('term-tooltip-related-transpiration');
    await user.click(relatedChip);

    // Stack pushed → the related term is fetched and a back button appears.
    await waitFor(() => expect(getTerm).toHaveBeenCalledWith('transpiration', 'beginner', 'en'));
    expect(await screen.findByText(/Water loss/)).toBeTruthy();
    const back = screen.getByTestId('term-tooltip-back');
    await user.click(back);
    expect(await screen.findByText(/thirsty the air/)).toBeTruthy();
  });

  it('shows an error message when the fetch fails', async () => {
    getTerm.mockRejectedValue(new Error('down'));
    const user = userEvent.setup();
    renderWithProviders(<TermTooltip slug="vpd">VPD</TermTooltip>);

    await user.click(screen.getByTestId('term-tooltip-trigger-vpd'));
    expect(await screen.findByTestId('term-tooltip-error')).toBeTruthy();
    expect(screen.queryByTestId('ai-badge')).toBeNull();
  });
});
