import { useCallback, useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useNavigate } from 'react-router-dom';
import Alert from '@mui/material/Alert';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import Chip from '@mui/material/Chip';
import IconButton from '@mui/material/IconButton';
import Table from '@mui/material/Table';
import TableBody from '@mui/material/TableBody';
import TableCell from '@mui/material/TableCell';
import TableContainer from '@mui/material/TableContainer';
import TableHead from '@mui/material/TableHead';
import TableRow from '@mui/material/TableRow';
import Typography from '@mui/material/Typography';
import ApartmentIcon from '@mui/icons-material/Apartment';
import BusinessIcon from '@mui/icons-material/Business';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import DataUsageIcon from '@mui/icons-material/DataUsage';
import EditIcon from '@mui/icons-material/Edit';
import GroupIcon from '@mui/icons-material/Group';
import HomeIcon from '@mui/icons-material/Home';
import PeopleIcon from '@mui/icons-material/People';
import ScheduleIcon from '@mui/icons-material/Schedule';
import UnarchiveIcon from '@mui/icons-material/Unarchive';
import VpnKeyIcon from '@mui/icons-material/VpnKey';
import PageTitle from '@/components/layout/PageTitle';
import LoadingSkeleton from '@/components/common/LoadingSkeleton';
import OptionsLoadError from '@/components/common/OptionsLoadError';
import TenantStatusChip from '@/components/tenants/TenantStatusChip';
import { PestContributionsAdminCard } from '@/components/admin/PestContributionsAdminCard';
import { fetchAdminStats, fetchAdminTenants, fetchAdminUsers } from '@/api/endpoints/adminPlatform';
import type { AdminPlatformStats, AdminTenant, AdminUser } from '@/api/types';
import { isFullMode, KAMERPLANTER_MODE } from '@/config/mode';
import { usePlatformAdmin } from '@/hooks/usePlatformAdmin';
import { captureHandledError } from '@/observability/errorTracking';

/** Responsive grid that fills the available width: stacked on phones, two columns from `md`. */
const GRID_2COL = {
  display: 'grid',
  gridTemplateColumns: { xs: '1fr', md: '1fr 1fr' },
  gap: 2,
} as const;

/** The three operating-mode cards: one column on phones, two from `sm`, three from `lg`. */
const GRID_3COL = {
  display: 'grid',
  gridTemplateColumns: { xs: '1fr', sm: '1fr 1fr', lg: '1fr 1fr 1fr' },
  gap: 2,
} as const;

/**
 * Admin › Platform — the platform administrator's hub (F-12, R-17, #2935).
 *
 * Until F-12 this content was the *platform* tab of the personal settings page,
 * which was also the only way into the admin pages. It now has its own route,
 * `/admin/platform`, reached from the sidebar entry only platform admins see, and
 * every admin page points its back link and breadcrumb here
 * (`ADMIN_PLATFORM_PATH`).
 *
 * The page shows the same content the tab showed — operating mode, statistics,
 * the ways into the admin pages, the tenant and user tables — plus the
 * pest-contribution moderation card, which used to sit in the integrations tab
 * although it is platform-admin-only.
 *
 * Gate: the route is wrapped in `<RequirePlatformAdmin>` (`PLATFORM_ADMIN_ROUTES`),
 * and the three `/admin/platform` reads additionally run only for a platform
 * admin in full mode — the mode in which those endpoints are mounted. In light
 * mode (REQ-027) the sole operator counts as platform admin and sees the mode
 * cards and the moderation card; there are no tenants or users to administer.
 * The reads happen once per visit, exactly as the tab did (MT-045.9, #2144):
 * who is an admin is the `/users/me` flag, never inferred from a 403.
 */
