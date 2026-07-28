/**
 * UI-NFR-021 R-024: on `xs` exactly one action stays directly visible (the
 * primary, G1) and every other action moves into the `⋮` overflow menu. R-017
 * adds that G1 never enters that menu.
 *
 * The breakpoint is driven through `matchMedia`, which jsdom does not implement
 * — `src/test/setup.ts` provides a stub, and each test sets the match result
 * before rendering.
 */
import { screen, fireEvent, within } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';

import PageHeaderActions, { type HeaderAction } from '@/components/layout/PageHeaderActions';

import { renderWithProviders } from '../helpers';

function setViewport(isXs: boolean) {
  window.matchMedia = vi.fn().mockImplementation((query: string) => ({
    // MUI asks `(max-width: …)` for `down('sm')`.
    matches: isXs && query.includes('max-width'),
    media: query,
    onchange: null,
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    addListener: vi.fn(),
    removeListener: vi.fn(),
    dispatchEvent: vi.fn(),
  }));
}

const primary: HeaderAction = { label: 'Anlegen', onClick: vi.fn(), variant: 'contained' };
const filter: HeaderAction = { label: 'Favoriten', onClick: vi.fn(), iconOnly: true };
const mix: HeaderAction = { label: 'Mischen', onClick: vi.fn(), variant: 'outlined' };

describe('PageHeaderActions', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('shows every action side by side from sm upwards', () => {
    setViewport(false);
    renderWithProviders(<PageHeaderActions primary={primary} secondary={[filter, mix]} />);

    expect(screen.getByRole('button', { name: 'Anlegen' })).toBeTruthy();
    expect(screen.getByRole('button', { name: 'Favoriten' })).toBeTruthy();
    expect(screen.getByRole('button', { name: 'Mischen' })).toBeTruthy();
    expect(screen.queryByTestId('page-header-overflow')).toBeNull();
  });

  it('leaves only the primary action visible on xs and collapses the rest', () => {
    setViewport(true);
    renderWithProviders(<PageHeaderActions primary={primary} secondary={[filter, mix]} />);

    expect(screen.getByRole('button', { name: 'Anlegen' })).toBeTruthy();
    // R-024: the secondary actions are gone from the header itself...
    expect(screen.queryByRole('button', { name: 'Favoriten' })).toBeNull();
    expect(screen.queryByRole('button', { name: 'Mischen' })).toBeNull();
    // ...and reachable through the overflow instead.
    fireEvent.click(screen.getByTestId('page-header-overflow'));
    const menu = screen.getByTestId('page-header-overflow-menu');
    expect(within(menu).getByText('Favoriten')).toBeTruthy();
    expect(within(menu).getByText('Mischen')).toBeTruthy();
  });

  it('never puts the primary action into the overflow menu (R-017)', () => {
    setViewport(true);
    renderWithProviders(<PageHeaderActions primary={primary} secondary={[filter]} />);

    fireEvent.click(screen.getByTestId('page-header-overflow'));
    const menu = screen.getByTestId('page-header-overflow-menu');
    expect(within(menu).queryByText('Anlegen')).toBeNull();
  });

  it('invokes the action and closes the menu when an entry is chosen', () => {
    setViewport(true);
    const onClick = vi.fn();
    renderWithProviders(
      <PageHeaderActions primary={primary} secondary={[{ label: 'Mischen', onClick }]} />,
    );

    fireEvent.click(screen.getByTestId('page-header-overflow'));
    fireEvent.click(within(screen.getByTestId('page-header-overflow-menu')).getByText('Mischen'));

    expect(onClick).toHaveBeenCalledTimes(1);
  });

  it('drops conditionally absent actions instead of rendering a gap', () => {
    setViewport(false);
    const hasFavorites = false;
    renderWithProviders(
      <PageHeaderActions primary={primary} secondary={[hasFavorites && filter, mix]} />,
    );

    expect(screen.queryByRole('button', { name: 'Favoriten' })).toBeNull();
    expect(screen.getByRole('button', { name: 'Mischen' })).toBeTruthy();
  });

  it('renders no overflow control when there is nothing to collapse', () => {
    setViewport(true);
    renderWithProviders(<PageHeaderActions primary={primary} secondary={[]} />);

    expect(screen.getByRole('button', { name: 'Anlegen' })).toBeTruthy();
    expect(screen.queryByTestId('page-header-overflow')).toBeNull();
  });

  it('keeps an escape-hatch control visible at both breakpoints', () => {
    setViewport(true);
    renderWithProviders(
      <PageHeaderActions
        primary={primary}
        secondary={[mix]}
        extra={<span data-testid="print-control">print</span>}
      />,
    );

    expect(screen.getByTestId('print-control')).toBeTruthy();
  });
});
