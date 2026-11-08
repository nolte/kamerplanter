import { useTranslation } from 'react-i18next';
import Button from '@mui/material/Button';
import Menu from '@mui/material/Menu';
import MenuItem from '@mui/material/MenuItem';
import ListItemIcon from '@mui/material/ListItemIcon';
import ListItemText from '@mui/material/ListItemText';
import Typography from '@mui/material/Typography';
import Divider from '@mui/material/Divider';
import CheckIcon from '@mui/icons-material/Check';
import GroupsIcon from '@mui/icons-material/Groups';
import PersonIcon from '@mui/icons-material/Person';
import AddIcon from '@mui/icons-material/Add';
import SettingsIcon from '@mui/icons-material/Settings';
import ArrowDropDownIcon from '@mui/icons-material/ArrowDropDown';
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAppDispatch, useAppSelector } from '@/store/hooks';
import { switchTenant } from '@/store/slices/tenantSlice';
import { clearOfflineData } from '@/pwa/offlineData';

export default function TenantSwitcher() {
  const { t } = useTranslation();
  const dispatch = useAppDispatch();
  const navigate = useNavigate();
  const myTenants = useAppSelector((s) => s.tenants.myTenants);
  const activeTenant = useAppSelector((s) => s.tenants.activeTenant);

  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);

  if (myTenants.length === 0) return null;

  const handleOpen = (event: React.MouseEvent<HTMLElement>) => {
    setAnchorEl(event.currentTarget);
  };

  const handleClose = () => {
    setAnchorEl(null);
  };

  const handleSwitch = async (slug: string) => {
    if (slug === activeTenant?.slug) {
      handleClose();
      return;
    }
    dispatch(switchTenant(slug));
    handleClose();
    // Reload to fetch all data for the new tenant.
    //
    // Explicit non-goal (#1091 A-4 AC 5): cache invalidation per slice. The
    // switch changes what *every* tenant-aware request means — the `/t/{slug}/`
    // path of `tenantClient` and, since #1091, the `X-Active-Tenant` header the
    // global client attaches to the species / cultivar / botanical-family /
    // companion-planting catalogues. `switchTenant` has already moved both
    // sources (Redux and `setActiveTenantSlug`), so a full reload re-issues every
    // request under the new tenant with no invalidation list to keep in sync — a
    // list that would silently rot each time a new tenant-aware slice is added.
    //
    // REQ-053 WP 9.1 (G-W9 b): the service worker's API cache and IndexedDB are
    // emptied completely BEFORE the reload, so the next tenant never reads the
    // previous one's answers offline. Pinned by
    // test/guards/offlineDataClearedOnSessionChange.test.ts. The offline write buffer (WP 9.4) is the
    // exception: the previous garden's unsent entries stay bound to it and are sent when the user returns
    // there (UI-NFR-012 R-050/R-051) — nothing is lost, nothing is shown in the new garden.
    await clearOfflineData();
    window.location.reload();
  };

  const handleCreateOrg = () => {
    handleClose();
    navigate('/tenants/create');
  };

  // #2166 — the garden settings list the gardens whose deletion is scheduled (they are missing
  // from this menu: such a garden resolves for nobody) and offer their management the cancellation.
  const handleGardenSettings = () => {
    handleClose();
    navigate('/tenants/settings');
  };

  return (
    <>
      <Button
        color="inherit"
        onClick={handleOpen}
        endIcon={<ArrowDropDownIcon />}
        sx={{ textTransform: 'none', mr: 1 }}
        size="small"
      >
        {/* `data-tenant-selected` distinguishes the two things this label can
            say. Without it "the switcher has rendered a tenant name" and "the
            switcher is asking you to pick one" are the same observation from
            the outside — a reader waiting for non-empty text accepts the
            placeholder, and an assertion on the active tenant passes on
            "Garten wählen". The placeholder branch is reachable:
            `clearActiveTenant` (store.ts, stale-slug recovery) nulls the active
            tenant while deliberately keeping `myTenants`, so the button stays
            in the toolbar with nothing selected. */}
        <Typography
          variant="body2"
          noWrap
          sx={{ maxWidth: 150 }}
          data-testid="tenant-switcher-active-name"
          data-tenant-selected={activeTenant ? 'true' : 'false'}
        >
          {activeTenant?.name ?? t('pages.tenants.selectTenant')}
        </Typography>
      </Button>
      <Menu
        anchorEl={anchorEl}
        open={Boolean(anchorEl)}
        onClose={handleClose}
        transformOrigin={{ horizontal: 'right', vertical: 'top' }}
        anchorOrigin={{ horizontal: 'right', vertical: 'bottom' }}
        data-testid="tenant-switcher-menu"
      >
        {myTenants.map((tenant) => (
          <MenuItem
            key={tenant.key}
            selected={tenant.slug === activeTenant?.slug}
            onClick={() => void handleSwitch(tenant.slug)}
            data-testid={`tenant-switcher-item-${tenant.slug}`}
          >
            <ListItemIcon>
              {tenant.tenant_type === 'organization' ? (
                <GroupsIcon fontSize="small" />
              ) : (
                <PersonIcon fontSize="small" />
              )}
            </ListItemIcon>
            <ListItemText primary={tenant.name} />
            {tenant.slug === activeTenant?.slug && (
              <CheckIcon fontSize="small" sx={{ ml: 1 }} />
            )}
          </MenuItem>
        ))}
        <Divider />
        <MenuItem onClick={handleGardenSettings} data-testid="tenant-switcher-garden-settings">
          <ListItemIcon>
            <SettingsIcon fontSize="small" />
          </ListItemIcon>
          {t('pages.tenants.gardenSettings')}
        </MenuItem>
        <MenuItem onClick={handleCreateOrg} data-testid="tenant-switcher-create-organization">
          <ListItemIcon>
            <AddIcon fontSize="small" />
          </ListItemIcon>
          {t('pages.tenants.createOrganization')}
        </MenuItem>
      </Menu>
    </>
  );
}
