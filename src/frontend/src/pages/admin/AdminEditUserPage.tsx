import { useState, useEffect, useCallback } from 'react';
import { useTranslation } from 'react-i18next';
import { useParams, useNavigate } from 'react-router-dom';
import Box from '@mui/material/Box';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import TextField from '@mui/material/TextField';
import Button from '@mui/material/Button';
import Alert from '@mui/material/Alert';
import Typography from '@mui/material/Typography';
import Chip from '@mui/material/Chip';
import FormControlLabel from '@mui/material/FormControlLabel';
import Switch from '@mui/material/Switch';
import CircularProgress from '@mui/material/CircularProgress';
import Divider from '@mui/material/Divider';
import IconButton from '@mui/material/IconButton';
import Table from '@mui/material/Table';
import TableBody from '@mui/material/TableBody';
import TableCell from '@mui/material/TableCell';
import TableContainer from '@mui/material/TableContainer';
import TableHead from '@mui/material/TableHead';
import TableRow from '@mui/material/TableRow';
import Select from '@mui/material/Select';
import MenuItem from '@mui/material/MenuItem';
import FormControl from '@mui/material/FormControl';
import InputLabel from '@mui/material/InputLabel';
import Autocomplete from '@mui/material/Autocomplete';
import DeleteIcon from '@mui/icons-material/Delete';
import AddIcon from '@mui/icons-material/Add';
import ArrowBackIcon from '@mui/icons-material/ArrowBack';
import PageTitle from '@/components/layout/PageTitle';
import LoadingSkeleton from '@/components/common/LoadingSkeleton';
import { useSnackbar } from 'notistack';
import {
  fetchAdminUsers,
  fetchAdminTenants,
  updateAdminUser,
  deleteAdminUser,
  fetchUserMemberships,
  addUserToTenant,
  removeUserFromTenant,
  changeUserMembershipRole,
} from '@/api/endpoints/adminPlatform';
import { isApiError, parseApiError } from '@/api/errors';
import ErrorPage from '@/pages/ErrorPage';
import StepUpConfirmDialog from '@/components/common/StepUpConfirmDialog';
import type { StepUpConfirmation } from '@/components/common/StepUpConfirmDialog';
import { toCredentialStepUpBody, toStepUpBody } from '@/utils/stepUp';
import type { AdminUser, AdminUserMembership, AdminTenant, AdminUserUpdate, TenantRole } from '@/api/types';
import { useStepUpResume } from '@/hooks/useStepUpReauth';

const GRID_2COL = {
  display: 'grid',
  gridTemplateColumns: { xs: '1fr', lg: '1fr 1fr' },
  gap: 3,
} as const;

