import { describe, it, expect } from 'vitest';
import { screen } from '@testing-library/react';

import ModuleGuard from '@/components/common/ModuleGuard';
import { renderWithProviders, createStoreWithModuleOverrides } from '../helpers';

describe('ModuleGuard', () => {
  it('renders children when the current path belongs to a visible module', () => {
    renderWithProviders(
      <ModuleGuard>
        <div data-testid="guarded-content">visible</div>
      </ModuleGuard>,
      {
        store: createStoreWithModuleOverrides('expert', {}),
        route: '/standorte/tanks',
      },
    );
    expect(screen.getByTestId('guarded-content')).toBeInTheDocument();
    expect(screen.queryByTestId('module-guard-hint')).not.toBeInTheDocument();
  });

  it('renders the reactivation hint when the module is disabled', () => {
    renderWithProviders(
      <ModuleGuard>
        <div data-testid="guarded-content">should not show</div>
      </ModuleGuard>,
      {
        store: createStoreWithModuleOverrides('expert', { tanks: 'disabled' }),
        route: '/standorte/tanks',
      },
    );
    expect(screen.getByTestId('module-guard-hint')).toBeInTheDocument();
    expect(screen.queryByTestId('guarded-content')).not.toBeInTheDocument();
    expect(screen.getByTestId('module-guard-action')).toBeInTheDocument();
  });

  it('renders children for core paths', () => {
    renderWithProviders(
      <ModuleGuard>
        <div data-testid="guarded-content">dashboard</div>
      </ModuleGuard>,
      {
        store: createStoreWithModuleOverrides('beginner', {}),
        route: '/dashboard',
      },
    );
    expect(screen.getByTestId('guarded-content')).toBeInTheDocument();
  });
});
