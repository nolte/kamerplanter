import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { screen, waitFor, cleanup } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { renderWithProviders, createStoreWithTenantRole } from '@/test/helpers';
import type { GlossaryTermAnswer, GlossaryTermSummary } from '@/api/types';

vi.mock('@/api', () => ({
  glossaryApi: {
    listTerms: vi.fn(),
    getTerm: vi.fn(),
    generateTerm: vi.fn(),
  },
}));

import { glossaryApi } from '@/api';
import GlossaryPage from '@/pages/glossar/GlossaryPage';
import { clearGlossaryCache } from '@/hooks/useGlossaryTerm';

const listTerms = vi.mocked(glossaryApi.listTerms);
const getTerm = vi.mocked(glossaryApi.getTerm);
const generateTerm = vi.mocked(glossaryApi.generateTerm);

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
    generateTerm.mockReset();
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

describe('GlossaryPage — generating a detailed explanation (#1460)', () => {
  beforeEach(() => {
    clearGlossaryCache();
    listTerms.mockReset();
    getTerm.mockReset();
    generateTerm.mockReset();
  });
  afterEach(() => cleanup());

  it('offers a grower the generate control on a fallback answer', async () => {
    // Reading a term no longer produces its detailed explanation, so a fallback
    // answer stays one until somebody asks. Without this control the POST would
    // be unreachable from the product.
    listTerms.mockResolvedValue(TERMS);
    getTerm.mockResolvedValue(answer({ is_fallback: true, answer_text: 'Short definition.' }));
    generateTerm.mockResolvedValue(answer({ answer_text: 'A detailed explanation.' }));
    const user = userEvent.setup();
    renderWithProviders(<GlossaryPage />, {
      route: '/glossar',
      store: createStoreWithTenantRole('grower'),
    });

    await user.click(await screen.findByTestId('glossary-term-vpd'));
    expect(await screen.findByTestId('glossary-detail-fallback-hint')).toBeTruthy();

    await user.click(screen.getByTestId('glossary-detail-generate'));

    // The slug and the expertise level are the load-bearing arguments; the
    // language follows the i18n locale the test harness runs in.
    await waitFor(() => expect(generateTerm).toHaveBeenCalled());
    expect(generateTerm.mock.calls[0][0]).toBe('vpd');
    expect(generateTerm.mock.calls[0][1]).toBe('beginner');
    expect(await screen.findByText('A detailed explanation.')).toBeTruthy();
    expect(screen.queryByTestId('glossary-detail-generate')).toBeNull();
  });

  it('offers a viewer no generate control', async () => {
    // Generating is a write (`require_permission(glossary, create)`); a viewer's
    // click would answer 403, so the control is absent rather than refused.
    listTerms.mockResolvedValue(TERMS);
    getTerm.mockResolvedValue(answer({ is_fallback: true, answer_text: 'Short definition.' }));
    const user = userEvent.setup();
    renderWithProviders(<GlossaryPage />, {
      route: '/glossar',
      store: createStoreWithTenantRole('viewer'),
    });

    await user.click(await screen.findByTestId('glossary-term-vpd'));

    // The read surface is asserted first, so the absence below cannot be
    // satisfied by a detail view that rendered nothing.
    expect(await screen.findByTestId('glossary-detail-fallback-hint')).toBeTruthy();
    expect(screen.queryByTestId('glossary-detail-generate')).toBeNull();
  });

  it('says so when generating is refused', async () => {
    // Review SCR-001 — the hook's empty `catch {}` turned a 403/429/502 into a
    // button that does nothing. The failure is reported inside the detail view's
    // existing `aria-live` region, so it is announced too.
    listTerms.mockResolvedValue(TERMS);
    getTerm.mockResolvedValue(answer({ is_fallback: true, answer_text: 'Short definition.' }));
    generateTerm.mockRejectedValue(new Error('refused'));
    const user = userEvent.setup();
    renderWithProviders(<GlossaryPage />, {
      route: '/glossar',
      store: createStoreWithTenantRole('grower'),
    });

    await user.click(await screen.findByTestId('glossary-term-vpd'));
    await user.click(await screen.findByTestId('glossary-detail-generate'));

    expect(await screen.findByTestId('glossary-detail-generate-error')).toBeTruthy();
    // The curated answer survives the failure — losing the read surface over a
    // refused generation would be the worse outcome.
    expect(screen.getByText('Short definition.')).toBeTruthy();
    expect(screen.getByTestId('glossary-detail-generate')).toBeTruthy();
  });

  it('explains a disabled-AI refusal instead of showing a generic failure', async () => {
    const { ApiError } = await import('@/api/errors');
    listTerms.mockResolvedValue(TERMS);
    getTerm.mockResolvedValue(answer({ is_fallback: true }));
    generateTerm.mockRejectedValue(
      new ApiError(
        {
          error_id: 'err-1',
          timestamp: '2026-09-18T00:00:00Z',
          error_code: 'AI_DISABLED_FOR_TENANT',
          message: 'forbidden',
          details: [],
          path: '/glossary/term/vpd/generate',
          method: 'POST',
        },
        403,
      ),
    );
    const user = userEvent.setup();
    renderWithProviders(<GlossaryPage />, {
      route: '/glossar',
      store: createStoreWithTenantRole('grower'),
    });

    await user.click(await screen.findByTestId('glossary-term-vpd'));
    await user.click(await screen.findByTestId('glossary-detail-generate'));

    const error = await screen.findByTestId('glossary-detail-generate-error');
    expect(error.textContent).toContain('disabled');
  });

  it('does not apply a generated answer to a term the reader has moved on from', async () => {
    // Review SCR-005 — a related-term chip switches the slug while the request is
    // in flight. Applying the answer then shows one term's explanation under
    // another's heading.
    listTerms.mockResolvedValue(TERMS);
    getTerm.mockImplementation((slug: string) =>
      Promise.resolve(
        answer({
          slug,
          long_label: slug === 'vpd' ? 'Vapor Pressure Deficit' : 'Electrical Conductivity',
          answer_text: `Short definition of ${slug}.`,
          is_fallback: true,
          related_terms: [{ slug: 'ec', label: 'EC' }],
        }),
      ),
    );
    let release: (value: GlossaryTermAnswer) => void = () => {};
    generateTerm.mockReturnValue(
      new Promise<GlossaryTermAnswer>((resolve) => {
        release = resolve;
      }),
    );
    const user = userEvent.setup();
    renderWithProviders(<GlossaryPage />, {
      route: '/glossar',
      store: createStoreWithTenantRole('grower'),
    });

    await user.click(await screen.findByTestId('glossary-term-vpd'));
    await user.click(await screen.findByTestId('glossary-detail-generate'));
    // Move to the related term while the generation is still in flight.
    await user.click(await screen.findByTestId('glossary-detail-related-ec'));
    await screen.findByText('Short definition of ec.');

    release(answer({ slug: 'vpd', answer_text: 'A detailed VPD explanation.' }));

    await waitFor(() => expect(screen.getByText('Short definition of ec.')).toBeTruthy());
    expect(screen.queryByText('A detailed VPD explanation.')).toBeNull();
  });

  it('moves focus to the answer when the generate button disappears', async () => {
    // Review SCR-010 — a successful generate unmounts the control the user just
    // pressed, so keyboard focus would fall back to <body> and a screen-reader
    // user would lose their place mid-task.
    listTerms.mockResolvedValue(TERMS);
    getTerm.mockResolvedValue(answer({ is_fallback: true, answer_text: 'Short definition.' }));
    generateTerm.mockResolvedValue(answer({ answer_text: 'A detailed explanation.' }));
    const user = userEvent.setup();
    renderWithProviders(<GlossaryPage />, {
      route: '/glossar',
      store: createStoreWithTenantRole('grower'),
    });

    await user.click(await screen.findByTestId('glossary-term-vpd'));
    await user.click(await screen.findByTestId('glossary-detail-generate'));

    await waitFor(() =>
      expect(document.activeElement).toBe(screen.getByTestId('glossary-detail-heading')),
    );
  });

  it('offers no generate control once a detailed explanation exists', async () => {
    listTerms.mockResolvedValue(TERMS);
    getTerm.mockResolvedValue(answer({ is_fallback: false }));
    const user = userEvent.setup();
    renderWithProviders(<GlossaryPage />, {
      route: '/glossar',
      store: createStoreWithTenantRole('grower'),
    });

    await user.click(await screen.findByTestId('glossary-term-vpd'));

    expect(await screen.findByTestId('glossary-detail-response')).toBeTruthy();
    expect(screen.queryByTestId('glossary-detail-generate')).toBeNull();
  });
});