export default function AdminEditUserPage() {
  const { key } = useParams<{ key: string }>();
  const { t } = useTranslation();
  const navigate = useNavigate();
  const { enqueueSnackbar } = useSnackbar();

  const [user, setUser] = useState<AdminUser | null>(null);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState<number | null>(null);
  const [reloadToken, setReloadToken] = useState(0);

  // Form
  const [displayName, setDisplayName] = useState('');
  const [isActive, setIsActive] = useState(true);
  const [emailVerified, setEmailVerified] = useState(false);
  const [saving, setSaving] = useState(false);
  // #1815 — back from the fresh sign-in at the identity provider: reopen the
  // account-deletion dialog it was started from (it then sends the token).
  const resumeDelete = useStepUpResume('delete-user');
  const [confirmDelete, setConfirmDelete] = useState(resumeDelete);
  // #1857 — raising another account's trust (e-mail verified, reactivated)
  // passes the admin's own step-up. The toggled switches do not survive the
  // round trip to the identity provider, so the resume context is only consumed;
  // the pending token is picked up when the admin saves again within its
  // five minutes — for this account only (#1884: token and dialog are bound to
  // the account's key, so a token obtained on another account's page stays unused).
  useStepUpResume('update-user');
  const [confirmTrustRaise, setConfirmTrustRaise] = useState(false);

  // Memberships
  const [memberships, setMemberships] = useState<AdminUserMembership[]>([]);
  const [membershipsLoading, setMembershipsLoading] = useState(false);
  const [allTenants, setAllTenants] = useState<AdminTenant[]>([]);
  const [showAddTenant, setShowAddTenant] = useState(false);
  const [selectedTenant, setSelectedTenant] = useState<AdminTenant | null>(null);
  const [selectedRole, setSelectedRole] = useState<TenantRole>('viewer');
  const [adding, setAdding] = useState(false);

  // Load user
  useEffect(() => {
    if (!key) return;
    setLoading(true);
    setLoadError(null);
    // A per-run flag, because the effect re-runs on `key` and on retry. Before
    // the `.catch` existed a late rejection from a superseded request was merely
    // unhandled; now it would call `setLoadError` and swap a healthy, fully
    // loaded page for an error state belonging to a record the operator has
    // already navigated away from. Same pattern as `useSiteWeatherForecast`.
    let cancelled = false;
    fetchAdminUsers()
      .then((users) => {
        if (cancelled) return;
        const found = users.find((u) => u.key === key);
        if (found) {
          setUser(found);
          setDisplayName(found.display_name);
          setIsActive(found.is_active);
          setEmailVerified(found.email_verified);
        }
      })
      // WITHOUT THIS `.catch` EVERY REJECTION LOOKED LIKE "NOT FOUND" (#1390).
      // A 403, a 500, a dropped connection and a rate limit all left `user` at
      // `null`, and the render below falls through to the not-found alert — so an
      // operator was told a record does not exist while it sits there untouched.
      // The rejection was also unhandled, surfacing as an unhandled promise
      // rejection rather than anywhere a user or an operator could see it.
      //
      // `<RequirePlatformAdmin>` (#1336) removed the 403-for-a-non-admin case by
      // not mounting the page at all for those callers. It does not touch the
      // rest: a platform admin who hits a 500 or loses the network still read
      // "not found" until this.
      .catch((err: unknown) => {
        if (cancelled) return;
        setLoadError(isApiError(err) ? err.statusCode : 0);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [key, reloadToken]);

  // Load memberships
  const loadMemberships = useCallback(async () => {
    if (!key) return;
    setMembershipsLoading(true);
    try {
      setMemberships(await fetchUserMemberships(key));
    } catch { /* ignore */ }
    finally { setMembershipsLoading(false); }
  }, [key]);

  useEffect(() => { loadMemberships(); }, [loadMemberships]);

  // Lazy-load tenants
  useEffect(() => {
    if (showAddTenant && allTenants.length === 0) {
      fetchAdminTenants().then(setAllTenants).catch(() => {});
    }
  }, [showAddTenant, allTenants.length]);

  const availableTenants = allTenants.filter(
    (t) => t.is_active && !memberships.some((m) => m.tenant_key === t.key),
  );

  const buildUpdate = (current: AdminUser): AdminUserUpdate => ({
    display_name: displayName !== current.display_name ? displayName : undefined,
    is_active: isActive !== current.is_active ? isActive : undefined,
    email_verified: emailVerified !== current.email_verified ? emailVerified : undefined,
  });

  // The backend asks for the admin's step-up exactly when the update turns
  // `email_verified` or `is_active` from false to true (#1857): a verified
  // address is the trust anchor of the OAuth auto-link. Lowering either, or
  // renaming, saves as before.
  const raisesTrust = (current: AdminUser): boolean =>
    (emailVerified && !current.email_verified) || (isActive && !current.is_active);

  const handleSave = async () => {
    if (!user) return;
    if (raisesTrust(user)) {
      setConfirmTrustRaise(true);
      return;
    }
    setSaving(true);
    try {
      const updated = await updateAdminUser(user.key, buildUpdate(user));
      setUser(updated);
      enqueueSnackbar(t('common.saved'), { variant: 'success' });
    } catch (err) {
      enqueueSnackbar(parseApiError(err), { variant: 'error' });
    } finally {
      setSaving(false);
    }
  };

  // The admin's OWN step-up (#1857). A rejection propagates to the dialog,
  // which shows it inside itself and stays open.
  const handleConfirmTrustRaise = async (credentials: StepUpConfirmation) => {
    if (!user) return;
    const updated = await updateAdminUser(user.key, {
      ...buildUpdate(user),
      ...toCredentialStepUpBody(credentials),
    });
    setUser(updated);
    setConfirmTrustRaise(false);
    enqueueSnackbar(t('common.saved'), { variant: 'success' });
  };

  // Erasing another account is a step-up (#1814): the TARGET's e-mail typed
  // back and the admin's OWN current password. A rejection propagates to the
  // dialog, which shows it inside itself and stays open.
  const handleDelete = async ({ echo, ...credentials }: StepUpConfirmation) => {
    if (!user) return;
    await deleteAdminUser(user.key, { confirm_email: echo, ...toStepUpBody(credentials) });
    setConfirmDelete(false);
    enqueueSnackbar(t('pages.auth.adminUserDeleted'), { variant: 'success' });
    navigate('/settings#platform');
  };

  const handleAddToTenant = async () => {
    if (!key || !selectedTenant) return;
    setAdding(true);
    try {
      const m = await addUserToTenant(key, { tenant_key: selectedTenant.key, role: selectedRole });
      setMemberships((prev) => [...prev, m]);
      setSelectedTenant(null);
      setSelectedRole('viewer');
      setShowAddTenant(false);
      enqueueSnackbar(t('pages.auth.adminMemberAdded'), { variant: 'success' });
    } catch (err) {
      enqueueSnackbar(parseApiError(err), { variant: 'error' });
    } finally {
      setAdding(false);
    }
  };

  const handleRemoveFromTenant = async (m: AdminUserMembership) => {
    if (!key) return;
    try {
      await removeUserFromTenant(key, m.membership_key);
      setMemberships((prev) => prev.filter((x) => x.membership_key !== m.membership_key));
      enqueueSnackbar(t('pages.auth.adminMemberRemoved'), { variant: 'success' });
    } catch (err) {
      enqueueSnackbar(parseApiError(err), { variant: 'error' });
    }
  };

  const handleRoleChange = async (m: AdminUserMembership, newRole: TenantRole) => {
    if (!key) return;
    try {
      const updated = await changeUserMembershipRole(key, m.membership_key, newRole);
      setMemberships((prev) => prev.map((x) => (x.membership_key === m.membership_key ? updated : x)));
      enqueueSnackbar(t('common.saved'), { variant: 'success' });
    } catch (err) {
      enqueueSnackbar(parseApiError(err), { variant: 'error' });
    }
  };

  if (loading) return <LoadingSkeleton variant="form" />;
  // THREE ANSWERS, NOT ONE (#1390). A failed request is not a missing record, and
  // only the third of these is genuinely "not found": the list came back and the
  // key was not in it.
  if (loadError !== null) {
    // `0` means the failure carried no status at all — a dropped connection, DNS,
    // a blocked request. Rendering that as 500 tells an offline operator the
    // server failed, which is a different and wrong diagnosis. 503 is the closest
    // honest answer: the service could not be reached.
    return (
      <ErrorPage
        statusCode={loadError === 0 ? 503 : loadError}
        onRetry={() => setReloadToken((n) => n + 1)}
        landmark={false}
      />
    );
  }
  if (!user) return <Alert severity="error">{t('pages.admin.userNotFound')}</Alert>;

  return (
    <Box sx={{ mt: 2 }}>
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
        <IconButton onClick={() => navigate('/settings#platform')} data-testid="back-btn">
          <ArrowBackIcon />
        </IconButton>
        <PageTitle title={`${t('pages.auth.editUserTitle')}: ${user.display_name}`} />
        <Chip
          label={user.is_active ? t('pages.auth.adminStatusActive') : t('pages.auth.adminStatusInactive')}
          color={user.is_active ? 'success' : 'default'}
          size="small"
        />
        {!user.email_verified && <Chip label={t('pages.auth.adminUnverified')} size="small" color="warning" variant="outlined" />}
      </Box>

      <Box sx={GRID_2COL}>
        {/* Left: User properties */}
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              {t('pages.auth.adminUserDisplayName')}
            </Typography>
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2.5 }}>
              <TextField
                label={t('pages.auth.adminUserDisplayName')}
                value={displayName}
                onChange={(e) => setDisplayName(e.target.value)}
                fullWidth
                required
                data-testid="edit-user-display-name"
              />
              <TextField
                label={t('pages.auth.adminUserEmail')}
                value={user.email}
                fullWidth
                disabled
                data-testid="edit-user-email"
              />
              <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
                <TextField label="Key" value={user.key} disabled sx={{ flex: 1 }} />
                <TextField
                  label={t('pages.auth.adminUserLastLogin')}
                  value={user.last_login_at ? new Date(user.last_login_at).toLocaleString() : '—'}
                  disabled
                  sx={{ flex: 1 }}
                />
              </Box>
              <FormControlLabel
                control={<Switch checked={isActive} onChange={(e) => setIsActive(e.target.checked)} data-testid="edit-user-active-switch" />}
                label={t('pages.auth.adminUserIsActive')}
              />
              <FormControlLabel
                control={<Switch checked={emailVerified} onChange={(e) => setEmailVerified(e.target.checked)} data-testid="edit-user-email-verified-switch" />}
                label={t('pages.auth.adminUserEmailVerified')}
              />
              <Button
                variant="contained"
                onClick={handleSave}
                disabled={saving || !displayName.trim()}
                startIcon={saving ? <CircularProgress size={16} /> : undefined}
                sx={{ alignSelf: 'flex-start' }}
                data-testid="edit-user-save"
              >
                {t('common.save')}
              </Button>
            </Box>
            <StepUpConfirmDialog
              open={confirmTrustRaise}
              title={t('pages.auth.adminUpdateUserStepUpTitle')}
              description={t('pages.auth.adminUpdateUserStepUpDescription', {
                name: user.display_name,
                email: user.email,
              })}
              passwordLabel={t('pages.auth.adminDeleteUserPasswordLabel')}
              passwordHelper={t('pages.auth.adminDeleteUserPasswordHelper')}
              confirmLabel={t('pages.auth.adminUpdateUserStepUpConfirm')}
              confirmColor="primary"
              testIdPrefix="update-user"
              stepUpAction="admin_account_update"
              stepUpTarget={user.key}
              onConfirm={handleConfirmTrustRaise}
              onCancel={() => setConfirmTrustRaise(false)}
            />

            {/* Danger zone */}
            <Divider sx={{ my: 3 }} />
            <Typography variant="subtitle2" color="error" gutterBottom>
              {t('pages.auth.dangerZone')}
            </Typography>
            <Button variant="outlined" color="error" onClick={() => setConfirmDelete(true)} data-testid="delete-user-btn">
              {t('pages.auth.adminDeleteUser')}
            </Button>
            <StepUpConfirmDialog
              open={confirmDelete}
              title={t('pages.auth.adminDeleteUserDialogTitle')}
              description={t('pages.auth.adminDeleteUserConfirm', { name: user.display_name, email: user.email })}
              echoLabel={t('pages.auth.adminDeleteUserEmailLabel')}
              echoHelper={t('pages.auth.adminDeleteUserEmailHelper', { email: user.email })}
              expectedEcho={user.email}
              echoMatch="caseInsensitive"
              echoInputType="email"
              passwordLabel={t('pages.auth.adminDeleteUserPasswordLabel')}
              passwordHelper={t('pages.auth.adminDeleteUserPasswordHelper')}
              confirmLabel={t('pages.auth.adminConfirmDelete')}
              testIdPrefix="delete-user"
              stepUpAction="admin_account_erasure"
              stepUpTarget={user.key}
              testIds={{ echo: 'delete-user-email', confirm: 'confirm-delete-user-btn' }}
              onConfirm={handleDelete}
              onCancel={() => setConfirmDelete(false)}
            />
          </CardContent>
        </Card>

        {/* Right: Organization memberships */}
        <Card>
          <CardContent>
            <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
              <Typography variant="h6">
                {t('pages.auth.adminUserTenants')} <Chip label={memberships.length} size="small" />
              </Typography>
              {!showAddTenant && (
                <Button size="small" startIcon={<AddIcon />} onClick={() => setShowAddTenant(true)} data-testid="show-add-tenant-btn">
                  {t('pages.auth.adminAssignToOrg')}
                </Button>
              )}
            </Box>

            {/* Add to org */}
            {showAddTenant && (
              <Box sx={{ display: 'flex', gap: 1, alignItems: 'flex-start', p: 2, mb: 2, border: 1, borderColor: 'divider', borderRadius: 1, flexWrap: 'wrap' }}>
                <Autocomplete
                  size="small"
                  options={availableTenants}
                  getOptionLabel={(opt) => `${opt.name} (${opt.slug})`}
                  value={selectedTenant}
                  onChange={(_, v) => setSelectedTenant(v)}
                  renderInput={(params) => <TextField {...params} label={t('pages.auth.adminSelectOrg')} />}
                  sx={{ flex: 1, minWidth: 220 }}
                />
                <FormControl size="small" sx={{ minWidth: 140 }}>
                  <InputLabel>{t('pages.auth.adminMemberRole')}</InputLabel>
                  <Select value={selectedRole} label={t('pages.auth.adminMemberRole')} onChange={(e) => setSelectedRole(e.target.value as TenantRole)}>
                    <MenuItem value="lead">{t('enums.tenantRole.lead')}</MenuItem>
                    <MenuItem value="grower">{t('enums.tenantRole.grower')}</MenuItem>
                    <MenuItem value="viewer">{t('enums.tenantRole.viewer')}</MenuItem>
                  </Select>
                </FormControl>
                <Button variant="contained" size="small" onClick={handleAddToTenant} disabled={adding || !selectedTenant}
                  startIcon={adding ? <CircularProgress size={14} /> : undefined} sx={{ mt: 0.25 }}>
                  {t('common.add')}
                </Button>
                <Button size="small" onClick={() => { setShowAddTenant(false); setSelectedTenant(null); }} sx={{ mt: 0.25 }}>
                  {t('common.cancel')}
                </Button>
              </Box>
            )}

            {/* Memberships table */}
            {membershipsLoading ? (
              <Box sx={{ display: 'flex', justifyContent: 'center', py: 3 }}><CircularProgress /></Box>
            ) : (
              <TableContainer>
                <Table size="small">
                  <TableHead>
                    <TableRow>
                      <TableCell>{t('pages.auth.adminTenantName')}</TableCell>
                      <TableCell>Slug</TableCell>
                      <TableCell>{t('pages.auth.adminMemberRole')}</TableCell>
                      <TableCell align="right" />
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {memberships.map((m) => (
                      <TableRow key={m.membership_key}>
                        <TableCell>
                          <Typography variant="body2" sx={{ fontWeight: 500 }}>{m.tenant_name}</Typography>
                        </TableCell>
                        <TableCell>
                          <Typography variant="body2" sx={{ fontFamily: 'monospace' }}>{m.tenant_slug}</Typography>
                        </TableCell>
                        <TableCell>
                          <Select
                            size="small"
                            value={m.role}
                            onChange={(e) => handleRoleChange(m, e.target.value as TenantRole)}
                            variant="standard"
                            sx={{ fontSize: '0.8125rem' }}
                            data-testid={`role-select-${m.tenant_key}`}
                          >
                            <MenuItem value="lead">{t('enums.tenantRole.lead')}</MenuItem>
                            <MenuItem value="grower">{t('enums.tenantRole.grower')}</MenuItem>
                            <MenuItem value="viewer">{t('enums.tenantRole.viewer')}</MenuItem>
                          </Select>
                        </TableCell>
                        <TableCell align="right">
                          <IconButton size="small" onClick={() => handleRemoveFromTenant(m)} data-testid={`remove-membership-${m.tenant_key}`}>
                            <DeleteIcon fontSize="small" />
                          </IconButton>
                        </TableCell>
                      </TableRow>
                    ))}
                    {memberships.length === 0 && (
                      <TableRow>
                        <TableCell colSpan={4} align="center">
                          <Typography variant="body2" color="text.secondary" sx={{ py: 2 }}>
                            {t('pages.auth.adminNoMemberships')}
                          </Typography>
                        </TableCell>
                      </TableRow>
                    )}
                  </TableBody>
                </Table>
              </TableContainer>
            )}
          </CardContent>
        </Card>
      </Box>
    </Box>
  );
}
