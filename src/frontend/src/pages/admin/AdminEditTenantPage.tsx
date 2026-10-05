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
import FormControlLabel from '@mui/material/FormControlLabel';
import Switch from '@mui/material/Switch';
import CircularProgress from '@mui/material/CircularProgress';
import Divider from '@mui/material/Divider';
import IconButton from '@mui/material/IconButton';
import Chip from '@mui/material/Chip';
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
import PersonAddIcon from '@mui/icons-material/PersonAdd';
import ArrowBackIcon from '@mui/icons-material/ArrowBack';
import PageTitle from '@/components/layout/PageTitle';
import LoadingSkeleton from '@/components/common/LoadingSkeleton';
import { useSnackbar } from 'notistack';
import {
  fetchAdminTenants,
  fetchAdminUsers,
  updateAdminTenant,
  deleteAdminTenant,
  cancelAdminTenantErasure,
  fetchTenantMembers,
  addTenantMember,
  removeTenantMember,
  changeTenantMemberRole,
} from '@/api/endpoints/adminPlatform';
import { isApiError, parseApiError } from '@/api/errors';
import ErrorPage from '@/pages/ErrorPage';
import type {
  AdminTenant,
  AdminTenantMember,
  AdminTenantUpdate,
  AdminUser,
  TenantDeleteRequest,
  TenantRole,
} from '@/api/types';
import TenantDeleteDialog from '@/components/tenants/TenantDeleteDialog';
import TenantStatusChip from '@/components/tenants/TenantStatusChip';
import StepUpConfirmDialog from '@/components/common/StepUpConfirmDialog';
import type { StepUpConfirmation } from '@/components/common/StepUpConfirmDialog';
import { toCredentialStepUpBody } from '@/utils/stepUp';
import { useStepUpResume } from '@/hooks/useStepUpReauth';

const GRID_2COL = {
  display: 'grid',
  gridTemplateColumns: { xs: '1fr', lg: '1fr 1fr' },
  gap: 3,
} as const;

