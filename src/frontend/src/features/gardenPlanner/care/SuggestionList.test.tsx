/**
 * The suggestions section of the bed care tab (REQ-053 GP-FR-086): the reason, the two decisions, nothing at all
 * without a suggestion, no decisions for a viewer, and no critical axe violation.
 */
import { cleanup, screen, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { expectNoA11yViolations } from '@/test/a11y/expectNoA11yViolations';
import { renderWithProviders } from '@/test/helpers';
import { careTask } from './careTestKit';
import type { CareTask } from './careTypes';
import SuggestionList from './SuggestionList';

const PLANTS = [{ plantKey: 'pi_1', instanceId: 'TOM-1' }];

function renderList(
  tasks: CareTask[],
  { canEdit = true, busy = false }: { canEdit?: boolean; busy?: boolean } = {},
) {
  const onAccept = vi.fn();
  const onDismiss = vi.fn();
  const view = renderWithProviders(
    <SuggestionList
      tasks={tasks}
      plants={PLANTS}
      canEdit={canEdit}
      busy={busy}
      onAccept={onAccept}
      onDismiss={onDismiss}
    />,
  );
  return { ...view, onAccept, onDismiss };
}

afterEach(() => cleanup());

describe('SuggestionList', () => {
  it('renders nothing when there is no suggestion', () => {
    const { container } = renderList([]);
    expect(screen.queryByTestId('care-section-suggested')).toBeNull();
    expect(container).toBeEmptyDOMElement();
  });

  it('names each suggestion with its reason under a counted heading', () => {
    renderList([
      careTask('t_bed', { name: 'Water the bed', suggested: true, suggestion_reason: 'ET0 demand 4.2 L/m2 over 3 days' }),
      careTask('t_plant', {
        name: 'Tie up',
        category: 'pruning',
        suggested: true,
        entity_type: 'plant_instance',
        entity_key: 'pi_1',
      }),
    ]);
    const section = screen.getByTestId('care-section-suggested');
    expect(within(section).getByRole('heading', { level: 2 })).toHaveTextContent('Suggestions (2)');
    expect(within(section).getByTestId('care-reason-t_bed')).toHaveTextContent('ET0 demand 4.2 L/m2 over 3 days');
    // Without a reason the row says so instead of staying silent.
    expect(within(section).getByTestId('care-reason-t_plant')).toHaveTextContent('No reason given.');
    expect(within(section).getByTestId('care-task-t_plant')).toHaveTextContent('Plant TOM-1');
  });

  it('hands the task to the matching decision', async () => {
    const task = careTask('t_sug', { name: 'Water (ET0)', suggested: true });
    const { onAccept, onDismiss } = renderList([task]);
    const user = userEvent.setup();

    await user.click(screen.getByRole('button', { name: 'Accept: Water (ET0)' }));
    await user.click(screen.getByRole('button', { name: 'Dismiss: Water (ET0)' }));

    expect(onAccept).toHaveBeenCalledWith(task);
    expect(onDismiss).toHaveBeenCalledWith(task);
  });

  it('locks both decisions while a write runs', () => {
    renderList([careTask('t_sug', { suggested: true })], { busy: true });
    expect(screen.getByTestId('care-accept-t_sug')).toBeDisabled();
    expect(screen.getByTestId('care-dismiss-t_sug')).toBeDisabled();
  });

  it('shows a viewer the suggestion without the decisions', () => {
    renderList([careTask('t_sug', { suggested: true, suggestion_reason: 'Dry spell' })], { canEdit: false });
    expect(screen.getByTestId('care-reason-t_sug')).toHaveTextContent('Dry spell');
    expect(screen.queryByRole('button')).toBeNull();
  });

  it('has no critical axe violations', async () => {
    const { container } = renderList([
      careTask('t_a', { name: 'Water (ET0)', suggested: true, suggestion_reason: 'Dry spell' }),
      careTask('t_b', { name: 'Hoe', category: 'weeding', suggested: true }),
    ]);
    await expectNoA11yViolations(container);
  });
});
