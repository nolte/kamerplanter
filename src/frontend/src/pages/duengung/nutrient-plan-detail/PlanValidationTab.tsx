import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import Typography from '@mui/material/Typography';
import Alert from '@mui/material/Alert';
import CircularProgress from '@mui/material/CircularProgress';
import IconButton from '@mui/material/IconButton';
import Tooltip from '@mui/material/Tooltip';
import EditIcon from '@mui/icons-material/Edit';
import type {
  PlanValidationResult,
  NutrientPlanPhaseEntry,
  DeliveryChannel,
} from '@/api/types';

interface PlanValidationTabProps {
  validation: PlanValidationResult | null;
  validating: boolean;
  entries: NutrientPlanPhaseEntry[];
  onEditChannel: (entryKey: string, channel: DeliveryChannel) => void;
}

export default function PlanValidationTab({
  validation,
  validating,
  entries,
  onEditChannel,
}: PlanValidationTabProps) {
  const { t } = useTranslation();

  return (
    <Box>
      {validating && !validation && (
        <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
          <CircularProgress />
        </Box>
      )}
      {validation && (
        <>
          <Card sx={{ mb: 2 }}>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                {t('pages.nutrientPlans.completeness')}
              </Typography>
              <Alert
                severity={validation.completeness.complete ? 'success' : 'warning'}
                sx={{ mb: 1 }}
              >
                {validation.completeness.complete
                  ? t('pages.nutrientPlans.planComplete')
                  : t('pages.nutrientPlans.planIncomplete')}
              </Alert>
              {(validation.completeness.issues ?? []).map((issue, i) => (
                <Alert key={i} severity="warning" sx={{ mb: 0.5 }}>
                  {issue}
                </Alert>
              ))}
            </CardContent>
          </Card>

          {/* Channel Validations with EC Budget */}
          {(validation.channel_validations ?? []).length > 0 && (
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  {t('pages.deliveryChannels.validation.title')}
                </Typography>
                {(validation.channel_validations ?? []).map((cv, i) => (
                  <Box key={i} sx={{ mb: 2 }}>
                    <Typography variant="subtitle2" sx={{ mb: 0.5 }}>
                      {t(`enums.phaseName.${cv.phase_name}`)}
                    </Typography>
                    {(cv.channel_results ?? []).map((cr, j) => (
                      <Alert
                        key={j}
                        severity={cr.issues.length === 0 ? 'success' : 'error'}
                        sx={{ mb: 0.5 }}
                        action={
                          <Tooltip title={t('common.edit')}>
                            <IconButton
                              size="small"
                              onClick={() => {
                                const entry = entries.find((e) => e.key === cv.entry_key);
                                if (!entry) return;
                                const channel = entry.delivery_channels.find(
                                  (ch) => ch.channel_id === cr.channel_id,
                                );
                                if (channel) {
                                  onEditChannel(entry.key, channel);
                                }
                              }}
                            >
                              <EditIcon fontSize="small" />
                            </IconButton>
                          </Tooltip>
                        }
                      >
                        <strong>{cr.label || cr.channel_id}</strong>:{' '}
                        {cr.issues.length === 0
                          ? t('pages.deliveryChannels.validation.noIssues')
                          : cr.issues.join('; ')}
                        {cr.ec_budget && (
                          <Box component="span" sx={{ display: 'block', mt: 0.5, fontSize: '0.85em' }}>
                            EC: {cr.ec_budget.calculated.toFixed(2)} / {cr.ec_budget.target} mS
                            {' '}({t('pages.nutrientPlans.delta')}: {cr.ec_budget.delta > 0 ? '+' : ''}{cr.ec_budget.delta.toFixed(2)},
                            {' '}{t('pages.deliveryChannels.validation.tolerance')}: ±{cr.ec_budget.tolerance.toFixed(2)})
                          </Box>
                        )}
                      </Alert>
                    ))}
                  </Box>
                ))}
              </CardContent>
            </Card>
          )}
        </>
      )}
    </Box>
  );
}
