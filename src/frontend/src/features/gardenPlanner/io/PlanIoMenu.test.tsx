/**
 * The "Export & import" entry of the plan page (REQ-053 GP-UX-050/051): who sees what, and why an entry is off.
 */
import { cleanup, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { authState, createTestStore, renderWithProviders, tenantState } from '@/test/helpers';
import { PlanIoMenu } from './PlanIoMenu';

function renderMenu(props: Partial<Parameters<typeof PlanIoMenu>[0]> = {}) {
  const store = createTestStore({ ...tenantState('lead'), ...authState() });
  renderWithProviders(
    <PlanIoMenu
      siteKey="s1"
      siteName="Mein Garten"
      canImport
      dirty={false}
      onImported={vi.fn()}
      {...props}
    />,
    { store },
  );
  return userEvent.setup();
}

afterEach(() => cleanup());

describe('PlanIoMenu', () => {
  it('offers both entries to a lead', async () => {
    const user = renderMenu();
    await user.click(screen.getByTestId('garden-plan-io-menu'));

    expect(screen.getByTestId('garden-plan-io-export')).not.toHaveAttribute('aria-disabled', 'true');
    expect(screen.getByTestId('garden-plan-io-import')).not.toHaveAttribute('aria-disabled', 'true');
  });

  it('keeps import off for anyone but a lead and says so, while export stays', async () => {
    const user = renderMenu({ canImport: false });
    await user.click(screen.getByTestId('garden-plan-io-menu'));

    expect(screen.getByTestId('garden-plan-io-import')).toHaveAttribute('aria-disabled', 'true');
    expect(screen.getByText('Only a lead can restore a backup.')).toBeInTheDocument();
    expect(screen.getByTestId('garden-plan-io-export')).not.toHaveAttribute('aria-disabled', 'true');
  });

  it('waits for unsaved changes before it offers a restore', async () => {
    const user = renderMenu({ dirty: true });
    await user.click(screen.getByTestId('garden-plan-io-menu'));

    expect(screen.getByTestId('garden-plan-io-import')).toHaveAttribute('aria-disabled', 'true');
    // import and the new season both wait for the plan to be saved
    expect(screen.getAllByText('Save or discard your changes to the plan first.')).toHaveLength(2);
  });

  it('offers the new season to a lead and keeps it off for anyone else', async () => {
    const user = renderMenu();
    await user.click(screen.getByTestId('garden-plan-io-menu'));
    expect(screen.getByTestId('garden-plan-io-season')).not.toHaveAttribute('aria-disabled', 'true');
    cleanup();

    const other = renderMenu({ canImport: false });
    await other.click(screen.getByTestId('garden-plan-io-menu'));
    expect(screen.getByTestId('garden-plan-io-season')).toHaveAttribute('aria-disabled', 'true');
    expect(screen.getByText('Only a lead can start a new season.')).toBeInTheDocument();
  });

  it('opens the new-season dialog lazily and not in the same breath as the others', async () => {
    const user = renderMenu();
    await user.click(screen.getByTestId('garden-plan-io-menu'));
    await user.click(screen.getByTestId('garden-plan-io-season'));

    expect(await screen.findByTestId('plan-season-dialog')).toBeInTheDocument();
    expect(screen.queryByTestId('plan-import-wizard')).not.toBeInTheDocument();
  });

  it('loads the dialogs only when they are opened', async () => {
    const user = renderMenu();
    expect(screen.queryByTestId('plan-export-dialog')).not.toBeInTheDocument();
    await user.click(screen.getByTestId('garden-plan-io-menu'));
    await user.click(screen.getByTestId('garden-plan-io-import'));

    expect(await screen.findByTestId('plan-import-wizard')).toBeInTheDocument();
    expect(screen.queryByTestId('plan-export-dialog')).not.toBeInTheDocument();
  });
});
