import { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import Button from '@mui/material/Button';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import Grid from '@mui/material/Grid';
import AutoFixHighIcon from '@mui/icons-material/AutoFixHigh';
import LoadingSkeleton from '@/components/common/LoadingSkeleton';
import { useNotification } from '@/hooks/useNotification';
import { useApiError } from '@/hooks/useApiError';
import * as phasesApi from '@/api/endpoints/phases';
import type { RequirementProfile, NutrientProfile } from '@/api/types';

interface Props {
  phaseKey: string;
  phaseName: string;
}

export default function ProfilesSection({ phaseKey, phaseName }: Props) {
  const { t } = useTranslation();
  const notification = useNotification();
  const { handleError } = useApiError();
  const [reqProfile, setReqProfile] = useState<RequirementProfile | null>(null);
  const [nutProfile, setNutProfile] = useState<NutrientProfile | null>(null);
  const [loading, setLoading] = useState(true);

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

  useEffect(() => { load(); }, [phaseKey]); // eslint-disable-line react-hooks/exhaustive-deps

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

  if (loading) return <LoadingSkeleton variant="card" />;

  return (
    <Box sx={{ mt: 3 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
        <Typography variant="h6">
          {phaseName} — {t('entities.profile')}
        </Typography>
        {!reqProfile && !nutProfile && (
          <Button startIcon={<AutoFixHighIcon />} onClick={generateDefaults}>
            {t('pages.profiles.generateDefaults')}
          </Button>
        )}
      </Box>

      <Grid container spacing={2}>
        {reqProfile && (
          <Grid size={{ xs: 12, md: 6 }}>
            <Card>
              <CardContent>
                <Typography variant="subtitle1" sx={{ mb: 1 }}>
                  {t('pages.profiles.requirements')}
                </Typography>
                <ProfileRow label={t('pages.profiles.lightPpfd')} value={reqProfile.light_ppfd_target} />
                <ProfileRow label={t('pages.profiles.photoperiodHours')} value={`${reqProfile.photoperiod_hours}h`} />
                <ProfileRow label={t('pages.profiles.tempDay')} value={`${reqProfile.temperature_day_c}°C`} />
                <ProfileRow label={t('pages.profiles.tempNight')} value={`${reqProfile.temperature_night_c}°C`} />
                <ProfileRow label={t('pages.profiles.humidityDay')} value={`${reqProfile.humidity_day_percent}%`} />
                <ProfileRow label={t('pages.profiles.humidityNight')} value={`${reqProfile.humidity_night_percent}%`} />
                <ProfileRow label={t('pages.profiles.vpdTarget')} value={`${reqProfile.vpd_target_kpa} kPa`} />
              </CardContent>
            </Card>
          </Grid>
        )}

        {nutProfile && (
          <Grid size={{ xs: 12, md: 6 }}>
            <Card>
              <CardContent>
                <Typography variant="subtitle1" sx={{ mb: 1 }}>
                  {t('pages.profiles.nutrients')}
                </Typography>
                <ProfileRow label={t('pages.profiles.npkRatio')} value={nutProfile.npk_ratio.join('-')} />
                <ProfileRow label={t('pages.profiles.targetEc')} value={`${nutProfile.target_ec_ms} mS/cm`} />
                <ProfileRow label={t('pages.profiles.targetPh')} value={nutProfile.target_ph} />
                {nutProfile.calcium_ppm && <ProfileRow label="Ca" value={`${nutProfile.calcium_ppm} ppm`} />}
                {nutProfile.magnesium_ppm && <ProfileRow label="Mg" value={`${nutProfile.magnesium_ppm} ppm`} />}
              </CardContent>
            </Card>
          </Grid>
        )}
      </Grid>
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