export default function AdminEditTenantPage() {
  const { key } = useParams<{ key: string }>();
  const { t } = useTranslation();
  const navigate = useNavigate();
  const { enqueueSnackbar } = useSnackbar();

  const [tenant, setTenant] = useState<AdminTenant | null>(null);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState<number | null>(null);
  const [reloadToken, setReloadToken] = useState(0);

  // Form
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [isActive, setIsActive] = useState(true);
  const [saving, setSaving] = useState(false);
  // #1815 — back from the fresh sign-in at the identity provider: reopen the
  // tenant-deletion dialog it was started from (it then sends the token).
  const resumeDelete = useStepUpResume('tenant-delete');
  const [confirmDelete, setConfirmDelete] = useState(resumeDelete);
  // #2009 — changing whether the tenant is active (deactivating locks every member
  // out) and removing a member pass the admin's own step-up. Neither the toggled
  // switch nor the chosen member survives the round trip to the identity provider,
  // so the resume contexts are only consumed; the pending token is picked up when
  // the admin repeats the act within its five minutes — for the same tenant or
  // membership only (#1884: token and dialog are bound to its key).
  useStepUpResume('update-tenant');
  useStepUpResume('remove-member');
  // #2032 — changing a member's role (demoting the last lead) passes it too, bound to the
  // membership. The chosen role does not survive the identity-provider round trip either.
  useStepUpResume('change-member-role');
  // #2106 — adding an account to the tenant passes it too, bound to `<tenant>|<user>`; the chosen
  // user and role do not survive the identity-provider round trip either.
  useStepUpResume('add-member');
  // #2123 — cancelling a scheduled deletion passes it too, bound to the tenant.
  useStepUpResume('cancel-tenant-erasure');
  const [confirmCancelErasure, setConfirmCancelErasure] = useState(false);
  const [roleChange, setRoleChange] = useState<{ member: AdminTenantMember; role: TenantRole } | null>(null);
  const [confirmActiveChange, setConfirmActiveChange] = useState(false);
  const [memberToRemove, setMemberToRemove] = useState<AdminTenantMember | null>(null);

  // Members
  const [members, setMembers] = useState<AdminTenantMember[]>([]);
  const [membersLoading, setMembersLoading] = useState(false);
  const [allUsers, setAllUsers] = useState<AdminUser[]>([]);
  const [showAddMember, setShowAddMember] = useState(false);
  const [selectedUser, setSelectedUser] = useState<AdminUser | null>(null);
  const [selectedRole, setSelectedRole] = useState<TenantRole>('viewer');
  const [confirmAdd, setConfirmAdd] = useState(false);

  const isPlatform = tenant?.is_platform === true;
  // #2123 — a tenant whose deletion is scheduled (or that was orphaned, #2134) can only be
  // cancelled, never toggled or deleted again; one being erased can no longer be touched.
  const lifecycle = tenant?.status ?? (tenant?.is_active === false ? 'suspended' : 'active');
  const deletionScheduled = lifecycle === 'pending_deletion' || lifecycle === 'orphaned';
  const lifecycleLocked = deletionScheduled || lifecycle === 'deleted';
  const scheduledDate = tenant?.deletion_scheduled_at
    ? new Date(tenant.deletion_scheduled_at).toLocaleDateString()
    : '';

  // Load tenant
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
    fetchAdminTenants()
      .then((tenants) => {
        if (cancelled) return;
        const found = tenants.find((t) => t.key === key);
        if (found) {
          setTenant(found);
          setName(found.name);
          setDescription(found.description ?? '');
          setIsActive(found.is_active);
        }
      })
      // WITHOUT THIS `.catch` EVERY REJECTION LOOKED LIKE "NOT FOUND" (#1390).
      // A 403, a 500, a dropped connection and a rate limit all left `tenant` at
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

  // Load members
  const loadMembers = useCallback(async () => {
    if (!key) return;
    setMembersLoading(true);
    try {
      setMembers(await fetchTenantMembers(key));
    } catch { /* ignore */ }
    finally { setMembersLoading(false); }
  }, [key]);

  useEffect(() => { loadMembers(); }, [loadMembers]);

  // Lazy-load all users when add-member opens
  useEffect(() => {
    if (showAddMember && allUsers.length === 0) {
      fetchAdminUsers().then(setAllUsers).catch(() => {});
    }
  }, [showAddMember, allUsers.length]);

  const availableUsers = allUsers.filter(
    (u) => u.is_active && !members.some((m) => m.user_key === u.key),
  );

  const buildUpdate = (current: AdminTenant): AdminTenantUpdate => ({
    name: name !== current.name ? name : undefined,
    description: description !== (current.description ?? '') ? description : undefined,
    is_active: isActive !== current.is_active ? isActive : undefined,
  });

  const handleSave = async () => {
    if (!tenant || isPlatform) return;
    // #2009 — a change of `is_active` asks for the admin's step-up first; a
    // rename or a new description saves as before.
    if (isActive !== tenant.is_active) {
      setConfirmActiveChange(true);
      return;
    }
    setSaving(true);
    try {
      const updated = await updateAdminTenant(tenant.key, buildUpdate(tenant));
      setTenant(updated);
      enqueueSnackbar(t('common.saved'), { variant: 'success' });
    } catch (err) {
      enqueueSnackbar(parseApiError(err), { variant: 'error' });
    } finally {
      setSaving(false);
    }
  };

  // The admin's OWN step-up (#2009). A rejection propagates to the dialog,
  // which shows it inside itself and stays open.
  const handleConfirmActiveChange = async (credentials: StepUpConfirmation) => {
    if (!tenant || isPlatform) return;
    const updated = await updateAdminTenant(tenant.key, {
      ...buildUpdate(tenant),
      ...toCredentialStepUpBody(credentials),
    });
    setTenant(updated);
    setConfirmActiveChange(false);
    enqueueSnackbar(t('common.saved'), { variant: 'success' });
  };

  // #1791 — the deletion carries its step-up (slug echo + current password);
  // a refusal is thrown back to the dialog, which shows it and stays open.
  const handleDelete = async (stepUp: TenantDeleteRequest) => {
    if (!tenant || isPlatform) return;
    const accepted = await deleteAdminTenant(tenant.key, stepUp);
    setConfirmDelete(false);
    // #2123 — with a grace period the deletion is only scheduled and can still be cancelled.
    const message =
      accepted.status === 'scheduled' && accepted.scheduled_for
        ? t('pages.auth.adminTenantDeletionScheduled', {
            date: new Date(accepted.scheduled_for).toLocaleDateString(),
          })
        : t('pages.auth.adminTenantDeletionAccepted');
    enqueueSnackbar(message, { variant: 'success' });
    navigate('/settings#platform');
  };

  // #2123 — the admin's OWN step-up; a rejection is shown inside the dialog, which stays open.
  const handleCancelErasure = async (credentials: StepUpConfirmation) => {
    if (!tenant) return;
    const restored = await cancelAdminTenantErasure(tenant.key, toCredentialStepUpBody(credentials));
    setTenant(restored);
    setIsActive(restored.is_active);
    setConfirmCancelErasure(false);
    enqueueSnackbar(t('pages.auth.adminTenantDeletionCancelled'), { variant: 'success' });
  };

  // Adding a member only opens the confirmation (#2106): nothing is written until the admin's OWN
  // step-up went through. A rejection propagates to the dialog, which shows it and stays open.
  const handleAddMember = () => {
    if (!key || !selectedUser) return;
    setConfirmAdd(true);
  };

  const handleConfirmAddMember = async (credentials: StepUpConfirmation) => {
    if (!key || !selectedUser) return;
    const m = await addTenantMember(
      key,
      { user_key: selectedUser.key, role: selectedRole },
      toCredentialStepUpBody(credentials),
    );
    setMembers((prev) => [...prev, m]);
    setSelectedUser(null);
    setSelectedRole('viewer');
    setShowAddMember(false);
    setConfirmAdd(false);
    enqueueSnackbar(t('pages.auth.adminMemberAdded'), { variant: 'success' });
  };

  // Removing a member passes the admin's OWN step-up (#2009); the dialog shows a
  // rejection inside itself and stays open.
  const handleRemoveMember = async (credentials: StepUpConfirmation) => {
    if (!key || !memberToRemove) return;
    const removed = memberToRemove;
    await removeTenantMember(key, removed.membership_key, toCredentialStepUpBody(credentials));
    setMembers((prev) => prev.filter((x) => x.membership_key !== removed.membership_key));
    setMemberToRemove(null);
    enqueueSnackbar(t('pages.auth.adminMemberRemoved'), { variant: 'success' });
  };

  // Choosing another role only opens the confirmation (#2032): the select keeps showing the
  // stored role until the admin's OWN step-up went through.
  const handleRoleChange = (m: AdminTenantMember, newRole: TenantRole) => {
    if (newRole === m.role) return;
    setRoleChange({ member: m, role: newRole });
  };

  // A rejection propagates to the dialog, which shows it inside itself and stays open.
  const handleConfirmRoleChange = async (credentials: StepUpConfirmation) => {
    if (!key || !roleChange) return;
    const { member, role } = roleChange;
    const updated = await changeTenantMemberRole(
      key,
      member.membership_key,
      role,
      toCredentialStepUpBody(credentials),
    );
    setMembers((prev) => prev.map((x) => (x.membership_key === member.membership_key ? updated : x)));
    setRoleChange(null);
    enqueueSnackbar(t('common.saved'), { variant: 'success' });
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
  if (!tenant) return <Alert severity="error">{t('pages.admin.tenantNotFound')}</Alert>;

  return (
    <Box sx={{ mt: 2 }}>
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
        <IconButton onClick={() => navigate('/settings#platform')} data-testid="back-btn">
          <ArrowBackIcon />
        </IconButton>
        <PageTitle title={`${t('pages.auth.editTenantTitle')}: ${tenant.name}`} />
        {isPlatform && <Chip label="Platform" color="warning" size="small" />}
        <TenantStatusChip status={tenant.status} isActive={tenant.is_active} testId="edit-tenant-status-chip" />
      </Box>

      {deletionScheduled && (
        <Alert
          severity="warning"
          sx={{ mb: 2 }}
          data-testid="edit-tenant-deletion-scheduled"
          action={
            // #2134 — an orphaned organization has nobody left who could administer it; it is
            // not handed back, only deleted after the grace (REQ-023 §5a.5 dropped).
            lifecycle === 'pending_deletion' ? (
              <Button
                color="inherit"
                size="small"
                onClick={() => setConfirmCancelErasure(true)}
                data-testid="cancel-tenant-erasure-btn"
              >
                {t('pages.auth.adminTenantCancelDeletion')}
              </Button>
            ) : undefined
          }
        >
          {lifecycle === 'orphaned'
            ? t('pages.auth.adminTenantOrphanedInfo', { date: scheduledDate })
            : t('pages.auth.adminTenantPendingDeletionInfo', { date: scheduledDate })}
        </Alert>
      )}
      {lifecycle === 'deleted' && (
        <Alert severity="error" sx={{ mb: 2 }} data-testid="edit-tenant-being-erased">
          {t('pages.auth.adminTenantErasingInfo')}
        </Alert>
      )}
      {lifecycle === 'pending_deletion' && (
        <StepUpConfirmDialog
          open={confirmCancelErasure}
          title={t('pages.auth.adminTenantCancelDeletionTitle')}
          description={t('pages.auth.adminTenantCancelDeletionDescription', { name: tenant.name })}
          passwordLabel={t('pages.auth.adminDeleteUserPasswordLabel')}
          passwordHelper={t('pages.auth.adminDeleteUserPasswordHelper')}
          confirmLabel={t('pages.auth.adminTenantCancelDeletion')}
          confirmColor="primary"
          testIdPrefix="cancel-tenant-erasure"
          stepUpAction="tenant_erasure_cancel"
          stepUpTarget={tenant.key}
          onConfirm={handleCancelErasure}
          onCancel={() => setConfirmCancelErasure(false)}
        />
      )}

      <Box sx={GRID_2COL}>
        {/* Left: Tenant properties */}
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              {t('pages.auth.adminTenantName')}
            </Typography>
            {isPlatform && (
              <Alert severity="info" sx={{ mb: 2 }}>{t('pages.auth.editTenantReadonly')}</Alert>
            )}
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2.5 }}>
              <TextField
                label={t('pages.auth.adminTenantName')}
                value={name}
                onChange={(e) => setName(e.target.value)}
                disabled={isPlatform}
                fullWidth
                required
                data-testid="edit-tenant-name"
              />
              <TextField
                label={t('pages.auth.adminTenantDescription')}
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                disabled={isPlatform}
                fullWidth
                multiline
                minRows={3}
                data-testid="edit-tenant-description"
              />
              <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
                <TextField label="Slug" value={tenant.slug} disabled sx={{ flex: 1 }} />
                <TextField label={t('pages.auth.adminTenantType')} value={t(`enums.tenantType.${tenant.tenant_type}`)} disabled sx={{ flex: 1 }} />
              </Box>
              <FormControlLabel
                control={
                  <Switch checked={isActive} onChange={(e) => setIsActive(e.target.checked)} disabled={isPlatform || lifecycleLocked} data-testid="edit-tenant-active-switch" />
                }
                label={t('pages.auth.adminUserIsActive')}
              />
              {!isPlatform && (
                <Button
                  variant="contained"
                  onClick={handleSave}
                  disabled={saving || !name.trim()}
                  startIcon={saving ? <CircularProgress size={16} /> : undefined}
                  sx={{ alignSelf: 'flex-start' }}
                  data-testid="edit-tenant-save"
                >
                  {t('common.save')}
                </Button>
              )}
            </Box>
            {!isPlatform && (
              <StepUpConfirmDialog
                open={confirmActiveChange}
                title={t('pages.auth.adminUpdateTenantStepUpTitle')}
                description={t('pages.auth.adminUpdateTenantStepUpDescription', { name: tenant.name })}
                passwordLabel={t('pages.auth.adminDeleteUserPasswordLabel')}
                passwordHelper={t('pages.auth.adminDeleteUserPasswordHelper')}
                confirmLabel={t('pages.auth.adminUpdateTenantStepUpConfirm')}
                confirmColor={isActive ? 'primary' : 'error'}
                testIdPrefix="update-tenant"
                stepUpAction="admin_tenant_update"
                stepUpTarget={tenant.key}
                onConfirm={handleConfirmActiveChange}
                onCancel={() => setConfirmActiveChange(false)}
              />
            )}

            {/* Danger zone */}
            {!isPlatform && (
              <>
                <Divider sx={{ my: 3 }} />
                <Typography variant="subtitle2" color="error" gutterBottom>
                  {t('pages.auth.dangerZone')}
                </Typography>
                <Button variant="outlined" color="error" onClick={() => setConfirmDelete(true)} disabled={lifecycleLocked} data-testid="delete-tenant-btn">
                  {t('pages.auth.adminDeleteTenant')}
                </Button>
                <TenantDeleteDialog
                  open={confirmDelete}
                  tenantName={tenant.name}
                  tenantSlug={tenant.slug}
                  tenantKey={tenant.key}
                  onConfirm={handleDelete}
                  onCancel={() => setConfirmDelete(false)}
                />
              </>
            )}
          </CardContent>
        </Card>

        {/* Right: Members */}
        <Card>
          <CardContent>
            <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
              <Typography variant="h6">
                {t('pages.auth.adminTenantMembersTitle')} <Chip label={members.length} size="small" />
              </Typography>
              {!showAddMember && (
                <Button size="small" startIcon={<PersonAddIcon />} onClick={() => setShowAddMember(true)} data-testid="show-add-member-btn">
                  {t('pages.auth.adminAddMember')}
                </Button>
              )}
            </Box>

            {/* Add member */}
            {showAddMember && (
              <Box sx={{ display: 'flex', gap: 1, alignItems: 'flex-start', p: 2, mb: 2, border: 1, borderColor: 'divider', borderRadius: 1, flexWrap: 'wrap' }}>
                <Autocomplete
                  size="small"
                  options={availableUsers}
                  getOptionLabel={(u) => `${u.display_name} (${u.email})`}
                  value={selectedUser}
                  onChange={(_, v) => setSelectedUser(v)}
                  renderInput={(params) => <TextField {...params} label={t('pages.auth.adminSelectUser')} data-testid="add-member-user-input" />}
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
                <Button variant="contained" size="small" onClick={handleAddMember} disabled={!selectedUser}
                  sx={{ mt: 0.25 }} data-testid="add-member-submit-btn">
                  {t('common.add')}
                </Button>
                <Button size="small" onClick={() => { setShowAddMember(false); setSelectedUser(null); }} sx={{ mt: 0.25 }}>
                  {t('common.cancel')}
                </Button>
              </Box>
            )}

            {/* Members table */}
            {membersLoading ? (
              <Box sx={{ display: 'flex', justifyContent: 'center', py: 3 }}><CircularProgress /></Box>
            ) : (
              <TableContainer>
                <Table size="small">
                  <TableHead>
                    <TableRow>
                      <TableCell>{t('pages.auth.adminUserName')}</TableCell>
                      <TableCell>{t('pages.auth.adminUserEmail')}</TableCell>
                      <TableCell>{t('pages.auth.adminMemberRole')}</TableCell>
                      <TableCell align="right" />
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {members.map((m) => (
                      <TableRow key={m.membership_key}>
                        <TableCell>
                          <Typography variant="body2" sx={{ fontWeight: 500 }}>{m.display_name}</Typography>
                        </TableCell>
                        <TableCell>
                          <Typography variant="body2" sx={{ fontFamily: 'monospace' }}>{m.email}</Typography>
                        </TableCell>
                        <TableCell>
                          <Select
                            size="small"
                            value={m.role}
                            onChange={(e) => handleRoleChange(m, e.target.value as TenantRole)}
                            variant="standard"
                            sx={{ fontSize: '0.8125rem' }}
                            data-testid={`role-select-${m.user_key}`}
                          >
                            <MenuItem value="lead">{t('enums.tenantRole.lead')}</MenuItem>
                            <MenuItem value="grower">{t('enums.tenantRole.grower')}</MenuItem>
                            <MenuItem value="viewer">{t('enums.tenantRole.viewer')}</MenuItem>
                          </Select>
                        </TableCell>
                        <TableCell align="right">
                          <IconButton size="small" onClick={() => setMemberToRemove(m)} data-testid={`remove-member-${m.user_key}`}>
                            <DeleteIcon fontSize="small" />
                          </IconButton>
                        </TableCell>
                      </TableRow>
                    ))}
                    {members.length === 0 && (
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
            <StepUpConfirmDialog
              open={confirmAdd && selectedUser !== null}
              title={t('pages.auth.adminAddMemberStepUpTitle')}
              description={t('pages.auth.adminAddMemberStepUpDescription', {
                name: selectedUser?.display_name ?? '',
                tenant: tenant.name,
                role: t(`enums.tenantRole.${selectedRole}`),
              })}
              passwordLabel={t('pages.auth.adminDeleteUserPasswordLabel')}
              passwordHelper={t('pages.auth.adminDeleteUserPasswordHelper')}
              confirmLabel={t('pages.auth.adminAddMemberStepUpConfirm')}
              confirmColor="primary"
              testIdPrefix="add-member"
              stepUpAction="admin_membership_add"
              stepUpTarget={selectedUser ? `${tenant.key}|${selectedUser.key}` : undefined}
              onConfirm={handleConfirmAddMember}
              onCancel={() => setConfirmAdd(false)}
            />
            <StepUpConfirmDialog
              open={memberToRemove !== null}
              title={t('pages.auth.adminRemoveMemberStepUpTitle')}
              description={t('pages.auth.adminRemoveMemberStepUpDescription', {
                name: memberToRemove?.display_name ?? '',
                tenant: tenant.name,
              })}
              passwordLabel={t('pages.auth.adminDeleteUserPasswordLabel')}
              passwordHelper={t('pages.auth.adminDeleteUserPasswordHelper')}
              confirmLabel={t('pages.auth.adminRemoveMemberStepUpConfirm')}
              testIdPrefix="remove-member"
              stepUpAction="admin_membership_removal"
              stepUpTarget={memberToRemove?.membership_key}
              onConfirm={handleRemoveMember}
              onCancel={() => setMemberToRemove(null)}
            />
            <StepUpConfirmDialog
              open={roleChange !== null}
              title={t('pages.auth.adminChangeRoleStepUpTitle')}
              description={t('pages.auth.adminChangeRoleStepUpDescription', {
                name: roleChange?.member.display_name ?? '',
                tenant: tenant.name,
                role: roleChange ? t(`enums.tenantRole.${roleChange.role}`) : '',
              })}
              passwordLabel={t('pages.auth.adminDeleteUserPasswordLabel')}
              passwordHelper={t('pages.auth.adminDeleteUserPasswordHelper')}
              confirmLabel={t('pages.auth.adminChangeRoleStepUpConfirm')}
              confirmColor="primary"
              testIdPrefix="change-member-role"
              stepUpAction="admin_membership_role_change"
              stepUpTarget={roleChange?.member.membership_key}
              onConfirm={handleConfirmRoleChange}
              onCancel={() => setRoleChange(null)}
            />
          </CardContent>
        </Card>
      </Box>
    </Box>
  );
}
