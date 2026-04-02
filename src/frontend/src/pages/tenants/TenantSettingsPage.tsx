import { useState, useEffect, useCallback, useMemo } from 'react';
import { useTabUrl } from '@/hooks/useTabUrl';
import { useTranslation } from 'react-i18next';
import { useSnackbar } from 'notistack';
import Box from '@mui/material/Box';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import TextField from '@mui/material/TextField';
import Button from '@mui/material/Button';
import Typography from '@mui/material/Typography';
import Tabs from '@mui/material/Tabs';
import Tab from '@mui/material/Tab';
import Chip from '@mui/material/Chip';
import IconButton from '@mui/material/IconButton';
import Tooltip from '@mui/material/Tooltip';
import DeleteIcon from '@mui/icons-material/Delete';
import PersonAddIcon from '@mui/icons-material/PersonAdd';
import LinkIcon from '@mui/icons-material/Link';
import * as tenantApi from '@/api/endpoints/tenants';
import { useAppSelector } from '@/store/hooks';
import { useTenantPermissions } from '@/hooks/useTenantPermissions';
import DataTable, { type Column } from '@/components/common/DataTable';
import MobileCard from '@/components/common/MobileCard';
import PageTitle from '@/components/layout/PageTitle';
import { parseApiError } from '@/api/errors';
import type { Membership, Invitation } from '@/api/types';

