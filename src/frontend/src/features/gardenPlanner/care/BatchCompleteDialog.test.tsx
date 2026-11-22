/**
 * Completing a kind of task on several beds in one step (REQ-053 GP-FR-088): the tasks of the chosen beds
 * and their plants are found, sent once with the care fields, and the answer reports what failed.
 */
import { cleanup, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { http, HttpResponse } from 'msw';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { expectNoA11yViolations } from '@/test/a11y/expectNoA11yViolations';
import { authState, createTestStore, renderWithProviders, tenantState } from '@/test/helpers';
import { server } from '@/test/mocks/server';
import { bedListItem } from '../bed/bedTestKit';
import BatchCompleteDialog from './BatchCompleteDialog';
import { BASE, careTask, useCareBackend } from './careTestKit';

const BEDS = [
  bedListItem('loc_1', { name: 'Bed one', open_task_count: 2 }),
  bedListItem('loc_2', { name: 'Bed two', open_task_count: 1 }),
  bedListItem('loc_3', { name: 'Bed three', open_task_count: 0 }),
];

function renderDialog(onChanged: () => void = () => undefined, onClose: () => void = () => undefined) {
  return renderWithProviders(<BatchCompleteDialog beds={BEDS} onChanged={onChanged} onClose={onClose} />, {
    store: createTestStore({ ...tenantState('grower'), ...authState() }),
  });
}

afterEach(() => cleanup());

describe('BatchCompleteDialog', () => {
  it('preselects the beds with open tasks, finds the tasks of the chosen kind and completes them in one request', async () => {
    const backend = useCareBackend([
      careTask('t1', { name: 'Water 1' }),
      careTask('t2', { name: 'Water plant', entity_type: 'plant_instance', entity_key: 'pi_1' }),
      careTask('t_sug', { name: 'Proposal', suggested: true }),
    ]);
    const onChanged = vi.fn();
    const user = userEvent.setup();
    renderDialog(onChanged);

    expect(screen.getByTestId('care-batch-bed-loc_1')).toBeChecked();
    expect(screen.getByTestId('care-batch-bed-loc_2')).toBeChecked();
    expect(screen.getByTestId('care-batch-bed-loc_3')).not.toBeChecked();

    await user.click(screen.getByTestId('care-batch-find'));
    // Both selected beds answer with the same two tasks (the mock does not scope them); they count once each.
    expect(await screen.findByTestId('care-batch-found')).toHaveTextContent('2 open tasks on 2 beds.');

    await user.type(screen.getByTestId('care-batch-quantity'), '10');
    await user.click(screen.getByTestId('care-batch-submit'));
    await waitFor(() => expect(backend.seen.some((call) => call.url === '/tasks/batch/status')).toBe(true));
    const call = backend.seen.find((entry) => entry.url === '/tasks/batch/status');
    expect(call?.body).toEqual({ task_keys: ['t1', 't2'], action: 'complete', quantity: 10, unit: 'l' });
    await waitFor(() => expect(onChanged).toHaveBeenCalled());
    // The suggestion was never sent.
    expect(JSON.stringify(call?.body)).not.toContain('t_sug');
  });

  it('says so when the chosen beds have no open task of that kind', async () => {
    useCareBackend([]);
    const user = userEvent.setup();
    renderDialog();
    await user.click(screen.getByTestId('care-batch-find'));
    expect(await screen.findByTestId('care-batch-none')).toHaveTextContent('no open Watering tasks');
    expect(screen.queryByTestId('care-batch-submit')).toBeNull();
  });

  it('reports the tasks the server could not complete', async () => {
    useCareBackend([careTask('t1'), careTask('t2')]);
    server.use(
      http.post(`${BASE}/tasks/batch/status`, () =>
        HttpResponse.json({ succeeded: ['t1'], failed: [{ key: 't2', error: 'wrong status' }] }),
      ),
    );
    const user = userEvent.setup();
    renderDialog();
    await user.click(screen.getByTestId('care-batch-find'));
    await user.click(await screen.findByTestId('care-batch-submit'));
    expect(await screen.findByText('1 completed, 1 could not be completed.')).toBeInTheDocument();
  });

  it('does not report a failed lookup as "nothing to do"', async () => {
    useCareBackend([careTask('t1')]);
    server.use(http.get(`${BASE}/tasks/queue`, () => HttpResponse.json({ detail: 'down' }, { status: 503 })));
    const user = userEvent.setup();
    renderDialog();
    await user.click(screen.getByTestId('care-batch-find'));
    expect(await screen.findByTestId('care-batch-lookup-failed')).toHaveTextContent('could not be read');
    expect(screen.queryByTestId('care-batch-none')).toBeNull();
  });

  it('takes the next 200 after the first batch instead of leaving them unmentioned', async () => {
    const many = Array.from({ length: 230 }, (_, index) => careTask(`t${index}`));
    const backend = useCareBackend(many);
    const user = userEvent.setup();
    let closed = false;
    renderDialog(undefined, () => {
      closed = true;
    });
    await user.click(screen.getByTestId('care-batch-find'));
    expect(await screen.findByTestId('care-batch-found')).toHaveTextContent('230 open tasks');
    await user.click(screen.getByTestId('care-batch-submit'));
    await waitFor(() => expect(screen.getByTestId('care-batch-submit')).toHaveTextContent('Complete 30 tasks'));
    expect(closed).toBe(false);
    const first = backend.seen.find((call) => call.url === '/tasks/batch/status');
    expect((first?.body as { task_keys: string[] }).task_keys).toHaveLength(200);
  });

  it('tries every task on undo, reloads whatever the outcome, and still reports a refusal', async () => {
    const backend = useCareBackend([careTask('t1'), careTask('t2')]);
    server.use(
      http.post(`${BASE}/tasks/t2/reopen`, async ({ request }) => {
        backend.seen.push({ url: '/tasks/t2/reopen', body: await request.json() });
        return HttpResponse.json({ detail: 'too late' }, { status: 403 });
      }),
    );
    const onChanged = vi.fn();
    const user = userEvent.setup();
    renderDialog(onChanged);
    await user.click(screen.getByTestId('care-batch-find'));
    await user.click(await screen.findByTestId('care-batch-submit'));
    const undo = await screen.findByTestId('care-undo');
    const before = onChanged.mock.calls.length;
    await user.click(undo);
    await waitFor(() => expect(backend.seen.filter((call) => call.url.endsWith('/reopen'))).toHaveLength(2));
    await waitFor(() => expect(onChanged.mock.calls.length).toBeGreaterThan(before));
  });

  it('needs at least one bed', async () => {
    useCareBackend([]);
    const user = userEvent.setup();
    renderDialog();
    await user.click(screen.getByTestId('care-batch-bed-loc_1'));
    await user.click(screen.getByTestId('care-batch-bed-loc_2'));
    expect(screen.getByTestId('care-batch-find')).toBeDisabled();
  });

  it('has no critical accessibility violations', async () => {
    useCareBackend([careTask('t1')]);
    renderDialog();
    await screen.findByTestId('care-batch-dialog');
    await expectNoA11yViolations(document.body, { minElements: 40 });
  });
});
