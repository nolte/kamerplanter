import { describe, it, expect, vi, beforeEach } from 'vitest';
import { screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { renderWithProviders, createStoreWithTenantRole } from '@/test/helpers';
import type { AiTipCard } from '@/api/types';

const getTips = vi.fn();
const refreshTips = vi.fn();

vi.mock('@/api', () => ({
  aiApi: {
    getTips: (...args: unknown[]) => getTips(...args),
    refreshTips: (...args: unknown[]) => refreshTips(...args),
  },
}));

import TipCardsPanel from '@/components/ai/TipCardsPanel';

/** The list response shape the read now answers with (#1461). */
function makeResponse(tips: AiTipCard[], refreshAvailable = true) {
  return { tips, refresh_available: refreshAvailable };
}

function makeTip(overrides: Partial<AiTipCard> = {}): AiTipCard {
  return {
    key: 'tip-1',
    context_type: 'planting_run',
    context_key: 'run-1',
    tip_type: 'care',
    priority: 'medium',
    title: 'Check the EC',
    body: 'The nutrient concentration is slightly high.',
    sources: [],
    language: 'de',
    language_mismatch_warning: false,
    uses_tenant_data: true,
    confidence: 'high',
    model_name: 'gemma3:12b',
    ...overrides,
  };
}

describe('TipCardsPanel', () => {
  beforeEach(() => {
    getTips.mockReset();
    refreshTips.mockReset();
  });

  it('renders tip cards wrapped in AIResponse', async () => {
    getTips.mockResolvedValue(makeResponse([makeTip()]));
renderWithProviders(<TipCardsPanel contextType="planting_run" contextKey="run-1" />, {
      store: createStoreWithTenantRole('grower'),
    });

    expect(await screen.findByTestId('tip-cards-panel')).toBeTruthy();
    expect(screen.getByText('Check the EC')).toBeTruthy();
    expect(screen.getByTestId('ai-badge')).toBeTruthy();
  });

  it('renders nothing when there are no tips and the caller cannot generate any', async () => {
    getTips.mockResolvedValue(makeResponse([], false));
renderWithProviders(<TipCardsPanel contextType="planting_run" contextKey="run-1" />, {
      store: createStoreWithTenantRole('viewer'),
    });

    await waitFor(() => expect(getTips).toHaveBeenCalled());
    expect(screen.queryByTestId('tip-cards-panel')).toBeNull();
  });

  it('invites a grower to generate when there are no tips yet', async () => {
    // #1461 — the read stopped generating on a cache miss, so an empty list is
    // now the normal first answer. Without this invitation a grower would never
    // discover that tips exist: the panel used to render nothing and the refresh
    // control lived inside it.
    getTips.mockResolvedValue(makeResponse([]));
    refreshTips.mockResolvedValue(makeResponse([makeTip({ title: 'Generated tip' })]));
    const user = userEvent.setup();
    renderWithProviders(<TipCardsPanel contextType="planting_run" contextKey="run-1" />, {
      store: createStoreWithTenantRole('grower'),
    });

    expect(await screen.findByTestId('tip-cards-empty')).toBeTruthy();
    await user.click(screen.getByTestId('tip-cards-generate'));

    await waitFor(() => expect(refreshTips).toHaveBeenCalled());
    expect(await screen.findByText('Generated tip')).toBeTruthy();
    expect(screen.queryByTestId('tip-cards-empty')).toBeNull();
  });

  it('offers no generate control when the server says the caller may not', async () => {
    // Both predicates have to agree. The client's `canEdit` is a rank copy and
    // the server's `refresh_available` is the authority; an older backend sends
    // no flag at all, which is why the client keeps its own check too.
    //
    // Review SCR-006 called this fixture server-side impossible for a grower, and
    // measured against the mounted router it is *currently* right: the KI toggle
    // 403s the read before the flag is computed, so a grower who reaches a 200
    // always sees `true`. It is kept as the guard for the direction that matters
    // — if the flag ever narrows (a per-feature toggle, a quota), the client must
    // obey it rather than fall back to its rank copy.
    getTips.mockResolvedValue(makeResponse([], false));
    renderWithProviders(<TipCardsPanel contextType="planting_run" contextKey="run-1" />, {
      store: createStoreWithTenantRole('grower'),
    });

    await waitFor(() => expect(getTips).toHaveBeenCalled());
    expect(screen.queryByTestId('tip-cards-generate')).toBeNull();
    expect(screen.queryByTestId('tip-cards-panel')).toBeNull();
  });

  it('says so when a generate attempt is refused', async () => {
    // Review SCR-003 — the `catch` kept the tips (right) and said nothing
    // (wrong). In the empty state that is total silence: the invitation is there,
    // the click is refused, and nothing on the page changes.
    getTips.mockResolvedValue(makeResponse([]));
    refreshTips.mockRejectedValue(new Error('refused'));
    const user = userEvent.setup();
    renderWithProviders(<TipCardsPanel contextType="planting_run" contextKey="run-1" />, {
      store: createStoreWithTenantRole('grower'),
    });

    await user.click(await screen.findByTestId('tip-cards-generate'));

    expect(await screen.findByTestId('tip-cards-refresh-error')).toBeTruthy();
    // The invitation text is replaced rather than stacked with the error.
    expect(screen.queryByTestId('tip-cards-empty')).toBeNull();
    // And the control invites a retry rather than repeating the first label.
    expect(screen.getByTestId('tip-cards-generate')).toBeTruthy();
  });

  it('keeps the cards AND reports the failure when a refresh over content fails', async () => {
    // The read surface survives — that is what the `catch` is for — but the user
    // is told why nothing changed.
    getTips.mockResolvedValue(makeResponse([makeTip({ title: 'Readable tip' })]));
    refreshTips.mockRejectedValue(new Error('refused'));
    const user = userEvent.setup();
    renderWithProviders(<TipCardsPanel contextType="plant_instance" contextKey="p-1" />, {
      store: createStoreWithTenantRole('grower'),
    });

    await screen.findByText('Readable tip');
    await user.click(screen.getByTestId('tip-cards-refresh'));

    expect(await screen.findByTestId('tip-cards-refresh-error')).toBeTruthy();
    expect(screen.getByText('Readable tip')).toBeTruthy();
  });

  it('explains a disabled-AI refusal instead of showing a generic failure', async () => {
    // `resolveAiErrorMessage` maps the two stable REQ-031 codes; without it the
    // user reads "could not be generated" over a feature an admin can switch on.
    const { ApiError } = await import('@/api/errors');
    getTips.mockResolvedValue(makeResponse([]));
    refreshTips.mockRejectedValue(
      new ApiError(
        {
          error_id: 'err-1',
          timestamp: '2026-09-18T00:00:00Z',
          error_code: 'AI_DISABLED_FOR_TENANT',
          message: 'forbidden',
          details: [],
          path: '/ai/tips/refresh',
          method: 'POST',
        },
        403,
      ),
    );
    const user = userEvent.setup();
    renderWithProviders(<TipCardsPanel contextType="planting_run" contextKey="run-1" />, {
      store: createStoreWithTenantRole('grower'),
    });

    await user.click(await screen.findByTestId('tip-cards-generate'));

    const error = await screen.findByTestId('tip-cards-refresh-error');
    expect(error.textContent).toContain('disabled');
  });

  it('force-refreshes tips via the refresh button', async () => {
    getTips.mockResolvedValue(makeResponse([makeTip()]));
    refreshTips.mockResolvedValue(makeResponse([makeTip({ title: 'Refreshed tip' })]));
    const user = userEvent.setup();
renderWithProviders(<TipCardsPanel contextType="planting_run" contextKey="run-1" />, {
      store: createStoreWithTenantRole('grower'),
    });

    await screen.findByTestId('tip-cards-panel');
    await user.click(screen.getByTestId('tip-cards-refresh'));

    await waitFor(() => expect(refreshTips).toHaveBeenCalled());
    expect(await screen.findByText('Refreshed tip')).toBeTruthy();
  });

  it('degrades to nothing on a fetch error', async () => {
    getTips.mockRejectedValue(new Error('offline'));
renderWithProviders(<TipCardsPanel contextType="plant_instance" contextKey="p-1" />, {
      store: createStoreWithTenantRole('grower'),
    });

    await waitFor(() => expect(getTips).toHaveBeenCalled());
    expect(screen.queryByTestId('tip-cards-panel')).toBeNull();
  });

  it('offers a viewer no refresh control', async () => {
    // Regenerating tips is a write on the server since #1353
    // (`require_tenant_role(grower)`), so a viewer's click would answer 403. A
    // control that looks live and is refused is the #1339 class; it is absent.
    //
    // `refresh_available: false` is what the server really sends a viewer: the
    // flag is `meets_tenant_role(ctx.role, GROWER)` (review SCR-006 checked that
    // a grower can never receive `false` — the KI toggle refuses the whole read
    // before the flag is computed, so rank is the only axis left).
    getTips.mockResolvedValue(makeResponse([makeTip({ title: 'Readable tip' })], false));
    renderWithProviders(<TipCardsPanel contextType="plant_instance" contextKey="p-1" />, {
      store: createStoreWithTenantRole('viewer'),
    });

    // The panel itself is a read surface and stays — asserted first, so the
    // absence below cannot be satisfied by a page that rendered nothing.
    expect(await screen.findByText('Readable tip')).toBeTruthy();
    expect(screen.queryByTestId('tip-cards-refresh')).toBeNull();
  });

  it('keeps the readable tips when a forced refresh fails', async () => {
    // The initial load hiding the panel is deliberate (UI-NFR-012, online-only).
    // A *failed refresh* is not the same case: the panel already holds tips the
    // reader may see, and clearing them turns a failed regeneration into the loss
    // of the read surface too.
    getTips.mockResolvedValue(makeResponse([makeTip({ title: 'Readable tip' })]));
    refreshTips.mockRejectedValue(new Error('refused'));
    const user = userEvent.setup();
    renderWithProviders(<TipCardsPanel contextType="plant_instance" contextKey="p-1" />, {
      store: createStoreWithTenantRole('grower'),
    });

    expect(await screen.findByText('Readable tip')).toBeTruthy();
    await user.click(screen.getByTestId('tip-cards-refresh'));

    await waitFor(() => expect(refreshTips).toHaveBeenCalled());
    expect(screen.getByTestId('tip-cards-panel')).toBeTruthy();
    expect(screen.getByText('Readable tip')).toBeTruthy();
  });
});

describe('TipCardsPanel — action_url is not an open href (#1460 review SCR-012)', () => {
  beforeEach(() => {
    getTips.mockReset();
    refreshTips.mockReset();
  });

  it.each([
    ['javascript:alert(1)'],
    ['https://evil.example/phish'],
    ['//evil.example/phish'],
    ['data:text/html,<script>alert(1)</script>'],
  ])('renders no "learn more" link for %s', async (actionUrl) => {
    getTips.mockResolvedValue(makeResponse([makeTip({ action_url: actionUrl })]));
    renderWithProviders(<TipCardsPanel contextType="planting_run" contextKey="run-1" />, {
      store: createStoreWithTenantRole('grower'),
    });

    // The card itself renders — asserted first, so the absence below cannot be
    // satisfied by a panel that failed to render at all.
    expect(await screen.findByText('Check the EC')).toBeTruthy();
    expect(screen.queryByRole('link', { name: /learn more/i })).toBeNull();
  });

  it('renders the link for a site-relative path — the control', async () => {
    getTips.mockResolvedValue(makeResponse([makeTip({ action_url: '/pflanzen/p-1' })]));
    renderWithProviders(<TipCardsPanel contextType="planting_run" contextKey="run-1" />, {
      store: createStoreWithTenantRole('grower'),
    });

    const link = await screen.findByRole('link', { name: /learn more/i });
    expect(link.getAttribute('href')).toBe('/pflanzen/p-1');
  });
});

describe('isSiteRelative', () => {
  it('accepts a path and refuses every absolute form', async () => {
    const { isSiteRelative } = await import('@/components/ai/TipCardsPanel');

    expect(isSiteRelative('/pflanzen/1')).toBe(true);
    expect(isSiteRelative('//evil.example')).toBe(false);
    expect(isSiteRelative('https://evil.example')).toBe(false);
    expect(isSiteRelative('javascript:alert(1)')).toBe(false);
    expect(isSiteRelative(null)).toBe(false);
    expect(isSiteRelative(undefined)).toBe(false);
    expect(isSiteRelative('')).toBe(false);
  });
});
