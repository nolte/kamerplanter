import { useState, useEffect, useCallback } from 'react';
import { useTranslation } from 'react-i18next';
import { useSnackbar } from 'notistack';
import Box from '@mui/material/Box';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import TextField from '@mui/material/TextField';
import Button from '@mui/material/Button';
import Tabs from '@mui/material/Tabs';
import Tab from '@mui/material/Tab';
import Chip from '@mui/material/Chip';
import Table from '@mui/material/Table';
import TableBody from '@mui/material/TableBody';
import TableCell from '@mui/material/TableCell';
import TableHead from '@mui/material/TableHead';
import TableRow from '@mui/material/TableRow';
import IconButton from '@mui/material/IconButton';
import DeleteIcon from '@mui/icons-material/Delete';
import ContentCopyIcon from '@mui/icons-material/ContentCopy';
import * as tenantApi from '@/api/endpoints/tenants';
import { useAppSelector } from '@/store/hooks';
import { useTenantPermissions } from '@/hooks/useTenantPermissions';
import PageTitle from '@/components/layout/PageTitle';
import { parseApiError } from '@/api/errors';
import type { Membership, Invitation } from '@/api/types';

export default function TenantSettingsPage() {
  const { t } = useTranslation();
  const { enqueueSnackbar } = useSnackbar();
  const activeTenant = useAppSelector((s) => s.tenants.activeTenant);
  const { isAdmin } = useTenantPermissions();
  const [tab, setTab] = useState(0);
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
            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell>{t('pages.tenants.memberName')}</TableCell>
                  <TableCell>{t('pages.tenants.memberEmail')}</TableCell>
                  <TableCell>{t('pages.tenants.memberRole')}</TableCell>
                  {isAdmin && <TableCell>{t('common.actions')}</TableCell>}
                </TableRow>
              </TableHead>
              <TableBody>
                {members.map((m) => (
                  <TableRow key={m.key}>
                    <TableCell>{m.display_name}</TableCell>
                    <TableCell>{m.email}</TableCell>
                    <TableCell>
                      <Chip label={t(`enums.tenantRole.${m.role}`)} size="small" />
                    </TableCell>
                    {isAdmin && (
                      <TableCell>
                        <IconButton size="small" onClick={() => handleRemoveMember(m.key)}>
                          <DeleteIcon fontSize="small" />
                        </IconButton>
                      </TableCell>
                    )}
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      )}

      {tab === 1 && isAdmin && (
        <Card>
          <CardContent>
            <Box sx={{ display: 'flex', gap: 1, mb: 3 }}>
              <TextField
                size="small"
                label={t('pages.tenants.inviteEmail')}
                value={inviteEmail}
                onChange={(e) => setInviteEmail(e.target.value)}
                type="email"
              />
              <Button variant="contained" size="small" onClick={handleInviteEmail} disabled={!inviteEmail}>
                {t('pages.tenants.sendInvitation')}
              </Button>
              <Button variant="outlined" size="small" onClick={handleCreateLink} startIcon={<ContentCopyIcon />}>
                {t('pages.tenants.createLink')}
              </Button>
            </Box>

            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell>{t('pages.tenants.invitationType')}</TableCell>
                  <TableCell>{t('pages.auth.email')}</TableCell>
                  <TableCell>{t('pages.tenants.memberRole')}</TableCell>
                  <TableCell>{t('pages.tenants.invitationStatus')}</TableCell>
                  <TableCell>{t('common.actions')}</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {invitations.map((inv) => (
                  <TableRow key={inv.key}>
                    <TableCell>{inv.invitation_type}</TableCell>
                    <TableCell>{inv.email ?? '—'}</TableCell>
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
                    <TableCell>
                      {inv.status === 'pending' && (
                        <IconButton size="small" onClick={() => handleRevokeInvitation(inv.key)}>
                          <DeleteIcon fontSize="small" />
                        </IconButton>
                      )}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      )}
    </Box>
  );
}
