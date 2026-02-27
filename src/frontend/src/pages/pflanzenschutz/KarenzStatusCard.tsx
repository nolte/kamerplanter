import { useEffect, useMemo } from 'react';
import { useTranslation } from 'react-i18next';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import Typography from '@mui/material/Typography';
import Box from '@mui/material/Box';
import Chip from '@mui/material/Chip';
import Alert from '@mui/material/Alert';
import WarningAmberIcon from '@mui/icons-material/WarningAmber';
import CheckCircleOutlineIcon from '@mui/icons-material/CheckCircleOutline';
import LoadingSkeleton from '@/components/common/LoadingSkeleton';
import { useAppDispatch, useAppSelector } from '@/store/hooks';
import { fetchKarenzPeriods } from '@/store/slices/ipmSlice';

interface Props {
  plantKey: string;
}

export default function KarenzStatusCard({ plantKey }: Props) {
  const { t } = useTranslation();
  const dispatch = useAppDispatch();
  const { karenzPeriods } = useAppSelector((s) => s.ipm);

  useEffect(() => {
    if (plantKey) {
      dispatch(fetchKarenzPeriods(plantKey));
    }
  }, [dispatch, plantKey]);

  const hasActiveKarenz = useMemo(
    () => karenzPeriods.length > 0,
    [karenzPeriods],
  );

  if (!plantKey) {
    return null;
  }

  return (
    <Card variant="outlined" data-testid="karenz-status-card">
      <CardContent>
        <Box
          sx={{
            display: 'flex',
            alignItems: 'center',
            gap: 1,
            mb: 2,
          }}
        >
          {hasActiveKarenz ? (
            <WarningAmberIcon color="warning" />
          ) : (
            <CheckCircleOutlineIcon color="success" />
          )}
          <Typography variant="h6" component="h3">
            {t('pages.ipm.karenzTitle')}
          </Typography>
        </Box>

        {karenzPeriods.length === 0 ? (
          <Alert severity="success" data-testid="karenz-safe">
            {t('pages.ipm.karenzSafe')}
          </Alert>
        ) : (
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
            <Alert severity="warning" data-testid="karenz-active">
              {t('pages.ipm.karenzActive', { count: karenzPeriods.length })}
            </Alert>
            {karenzPeriods.map((period, index) => (
              <Box
                key={index}
                sx={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 1,
                  flexWrap: 'wrap',
                }}
              >
                <Chip
                  label={period.treatment_name ?? period.active_ingredient ?? '—'}
                  color="warning"
                  size="small"
                />
                <Typography variant="body2" color="text.secondary">
                  {period.safety_interval_days != null
                    ? t('pages.ipm.karenzDays', {
                        days: period.safety_interval_days,
                      })
                    : ''}
                </Typography>
                {period.safe_date && (
                  <Typography variant="body2" color="text.secondary">
                    {t('pages.ipm.karenzSafeDate', {
                      date: period.safe_date,
                    })}
                  </Typography>
                )}
              </Box>
            ))}
          </Box>
        )}
      </CardContent>
    </Card>
  );
}

// Re-export with a loading wrapper for use in detail pages
export function KarenzStatusCardWithLoading({ plantKey }: Props) {
  const { karenzPeriods } = useAppSelector((s) => s.ipm);
  const dispatch = useAppDispatch();

  useEffect(() => {
    if (plantKey) {
      dispatch(fetchKarenzPeriods(plantKey));
    }
  }, [dispatch, plantKey]);

  if (!karenzPeriods) {
    return <LoadingSkeleton variant="card" />;
  }

  return <KarenzStatusCard plantKey={plantKey} />;
}
