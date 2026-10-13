import { useState, useEffect, useCallback, useMemo, useRef } from 'react';
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
import Alert from '@mui/material/Alert';
import ContentCopyIcon from '@mui/icons-material/ContentCopy';
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
import StepUpConfirmDialog from '@/components/common/StepUpConfirmDialog';
import ScheduledTenantDeletionsCard from '@/components/tenants/ScheduledTenantDeletionsCard';
import TenantQuotaCard from '@/components/tenants/TenantQuotaCard';
import TenantExportCard from '@/components/tenants/TenantExportCard';
import { isLightMode } from '@/config/mode';
import type { StepUpConfirmation } from '@/components/common/StepUpConfirmDialog';
import { useStepUpResume } from '@/hooks/useStepUpReauth';
import { toCredentialStepUpBody } from '@/utils/stepUp';
import { INVITATION_MAX_USES_LIMIT } from '@/api/types';
import type { Membership, Invitation, InvitationCreated } from '@/api/types';

/**
 * The accept link the inviter has to pass on (#2162): a link invitation always, an e-mail invitation
 * when its mail did not leave. `kind` picks the explanation shown above it.
 */
interface ShareableInvitation {
  kind: 'link' | 'notDelivered';
  url: string;
  /** When the invitation expires (the backend's `expires_at`) — shown, never assumed. */
  expiresAt: string;
  /** How many accounts may join with it (#2182) — the backend's answer, `1` for an e-mail invitation. */
  maxUses: number;
}

/** `max_uses` typed into the link form as a whole number within its bounds, else `null` (REQ-024 AK-07). */
function parseMaxUses(raw: string): number | null {
  if (!/^\d+$/.test(raw.trim())) return null;
  const value = Number(raw.trim());
  return value >= 1 && value <= INVITATION_MAX_USES_LIMIT ? value : null;
}

