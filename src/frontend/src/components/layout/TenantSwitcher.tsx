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
import ArrowDropDownIcon from '@mui/icons-material/ArrowDropDown';
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAppDispatch, useAppSelector } from '@/store/hooks';
import { switchTenant } from '@/store/slices/tenantSlice';

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

  const handleSwitch = (slug: string) => {
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
    window.location.reload();
  };

  const handleCreateOrg = () => {
    handleClose();
    navigate('/tenants/create');
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
            onClick={() => handleSwitch(tenant.slug)}
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
        <MenuItem onClick={handleCreateOrg}>
          <ListItemIcon>
            <AddIcon fontSize="small" />
          </ListItemIcon>
          {t('pages.tenants.createOrganization')}
        </MenuItem>
      </Menu>
    </>
  );
}
