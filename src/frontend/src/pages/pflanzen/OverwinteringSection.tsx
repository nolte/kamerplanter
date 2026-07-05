import { useEffect, useMemo, useState } from 'react';
import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import Typography from '@mui/material/Typography';
import Chip from '@mui/material/Chip';
import Button from '@mui/material/Button';
import Tooltip from '@mui/material/Tooltip';
import Divider from '@mui/material/Divider';
import AutoAwesomeIcon from '@mui/icons-material/AutoAwesome';
import EditIcon from '@mui/icons-material/Edit';
import RestartAltIcon from '@mui/icons-material/RestartAlt';
import AcUnitIcon from '@mui/icons-material/AcUnit';
import LoadingSkeleton from '@/components/common/LoadingSkeleton';
import ConfirmDialog from '@/components/common/ConfirmDialog';
import { useAppDispatch, useAppSelector } from '@/store/hooks';
import {
  clearCurrentProfile,
  fetchOverwintering,
  resetOverwintering,
} from '@/store/slices/seasonSlice';
import { useNotification } from '@/hooks/useNotification';
import { useApiError } from '@/hooks/useApiError';
import OverwinteringOverrideDialog from './OverwinteringOverrideDialog';

interface Props {
  plantKey: string;
}

/** One read-only labelled field in the profile summary. */
function Field({ label, value }: { label: string; value: string }) {
  return (
    <Box>
      <Typography variant="caption" color="text.secondary" sx={{ display: 'block' }}>
        {label}
      </Typography>
      <Typography variant="body2">{value}</Typography>
    </Box>
  );
}

/**
 * REQ-047 §4.3 — overwintering section on the plant-instance detail page.
 *
 * Shows the auto-materialised overwintering profile read-only with an
 * "automatically derived from the species profile" hint, offers an "adjust"
 * affordance (override dialog → PATCH, sets `user_overridden`) and a
 * "reset to automatic" button (re-materialise). Winter-hardy plants have no
 * profile — the section then explains why nothing needs to be done.
 */
