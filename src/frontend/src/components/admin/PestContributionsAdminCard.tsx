import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { useTranslation } from 'react-i18next';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import Typography from '@mui/material/Typography';
import Box from '@mui/material/Box';
import Chip from '@mui/material/Chip';
import Alert from '@mui/material/Alert';
import Skeleton from '@mui/material/Skeleton';
import CircularProgress from '@mui/material/CircularProgress';
import Autocomplete from '@mui/material/Autocomplete';
import TextField from '@mui/material/TextField';
import Button from '@mui/material/Button';
import Tooltip from '@mui/material/Tooltip';
import PestControlIcon from '@mui/icons-material/PestControl';
import PublicIcon from '@mui/icons-material/Public';
import LockIcon from '@mui/icons-material/Lock';
import { visuallyHidden } from '@mui/utils';
import AuthImage from '@/components/common/AuthImage';
import ConfirmDialog from '@/components/common/ConfirmDialog';
import { useNotification } from '@/hooks/useNotification';
import { listAllPests } from '@/api/endpoints/ipm';
import {
  listPestContributions,
  setPestContributionPromotion,
} from '@/api/endpoints/adminPestRecognition';
import { formatDate } from '@/utils/formatting';
import type { Pest, PestContribution } from '@/api/types';
import LoadingStatus from '@/components/common/LoadingStatus';

type GridColumnValue = string | Record<string, string>;

interface PestContributionsAdminCardProps {
  gridColumn?: GridColumnValue;
}

/**
 * REQ-010 — admin moderation of user-contributed pest reference images.
 *
 * Users contribute photos privately (scoped to their tenant). A platform admin
 * reviews every tenant's photos for a pest here and promotes the good ones to
 * global visibility (served via the global `/ipm/pest-images` content endpoint).
 * Promotion is also the seam that feeds the Phase-2 recognition index.
 *
 * Pest selection mirrors the pest-centric data model (contributions are keyed by
 * `pest_key`): the admin picks a pest, then moderates its contributed images.
 * Platform-admin only.
 */
