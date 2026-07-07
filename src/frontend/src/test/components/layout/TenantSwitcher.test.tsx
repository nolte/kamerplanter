import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { screen, within, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import i18n from 'i18next';

import TenantSwitcher from '@/components/layout/TenantSwitcher';
import { createTestStore, renderWithProviders } from '../../helpers';

const personalTenant = {
  key: 'tenant-a',
  slug: 'mein-garten',
  name: 'Mein Garten',
  tenant_type: 'personal',
  role: 'admin',
};
const orgTenant = {
  key: 'tenant-b',
  slug: 'gemeinschaft',
  name: 'Gemeinschaftsgarten',
  tenant_type: 'organization',
  role: 'grower',
};

function storeWith(active: unknown, tenants: unknown[]) {
  return createTestStore({
    tenants: {
      activeTenant: active,
      myTenants: tenants,
      isLoading: false,
      error: null,
    },
  });
}

describe('TenantSwitcher', () => {
  let reloadMock: ReturnType<typeof vi.fn>;
  let originalLocation: Location;

  beforeEach(() => {
    i18n.changeLanguage('de');
    originalLocation = window.location;
    reloadMock = vi.fn();
    Object.defineProperty(window, 'location', {
      configurable: true,
      value: { ...originalLocation, reload: reloadMock },
    });
  });

  afterEach(() => {
    Object.defineProperty(window, 'location', {
      configurable: true,
      value: originalLocation,
    });
  });

  it('renders nothing when the user has no tenants', () => {
    const { container } = renderWithProviders(<TenantSwitcher />, {
      store: storeWith(null, []),
    });
    expect(container).toBeEmptyDOMElement();
  });

  it('shows the active tenant name and lists tenants with a check on the active one', async () => {
    const user = userEvent.setup();
    renderWithProviders(<TenantSwitcher />, {
      store: storeWith(personalTenant, [personalTenant, orgTenant]),
    });

    expect(screen.getByRole('button', { name: /Mein Garten/ })).toBeInTheDocument();
    await user.click(screen.getByRole('button', { name: /Mein Garten/ }));

    const activeItem = screen.getByRole('menuitem', { name: /Mein Garten/ });
    expect(activeItem).toHaveClass('Mui-selected');
    expect(within(activeItem).getByTestId('CheckIcon')).toBeInTheDocument();
    expect(screen.getByRole('menuitem', { name: /Gemeinschaftsgarten/ })).toBeInTheDocument();
    expect(screen.getByRole('menuitem', { name: 'Organisation erstellen' })).toBeInTheDocument();
  });

  it('falls back to the placeholder label when no tenant is active', () => {
    renderWithProviders(<TenantSwitcher />, {
      store: storeWith(null, [personalTenant]),
    });
    expect(screen.getByRole('button', { name: /Garten wählen/ })).toBeInTheDocument();
  });

  it('switches to another tenant and reloads the page', async () => {
    const user = userEvent.setup();
    const { store } = renderWithProviders(<TenantSwitcher />, {
      store: storeWith(personalTenant, [personalTenant, orgTenant]),
    });

    await user.click(screen.getByRole('button', { name: /Mein Garten/ }));
    await user.click(screen.getByRole('menuitem', { name: /Gemeinschaftsgarten/ }));

    await waitFor(() =>
      expect(store.getState().tenants.activeTenant?.slug).toBe('gemeinschaft'),
    );
    expect(reloadMock).toHaveBeenCalledTimes(1);
  });

  it('does not reload when selecting the already-active tenant', async () => {
    const user = userEvent.setup();
    renderWithProviders(<TenantSwitcher />, {
      store: storeWith(personalTenant, [personalTenant, orgTenant]),
    });

    await user.click(screen.getByRole('button', { name: /Mein Garten/ }));
    await user.click(screen.getByRole('menuitem', { name: /Mein Garten/ }));

    expect(reloadMock).not.toHaveBeenCalled();
    // Menu closed again.
    await waitFor(() =>
      expect(screen.queryByRole('menuitem', { name: 'Organisation erstellen' })).toBeNull(),
    );
  });

  it('navigates to the create-organization route and closes the menu', async () => {
    const user = userEvent.setup();
    renderWithProviders(<TenantSwitcher />, {
      store: storeWith(personalTenant, [personalTenant, orgTenant]),
    });

    await user.click(screen.getByRole('button', { name: /Mein Garten/ }));
    await user.click(screen.getByRole('menuitem', { name: 'Organisation erstellen' }));

    expect(reloadMock).not.toHaveBeenCalled();
    await waitFor(() =>
      expect(screen.queryByRole('menuitem', { name: 'Organisation erstellen' })).toBeNull(),
    );
  });
});
