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
import Table from '@mui/material/Table';
import TableBody from '@mui/material/TableBody';
import TableCell from '@mui/material/TableCell';
import TableHead from '@mui/material/TableHead';
import TableRow from '@mui/material/TableRow';
import IconButton from '@mui/material/IconButton';
import Tooltip from '@mui/material/Tooltip';
import useMediaQuery from '@mui/material/useMediaQuery';
import { useTheme } from '@mui/material/styles';
import DeleteIcon from '@mui/icons-material/Delete';
import PersonAddIcon from '@mui/icons-material/PersonAdd';
import LinkIcon from '@mui/icons-material/Link';
import * as tenantApi from '@/api/endpoints/tenants';
import { useAppSelector } from '@/store/hooks';
import { useTenantPermissions } from '@/hooks/useTenantPermissions';
import MobileCard from '@/components/common/MobileCard';
import PageTitle from '@/components/layout/PageTitle';
import EmptyState from '@/components/common/EmptyState';
import { parseApiError } from '@/api/errors';
import type { Membership, Invitation } from '@/api/types';

export default function TenantSettingsPage() {
  const { t } = useTranslation();
  const { enqueueSnackbar } = useSnackbar();
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));
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
    loadMembers();
    loadInvitations();
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

  const handleRevokeInvitation = async (key: string) => {
    if (!slug) return;
    try {
      await tenantApi.revokeInvitation(slug, key);
      loadInvitations();
    } catch (err) {
      enqueueSnackbar(parseApiError(err), { variant: 'error' });
    }
  };

  const handleRemoveMember = async (key: string) => {
    if (!slug) return;
    try {
      await tenantApi.removeMember(slug, key);
      enqueueSnackbar(t('pages.tenants.memberRemoved'), { variant: 'success' });
      loadMembers();
    } catch (err) {
      enqueueSnackbar(parseApiError(err), { variant: 'error' });
    }
  };

  if (!activeTenant) return null;

  return (
    <Box>
      <PageTitle title={`${activeTenant.name} — ${t('pages.tenants.settings')}`} />
      <Tabs value={tab} onChange={(_, v) => setTab(v)} sx={{ mb: 2 }}>
        <Tab label={t('pages.tenants.tabMembers')} />
        {isAdmin && <Tab label={t('pages.tenants.tabInvitations')} />}
      </Tabs>

      {tab === 0 && (
        <Card>
          <CardContent>
            {members.length === 0 ? (
              <EmptyState message={t('pages.tenants.noMembers')} />
            ) : isMobile ? (
              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                {members.map((m) => (
                  <MobileCard
                    key={m.key}
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
                ))}
              </Box>
            ) : (
              <Table size="small" aria-label={t('pages.tenants.tabMembers')}>
                <TableHead>
                  <TableRow>
                    <TableCell>{t('pages.tenants.memberName')}</TableCell>
                    <TableCell>{t('pages.tenants.memberEmail')}</TableCell>
                    <TableCell>{t('pages.tenants.memberRole')}</TableCell>
                    {isAdmin && <TableCell align="right">{t('common.actions')}</TableCell>}
                  </TableRow>
                </TableHead>
                <TableBody>
                  {members.map((m) => (
                    <TableRow key={m.key} hover>
                      <TableCell>{m.display_name || '\u2014'}</TableCell>
                      <TableCell>{m.email}</TableCell>
                      <TableCell>
                        <Chip
                          label={t(`enums.tenantRole.${m.role}`)}
                          size="small"
                          color={m.role === 'admin' ? 'primary' : 'default'}
                        />
                      </TableCell>
                      {isAdmin && (
                        <TableCell align="right">
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
                        </TableCell>
                      )}
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            )}
          </CardContent>
        </Card>
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

            {invitations.length === 0 ? (
              <EmptyState message={t('pages.tenants.noInvitations')} />
            ) : (
              <Table size="small" aria-label={t('pages.tenants.tabInvitations')}>
                <TableHead>
                  <TableRow>
                    <TableCell>{t('pages.tenants.invitationType')}</TableCell>
                    <TableCell>{t('pages.auth.email')}</TableCell>
                    <TableCell>{t('pages.tenants.memberRole')}</TableCell>
                    <TableCell>{t('pages.tenants.invitationStatus')}</TableCell>
                    <TableCell align="right">{t('common.actions')}</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {invitations.map((inv) => (
                    <TableRow key={inv.key} hover>
                      <TableCell>
                        <Typography variant="body2">
                          {t(`enums.invitationType.${inv.invitation_type}`, { defaultValue: inv.invitation_type })}
                        </Typography>
                      </TableCell>
                      <TableCell>{inv.email ?? '\u2014'}</TableCell>
                      <TableCell>
                        <Chip label={t(`enums.tenantRole.${inv.role}`)} size="small" />
                      </TableCell>
                      <TableCell>
                        <Chip
                          label={t(`enums.invitationStatus.${inv.status}`)}
                          size="small"
                          color={inv.status === 'pending' ? 'warning' : 'default'}
                        />
                      </TableCell>
                      <TableCell align="right">
                        {inv.status === 'pending' && (
                          <Tooltip title={t('pages.tenants.revokeInvitation')}>
                            <IconButton
                              size="small"
                              onClick={() => handleRevokeInvitation(inv.key)}
                              aria-label={t('pages.tenants.revokeInvitation')}
                              data-testid={`revoke-invitation-${inv.key}`}
                            >
                              <DeleteIcon fontSize="small" />
                            </IconButton>
                          </Tooltip>
                        )}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            )}
          </CardContent>
        </Card>
      )}
    </Box>
  );
}