export default function AdminPlatformPage() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const isPlatformAdminUser = usePlatformAdmin();

  const [adminStats, setAdminStats] = useState<AdminPlatformStats | null>(null);
  const [adminTenants, setAdminTenants] = useState<AdminTenant[]>([]);
  const [adminUsers, setAdminUsers] = useState<AdminUser[]>([]);
  // Whether the admin data has been read (once per visit).
  const [adminLoaded, setAdminLoaded] = useState(false);
  // The admin tables render only after a successful read: a 403 here means the
  // flag is stale (the role was taken away in the meantime), and the page then
  // shows a load error with retry rather than empty tables (#3037).
  const [adminDataOk, setAdminDataOk] = useState(false);
  const [adminLoading, setAdminLoading] = useState(false);

  const loadAdminData = useCallback(async () => {
    if (!isFullMode || !isPlatformAdminUser) return;
    setAdminLoading(true);
    try {
      const [stats, tenants, users] = await Promise.all([
        fetchAdminStats(),
        fetchAdminTenants(),
        fetchAdminUsers(),
      ]);
      setAdminStats(stats);
      setAdminTenants(tenants);
      setAdminUsers(users);
      setAdminDataOk(true);
    } catch (err) {
      // Rendered below as a load error with retry, not as an absent admin section (#3037).
      captureHandledError(err, { source: 'AdminPlatformPage.adminData' });
      setAdminDataOk(false);
    } finally {
      setAdminLoaded(true);
      setAdminLoading(false);
    }
  }, [isPlatformAdminUser]);

  useEffect(() => {
    if (isFullMode && isPlatformAdminUser && !adminLoaded && !adminLoading) {
      void loadAdminData();
    }
  }, [isPlatformAdminUser, adminLoaded, adminLoading, loadAdminData]);

  return (
    <Box data-testid="admin-platform-page">
      <PageTitle title={t('pages.adminPlatform.title')} sx={{ mb: 1 }} />
      <Typography variant="body1" color="text.secondary" sx={{ mb: 3 }}>
        {t('pages.adminPlatform.intro')}
      </Typography>
      <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
        {/* Mode Cards in 3-col grid */}
        <Box sx={GRID_3COL}>
          {/* Light Mode */}
          <Card
            variant="outlined"
            sx={{
              borderColor: KAMERPLANTER_MODE === 'light' ? 'primary.main' : 'divider',
              borderWidth: KAMERPLANTER_MODE === 'light' ? 2 : 1,
            }}
          >
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, mb: 1 }}>
                <HomeIcon color={KAMERPLANTER_MODE === 'light' ? 'primary' : 'action'} />
                <Typography variant="h6" component="h2">{t('pages.auth.platformModeLight')}</Typography>
                {KAMERPLANTER_MODE === 'light' && (
                  <Chip icon={<CheckCircleIcon />} label={t('pages.auth.platformModeActive')} color="primary" size="small" />
                )}
              </Box>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 1.5 }}>
                {t('pages.auth.platformModeLightDescription')}
              </Typography>
              <Box component="ul" sx={{ m: 0, pl: 2.5 }}>
                {t('pages.auth.platformModeLightFeatures').split(';').map((f) => (
                  <Typography component="li" variant="body2" key={f} sx={{ mb: 0.25 }}>{f}</Typography>
                ))}
              </Box>
            </CardContent>
          </Card>

          {/* Full Mode */}
          <Card
            variant="outlined"
            sx={{
              borderColor: KAMERPLANTER_MODE === 'full' ? 'primary.main' : 'divider',
              borderWidth: KAMERPLANTER_MODE === 'full' ? 2 : 1,
            }}
          >
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, mb: 1 }}>
                <GroupIcon color={KAMERPLANTER_MODE === 'full' ? 'primary' : 'action'} />
                <Typography variant="h6" component="h2">{t('pages.auth.platformModeFull')}</Typography>
                {KAMERPLANTER_MODE === 'full' && (
                  <Chip icon={<CheckCircleIcon />} label={t('pages.auth.platformModeActive')} color="primary" size="small" />
                )}
              </Box>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 1.5 }}>
                {t('pages.auth.platformModeFullDescription')}
              </Typography>
              <Box component="ul" sx={{ m: 0, pl: 2.5 }}>
                {t('pages.auth.platformModeFullFeatures').split(';').map((f) => (
                  <Typography component="li" variant="body2" key={f} sx={{ mb: 0.25 }}>{f}</Typography>
                ))}
              </Box>
            </CardContent>
          </Card>

          {/* Enterprise Mode */}
          <Card variant="outlined" sx={{ borderColor: 'divider', opacity: 0.7 }}>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, mb: 1 }}>
                <BusinessIcon color="action" />
                <Typography variant="h6" component="h2">{t('pages.auth.platformModeEnterprise')}</Typography>
                <Chip icon={<ScheduleIcon />} label={t('pages.auth.platformModeComingSoon')} size="small" variant="outlined" />
              </Box>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 1.5 }}>
                {t('pages.auth.platformModeEnterpriseDescription')}
              </Typography>
              <Box component="ul" sx={{ m: 0, pl: 2.5 }}>
                {t('pages.auth.platformModeEnterpriseFeatures').split(';').map((f) => (
                  <Typography component="li" variant="body2" key={f} sx={{ mb: 0.25 }}>{f}</Typography>
                ))}
              </Box>
            </CardContent>
          </Card>
        </Box>

        <Alert severity="info">
          <Typography variant="body2">
            {t('pages.auth.platformModeEnvHint')}
            {' '}
            <Typography component="code" variant="body2" sx={{ fontFamily: 'monospace' }}>
              KAMERPLANTER_MODE=light | full
            </Typography>
          </Typography>
        </Alert>

        {isFullMode && isPlatformAdminUser && adminLoaded && !adminLoading && !adminDataOk && (
          <OptionsLoadError
            messageKey="errors.loadFailed"
            onRetry={() => void loadAdminData()}
            data-testid="admin-data-load-error"
          />
        )}

        {/* Admin: Stats + Org/User tables */}
        {isFullMode && isPlatformAdminUser && adminDataOk && (
          <>
            {/* Stats in 4-col grid */}
            {adminStats && (
              <Box sx={{ display: 'grid', gridTemplateColumns: { xs: 'repeat(2, 1fr)', sm: 'repeat(4, 1fr)' }, gap: 2 }}>
                {([
                  { value: adminStats.active_users, label: t('pages.auth.adminActiveUsers') },
                  { value: adminStats.total_users, label: t('pages.auth.adminTotalUsers') },
                  { value: adminStats.active_tenants, label: t('pages.auth.adminActiveTenants') },
                  { value: adminStats.total_memberships, label: t('pages.auth.adminTotalMemberships') },
                ] as const).map(({ value, label }) => (
                  <Card key={label} variant="outlined">
                    <CardContent sx={{ textAlign: 'center', py: 2, '&:last-child': { pb: 2 } }}>
                      <Typography variant="h3" component="p" sx={{ fontWeight: 300 }}>{value}</Typography>
                      <Typography variant="caption" color="text.secondary">{label}</Typography>
                    </CardContent>
                  </Card>
                ))}
              </Box>
            )}

            {/* #1906: sign-in providers (OIDC) — its own page, platform admin only */}
            <Card variant="outlined" data-testid="admin-oidc-card">
              <CardContent
                sx={{ display: 'flex', flexDirection: { xs: 'column', sm: 'row' }, alignItems: { sm: 'center' }, gap: 2 }}
              >
                <VpnKeyIcon color="primary" aria-hidden />
                <Box sx={{ flex: 1 }}>
                  <Typography variant="h6" component="h2">{t('pages.admin.oidc.navCardTitle')}</Typography>
                  <Typography variant="body2" color="text.secondary">
                    {t('pages.admin.oidc.navCardDescription')}
                  </Typography>
                </Box>
                <Button
                  variant="outlined"
                  onClick={() => navigate('/admin/oidc-providers')}
                  data-testid="admin-oidc-open"
                >
                  {t('pages.admin.oidc.navCardOpen')}
                </Button>
              </CardContent>
            </Card>

            {/* REQ-056 §15 (AK-45): the plan catalogue — its own page, platform admin only */}
            <Card variant="outlined" data-testid="admin-plans-card">
              <CardContent
                sx={{ display: 'flex', flexDirection: { xs: 'column', sm: 'row' }, alignItems: { sm: 'center' }, gap: 2 }}
              >
                <DataUsageIcon color="primary" aria-hidden />
                <Box sx={{ flex: 1 }}>
                  <Typography variant="h6" component="h2">{t('pages.plans.navCardTitle')}</Typography>
                  <Typography variant="body2" color="text.secondary">
                    {t('pages.plans.navCardDescription')}
                  </Typography>
                </Box>
                <Button
                  variant="outlined"
                  onClick={() => navigate('/admin/plans')}
                  sx={{ minHeight: { xs: 48, sm: 36 } }}
                  data-testid="admin-plans-open"
                >
                  {t('pages.plans.navCardOpen')}
                </Button>
              </CardContent>
            </Card>

            {/* REQ-056 §8.4 / §15 (#2138): import a tenant archive — its own page, platform admin only */}
            <Card variant="outlined" data-testid="admin-tenant-imports-card">
              <CardContent
                sx={{ display: 'flex', flexDirection: { xs: 'column', sm: 'row' }, alignItems: { sm: 'center' }, gap: 2 }}
              >
                <UnarchiveIcon color="primary" aria-hidden />
                <Box sx={{ flex: 1 }}>
                  <Typography variant="h6" component="h2">{t('pages.tenantImports.navCardTitle')}</Typography>
                  <Typography variant="body2" color="text.secondary">
                    {t('pages.tenantImports.navCardDescription')}
                  </Typography>
                </Box>
                <Button
                  variant="outlined"
                  onClick={() => navigate('/admin/tenant-imports')}
                  sx={{ minHeight: { xs: 48, sm: 36 } }}
                  data-testid="admin-tenant-imports-open"
                >
                  {t('pages.tenantImports.navCardOpen')}
                </Button>
              </CardContent>
            </Card>

            {/* Organizations & Users in 2-col grid on large, stacked on small */}
            <Box sx={GRID_2COL}>
              {/* Organizations */}
              <Card>
                <CardContent>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, mb: 2 }}>
                    <ApartmentIcon color="primary" />
                    <Typography variant="h6" component="h2">{t('pages.auth.adminTenantsTitle')}</Typography>
                    <Chip label={adminTenants.length} size="small" />
                  </Box>
                  <TableContainer>
                    <Table size="small">
                      <TableHead>
                        <TableRow>
                          <TableCell>{t('pages.auth.adminTenantName')}</TableCell>
                          <TableCell>{t('pages.auth.adminTenantType')}</TableCell>
                          <TableCell align="right">{t('pages.auth.adminTenantMembers')}</TableCell>
                          <TableCell>{t('pages.auth.adminTenantStatus')}</TableCell>
                          <TableCell align="right" />
                        </TableRow>
                      </TableHead>
                      <TableBody>
                        {adminTenants.map((tenant) => (
                          <TableRow key={tenant.key}>
                            <TableCell>
                              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                                <Typography variant="body2" sx={{ fontWeight: 500 }}>{tenant.name}</Typography>
                                {tenant.is_platform && (
                                  <Chip label={t('pages.auth.platformChip')} size="small" color="warning" variant="outlined" />
                                )}
                              </Box>
                              <Typography variant="caption" color="text.secondary" sx={{ fontFamily: 'monospace' }}>
                                {tenant.slug}
                              </Typography>
                            </TableCell>
                            <TableCell>
                              <Chip
                                label={t(`enums.tenantType.${tenant.tenant_type}`)}
                                size="small"
                                variant="outlined"
                                color={tenant.tenant_type === 'organization' ? 'info' : 'default'}
                              />
                            </TableCell>
                            <TableCell align="right">{tenant.member_count}</TableCell>
                            <TableCell>
                              <TenantStatusChip
                                status={tenant.status}
                                isActive={tenant.is_active}
                                testId={`tenant-status-${tenant.key}`}
                              />
                            </TableCell>
                            <TableCell align="right">
                              <IconButton
                                size="small"
                                onClick={() => navigate(`/admin/tenants/${tenant.key}`)}
                                data-testid={`edit-tenant-${tenant.key}`}
                                aria-label={t('pages.auth.editTenantTitle')}
                              >
                                <EditIcon fontSize="small" />
                              </IconButton>
                            </TableCell>
                          </TableRow>
                        ))}
                        {adminTenants.length === 0 && (
                          <TableRow>
                            <TableCell colSpan={5} align="center">
                              <Typography variant="body2" color="text.secondary" sx={{ py: 2 }}>
                                {t('pages.auth.adminNoTenants')}
                              </Typography>
                            </TableCell>
                          </TableRow>
                        )}
                      </TableBody>
                    </Table>
                  </TableContainer>
                </CardContent>
              </Card>

              {/* Users */}
              <Card>
                <CardContent>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, mb: 2 }}>
                    <PeopleIcon color="primary" />
                    <Typography variant="h6" component="h2">{t('pages.auth.adminUsersTitle')}</Typography>
                    <Chip label={adminUsers.length} size="small" />
                  </Box>
                  <TableContainer>
                    <Table size="small">
                      <TableHead>
                        <TableRow>
                          <TableCell>{t('pages.auth.adminUserName')}</TableCell>
                          <TableCell>{t('pages.auth.adminUserTenants')}</TableCell>
                          <TableCell>{t('pages.auth.adminUserStatus')}</TableCell>
                          <TableCell align="right" />
                        </TableRow>
                      </TableHead>
                      <TableBody>
                        {adminUsers.map((u) => (
                          <TableRow key={u.key}>
                            <TableCell>
                              <Typography variant="body2" sx={{ fontWeight: 500 }}>{u.display_name}</Typography>
                              <Typography variant="caption" color="text.secondary" sx={{ fontFamily: 'monospace' }}>
                                {u.email}
                              </Typography>
                            </TableCell>
                            <TableCell>
                              <Box sx={{ display: 'flex', gap: 0.5, flexWrap: 'wrap' }}>
                                {u.roles.map((r) => (
                                  <Chip
                                    key={r.tenant_key}
                                    label={`${r.tenant_name} (${r.role})`}
                                    size="small"
                                    variant="outlined"
                                    color={r.role === 'lead' ? 'warning' : r.role === 'grower' ? 'success' : 'default'}
                                  />
                                ))}
                                {u.roles.length === 0 && (
                                  <Typography variant="caption" color="text.secondary">
                                    {t('pages.auth.adminNoMemberships')}
                                  </Typography>
                                )}
                              </Box>
                            </TableCell>
                            <TableCell>
                              <Box sx={{ display: 'flex', gap: 0.5, flexDirection: 'column', alignItems: 'flex-start' }}>
                                <Chip
                                  label={u.is_active ? t('pages.auth.adminStatusActive') : t('pages.auth.adminStatusInactive')}
                                  size="small"
                                  color={u.is_active ? 'success' : 'default'}
                                />
                                {!u.email_verified && (
                                  <Chip label={t('pages.auth.adminUnverified')} size="small" color="warning" variant="outlined" />
                                )}
                              </Box>
                            </TableCell>
                            <TableCell align="right">
                              <IconButton
                                size="small"
                                onClick={() => navigate(`/admin/users/${u.key}`)}
                                data-testid={`edit-user-${u.key}`}
                                aria-label={t('pages.auth.editUserTitle')}
                              >
                                <EditIcon fontSize="small" />
                              </IconButton>
                            </TableCell>
                          </TableRow>
                        ))}
                        {adminUsers.length === 0 && (
                          <TableRow>
                            <TableCell colSpan={4} align="center">
                              <Typography variant="body2" color="text.secondary" sx={{ py: 2 }}>
                                {t('pages.auth.adminNoUsers')}
                              </Typography>
                            </TableCell>
                          </TableRow>
                        )}
                      </TableBody>
                    </Table>
                  </TableContainer>
                </CardContent>
              </Card>
            </Box>
          </>
        )}

        {isFullMode && isPlatformAdminUser && adminLoading && !adminLoaded && (
          <LoadingSkeleton variant="card" />
        )}

        {/* REQ-010 / SEC-003 — moderate user-contributed pest photos and promote the
            good ones to global visibility. Platform-admin only on both sides; it used
            to sit in the integrations tab of the settings page (F-12). */}
        {isPlatformAdminUser && <PestContributionsAdminCard />}
      </Box>
    </Box>
  );
}