export default function TenantSettingsPage() {
  const { t } = useTranslation();
  const { enqueueSnackbar } = useSnackbar();
  const activeTenant = useAppSelector((s) => s.tenants.activeTenant);
  const { isAdmin } = useTenantPermissions();
  const tabSlugs = useMemo(
    () => isAdmin ? ['members', 'invitations'] as const : ['members'] as const,
    [isAdmin],
  );
  const [tab, setTab] = useTabUrl(tabSlugs);
  const [members, setMembers] = useState<Membership[]>([]);
  const [invitations, setInvitations] = useState<Invitation[]>([]);
  const [inviteEmail, setInviteEmail] = useState('');

  const slug = activeTenant?.slug ?? '';

  const loadMembers = useCallback(async () => {
    if (!slug) return;
    try {
      const data = await tenantApi.listMembers(slug);
      setMembers(data);
    } catch { /* ignore */ }
  }, [slug]);

  const loadInvitations = useCallback(async () => {
    if (!slug || !isAdmin) return;
    try {
      const data = await tenantApi.listInvitations(slug);
      setInvitations(data);
    } catch { /* ignore */ }
  }, [slug, isAdmin]);

  useEffect(() => {
    void loadMembers(); // eslint-disable-line react-hooks/set-state-in-effect -- async function, setState is after await
    void loadInvitations();
  }, [loadMembers, loadInvitations]);

  const handleInviteEmail = async () => {
    if (!inviteEmail || !slug) return;
    try {
      await tenantApi.createEmailInvitation(slug, { email: inviteEmail, role: 'viewer' });
      enqueueSnackbar(t('pages.tenants.invitationSent'), { variant: 'success' });
      setInviteEmail('');
      loadInvitations();
    } catch (err) {
      enqueueSnackbar(parseApiError(err), { variant: 'error' });
    }
  };

  const handleCreateLink = async () => {
    if (!slug) return;
    try {
      const result = await tenantApi.createLinkInvitation(slug, { role: 'viewer' });
      await navigator.clipboard.writeText(result.token);
      enqueueSnackbar(t('pages.tenants.linkCopied'), { variant: 'success' });
      loadInvitations();
    } catch (err) {
      enqueueSnackbar(parseApiError(err), { variant: 'error' });
    }
  };

  const handleRevokeInvitation = useCallback(async (key: string) => {
    if (!slug) return;
    try {
      await tenantApi.revokeInvitation(slug, key);
      loadInvitations();
    } catch (err) {
      enqueueSnackbar(parseApiError(err), { variant: 'error' });
    }
  }, [slug, loadInvitations, enqueueSnackbar]);

  const handleRemoveMember = useCallback(async (key: string) => {
    if (!slug) return;
    try {
      await tenantApi.removeMember(slug, key);
      enqueueSnackbar(t('pages.tenants.memberRemoved'), { variant: 'success' });
      loadMembers();
    } catch (err) {
      enqueueSnackbar(parseApiError(err), { variant: 'error' });
    }
  }, [slug, t, enqueueSnackbar, loadMembers]);

  const memberColumns: Column<Membership>[] = useMemo(() => {
    const cols: Column<Membership>[] = [
      { id: 'display_name', label: t('pages.tenants.memberName'), render: (r) => r.display_name || '\u2014' },
      { id: 'email', label: t('pages.tenants.memberEmail'), render: (r) => r.email },
      {
        id: 'role', label: t('pages.tenants.memberRole'), render: (r) => (
          <Chip
            label={t(`enums.tenantRole.${r.role}`)}
            size="small"
            color={r.role === 'admin' ? 'primary' : 'default'}
          />
        ), searchValue: (r) => t(`enums.tenantRole.${r.role}`),
      },
    ];
    if (isAdmin) {
      cols.push({
        id: 'actions', label: t('common.actions'), align: 'right', sortable: false, searchable: false, render: (r) => (
          <Tooltip title={t('pages.tenants.removeMember')}>
            <IconButton
              size="small"
              onClick={(e) => { e.stopPropagation(); handleRemoveMember(r.key); }}
              aria-label={t('pages.tenants.removeMember')}
              data-testid={`remove-member-${r.key}`}
            >
              <DeleteIcon fontSize="small" />
            </IconButton>
          </Tooltip>
        ),
      });
    }
    return cols;
  }, [isAdmin, t, handleRemoveMember]);

  const invitationColumns: Column<Invitation>[] = useMemo(() => [
    {
      id: 'invitation_type', label: t('pages.tenants.invitationType'), render: (r) => (
        <Typography variant="body2">
          {t(`enums.invitationType.${r.invitation_type}`, { defaultValue: r.invitation_type })}
        </Typography>
      ), searchValue: (r) => t(`enums.invitationType.${r.invitation_type}`, { defaultValue: r.invitation_type }),
    },
    { id: 'email', label: t('pages.auth.email'), render: (r) => r.email ?? '\u2014' },
    {
      id: 'role', label: t('pages.tenants.memberRole'), render: (r) => (
        <Chip label={t(`enums.tenantRole.${r.role}`)} size="small" />
      ), searchValue: (r) => t(`enums.tenantRole.${r.role}`),
    },
    {
      id: 'status', label: t('pages.tenants.invitationStatus'), render: (r) => (
        <Chip
          label={t(`enums.invitationStatus.${r.status}`)}
          size="small"
          color={r.status === 'pending' ? 'warning' : 'default'}
        />
      ), searchValue: (r) => t(`enums.invitationStatus.${r.status}`),
    },
    {
      id: 'actions', label: t('common.actions'), align: 'right', sortable: false, searchable: false, render: (r) => (
        r.status === 'pending' ? (
          <Tooltip title={t('pages.tenants.revokeInvitation')}>
            <IconButton
              size="small"
              onClick={(e) => { e.stopPropagation(); handleRevokeInvitation(r.key); }}
              aria-label={t('pages.tenants.revokeInvitation')}
              data-testid={`revoke-invitation-${r.key}`}
            >
              <DeleteIcon fontSize="small" />
            </IconButton>
          </Tooltip>
        ) : null
      ),
    },
  ], [t, handleRevokeInvitation]);

  if (!activeTenant) return null;

  return (
    <Box>
      <PageTitle title={`${activeTenant.name} — ${t('pages.tenants.settings')}`} />
      <Tabs value={tab} onChange={(_, v) => setTab(v)} sx={{ mb: 2 }}>
        <Tab label={t('pages.tenants.tabMembers')} />
        {isAdmin && <Tab label={t('pages.tenants.tabInvitations')} />}
      </Tabs>

      {tab === 0 && (
        <DataTable
          columns={memberColumns}
          rows={members}
          getRowKey={(r) => r.key}
          variant="simple"
          ariaLabel={t('pages.tenants.tabMembers')}
          emptyMessage={t('pages.tenants.noMembers')}
          mobileCardRenderer={(m) => (
            <MobileCard
              title={m.display_name || '\u2014'}
              subtitle={m.email}
              chips={
                <Chip
                  label={t(`enums.tenantRole.${m.role}`)}
                  size="small"
                  color={m.role === 'admin' ? 'primary' : 'default'}
                />
              }
              trailing={
                isAdmin ? (
                  <Tooltip title={t('pages.tenants.removeMember')}>
                    <IconButton
                      size="small"
                      onClick={() => handleRemoveMember(m.key)}
                      aria-label={t('pages.tenants.removeMember')}
                      data-testid={`remove-member-${m.key}`}
                    >
                      <DeleteIcon fontSize="small" />
                    </IconButton>
                  </Tooltip>
                ) : undefined
              }
            />
          )}
        />
      )}

      {tab === 1 && isAdmin && (
        <Card>
          <CardContent>
            <Typography variant="subtitle2" color="text.secondary" gutterBottom>
              {t('pages.tenants.inviteNewMember')}
            </Typography>
            <Box
              sx={{
                display: 'flex',
                gap: 1,
                mb: 3,
                flexWrap: { xs: 'wrap', sm: 'nowrap' },
                alignItems: 'flex-start',
              }}
            >
              <TextField
                size="small"
                label={t('pages.tenants.inviteEmail')}
                value={inviteEmail}
                onChange={(e) => setInviteEmail(e.target.value)}
                type="email"
                sx={{ flex: '1 1 220px', minWidth: 0 }}
                onKeyDown={(e) => { if (e.key === 'Enter' && inviteEmail) handleInviteEmail(); }}
                data-testid="invite-email-field"
              />
              <Button
                variant="contained"
                size="small"
                onClick={handleInviteEmail}
                disabled={!inviteEmail}
                startIcon={<PersonAddIcon />}
                data-testid="send-invitation-btn"
                sx={{ flexShrink: 0 }}
              >
                {t('pages.tenants.sendInvitation')}
              </Button>
              <Button
                variant="outlined"
                size="small"
                onClick={handleCreateLink}
                startIcon={<LinkIcon />}
                data-testid="create-link-btn"
                sx={{ flexShrink: 0 }}
              >
                {t('pages.tenants.createLink')}
              </Button>
            </Box>

            <DataTable
              columns={invitationColumns}
              rows={invitations}
              getRowKey={(r) => r.key}
              variant="simple"
              ariaLabel={t('pages.tenants.tabInvitations')}
              emptyMessage={t('pages.tenants.noInvitations')}
            />
          </CardContent>
        </Card>
      )}
    </Box>
  );
}
