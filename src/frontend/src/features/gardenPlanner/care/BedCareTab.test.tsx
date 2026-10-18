/**
 * The care tab (REQ-053 GP-FR-083…086, GP-FR-090): sections, completion with the category dialog, the
 * double-tap guard, the undo, suggestions, tasks for the bed or for every plant, care without a task.
 */
import { cleanup, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { expectNoA11yViolations } from '@/test/a11y/expectNoA11yViolations';
import { authState, createTestStore, renderWithProviders, tenantState } from '@/test/helpers';
import { bedSummary } from '../bed/bedTestKit';
import type { BedSummary } from '../bed/types';
import BedCareTab from './BedCareTab';
import { careTask, useCareBackend } from './careTestKit';

const PLANTS = [
  { plant_key: 'pi_1', instance_id: 'TOM-1' },
  { plant_key: 'pi_2', instance_id: 'TOM-2' },
];
const PAST = '2020-01-01T00:00:00Z';
const FUTURE = '2099-01-01T00:00:00Z';

function renderTab(
  bed: BedSummary = bedSummary(),
  role: 'viewer' | 'grower' | 'lead' = 'grower',
  onChanged: () => void = () => undefined,
) {
  return renderWithProviders(<BedCareTab bed={bed} onChanged={onChanged} />, {
    store: createTestStore({ ...tenantState(role), ...authState() }),
    route: '/standorte/locations/loc_b03#care',
  });
}

afterEach(() => cleanup());

describe('BedCareTab sections', () => {
  it('splits overdue, open and suggested tasks and names plant tasks by their instance id', async () => {
    useCareBackend(
      [
        careTask('t_over', { name: 'Water the bed', due_date: PAST }),
        careTask('t_open', { name: 'Mulch', category: 'mulching', due_date: FUTURE }),
        careTask('t_plant', { name: 'Tie up', category: 'pruning', entity_type: 'plant_instance', entity_key: 'pi_1' }),
        careTask('t_sug', {
          name: 'Water (ET0)',
          suggested: true,
          suggestion_reason: 'ET0 demand 4.2 L/m2 over 3 days',
        }),
      ],
      PLANTS,
    );
    renderTab();

    const overdue = await screen.findByTestId('care-section-overdue');
    expect(within(overdue).getByTestId('care-task-t_over')).toHaveTextContent('Water the bed');
    expect(within(overdue).getByRole('heading', { level: 2 })).toHaveTextContent('Overdue (1)');
    const open = screen.getByTestId('care-section-open');
    expect(within(open).getByTestId('care-task-t_open')).toBeInTheDocument();
    expect(within(open).getByTestId('care-task-t_plant')).toHaveTextContent('Plant TOM-1');
    const suggested = screen.getByTestId('care-section-suggested');
    expect(within(suggested).getByTestId('care-reason-t_sug')).toHaveTextContent('ET0 demand 4.2 L/m2 over 3 days');
    // A suggestion is not in the open list.
    expect(within(open).queryByTestId('care-task-t_sug')).toBeNull();
  });

  it('says so when nothing is open', async () => {
    useCareBackend([]);
    renderTab();
    expect(await screen.findByText('Nothing to do here')).toBeInTheDocument();
  });

  it('shows no write controls to a viewer', async () => {
    useCareBackend([careTask('t1', { name: 'Water the bed' })]);
    renderTab(bedSummary(), 'viewer');
    expect(await screen.findByTestId('care-task-t1')).toBeInTheDocument();
    expect(screen.queryByTestId('care-done-t1')).toBeNull();
    expect(screen.queryByTestId('care-create')).toBeNull();
    expect(screen.queryByTestId('care-log')).toBeNull();
  });
});

describe('completing a task (GP-FR-083/084)', () => {
  it('asks the watering fields, sends them with one request and takes the task out of the list', async () => {
    const backend = useCareBackend([careTask('t1', { name: 'Water the bed' })], PLANTS);
    const onChanged = vi.fn();
    const user = userEvent.setup();
    renderTab(bedSummary(), 'grower', onChanged);

    await user.click(await screen.findByTestId('care-done-t1'));
    const dialog = await screen.findByTestId('care-complete-dialog');
    await user.type(within(dialog).getByTestId('care-complete-quantity'), '12,5');
    await user.click(within(dialog).getByTestId('care-complete-submit'));

    await waitFor(() => expect(screen.queryByTestId('care-task-t1')).toBeNull());
    expect(backend.seen).toEqual([
      { url: '/tasks/t1/complete', body: { quantity: 12.5, unit: 'l' } },
    ]);
    expect(onChanged).toHaveBeenCalled();
    expect(await screen.findByText('Done: Water the bed')).toBeInTheDocument();
  });

  it('completes without any input (GP-FR-084: an empty form is valid)', async () => {
    const backend = useCareBackend([careTask('t1', { category: 'weeding', name: 'Weed' })]);
    const user = userEvent.setup();
    renderTab();
    await user.click(await screen.findByTestId('care-done-t1'));
    await user.click(await screen.findByTestId('care-complete-submit'));
    await waitFor(() => expect(backend.seen).toHaveLength(1));
    expect(backend.seen[0]).toEqual({ url: '/tasks/t1/complete', body: {} });
  });

  it('asks material and thickness for mulching and sends a backdated instant', async () => {
    const backend = useCareBackend([careTask('t1', { category: 'mulching', name: 'Mulch' })]);
    const user = userEvent.setup();
    renderTab();
    await user.click(await screen.findByTestId('care-done-t1'));
    const dialog = await screen.findByTestId('care-complete-dialog');
    await user.type(within(dialog).getByTestId('care-complete-material'), 'straw');
    await user.type(within(dialog).getByTestId('care-complete-quantity'), '5');
    const when = within(dialog).getByTestId('care-complete-performed-at');
    const past = new Date(Date.now() - 3 * 86_400_000);
    const local = `${past.getFullYear()}-${String(past.getMonth() + 1).padStart(2, '0')}-${String(past.getDate()).padStart(2, '0')}T08:00`;
    await user.clear(when);
    await user.type(when, local);
    await user.click(within(dialog).getByTestId('care-complete-submit'));
    await waitFor(() => expect(backend.seen).toHaveLength(1));
    expect(backend.seen[0].body).toMatchObject({
      material: 'straw',
      quantity: 5,
      unit: 'cm',
      performed_at: new Date(`${local}:00`).toISOString(),
    });
  });

  it('refuses a future instant before any request (GP-FR-085)', async () => {
    const backend = useCareBackend([careTask('t1', { category: 'weeding' })]);
    const user = userEvent.setup();
    renderTab();
    await user.click(await screen.findByTestId('care-done-t1'));
    const dialog = await screen.findByTestId('care-complete-dialog');
    const when = within(dialog).getByTestId('care-complete-performed-at');
    await user.clear(when);
    await user.type(when, '2099-01-01T08:00');
    await user.click(within(dialog).getByTestId('care-complete-submit'));
    expect(await within(dialog).findByText('The time lies in the future.')).toBeInTheDocument();
    expect(backend.seen).toHaveLength(0);
  });

  it('sends one request however often "Complete" is tapped (the guard itself is pinned in submitGuard.test)', async () => {
    const backend = useCareBackend([careTask('t1', { category: 'weeding' })]);
    const user = userEvent.setup();
    renderTab();
    await user.click(await screen.findByTestId('care-done-t1'));
    const submit = await screen.findByTestId('care-complete-submit');
    await user.dblClick(submit);
    await user.click(submit).catch(() => undefined);
    await waitFor(() => expect(screen.queryByTestId('care-complete-dialog')).toBeNull());
    expect(backend.seen.filter((call) => call.url.endsWith('/complete'))).toHaveLength(1);
  });

  it('undoes through reopen with undo=true and puts the task back', async () => {
    const backend = useCareBackend([careTask('t1', { category: 'weeding', name: 'Weed' })]);
    const user = userEvent.setup();
    renderTab();
    await user.click(await screen.findByTestId('care-done-t1'));
    await user.click(await screen.findByTestId('care-complete-submit'));
    await waitFor(() => expect(screen.queryByTestId('care-task-t1')).toBeNull());

    await user.click(await screen.findByTestId('care-undo'));
    expect(await screen.findByTestId('care-task-t1')).toBeInTheDocument();
    expect(backend.seen[backend.seen.length - 1]).toEqual({ url: '/tasks/t1/reopen', body: { undo: true } });
  });
});

describe('suggestions (GP-FR-086)', () => {
  it('dismisses one by skipping it, with an undo', async () => {
    const backend = useCareBackend([careTask('t_sug', { suggested: true, suggestion_reason: 'Dry spell' })]);
    const user = userEvent.setup();
    renderTab();
    await user.click(await screen.findByTestId('care-dismiss-t_sug'));
    await waitFor(() => expect(screen.queryByTestId('care-task-t_sug')).toBeNull());
    expect(backend.seen[0].url).toBe('/tasks/t_sug/skip');
    await user.click(await screen.findByTestId('care-undo'));
    expect(await screen.findByTestId('care-task-t_sug')).toBeInTheDocument();
  });

  it('"Do now" opens the same completion dialog', async () => {
    useCareBackend([careTask('t_sug', { suggested: true, category: 'watering' })]);
    const user = userEvent.setup();
    renderTab();
    await user.click(await screen.findByTestId('care-done-t_sug'));
    expect(await screen.findByTestId('care-complete-dialog')).toBeInTheDocument();
  });
});

describe('creating a task (GP-FR-080/081)', () => {
  it('"for the bed" creates one task bound to the bed', async () => {
    const backend = useCareBackend([], PLANTS);
    const user = userEvent.setup();
    renderTab();
    await user.click(await screen.findByTestId('care-create'));
    const dialog = await screen.findByTestId('care-task-dialog');
    await user.click(within(dialog).getByTestId('care-task-submit'));
    await waitFor(() => expect(screen.queryByTestId('care-task-dialog')).toBeNull());
    expect(backend.seen).toHaveLength(1);
    expect(backend.seen[0]).toMatchObject({
      url: '/tasks',
      body: { entity_type: 'location', entity_key: 'loc_b03', category: 'watering', name: 'Watering' },
    });
  });

  it('"for every plant" creates the bed task and fans it out', async () => {
    const backend = useCareBackend([], PLANTS);
    const user = userEvent.setup();
    renderTab();
    await user.click(await screen.findByTestId('care-create'));
    const dialog = await screen.findByTestId('care-task-dialog');
    await user.click(within(dialog).getByTestId('care-task-scope-plants'));
    await user.click(within(dialog).getByTestId('care-task-submit'));
    await waitFor(() => expect(screen.queryByTestId('care-task-dialog')).toBeNull());
    expect(backend.seen.map((call) => call.url)).toEqual(['/tasks', '/tasks/new_1/fan-out']);
    expect(backend.seen[1].body).toEqual({ include_children: true, keep_source: false });
    expect(await screen.findByText('2 tasks created, one per plant.')).toBeInTheDocument();
  });

  it('offers "every plant" only when plants stand in the bed', async () => {
    useCareBackend([], []);
    const user = userEvent.setup();
    renderTab(bedSummary({ active_plant_count: 0 }));
    await user.click(await screen.findByTestId('care-create'));
    const radio = within(await screen.findByTestId('care-task-scope-plants')).getByRole('radio');
    expect(radio).toBeDisabled();
  });
});

describe('logging care without a task (GP-FR-090)', () => {
  it('posts a care event with trigger-free body and offers the undo through void', async () => {
    const backend = useCareBackend([], PLANTS);
    const user = userEvent.setup();
    renderTab();
    await user.click(await screen.findByTestId('care-log'));
    const dialog = await screen.findByTestId('care-log-dialog');
    await user.click(within(dialog).getByTestId('care-log-submit'));
    await waitFor(() => expect(screen.queryByTestId('care-log-dialog')).toBeNull());
    expect(backend.seen[0].url).toBe('/care-events');
    expect(backend.seen[0].body).toMatchObject({ location_key: 'loc_b03', category: 'watering', summary: 'Watering' });
    expect(backend.seen[0].body).not.toHaveProperty('trigger');

    await user.click(await screen.findByTestId('care-undo'));
    await waitFor(() => expect(backend.seen[backend.seen.length - 1]).toEqual({ url: '/care-events/ce_1/void', body: { reason: 'undo' } }));
  });

  it('offers only the categories that fit the bed (F-03) and no plant protection', async () => {
    useCareBackend([]);
    const user = userEvent.setup();
    renderTab(
      bedSummary({
        location_type_key: 'raised_bed',
        soil_profile: {
          soil_texture: 'loam',
          drainage: 'good',
          site_water_regime: 'fresh',
          conditions: [],
          growing_medium_kind: 'native_soil',
        },
      }),
    );
    await user.click(await screen.findByTestId('care-log'));
    const select = await screen.findByTestId('care-log-category');
    await user.click(select.parentElement!.querySelector('[role="combobox"]') ?? select);
    const options = (await screen.findAllByRole('option')).map((option) => option.textContent);
    expect(options).toContain('Hilling');
    expect(options).toContain('Note');
    expect(options).not.toContain('Flush');
    expect(options).not.toContain('Ventilating');
    expect(options).not.toContain('Pest Control');
  });
});

describe('accessibility', () => {
  it('the tab and the completion dialog have no critical axe violations', async () => {
    useCareBackend(
      [
        careTask('t_over', { name: 'Water the bed', due_date: PAST }),
        careTask('t_sug', { name: 'Water (ET0)', suggested: true, suggestion_reason: 'Dry spell' }),
      ],
      PLANTS,
    );
    const user = userEvent.setup();
    const { container } = renderTab();
    await screen.findByTestId('care-task-t_over');
    await expectNoA11yViolations(container, { minElements: 40 });
    await user.click(screen.getByTestId('care-done-t_over'));
    await screen.findByTestId('care-complete-dialog');
    await expectNoA11yViolations(document.body, { minElements: 60 });
  });
});