export function PestContributionsAdminCard({ gridColumn }: PestContributionsAdminCardProps) {
  const { t } = useTranslation();
  const notify = useNotification();

  const [pests, setPests] = useState<Pest[] | null>(null);
  const [pestsFailed, setPestsFailed] = useState(false);
  const [selectedPest, setSelectedPest] = useState<Pest | null>(null);

  const [contributions, setContributions] = useState<PestContribution[] | null>(null);
  const [loadingContributions, setLoadingContributions] = useState(false);
  const [contributionsFailed, setContributionsFailed] = useState(false);

  const [busyId, setBusyId] = useState<string | null>(null);
  /** Contribution pending demotion confirmation — null means the dialog is closed. */
  const [demoteTarget, setDemoteTarget] = useState<PestContribution | null>(null);
  const [demoting, setDemoting] = useState(false);
  // Trigger that opened the demote dialog — focus returns here on close (WCAG 2.4.3).
  const demoteTriggerRef = useRef<HTMLButtonElement | null>(null);

  useEffect(() => {
    let active = true;
    const load = async () => {
      try {
        const data = await listAllPests();
        if (active) {
          setPests(data);
          setPestsFailed(false);
        }
      } catch {
        if (active) setPestsFailed(true);
      }
    };
    void load();
    return () => {
      active = false;
    };
  }, []);

  const loadContributions = useCallback(async (pestKey: string) => {
    setLoadingContributions(true);
    setContributionsFailed(false);
    try {
      const data = await listPestContributions(pestKey);
      setContributions(data.images);
    } catch {
      setContributions([]);
      setContributionsFailed(true);
    } finally {
      setLoadingContributions(false);
    }
  }, []);

  const handleSelectPest = useCallback(
    (pest: Pest | null) => {
      setSelectedPest(pest);
      setContributions(null);
      setContributionsFailed(false);
      if (pest) void loadContributions(pest.key);
    },
    [loadContributions],
  );

  const applyPromotion = useCallback(
    async (contribution: PestContribution, promote: boolean) => {
      if (!selectedPest) return;
      setBusyId(contribution.id);
      try {
        const result = await setPestContributionPromotion(selectedPest.key, contribution.id, promote);
        setContributions((prev) =>
          (prev ?? []).map((c) =>
            c.id === contribution.id
              ? { ...c, status: result.status, promoted_at: result.promoted_at, promoted_by: result.promoted_by }
              : c,
          ),
        );
        notify.success(
          promote
            ? t('pages.admin.pestContributions.promoteSuccess')
            : t('pages.admin.pestContributions.demoteSuccess'),
        );
      } catch {
        notify.error(t('pages.admin.pestContributions.actionError'));
      } finally {
        setBusyId(null);
      }
    },
    [selectedPest, notify, t],
  );

  const confirmDemote = useCallback(async () => {
    if (!demoteTarget) return;
    const target = demoteTarget;
    const trigger = demoteTriggerRef.current;
    setDemoting(true);
    try {
      await applyPromotion(target, false);
    } finally {
      setDemoting(false);
      setDemoteTarget(null);
      // Restore focus to the toggle that opened the dialog (WCAG 2.4.3).
      if (trigger) requestAnimationFrame(() => trigger.focus());
    }
  }, [demoteTarget, applyPromotion]);

  const cancelDemote = useCallback(() => {
    const trigger = demoteTriggerRef.current;
    setDemoteTarget(null);
    if (trigger) requestAnimationFrame(() => trigger.focus());
  }, []);

  const pestLabel = useCallback(
    (pest: Pest) => pest.common_name_de || pest.common_name || pest.scientific_name,
    [],
  );

  const promotedCount = useMemo(
    () => (contributions ?? []).filter((c) => c.status === 'promoted').length,
    [contributions],
  );

  return (
    <Card variant="outlined" sx={{ gridColumn }} data-testid="pest-contributions-admin-card">
      <CardContent sx={{ px: 2, pt: 2, '&:last-child': { pb: 2 } }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 0.5 }}>
          <PestControlIcon color="action" aria-hidden="true" />
          <Typography variant="h6">{t('pages.admin.pestContributions.section')}</Typography>
        </Box>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
          {t('pages.admin.pestContributions.sectionHelper')}
        </Typography>

        {/* ARIA live region — announces promote/demote results to screen readers (UI-NFR-002 R-011). */}
        <Box
          role="status"
          aria-live="polite"
          aria-atomic="true"
          sx={visuallyHidden}
          data-testid="pest-contributions-live-region"
        >
          {busyId !== null
            ? t('pages.admin.pestContributions.actionBusy')
            : ''}
        </Box>

        {pestsFailed && (
          <Alert severity="info" data-testid="pest-contributions-pests-unavailable">
            {t('pages.admin.pestContributions.pestsUnavailable')}
          </Alert>
        )}

        {!pestsFailed && (
          <Autocomplete
            options={pests ?? []}
            loading={pests === null}
            value={selectedPest}
            onChange={(_e, value) => handleSelectPest(value)}
            getOptionLabel={pestLabel}
            isOptionEqualToValue={(option, value) => option.key === value.key}
            renderInput={(params) => (
              <TextField
                {...params}
                label={t('pages.admin.pestContributions.selectPestLabel')}
                helperText={t('pages.admin.pestContributions.selectPestHelper')}
                size="small"
              />
            )}
            sx={{ maxWidth: 480 }}
            data-testid="pest-contributions-pest-select"
          />
        )}

        {selectedPest && (
          <Box sx={{ mt: 2 }}>
            {loadingContributions && (
              <Box
                sx={{ display: 'flex', flexDirection: 'column', gap: 1.5 }}
                aria-busy="true"
              >
                <LoadingStatus label={t('pages.admin.pestContributions.loading')} />
                {[0, 1, 2].map((i) => (
                  <Skeleton key={i} variant="rectangular" height={88} sx={{ borderRadius: 1 }} />
                ))}
              </Box>
            )}

            {!loadingContributions && contributionsFailed && (
              <Alert severity="info" data-testid="pest-contributions-unavailable">
                {t('pages.admin.pestContributions.contributionsUnavailable')}
              </Alert>
            )}

            {!loadingContributions && !contributionsFailed && contributions != null && contributions.length === 0 && (
              <Typography
                variant="body2"
                color="text.secondary"
                data-testid="pest-contributions-empty"
              >
                {t('pages.admin.pestContributions.empty')}
              </Typography>
            )}

            {!loadingContributions && contributions != null && contributions.length > 0 && (
              <>
                <Typography
                  variant="caption"
                  color="text.secondary"
                  sx={{ display: 'block', mb: 1 }}
                  aria-live="polite"
                  data-testid="pest-contributions-summary"
                >
                  {t('pages.admin.pestContributions.summary', {
                    count: contributions.length,
                    promoted: promotedCount,
                  })}
                </Typography>
                <Box
                  sx={{ display: 'flex', flexDirection: 'column', gap: 1.5 }}
                  role="list"
                  aria-label={t('pages.admin.pestContributions.listAriaLabel', {
                    name: pestLabel(selectedPest),
                  })}
                >
                  {contributions.map((contribution) => {
                    const promoted = contribution.status === 'promoted';
                    return (
                      <Box
                        key={contribution.id}
                        role="listitem"
                        data-testid="pest-contribution-row"
                        data-status={contribution.status}
                        sx={{
                          display: 'flex',
                          gap: 1.5,
                          alignItems: { xs: 'flex-start', sm: 'center' },
                          flexDirection: { xs: 'column', sm: 'row' },
                          p: 1,
                          border: '1px solid',
                          borderColor: 'divider',
                          borderRadius: 1,
                        }}
                      >
                        <AuthImage
                          uri={contribution.thumbnail_uri ?? contribution.content_uri}
                          alt={
                            contribution.caption ||
                            t('pages.admin.pestContributions.imageAlt', { name: pestLabel(selectedPest) })
                          }
                          width={96}
                          height={96}
                          sx={{ borderRadius: 1, flexShrink: 0 }}
                          data-testid="pest-contribution-thumb"
                        />
                        <Box sx={{ flexGrow: 1, minWidth: 0, width: '100%' }}>
                          {contribution.caption && (
                            <Typography variant="body2" sx={{ fontWeight: 500 }}>
                              {contribution.caption}
                            </Typography>
                          )}
                          <Typography variant="caption" color="text.secondary" sx={{ display: 'block' }}>
                            {t('pages.admin.pestContributions.provenance', {
                              user: contribution.contributed_by,
                              tenant: contribution.tenant_key,
                              date: formatDate(contribution.created_at),
                            })}
                          </Typography>
                          <Box sx={{ mt: 0.5 }}>
                            {promoted ? (
                              <Chip
                                size="small"
                                color="success"
                                icon={<PublicIcon aria-hidden="true" />}
                                label={t('pages.admin.pestContributions.statusGlobal')}
                                aria-label={t('pages.admin.pestContributions.statusGlobalAriaLabel')}
                                data-testid="pest-contribution-status"
                              />
                            ) : (
                              <Chip
                                size="small"
                                variant="outlined"
                                icon={<LockIcon aria-hidden="true" />}
                                label={t('pages.admin.pestContributions.statusPrivate')}
                                aria-label={t('pages.admin.pestContributions.statusPrivateAriaLabel')}
                                data-testid="pest-contribution-status"
                              />
                            )}
                          </Box>
                        </Box>
                        <Box sx={{ flexShrink: 0, alignSelf: { xs: 'stretch', sm: 'center' } }}>
                          {promoted ? (
                            <Tooltip title={t('pages.admin.pestContributions.demoteTooltip')}>
                              <span>
                                <Button
                                  size="small"
                                  variant="outlined"
                                  color="warning"
                                  disabled={busyId === contribution.id}
                                  startIcon={
                                    busyId === contribution.id ? (
                                      <CircularProgress size={14} color="inherit" aria-hidden="true" />
                                    ) : undefined
                                  }
                                  onClick={(e) => {
                                    demoteTriggerRef.current = e.currentTarget;
                                    setDemoteTarget(contribution);
                                  }}
                                  aria-label={t('pages.admin.pestContributions.demoteAria', {
                                    name: pestLabel(selectedPest),
                                  })}
                                  aria-busy={busyId === contribution.id}
                                  data-testid="pest-contribution-promote"
                                  data-promoted="true"
                                  sx={{ minHeight: 44, width: { xs: '100%', sm: 'auto' } }}
                                >
                                  {t('pages.admin.pestContributions.demoteButton')}
                                </Button>
                              </span>
                            </Tooltip>
                          ) : (
                            <Tooltip title={t('pages.admin.pestContributions.promoteTooltip')}>
                              <span>
                                <Button
                                  size="small"
                                  variant="contained"
                                  color="success"
                                  disabled={busyId === contribution.id}
                                  startIcon={
                                    busyId === contribution.id ? (
                                      <CircularProgress size={14} color="inherit" aria-hidden="true" />
                                    ) : undefined
                                  }
                                  onClick={() => void applyPromotion(contribution, true)}
                                  aria-label={t('pages.admin.pestContributions.promoteAria', {
                                    name: pestLabel(selectedPest),
                                  })}
                                  aria-busy={busyId === contribution.id}
                                  data-testid="pest-contribution-promote"
                                  data-promoted="false"
                                  sx={{ minHeight: 44, width: { xs: '100%', sm: 'auto' } }}
                                >
                                  {t('pages.admin.pestContributions.promoteButton')}
                                </Button>
                              </span>
                            </Tooltip>
                          )}
                        </Box>
                      </Box>
                    );
                  })}
                </Box>
              </>
            )}
          </Box>
        )}

        <ConfirmDialog
          open={demoteTarget !== null}
          title={t('pages.admin.pestContributions.demoteConfirmTitle')}
          message={t('pages.admin.pestContributions.demoteConfirmMessage')}
          confirmLabel={t('pages.admin.pestContributions.demoteButton')}
          onConfirm={() => void confirmDemote()}
          onCancel={cancelDemote}
          destructive
          loading={demoting}
        />
      </CardContent>
    </Card>
  );
}
