import { describe, it, expect } from 'vitest';
import { screen } from '@testing-library/react';

import Sidebar from '@/layouts/Sidebar';
import {
  createStoreWithExpertise,
  createStoreWithModuleOverrides,
  renderWithProviders,
} from '../helpers';

describe('Sidebar — REQ-042 module overrides vs. experience level', () => {
  it('hides the expert-gated Ernte section for a beginner by default', () => {
    renderWithProviders(<Sidebar open />, {
      store: createStoreWithExpertise('beginner'),
    });
    expect(screen.queryByTestId('nav-/ernte/batches')).toBeNull();
  });

  it('reveals the Ernte section when the harvest module is enabled via a personal override', () => {
    // Regression test: the section-level gate is override-blind, so enabling the
    // harvest module as a beginner must still surface its menu item.
    renderWithProviders(<Sidebar open />, {
      store: createStoreWithModuleOverrides('beginner', { harvest: 'enabled' }),
    });
    expect(screen.getByTestId('nav-/ernte/batches')).toBeInTheDocument();
  });

  it('keeps a disabled override hidden even when the level would show the item', () => {
    renderWithProviders(<Sidebar open />, {
      store: createStoreWithModuleOverrides('expert', { harvest: 'disabled' }),
    });
    expect(screen.queryByTestId('nav-/ernte/batches')).toBeNull();
  });
});
