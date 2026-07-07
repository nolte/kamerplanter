import { describe, it, expect, beforeEach } from 'vitest';
import { screen } from '@testing-library/react';
import i18n from 'i18next';

import Breadcrumbs from '@/components/layout/Breadcrumbs';
import { createTestStore, renderWithProviders } from '../../helpers';

describe('Breadcrumbs', () => {
  beforeEach(() => {
    i18n.changeLanguage('de');
  });

  it('renders nothing on an unmapped route with no dynamic crumbs', () => {
    const { container } = renderWithProviders(<Breadcrumbs />, { route: '/unknown-path' });
    expect(container.querySelector('nav[aria-label="breadcrumb"]')).toBeNull();
  });

  it('renders static path-based crumbs with a linked parent and a plain current page', () => {
    renderWithProviders(<Breadcrumbs />, { route: '/pflanzen/plant-instances' });

    const nav = screen.getByLabelText('breadcrumb');
    expect(nav).toBeInTheDocument();

    // Parent (Dashboard) is a router link; the current page is plain text.
    const dashboardLink = screen.getByRole('link', { name: 'Dashboard' });
    expect(dashboardLink).toHaveAttribute('href', '/dashboard');
    expect(screen.getByText('Pflanzeninstanzen')).toBeInTheDocument();
    expect(screen.queryByRole('link', { name: 'Pflanzeninstanzen' })).toBeNull();
  });

  it('prefers page-supplied dynamic breadcrumbs over static ones', () => {
    const store = createTestStore({
      ui: {
        sidebarOpen: true,
        breadcrumbs: [
          { label: 'Custom Root', path: '/dashboard' },
          { label: 'Custom Leaf', path: null },
        ],
      },
    });

    renderWithProviders(<Breadcrumbs />, { store, route: '/pflanzen/plant-instances' });

    expect(screen.getByRole('link', { name: 'Custom Root' })).toHaveAttribute('href', '/dashboard');
    expect(screen.getByText('Custom Leaf')).toBeInTheDocument();
    // Static crumbs are suppressed when dynamic ones exist.
    expect(screen.queryByText('Pflanzeninstanzen')).toBeNull();
  });
});
