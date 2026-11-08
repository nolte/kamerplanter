/**
 * REQ-053 WP 9.13 (#2753, GP-FR-117): the watering-round dialog's "rain - skipped" action and `by_demand`.
 *
 * Pinned: "rain - skipped" sends no amount, only the note and one `client_event_id` made per opening of the dialog
 * (a second press and a retry after an error send the same id, so the server answers the first round instead of
 * writing it twice); the result names the beds and says the open tasks stay open; `by_demand` is offered and its
 * refusal is worded.
 */
import { cleanup, screen, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { http, HttpResponse } from 'msw';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { expectNoA11yViolations } from '@/test/a11y/expectNoA11yViolations';
import { authState, createTestStore, renderWithProviders, tenantState } from '@/test/helpers';
import { server } from '@/test/mocks/server';
import { WateringRoundDialog } from './WateringRoundDialog';
import { BASE, zone, zonePlan } from './zonesTestKit';

afterEach(() => cleanup());

const UUID = /^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/;

function renderDialog(locationKeys: string[] = ['loc_a', 'loc_c']) {
  const onLogged = vi.fn();
  const onClose = vi.fn();
  const view = renderWithProviders(
    <WateringRoundDialog
      open
      zone={zone('z1', { name: 'South line', location_keys: locationKeys })}
      plan={zonePlan()}
      onClose={onClose}
      onLogged={onLogged}
    />,
    { store: createTestStore({ ...tenantState('grower'), ...authState() }) },
  );
  return { ...view, onLogged, onClose };
}

const errorBody = (code: string, status: number) =>
  HttpResponse.json({ error_id: 'e', error_code: code, message: 'x', details: [], path: '', method: 'X' }, { status });

describe('rain - skipped', () => {
  it('writes the round without an amount, with the note, and names the beds it was saved for', async () => {
    const user = userEvent.setup();
    const sent: Record<string, unknown>[] = [];
    server.use(
      http.post(`${BASE}/irrigation-zones/z1/rain-skipped`, async ({ request }) => {
        sent.push((await request.json()) as Record<string, unknown>);
        return HttpResponse.json(
          { event_keys: ['e1', 'e2'], location_keys: ['loc_a', 'loc_c'], performed_at: '2026-11-08T06:00:00Z', replayed: false },
          { status: 201 },
        );
      }),
    );
    const { onLogged } = renderDialog();

    const dialog = screen.getByTestId('garden-plan-round-dialog');
    expect(within(dialog).getByText(/Open watering tasks stay open/)).toBeInTheDocument();
    // No amount is needed: the action is enabled while the round's own submit is not.
    expect(within(dialog).getByTestId('garden-plan-round-submit')).toBeDisabled();
    await user.type(within(dialog).getByTestId('garden-plan-round-summary'), '12 mm overnight');
    await user.click(within(dialog).getByTestId('garden-plan-round-rain-skipped'));

    const result = await screen.findByTestId('garden-plan-round-rain-result');
    expect(sent).toHaveLength(1);
    expect(Object.keys(sent[0]).sort()).toEqual(['client_event_id', 'summary']);
    expect(sent[0].summary).toBe('12 mm overnight');
    expect(sent[0].client_event_id).toMatch(UUID);
    expect(result).toHaveTextContent('Round saved as skipped');
    expect(result).toHaveTextContent('Open watering tasks stay open');
    expect(screen.getByTestId('garden-plan-round-rain-result-beds')).toHaveTextContent('Saved for 2 beds: North bed, East bed.');
    expect(onLogged).toHaveBeenCalledTimes(1);
  });

  it('retries with the same client_event_id after a failure, and a new opening makes a new one', async () => {
    const user = userEvent.setup();
    const ids: unknown[] = [];
    let answer = 0;
    server.use(
      http.post(`${BASE}/irrigation-zones/z1/rain-skipped`, async ({ request }) => {
        ids.push(((await request.json()) as Record<string, unknown>).client_event_id);
        answer += 1;
        if (answer === 1) return errorBody('x', 503);
        return HttpResponse.json(
          { event_keys: ['e1'], location_keys: ['loc_a'], performed_at: '2026-11-08T06:00:00Z', replayed: answer === 2 },
          { status: answer === 2 ? 200 : 201 },
        );
      }),
    );
    const first = renderDialog(['loc_a']);

    await user.click(screen.getByTestId('garden-plan-round-rain-skipped'));
    expect(await screen.findByTestId('garden-plan-round-error')).toBeInTheDocument();
    await user.click(screen.getByTestId('garden-plan-round-rain-skipped'));
    await screen.findByTestId('garden-plan-round-rain-result');
    first.unmount();
    renderDialog(['loc_a']);
    await user.click(screen.getByTestId('garden-plan-round-rain-skipped'));
    await screen.findByTestId('garden-plan-round-rain-result');

    expect(ids).toHaveLength(3);
    expect(ids[1]).toBe(ids[0]); // the retry is the same press: the server answers the stored round, never 2n
    expect(ids[2]).not.toBe(ids[0]); // a new opening is a new round
  });

  it('is not offered for a zone without beds', () => {
    renderDialog([]);

    expect(screen.getByTestId('garden-plan-round-rain-skipped')).toBeDisabled();
  });

  it.each([
    ['client_event.payload_mismatch', 409, /already saved as skipped with a different note/],
    ['irrigation_zone.no_beds', 422, /no bed yet/],
    ['x', 403, /permission/],
  ])('words %s (%i)', async (code, status_, text) => {
    const user = userEvent.setup();
    server.use(http.post(`${BASE}/irrigation-zones/z1/rain-skipped`, () => errorBody(code, status_)));
    renderDialog();

    await user.click(screen.getByTestId('garden-plan-round-rain-skipped'));

    expect(await screen.findByTestId('garden-plan-round-error')).toHaveTextContent(text);
  });

  it('has no axe violations', async () => {
    renderDialog();

    await expectNoA11yViolations(screen.getByTestId('garden-plan-round-dialog'));
  });
});

describe('by demand', () => {
  it('is offered, sends by_demand and names the beds without a demand', async () => {
    const user = userEvent.setup();
    const sent: unknown[] = [];
    server.use(
      http.post(`${BASE}/irrigation-zones/z1/log-watering`, async ({ request }) => {
        sent.push(await request.json());
        return HttpResponse.json(
          {
            event_keys: ['e1'],
            shares: [{ location_key: 'loc_a', liters: 20 }],
            allocation: 'by_demand',
            performed_at: '2026-11-08T06:00:00Z',
            skipped_location_keys: ['loc_c'],
          },
          { status: 201 },
        );
      }),
    );
    renderDialog();

    await user.click(screen.getByTestId('garden-plan-round-allocation-by_demand'));
    expect(screen.getByText(/by its calculated water demand on that day/)).toBeInTheDocument();
    await user.type(screen.getByTestId('garden-plan-round-volume'), '20');
    await user.click(screen.getByTestId('garden-plan-round-submit'));

    await screen.findByTestId('garden-plan-round-result');
    expect(sent[0]).toEqual({ volume_liters: 20, allocation: 'by_demand', summary: null });
    expect(screen.getByTestId('garden-plan-round-result-marker')).toHaveTextContent('Divided by demand');
    expect(screen.getByTestId('garden-plan-round-result-skipped')).toHaveTextContent(
      'no water demand on that day: East bed',
    );
  });

  it('words the refusal when no bed has a demand', async () => {
    const user = userEvent.setup();
    server.use(
      http.post(`${BASE}/irrigation-zones/z1/log-watering`, () => errorBody('irrigation_zone.no_bed_demand', 422)),
    );
    renderDialog();

    await user.click(screen.getByTestId('garden-plan-round-allocation-by_demand'));
    await user.type(screen.getByTestId('garden-plan-round-volume'), '20');
    await user.click(screen.getByTestId('garden-plan-round-submit'));

    expect(await screen.findByTestId('garden-plan-round-error')).toHaveTextContent(/calculated water demand/);
  });
});
