/**
 * REQ-053 W-015 — the thinning dialog: the run's spacing and the count it gives, the grower's own spacing or count,
 * and no default when the run has no spacing (E-10).
 */
import { cleanup, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { http, HttpResponse } from 'msw';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { expectNoA11yViolations } from '@/test/a11y/expectNoA11yViolations';
import { authState, createTestStore, renderWithProviders, tenantState } from '@/test/helpers';
import { server } from '@/test/mocks/server';
import { BASE } from './plantingTestKit';
import type { ThinningPlan } from './plantingTypes';
import ThinningDialog from './ThinningDialog';

function plan(overrides: Partial<ThinningPlan> = {}): ThinningPlan {
  return {
    slot_key: 'r1',
    slot_id: 'BED_R01',
    slot_role: 'row',
    sown_at: '2026-04-12',
    run_key: 'run_1',
    entry_key: 'e_1',
    species_key: 'sp_carrot',
    measure_kind: 'length',
    measure_value: 1.2,
    thinning_to_cm: 5,
    suggested_count: 24,
    max_count: 500,
    ...overrides,
  };
}

function useBackend(answer: ThinningPlan) {
  const posts: unknown[] = [];
  server.use(
    http.get(`${BASE}/slots/:key/thinning`, () => HttpResponse.json(answer)),
    http.post(`${BASE}/slots/:key/thinning`, async ({ request }) => {
      const body = await request.json();
      posts.push(body);
      return HttpResponse.json({ plant_keys: ['p1', 'p2'], instance_ids: ['A', 'B'], care_event_key: 'ce1' }, { status: 201 });
    }),
  );
  return posts;
}

function renderDialog(onThinned = vi.fn()) {
  renderWithProviders(
    <ThinningDialog slotKey="r1" slotLabel="BED_R01" speciesName="Carrot" onClose={vi.fn()} onThinned={onThinned} />,
    { store: createTestStore({ ...tenantState('grower'), ...authState() }) },
  );
  return onThinned;
}

afterEach(() => cleanup());

describe('ThinningDialog', () => {
  it("takes the run's spacing and shows the count it gives", async () => {
    const posts = useBackend(plan());
    const user = userEvent.setup();
    const onThinned = renderDialog();

    expect(await screen.findByTestId('thinning-spacing')).toHaveValue(5);
    expect(screen.getByTestId('thinning-result')).toHaveTextContent('24');
    await user.click(screen.getByTestId('thinning-submit'));

    await waitFor(() => expect(onThinned).toHaveBeenCalled());
    expect(posts).toEqual([{ thinning_to_cm: 5, planted_on: expect.any(String) }]);
  });

  it('recounts when the grower thinned wider', async () => {
    useBackend(plan());
    const user = userEvent.setup();
    renderDialog();
    const spacing = await screen.findByTestId('thinning-spacing');
    await user.clear(spacing);
    await user.type(spacing, '10');
    expect(screen.getByTestId('thinning-result')).toHaveTextContent('12');
  });

  it('asks for a spacing when the run has none and sends nothing without one', async () => {
    const posts = useBackend(plan({ thinning_to_cm: null, suggested_count: null }));
    const user = userEvent.setup();
    renderDialog();

    expect(await screen.findByTestId('thinning-no-spacing')).toBeInTheDocument();
    expect(screen.getByTestId('thinning-spacing')).toHaveValue(null);
    expect(screen.queryByTestId('thinning-result')).toBeNull();
    await user.click(screen.getByTestId('thinning-submit'));

    expect(await screen.findByTestId('thinning-missing')).toBeInTheDocument();
    expect(posts).toEqual([]);
  });

  it("sends the grower's count instead of a spacing", async () => {
    const posts = useBackend(plan({ thinning_to_cm: null, suggested_count: null }));
    const user = userEvent.setup();
    const onThinned = renderDialog();
    await user.type(await screen.findByTestId('thinning-count'), '7');
    await user.click(screen.getByTestId('thinning-submit'));

    await waitFor(() => expect(onThinned).toHaveBeenCalled());
    expect(posts).toEqual([{ count: 7, planted_on: expect.any(String) }]);
  });

  it('has no accessibility violations', async () => {
    useBackend(plan());
    renderDialog();
    await screen.findByTestId('thinning-result');
    await expectNoA11yViolations(screen.getByTestId('thinning-dialog'));
  });
});