export default function OverwinteringSection({ plantKey }: Props) {
  const { t, i18n } = useTranslation();
  const dispatch = useAppDispatch();
  const notification = useNotification();
  const { handleError } = useApiError();
  const { currentProfile, profileLoading } = useAppSelector((s) => s.season);
  const [editOpen, setEditOpen] = useState(false);
  const [resetOpen, setResetOpen] = useState(false);
  const [resetting, setResetting] = useState(false);

  useEffect(() => {
    dispatch(fetchOverwintering(plantKey));
    return () => {
      dispatch(clearCurrentProfile());
    };
  }, [dispatch, plantKey]);

  const locale = i18n.language === 'de' ? 'de-DE' : 'en-GB';
  const monthName = (m: number | null) =>
    m ? new Date(2024, m - 1).toLocaleString(i18n.language, { month: 'long' }) : '—';

  const originChip = useMemo(() => {
    if (!currentProfile) return null;
    if (currentProfile.user_overridden) {
      return (
        <Chip
          icon={<EditIcon />}
          label={t('pages.season.override.overriddenBadge')}
          size="small"
          color="secondary"
          variant="outlined"
          data-testid="overwintering-overridden-badge"
        />
      );
    }
    if (currentProfile.auto_generated) {
      return (
        <Chip
          icon={<AutoAwesomeIcon />}
          label={t('pages.season.override.autoBadge')}
          size="small"
          color="info"
          variant="outlined"
          data-testid="overwintering-auto-badge"
        />
      );
    }
    return null;
  }, [currentProfile, t]);

  const handleReset = async () => {
    try {
      setResetting(true);
      await dispatch(resetOverwintering(plantKey)).unwrap();
      notification.success(t('pages.season.override.resetDone'));
      setResetOpen(false);
    } catch (err) {
      handleError(err);
    } finally {
      setResetting(false);
    }
  };

  if (profileLoading && !currentProfile) {
    return <LoadingSkeleton variant="card" />;
  }

  // No profile: winter-hardy plant or not yet materialised. Explain, don't alarm.
  if (!currentProfile) {
    return (
      <Card data-testid="overwintering-section-empty">
        <CardContent>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
            <AcUnitIcon color="primary" />
            <Typography variant="h6" component="h2">
              {t('pages.season.override.title')}
            </Typography>
          </Box>
          <Typography variant="body2" color="text.secondary">
            {t('pages.season.override.emptyHint')}
          </Typography>
        </CardContent>
      </Card>
    );
  }

  const p = currentProfile;

  return (
    <Card data-testid="overwintering-section">
      <CardContent>
        <Box
          sx={{
            display: 'flex',
            flexDirection: { xs: 'column', sm: 'row' },
            alignItems: { xs: 'flex-start', sm: 'center' },
            justifyContent: 'space-between',
            gap: 1,
            mb: 1.5,
          }}
        >
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, flexWrap: 'wrap' }}>
            <AcUnitIcon color="primary" />
            <Typography variant="h6" component="h2">
              {t('pages.season.override.title')}
            </Typography>
            {originChip}
          </Box>
          <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
            <Button
              size="small"
              startIcon={<EditIcon />}
              onClick={() => setEditOpen(true)}
              data-testid="overwintering-adjust-button"
            >
              {t('pages.season.override.adjust')}
            </Button>
            {p.user_overridden && (
              <Button
                size="small"
                color="warning"
                startIcon={<RestartAltIcon />}
                onClick={() => setResetOpen(true)}
                data-testid="overwintering-reset-button"
              >
                {t('pages.season.override.resetButton')}
              </Button>
            )}
          </Box>
        </Box>

        {/* Auto-derivation hint + traceability (materialised date). */}
        {p.auto_generated && !p.user_overridden && (
          <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
            {t('pages.season.override.autoHint')}
            {p.materialized_at &&
              ` (${new Date(p.materialized_at).toLocaleDateString(locale)})`}
          </Typography>
        )}

        <Box
          sx={{
            display: 'grid',
            gridTemplateColumns: { xs: 'repeat(2, 1fr)', sm: 'repeat(3, 1fr)' },
            gap: 2,
          }}
        >
          {p.derived_path && (
            <Box>
              <Tooltip title={t(`pages.season.override.pathHelp.${p.derived_path}`)} arrow enterTouchDelay={0}>
                <Typography
                  variant="caption"
                  color="text.secondary"
                  sx={{ display: 'block', cursor: 'help', textDecoration: 'underline dotted' }}
                >
                  {t('pages.season.override.winterPath')}
                </Typography>
              </Tooltip>
              <Chip
                label={t(`pages.season.override.path.${p.derived_path}`)}
                size="small"
                color={p.derived_path === 'B' ? 'error' : 'warning'}
                variant="outlined"
              />
            </Box>
          )}
          <Field
            label={t('pages.overwintering.hardinessRating')}
            value={t(`enums.hardinessRating.${p.hardiness_rating}`)}
          />
          <Field
            label={t('pages.overwintering.winterAction')}
            value={t(`enums.winterAction.${p.winter_action}`)}
          />
          <Field
            label={t('pages.overwintering.winterActionMonth')}
            value={monthName(p.winter_action_month)}
          />
          {p.spring_action && (
            <Field
              label={t('pages.overwintering.springAction')}
              value={t(`enums.springAction.${p.spring_action}`)}
            />
          )}
          {p.spring_action_month != null && (
            <Field
              label={t('pages.overwintering.springActionMonth')}
              value={monthName(p.spring_action_month)}
            />
          )}
          {p.winter_watering && (
            <Field
              label={t('pages.overwintering.winterWatering')}
              value={t(`enums.winterWatering.${p.winter_watering}`)}
            />
          )}
          {p.winter_quarter_light && (
            <Field
              label={t('pages.overwintering.winterQuarterLight')}
              value={t(`enums.winterQuarterLight.${p.winter_quarter_light}`)}
            />
          )}
          {(p.winter_quarter_temp_min != null || p.winter_quarter_temp_max != null) && (
            <Field
              label={t('pages.season.override.winterQuarterTemp')}
              value={`${p.winter_quarter_temp_min ?? '—'} … ${p.winter_quarter_temp_max ?? '—'} °C`}
            />
          )}
          {p.storage_check_interval_days != null && (
            <Field
              label={t('pages.overwintering.storageCheckIntervalDays')}
              value={`${p.storage_check_interval_days} ${t('pages.overwintering.daysUnit')}`}
            />
          )}
          {p.tuber_status && (
            <Field
              label={t('pages.overwintering.tuberStatus')}
              value={t(`enums.tuberStatus.${p.tuber_status}`)}
            />
          )}
        </Box>

        {p.notes && (
          <>
            <Divider sx={{ my: 2 }} />
            <Typography variant="body2" color="text.secondary" sx={{ fontStyle: 'italic' }}>
              {p.notes}
            </Typography>
          </>
        )}

        {p.dormancy_care_active && (
          <Chip
            icon={<AcUnitIcon />}
            label={t('pages.season.override.dormancyActive')}
            size="small"
            color="info"
            sx={{ mt: 2 }}
            data-testid="overwintering-dormancy-active"
          />
        )}
      </CardContent>

      {editOpen && (
        <OverwinteringOverrideDialog
          open={editOpen}
          onClose={() => setEditOpen(false)}
          plantKey={plantKey}
          profile={p}
        />
      )}

      <ConfirmDialog
        open={resetOpen}
        title={t('pages.season.override.resetConfirmTitle')}
        message={t('pages.season.override.resetConfirmMessage')}
        confirmLabel={t('pages.season.override.resetButton')}
        onConfirm={handleReset}
        onCancel={() => setResetOpen(false)}
        loading={resetting}
      />
    </Card>
  );
}
