import { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import Button from '@mui/material/Button';
import IconButton from '@mui/material/IconButton';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import Divider from '@mui/material/Divider';
import Grid from '@mui/material/Grid';
import AutoFixHighIcon from '@mui/icons-material/AutoFixHigh';
import EditIcon from '@mui/icons-material/Edit';
import LoadingSkeleton from '@/components/common/LoadingSkeleton';
import EmptyState from '@/components/common/EmptyState';
import ProfileEditDialog from './ProfileEditDialog';
import { useNotification } from '@/hooks/useNotification';
import { useApiError } from '@/hooks/useApiError';
import * as phasesApi from '@/api/endpoints/phases';
import type { RequirementProfile, NutrientProfile } from '@/api/types';

interface Props {
  phaseKey: string;
  phaseName: string;
  readOnly?: boolean;
}

export default function ProfilesSection({ phaseKey, phaseName, readOnly }: Props) {
  const { t } = useTranslation();
  const notification = useNotification();
  const { handleError } = useApiError();
  const [reqProfile, setReqProfile] = useState<RequirementProfile | null>(null);
  const [nutProfile, setNutProfile] = useState<NutrientProfile | null>(null);
  const [loading, setLoading] = useState(true);
  const [editOpen, setEditOpen] = useState(false);

  const load = async () => {
    setLoading(true);
    try {
      const req = await phasesApi.getRequirementProfile(phaseKey);
      setReqProfile(req);
    } catch {
      setReqProfile(null);
    }
    try {
      const nut = await phasesApi.getNutrientProfile(phaseKey);
      setNutProfile(nut);
    } catch {
      setNutProfile(null);
    }
    setLoading(false);
  };

  useEffect(() => { void load(); }, [phaseKey]); // eslint-disable-line react-hooks/exhaustive-deps, react-hooks/set-state-in-effect

  const generateDefaults = async () => {
    try {
      const result = await phasesApi.generateDefaultProfiles(phaseKey);
      setReqProfile(result.requirement);
      setNutProfile(result.nutrient);
      notification.success(t('pages.profiles.generateDefaults'));
    } catch (err) {
      handleError(err);
    }
  };

  const handleEditSaved = () => {
    setEditOpen(false);
    load();
  };

  if (loading) return <LoadingSkeleton variant="card" />;

  const hasProfiles = !!(reqProfile || nutProfile);

  return (
    <Box sx={{ mt: 3 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
        <Typography variant="h6">
          {phaseName} — {t('entities.profile')}
        </Typography>
        <Box sx={{ display: 'flex', gap: 1 }}>
          {!readOnly && !hasProfiles && (
            <Button startIcon={<AutoFixHighIcon />} onClick={generateDefaults} variant="outlined" size="small">
              {t('pages.profiles.generateDefaults')}
            </Button>
          )}
          {!readOnly && hasProfiles && (
            <IconButton onClick={() => setEditOpen(true)} aria-label={t('common.edit')} data-testid="edit-profiles-btn">
              <EditIcon />
            </IconButton>
          )}
        </Box>
      </Box>

      {!hasProfiles ? (
        <EmptyState
          message={t('pages.profiles.noProfiles')}
          actionLabel={!readOnly ? t('pages.profiles.generateDefaults') : undefined}
          onAction={!readOnly ? generateDefaults : undefined}
        />
      ) : (
        <Grid container spacing={2}>
          {reqProfile && (
            <Grid size={{ xs: 12, md: 6 }}>
              <Card variant="outlined">
                <CardContent>
                  <Typography variant="subtitle2" color="text.secondary" sx={{ mb: 1.5 }}>
                    {t('pages.profiles.requirements')}
                  </Typography>
                  <ProfileRow label={`${t('pages.profiles.lightPpfd')} (PPFD)`} value={reqProfile.light_ppfd_target} />
                  <ProfileRow label={t('pages.profiles.photoperiodHours')} value={`${reqProfile.photoperiod_hours} h`} />
                  <Divider sx={{ my: 1 }} />
                  <ProfileRow label={t('pages.profiles.tempDay')} value={`${reqProfile.temperature_day_c} °C`} />
                  <ProfileRow label={t('pages.profiles.tempNight')} value={`${reqProfile.temperature_night_c} °C`} />
                  <ProfileRow label={t('pages.profiles.humidityDay')} value={`${reqProfile.humidity_day_percent} %`} />
                  <ProfileRow label={t('pages.profiles.humidityNight')} value={`${reqProfile.humidity_night_percent} %`} />
                  <ProfileRow label={`VPD ${t('pages.profiles.vpdTarget')}`} value={`${reqProfile.vpd_target_kpa} kPa`} />
                </CardContent>
              </Card>
            </Grid>
          )}

          {nutProfile && (
            <Grid size={{ xs: 12, md: 6 }}>
              <Card variant="outlined">
                <CardContent>
                  <Typography variant="subtitle2" color="text.secondary" sx={{ mb: 1.5 }}>
                    {t('pages.profiles.nutrients')}
                  </Typography>
                  <ProfileRow label={t('pages.profiles.npkRatio')} value={nutProfile.npk_ratio.join(' \u2013 ')} />
                  <Divider sx={{ my: 1 }} />
                  <ProfileRow label="EC" value={`${nutProfile.target_ec_ms} mS/cm`} />
                  <ProfileRow label="pH" value={nutProfile.target_ph} />
                  {nutProfile.calcium_ppm != null && <ProfileRow label="Ca" value={`${nutProfile.calcium_ppm} ppm`} />}
                  {nutProfile.magnesium_ppm != null && <ProfileRow label="Mg" value={`${nutProfile.magnesium_ppm} ppm`} />}
                </CardContent>
              </Card>
            </Grid>
          )}
        </Grid>
      )}

      {!readOnly && (
        <ProfileEditDialog
          open={editOpen}
          onClose={() => setEditOpen(false)}
          onSaved={handleEditSaved}
          phaseKey={phaseKey}
          phaseName={phaseName}
          reqProfile={reqProfile}
          nutProfile={nutProfile}
        />
      )}
    </Box>
  );
}

function ProfileRow({ label, value }: { label: string; value: string | number }) {
  return (
    <Box sx={{ display: 'flex', justifyContent: 'space-between', py: 0.5 }}>
      <Typography variant="body2" color="text.secondary">{label}</Typography>
      <Typography variant="body2">{value}</Typography>
    </Box>
  );
}