export default function TenantSettingsPage() {
  const { t, i18n } = useTranslation();
  const { enqueueSnackbar } = useSnackbar();
  const activeTenant = useAppSelector((s) => s.tenants.activeTenant);
  // REQ-049: member and invitation management hangs off the `management`
  // scope, not off the domain rank — a lead is not automatically an admin.
  const { canManageMembers: isAdmin } = useTenantPermissions();
  // REQ-056 §15 (AK-45): the quota tab is for every member — reading the plan and the usage is open
  // to all of them (REQ-024 §1a); the backend trims what a member who is not a lead may see.
  // REQ-056 §8.2/§15 (#2138): the export is for a lead holding the `management` scope, and only in
  // full mode — the routes exist nowhere else. The backend decides again from the stored membership.
  const canExport = !isLightMode && isAdmin && activeTenant?.role === 'lead';
  const tabSlugs = useMemo(() => {
    const slugs: string[] = isAdmin ? ['members', 'invitations', 'quota'] : ['members', 'quota'];
    if (canExport) slugs.push('export');
    return slugs;
  }, [isAdmin, canExport]);
  const [tab, setTab] = useTabUrl(tabSlugs);
  const activeTab = tabSlugs[tab] ?? 'members';
  const [members, setMembers] = useState<Membership[]>([]);
  const [invitations, setInvitations] = useState<Invitation[]>([]);
  const [inviteEmail, setInviteEmail] = useState('');
  // #2182 (REQ-024 AK-07) — how many people one link admits; kept as typed so an empty field can be edited.
  const [linkMaxUses, setLinkMaxUses] = useState('1');
  const maxUses = parseMaxUses(linkMaxUses);
  const [shareable, setShareable] = useState<ShareableInvitation | null>(null);
  // #2162 review S5 — one invitation request at a time: a double click would send two mails.
  const [submitting, setSubmitting] = useState(false);
  // #2162 review S1 — the link panel takes the focus when it appears, so keyboard and screen-reader
  // users land on what they have to do next.
  const copyButtonRef = useRef<HTMLButtonElement>(null);
  useEffect(() => {
    if (shareable) copyButtonRef.current?.focus();
  }, [shareable]);
  // #2032 — removing a member locks that person out, so it passes the acting administrator's
  // own step-up, bound to the membership (#1884). The chosen member does not survive the round
  // trip to the identity provider, so the resume context is only consumed; the pending token is
  // picked up when the administrator repeats the removal within its five minutes — for the same
  // membership only.
  useStepUpResume('remove-tenant-member');
  const [memberToRemove, setMemberToRemove] = useState<Membership | null>(null);

  const slug = activeTenant?.slug ?? '';

  const loadMembers = useCallback(async () => {
    if (!slug) return;
    try {
      const data = await tenantApi.listMembers(slug);
      setMembers(data);
    } catch {
      /* ignore */
    }
  }, [slug]);

  const loadInvitations = useCallback(async () => {
    if (!slug || !isAdmin) return;
    try {
      const data = await tenantApi.listInvitations(slug);
      setInvitations(data);
    } catch {
      /* ignore */
    }
  }, [slug, isAdmin]);

  useEffect(() => {
    void loadMembers(); // eslint-disable-line react-hooks/set-state-in-effect -- async function, setState is after await
    void loadInvitations();
  }, [loadMembers, loadInvitations]);

  /** Copy *url*; whether it worked (the clipboard is refused outside a secure context or by policy). */
  const copyToClipboard = async (url: string): Promise<boolean> => {
    try {
      await navigator.clipboard.writeText(url);
      return true;
    } catch {
      return false;
    }
  };

  // #2162 — the answer says whether the mail left. Only then is "sent" true; otherwise the
  // invitation exists and its link is shown for the inviter to pass on themselves.
  const handleInviteEmail = async () => {
    if (!inviteEmail || !slug || submitting) return;
    let result: InvitationCreated;
    setSubmitting(true);
    try {
      result = await tenantApi.createEmailInvitation(slug, { email: inviteEmail, role: 'viewer' });
    } catch (err) {
      enqueueSnackbar(parseApiError(err), { variant: 'error' });
      return;
    } finally {
      setSubmitting(false);
    }
    setInviteEmail('');
    void loadInvitations();
    if (result.delivered) {
      setShareable(null);
      enqueueSnackbar(t('pages.tenants.invitationSent'), { variant: 'success' });
    } else {
      // The warning panel carries the message (review S2): no second, vanishing copy of it.
      setShareable({ kind: 'notDelivered', url: result.accept_url, expiresAt: result.expires_at, maxUses: 1 });
    }
  };

  // #2162 — the link copied is the accept page's link, not the bare token nobody could use.
  const handleCreateLink = async () => {
    if (!slug || submitting || maxUses === null) return;
    let result: InvitationCreated;
    setSubmitting(true);
    try {
      result = await tenantApi.createLinkInvitation(slug, { role: 'viewer', max_uses: maxUses });
    } catch (err) {
      enqueueSnackbar(parseApiError(err), { variant: 'error' });
      return;
    } finally {
      setSubmitting(false);
    }
    void loadInvitations();
    setShareable({
      kind: 'link',
      url: result.accept_url,
      expiresAt: result.expires_at,
      maxUses: result.max_uses,
    });
    const copied = await copyToClipboard(result.accept_url);
    enqueueSnackbar(t(copied ? 'pages.tenants.linkCopied' : 'pages.tenants.linkCopyFailed'), {
      variant: copied ? 'success' : 'info',
    });
  };

  const handleCopyShareable = async () => {
    if (!shareable) return;
    const copied = await copyToClipboard(shareable.url);
    enqueueSnackbar(t(copied ? 'pages.tenants.linkCopied' : 'pages.tenants.linkCopyFailed'), {
      variant: copied ? 'success' : 'info',
    });
  };

  const handleRevokeInvitation = useCallback(
    async (key: string) => {
      if (!slug) return;
      try {
        await tenantApi.revokeInvitation(slug, key);
        loadInvitations();
      } catch (err) {
        enqueueSnackbar(parseApiError(err), { variant: 'error' });
      }
    },
    [slug, loadInvitations, enqueueSnackbar],
  );

  // The acting administrator's OWN step-up (#2032); a rejection propagates to the dialog,
  // which shows it inside itself and stays open.
  const handleConfirmRemoveMember = async (credentials: StepUpConfirmation) => {
    if (!slug || !memberToRemove) return;
    const removed = memberToRemove;
    await tenantApi.removeMember(slug, removed.key, toCredentialStepUpBody(credentials));
    setMemberToRemove(null);
    enqueueSnackbar(t('pages.tenants.memberRemoved'), { variant: 'success' });
    void loadMembers();
  };

  const memberColumns: Column<Membership>[] = useMemo(() => {
    const cols: Column<Membership>[] = [
      {
        id: 'display_name',
        label: t('pages.tenants.memberName'),
        render: (r) => r.display_name || '—',
      },
      { id: 'email', label: t('pages.tenants.memberEmail'), render: (r) => r.email },
      {
        id: 'role',
        label: t('pages.tenants.memberRole'),
        render: (r) => (
          <Chip
            label={t(`enums.tenantRole.${r.role}`)}
            size="small"
            color={r.role === 'lead' ? 'primary' : 'default'}
          />
        ),
        searchValue: (r) => t(`enums.tenantRole.${r.role}`),
      },
    ];
    if (isAdmin) {
      cols.push({
        id: 'actions',
        label: t('common.actions'),
        align: 'right',
        sortable: false,
        searchable: false,
        render: (r) => (
          <Tooltip title={t('pages.tenants.removeMember')}>
            <IconButton
              size="small"
              onClick={(e) => {
                e.stopPropagation();
                setMemberToRemove(r);
              }}
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
  }, [isAdmin, t]);

  // #2182 review SCR-001 — one revoke control for the table row and the mobile card, so both
  // layouts keep the `revoke-invitation-<key>` hook and the same accessible name.
  const renderRevokeInvitation = useCallback(
    (r: Invitation) =>
      r.status === 'pending' ? (
        <Tooltip title={t('pages.tenants.revokeInvitation')}>
          <IconButton
            size="small"
            onClick={(e) => {
              e.stopPropagation();
              handleRevokeInvitation(r.key);
            }}
            aria-label={t('pages.tenants.revokeInvitation')}
            data-testid={`revoke-invitation-${r.key}`}
            sx={{ minWidth: 44, minHeight: 44 }}
          >
            <DeleteIcon fontSize="small" />
          </IconButton>
        </Tooltip>
      ) : null,
    [t, handleRevokeInvitation],
  );

  const invitationColumns: Column<Invitation>[] = useMemo(
    () => [
      {
        id: 'invitation_type',
        label: t('pages.tenants.invitationType'),
        render: (r) => (
          <Typography variant="body2">
            {t(`enums.invitationType.${r.invitation_type}`, { defaultValue: r.invitation_type })}
          </Typography>
        ),
        searchValue: (r) =>
          t(`enums.invitationType.${r.invitation_type}`, { defaultValue: r.invitation_type }),
      },
      { id: 'email', label: t('pages.auth.email'), render: (r) => r.email ?? '—' },
      {
        id: 'role',
        label: t('pages.tenants.memberRole'),
        render: (r) => <Chip label={t(`enums.tenantRole.${r.role}`)} size="small" />,
        searchValue: (r) => t(`enums.tenantRole.${r.role}`),
      },
      {
        id: 'status',
        label: t('pages.tenants.invitationStatus'),
        render: (r) => (
          <Chip
            label={t(`enums.invitationStatus.${r.status}`)}
            size="small"
            color={r.status === 'pending' ? 'warning' : 'default'}
          />
        ),
        searchValue: (r) => t(`enums.invitationStatus.${r.status}`),
      },
      {
        // #2182 (REQ-024 AK-07) — a link may admit several people: uses consumed / uses granted.
        id: 'uses',
        label: t('pages.tenants.invitationUses'),
        render: (r) => (
          <Typography variant="body2" data-testid={`invitation-uses-${r.key}`}>
            {t('pages.tenants.invitationUsesValue', { used: r.use_count, max: r.max_uses })}
          </Typography>
        ),
        searchable: false,
      },
      {
        id: 'actions',
        label: t('common.actions'),
        align: 'right',
        sortable: false,
        searchable: false,
        render: renderRevokeInvitation,
      },
    ],
    [t, renderRevokeInvitation],
  );

  // #2166 — a garden whose deletion is scheduled resolves for nobody, so it can never be the
  // active tenant; the card lists it (and offers its management the cancellation) either way.
  // Without an active garden the page still has its heading and says what to do (review SCR-005).
  if (!activeTenant) {
    return (
      <Box>
        <PageTitle title={t('pages.tenants.gardenSettings')} />
        <Alert severity="info" sx={{ mb: 3 }} data-testid="tenant-settings-no-active-tenant">
          {t('pages.tenants.noActiveTenantHint')}
        </Alert>
        <ScheduledTenantDeletionsCard />
      </Box>
    );
  }

  return (
    <Box>
      <PageTitle title={`${activeTenant.name} — ${t('pages.tenants.settings')}`} />
      <ScheduledTenantDeletionsCard />
      <Tabs value={tab} onChange={(_, v) => setTab(v)} sx={{ mb: 2 }}>
        <Tab label={t('pages.tenants.tabMembers')} />
        {isAdmin && <Tab label={t('pages.tenants.tabInvitations')} />}
        <Tab label={t('pages.tenants.tabQuota')} data-testid="tenant-tab-quota" />
        {canExport && <Tab label={t('pages.tenants.tabExport')} data-testid="tenant-tab-export" />}
      </Tabs>

      {activeTab === 'members' && (
        <DataTable
          columns={memberColumns}
          rows={members}
          getRowKey={(r) => r.key}
          variant="simple"
          ariaLabel={t('pages.tenants.tabMembers')}
          emptyMessage={t('pages.tenants.noMembers')}
          mobileCardRenderer={(m) => (
            <MobileCard
              title={m.display_name || '—'}
              titleId="display_name"
              subtitle={m.email}
              subtitleId="email"
              // Keyed so the member role is read by its column id instead of a
              // bare `.MuiChip-root` inside the page (#778 A1/A11): that
              // selector was ambiguous within this very page, which renders
              // chips for both members and invitations.
              chips={[
                {
                  id: 'role',
                  content: (
                    <Chip
                      label={t(`enums.tenantRole.${m.role}`)}
                      size="small"
                      color={m.role === 'lead' ? 'primary' : 'default'}
                    />
                  ),
                },
              ]}
              trailing={
                isAdmin ? (
                  <Tooltip title={t('pages.tenants.removeMember')}>
                    <IconButton
                      size="small"
                      onClick={() => setMemberToRemove(m)}
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

      {activeTab === 'invitations' && isAdmin && (
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
                // #2182 review SCR-007 — four controls share the row: one line only from `md`;
                // below that the e-mail field takes the first line and the link controls wrap.
                flexWrap: { xs: 'wrap', md: 'nowrap' },
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
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && inviteEmail && !submitting) handleInviteEmail();
                }}
                data-testid="invite-email-field"
              />
              <Button
                variant="contained"
                size="small"
                onClick={handleInviteEmail}
                disabled={!inviteEmail || submitting}
                startIcon={<PersonAddIcon />}
                data-testid="send-invitation-btn"
                sx={{ flexShrink: 0, minHeight: 44 }}
              >
                {t('pages.tenants.sendInvitation')}
              </Button>
              <TextField
                size="small"
                type="number"
                label={t('pages.tenants.linkMaxUses')}
                value={linkMaxUses}
                onChange={(e) => setLinkMaxUses(e.target.value)}
                error={maxUses === null}
                helperText={t('pages.tenants.linkMaxUsesHelper', { max: INVITATION_MAX_USES_LIMIT })}
                sx={{ flex: '0 1 200px', minWidth: 140 }}
                slotProps={{ htmlInput: { min: 1, max: INVITATION_MAX_USES_LIMIT, step: 1, inputMode: 'numeric' } }}
                data-testid="form-field-link-max-uses"
              />
              <Button
                variant="outlined"
                size="small"
                onClick={handleCreateLink}
                disabled={submitting || maxUses === null}
                startIcon={<LinkIcon />}
                data-testid="create-link-btn"
                sx={{ flexShrink: 0, minHeight: 44 }}
              >
                {t('pages.tenants.createLink')}
              </Button>
            </Box>

            {shareable && (
              <Alert
                severity={shareable.kind === 'notDelivered' ? 'warning' : 'info'}
                onClose={() => setShareable(null)}
                sx={{ mb: 3 }}
                data-testid={
                  shareable.kind === 'notDelivered' ? 'invitation-not-delivered' : 'invitation-link-created'
                }
              >
                <Typography variant="body2" gutterBottom>
                  {t(
                    shareable.kind === 'notDelivered'
                      ? 'pages.tenants.invitationNotDeliveredHint'
                      : 'pages.tenants.invitationLinkHint',
                    {
                      date: new Date(shareable.expiresAt).toLocaleDateString(i18n.language),
                      count: shareable.maxUses,
                    },
                  )}
                </Typography>
                <Box sx={{ display: 'flex', gap: 1, alignItems: 'center', flexWrap: { xs: 'wrap', sm: 'nowrap' } }}>
                  <TextField
                    size="small"
                    fullWidth
                    value={shareable.url}
                    label={t('pages.tenants.invitationAcceptLink')}
                    slotProps={{ htmlInput: { readOnly: true, 'data-testid': 'invitation-accept-url' } }}
                    onFocus={(e) => e.target.select()}
                  />
                  <Button
                    size="small"
                    variant="outlined"
                    startIcon={<ContentCopyIcon />}
                    onClick={handleCopyShareable}
                    ref={copyButtonRef}
                    data-testid="copy-invitation-link-btn"
                    sx={{ flexShrink: 0, minHeight: 44 }}
                  >
                    {t('pages.tenants.copyInvitationLink')}
                  </Button>
                </Box>
              </Alert>
            )}

            <DataTable
              columns={invitationColumns}
              rows={invitations}
              getRowKey={(r) => r.key}
              variant="simple"
              ariaLabel={t('pages.tenants.tabInvitations')}
              emptyMessage={t('pages.tenants.noInvitations')}
              // #2182 review SCR-001 — below `sm` the five-column table becomes cards: type, role and
              // status as keyed chips, the uses as the subtitle, the revoke control as trailing.
              mobileCardRenderer={(r) => (
                <MobileCard
                  title={r.email ?? t('pages.tenants.invitationAcceptLink')}
                  subtitle={
                    <span data-testid={`invitation-uses-${r.key}`}>
                      {t('pages.tenants.invitationUsesSubtitle', { used: r.use_count, max: r.max_uses })}
                    </span>
                  }
                  subtitleId="uses"
                  chips={[
                    {
                      id: 'invitation_type',
                      content: (
                        <Chip
                          label={t(`enums.invitationType.${r.invitation_type}`, {
                            defaultValue: r.invitation_type,
                          })}
                          size="small"
                          variant="outlined"
                        />
                      ),
                    },
                    {
                      id: 'role',
                      content: <Chip label={t(`enums.tenantRole.${r.role}`)} size="small" />,
                    },
                    {
                      id: 'status',
                      content: (
                        <Chip
                          label={t(`enums.invitationStatus.${r.status}`)}
                          size="small"
                          color={r.status === 'pending' ? 'warning' : 'default'}
                        />
                      ),
                    },
                  ]}
                  trailing={renderRevokeInvitation(r) ?? undefined}
                />
              )}
            />
          </CardContent>
        </Card>
      )}

      {activeTab === 'quota' && (
        <TenantQuotaCard slug={activeTenant.slug} isLead={activeTenant.role === 'lead'} />
      )}

      {activeTab === 'export' && canExport && (
        <TenantExportCard
          slug={activeTenant.slug}
          tenantKey={activeTenant.key}
          tenantName={activeTenant.name}
        />
      )}

      {isAdmin && (
        <StepUpConfirmDialog
          open={memberToRemove !== null}
          title={t('pages.tenants.removeMemberStepUpTitle')}
          description={t('pages.tenants.removeMemberStepUpDescription', {
            name: memberToRemove?.display_name || memberToRemove?.email || '',
            tenant: activeTenant?.name ?? '',
          })}
          confirmLabel={t('pages.tenants.removeMemberStepUpConfirm')}
          testIdPrefix="remove-tenant-member"
          stepUpAction="tenant_member_removal"
          stepUpTarget={memberToRemove?.key}
          onConfirm={handleConfirmRemoveMember}
          onCancel={() => setMemberToRemove(null)}
        />
      )}
    </Box>
  );
}
