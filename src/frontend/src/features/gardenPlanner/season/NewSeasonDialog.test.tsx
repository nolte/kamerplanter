/**
 * The new-season dialog (REQ-053 GP-FR-171, WP 7.17): year, check report, confirmation, the optional "Here stood"
 * hint. The server decides every answer; pinned here is what the person is shown and which requests that sends.
 */
import { cleanup, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { http, HttpResponse } from 'msw';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { expectNoA11yViolations } from '@/test/a11y/expectNoA11yViolations';
import { authState, createTestStore, renderWithProviders, tenantState } from '@/test/helpers';
import { server } from '@/test/mocks/server';
import NewSeasonDialog from './NewSeasonDialog';
import type { SeasonReport } from './seasonTypes';

const BASE = '/api/v1/t/:tenant';
const YEAR = new Date().getFullYear() + 1;

function report(overrides: Partial<SeasonReport> = {}): SeasonReport {
  return {
    year: YEAR,
    source_year: YEAR - 1,
    dry_run: true,
    applied: false,
    plan_revision: 7,
    beds_copied: 1,
    beds_skipped: 1,
    slots_to_create: 12,
    beds: [
      { location_key: 'b1', status: 'copied', slots: 12, slots_outside_bed: 0 },
      { location_key: 'b2', status: 'skipped_active_plants', slots: 0, slots_outside_bed: 0 },
    ],
    ...overrides,
  };
}

function useBackend(
  bodies: Record<string, unknown>[],
  answer: (body: Record<string, unknown>) => Response | SeasonReport,
) {
  server.use(
    http.post(`${BASE}/sites/s1/plan/new-season`, async ({ request }) => {
      const body = (await request.json()) as Record<string, unknown>;
      bodies.push(body);
      const out = answer(body);
      return out instanceof Response ? out : HttpResponse.json(out);
    }),
  );
}

function renderDialog(onApplied = vi.fn(), onClose = vi.fn()) {
  const store = createTestStore({ ...tenantState('lead'), ...authState() });
  renderWithProviders(
    <NewSeasonDialog
      open
      siteKey="s1"
      bedNames={{ b1: 'Beet Nord', b2: 'Beet Süd' }}
      onClose={onClose}
      onApplied={onApplied}
    />,
    { store },
  );
  return userEvent.setup();
}

afterEach(() => cleanup());

describe('NewSeasonDialog', () => {
  it('checks first and names what is created and what is skipped, by bed name', async () => {
    const bodies: Record<string, unknown>[] = [];
    useBackend(bodies, () => report());
    const user = renderDialog();

    expect(screen.getByTestId('plan-season-confirm')).toBeDisabled();
    await user.click(screen.getByTestId('plan-season-check'));

    const view = await screen.findByTestId('plan-season-report');
    expect(within(view).getByText('12 free slots in 1 beds will be created.')).toBeInTheDocument();
    expect(within(view).getByText(/Beet Nord: 12 free slots/)).toBeInTheDocument();
    expect(
      within(view).getByText(/Beet Süd: skipped, active plants stand in it/),
    ).toBeInTheDocument();
    expect(bodies).toEqual([{ year: YEAR, dry_run: true, expected_revision: null }]);
    expect(screen.getByTestId('plan-season-confirm')).toBeEnabled();
  });

  it('writes only after the confirmation, with the revision the check saw', async () => {
    const bodies: Record<string, unknown>[] = [];
    useBackend(bodies, (body) =>
      report({ dry_run: body.dry_run as boolean, applied: body.dry_run === false }),
    );
    const onApplied = vi.fn();
    const user = renderDialog(onApplied);

    await user.click(screen.getByTestId('plan-season-check'));
    await screen.findByTestId('plan-season-report');
    expect(onApplied).not.toHaveBeenCalled();
    await user.click(screen.getByTestId('plan-season-confirm'));

    expect(await screen.findByTestId('plan-season-done')).toHaveTextContent(
      '12 free slots created in 1 beds.',
    );
    expect(bodies[1]).toEqual({ year: YEAR, dry_run: false, expected_revision: 7 });
    expect(onApplied).toHaveBeenCalledTimes(1);
  });

  it('refuses a year the server would refuse, before any request', async () => {
    const bodies: Record<string, unknown>[] = [];
    useBackend(bodies, () => report());
    const user = renderDialog();

    for (const bad of ['12', '1999', 'abc', '-202', '2.5']) {
      const field = screen.getByTestId('plan-season-year');
      await user.clear(field);
      await user.type(field, bad);
      expect(screen.getByTestId('plan-season-check')).toBeDisabled();
    }
    expect(screen.getByText(/Enter a year between 2001 and/)).toBeInTheDocument();
    expect(bodies).toEqual([]);
  });

  it('needs a new check when the year changes', async () => {
    useBackend([], () => report());
    const user = renderDialog();
    await user.click(screen.getByTestId('plan-season-check'));
    await screen.findByTestId('plan-season-report');

    const field = screen.getByTestId('plan-season-year');
    await user.clear(field);
    await user.type(field, String(YEAR - 1));

    expect(screen.queryByTestId('plan-season-report')).not.toBeInTheDocument();
    expect(screen.getByTestId('plan-season-confirm')).toBeDisabled();
  });

  it('offers no confirmation when there is nothing to create', async () => {
    useBackend([], () => report({ beds_copied: 0, slots_to_create: 0, beds: [] }));
    const user = renderDialog();
    await user.click(screen.getByTestId('plan-season-check'));

    expect(
      await screen.findByText(`No finished places are stored for ${YEAR - 1}.`),
    ).toBeInTheDocument();
    expect(screen.getByTestId('plan-season-confirm')).toBeDisabled();
  });

  it.each([
    [403, 'season.forbidden', 'Only a lead can start a new season.'],
    [409, 'plan.revision_conflict', 'The plan was changed in the meantime. Check again.'],
    [422, 'season.invalid_year', 'This year is not possible.'],
    [429, 'RATE_LIMIT_EXCEEDED', 'Too many requests. Wait a moment and try again.'],
  ])('says what a %i means', async (status, code, text) => {
    useBackend([], () =>
      HttpResponse.json(
        { error_id: 'e1', error_code: code, message: 'x', details: [], path: '', method: 'POST' },
        { status },
      ),
    );
    const user = renderDialog();
    await user.click(screen.getByTestId('plan-season-check'));

    expect(await screen.findByTestId('plan-season-failure')).toHaveTextContent(text);
  });

  it('shows "Here stood" as a display-only hint from the rotation timeline', async () => {
    const bodies: Record<string, unknown>[] = [];
    useBackend(bodies, () => report());
    const rotation = vi.fn();
    server.use(
      http.get(`${BASE}/locations/b1/rotation`, ({ request }) => {
        rotation(new URL(request.url).searchParams.get('years'));
        return HttpResponse.json({
          location_key: 'b1',
          years: 2,
          rotation_applicable: true,
          not_applicable_reason: null,
          rotation_reset_at: null,
          timeline: [
            {
              year: YEAR - 1,
              plantings: [
                {
                  family_name: 'Nightshades',
                  family_key: 'sol',
                  plan_role: 'main_crop',
                  source: 'plant',
                },
              ],
            },
            {
              year: YEAR - 2,
              plantings: [
                {
                  family_name: 'Brassicas',
                  family_key: 'bra',
                  plan_role: 'main_crop',
                  source: 'plant',
                },
              ],
            },
          ],
        });
      }),
    );
    const user = renderDialog();
    await user.click(screen.getByTestId('plan-season-check'));
    await screen.findByTestId('plan-season-report');
    expect(rotation).not.toHaveBeenCalled();

    await user.click(screen.getByRole('checkbox', { name: 'Show "Here stood …"' }));

    expect(await screen.findByText('Here stood: Nightshades')).toBeInTheDocument();
    expect(screen.queryByText(/Brassicas/)).not.toBeInTheDocument();
    await waitFor(() => expect(rotation).toHaveBeenCalledTimes(1));
    expect(bodies).toHaveLength(1); // the hint never touches the season request
  });

  it('has no accessibility violations before and after the check', async () => {
    useBackend([], () => report());
    const user = renderDialog();
    await expectNoA11yViolations(document.body, { minElements: 8 });

    await user.click(screen.getByTestId('plan-season-check'));
    await screen.findByTestId('plan-season-report');
    await expectNoA11yViolations(document.body, { minElements: 15 });
  });
});
