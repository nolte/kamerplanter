import { useTranslation } from 'react-i18next';
import Accordion from '@mui/material/Accordion';
import AccordionSummary from '@mui/material/AccordionSummary';
import AccordionDetails from '@mui/material/AccordionDetails';
import Box from '@mui/material/Box';
import Chip from '@mui/material/Chip';
import Typography from '@mui/material/Typography';
import Table from '@mui/material/Table';
import TableBody from '@mui/material/TableBody';
import TableCell from '@mui/material/TableCell';
import TableHead from '@mui/material/TableHead';
import TableRow from '@mui/material/TableRow';
import IconButton from '@mui/material/IconButton';
import Button from '@mui/material/Button';
import Tooltip from '@mui/material/Tooltip';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import DeleteIcon from '@mui/icons-material/Delete';
import EditIcon from '@mui/icons-material/Edit';
import AddIcon from '@mui/icons-material/Add';
import type { DeliveryChannel, Fertilizer, FertilizerDosage } from '@/api/types';

interface Props {
  channels: DeliveryChannel[];
  fertilizers: Fertilizer[];
  onEditChannel?: (channel: DeliveryChannel) => void;
  onDeleteChannel?: (channelId: string) => void;
  onAddFertilizer?: (channelId: string) => void;
  onEditFertilizer?: (channelId: string, dosage: FertilizerDosage) => void;
  onRemoveFertilizer?: (channelId: string, fertilizerKey: string) => void;
}

export default function DeliveryChannelAccordion({
  channels,
  fertilizers,
  onEditChannel,
  onDeleteChannel,
  onAddFertilizer,
  onEditFertilizer,
  onRemoveFertilizer,
}: Props) {
  const { t } = useTranslation();

  const getFertilizerName = (fertKey: string): string => {
    const f = fertilizers.find((fert) => fert.key === fertKey);
    return f ? `${f.product_name} (${f.brand})` : fertKey;
  };

  const formatDuration = (seconds: number): string => {
    if (seconds >= 60 && seconds % 60 === 0) {
      return `${seconds / 60} min`;
    }
    return `${seconds}s`;
  };

  const getMethodParamsLabel = (ch: DeliveryChannel): string | null => {
    if (!ch.method_params) return null;
    switch (ch.method_params.method) {
      case 'fertigation':
        return `${ch.method_params.runs_per_day}x/day, ${formatDuration(ch.method_params.duration_seconds)}`;
      case 'drench':
        return `${ch.method_params.volume_per_feeding_liters} L`;
      case 'foliar':
        return `${ch.method_params.volume_per_spray_liters} L spray`;
      case 'top_dress':
        if (ch.method_params.grams_per_plant) return `${ch.method_params.grams_per_plant} g/plant`;
        if (ch.method_params.grams_per_m2) return `${ch.method_params.grams_per_m2} g/m²`;
        return null;
      default:
        return null;
    }
  };

  return (
    <Box sx={{ mt: 1 }}>
      {channels.map((ch) => (
        <Accordion key={ch.channel_id} variant="outlined" disableGutters>
          <AccordionSummary expandIcon={<ExpandMoreIcon />}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, flexWrap: 'wrap', width: '100%' }}>
              <Chip
                label={ch.label || ch.channel_id}
                size="small"
                color={ch.enabled ? 'info' : 'default'}
                variant={ch.enabled ? 'filled' : 'outlined'}
              />
              <Chip
                label={t(`enums.applicationMethod.${ch.application_method}`)}
                size="small"
                variant="outlined"
              />
              {!ch.enabled && (
                <Chip
                  label={t('pages.deliveryChannels.disabled')}
                  size="small"
                  color="warning"
                  variant="outlined"
                />
              )}
              {ch.target_ec_ms != null && (
                <Typography variant="body2" color="text.secondary">
                  EC: {ch.target_ec_ms} mS
                </Typography>
              )}
              {ch.target_ph != null && (
                <Typography variant="body2" color="text.secondary">
                  pH: {ch.target_ph}
                </Typography>
              )}
              {getMethodParamsLabel(ch) && (
                <Typography variant="body2" color="text.secondary">
                  {getMethodParamsLabel(ch)}
                </Typography>
              )}
              {ch.schedule && (
                <Chip
                  label={
                    ch.schedule.schedule_mode === 'weekdays'
                      ? t('pages.wateringSchedule.weekdays')
                      : `${ch.schedule.interval_days}d`
                  }
                  size="small"
                  variant="outlined"
                  color="secondary"
                />
              )}
            </Box>
          </AccordionSummary>
          <AccordionDetails>
            {/* Channel action buttons */}
            {(onEditChannel || onDeleteChannel) && (
              <Box sx={{ display: 'flex', justifyContent: 'flex-end', gap: 0.5, mb: 1 }}>
                {onEditChannel && (
                  <Tooltip title={t('pages.deliveryChannels.editChannel')}>
                    <IconButton
                      size="small"
                      onClick={() => onEditChannel(ch)}
                    >
                      <EditIcon fontSize="small" />
                    </IconButton>
                  </Tooltip>
                )}
                {onDeleteChannel && (
                  <Tooltip title={t('pages.deliveryChannels.deleteChannel')}>
                    <IconButton
                      size="small"
                      color="error"
                      onClick={() => onDeleteChannel(ch.channel_id)}
                    >
                      <DeleteIcon fontSize="small" />
                    </IconButton>
                  </Tooltip>
                )}
              </Box>
            )}

            {ch.notes && (
              <Typography variant="body2" color="text.secondary" sx={{ mb: 1, fontStyle: 'italic' }}>
                {ch.notes}
              </Typography>
            )}

            {/* Fertilizer dosages table */}
            <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 1 }}>
              <Typography variant="subtitle2">
                {t('pages.deliveryChannels.fertilizers')}
              </Typography>
              {onAddFertilizer && (
                <Button
                  size="small"
                  startIcon={<AddIcon />}
                  onClick={() => onAddFertilizer(ch.channel_id)}
                >
                  {t('pages.nutrientPlans.addFertilizer')}
                </Button>
              )}
            </Box>
            {ch.fertilizer_dosages.length === 0 ? (
              <Typography variant="body2" color="text.secondary">
                {t('pages.nutrientPlans.noFertilizers')}
              </Typography>
            ) : (
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell>{t('entities.fertilizer')}</TableCell>
                    <TableCell align="right">{t('pages.nutrientPlans.mlPerLiter')}</TableCell>
                    <TableCell align="center">{t('common.optional')}</TableCell>
                    {(onEditFertilizer || onRemoveFertilizer) && (
                      <TableCell align="right">{t('common.actions')}</TableCell>
                    )}
                  </TableRow>
                </TableHead>
                <TableBody>
                  {ch.fertilizer_dosages.map((dosage) => (
                    <TableRow key={dosage.fertilizer_key}>
                      <TableCell>{getFertilizerName(dosage.fertilizer_key)}</TableCell>
                      <TableCell align="right">{dosage.ml_per_liter} ml/L</TableCell>
                      <TableCell align="center">
                        <Chip
                          label={dosage.optional ? t('common.yes') : t('common.no')}
                          size="small"
                          variant={dosage.optional ? 'outlined' : 'filled'}
                        />
                      </TableCell>
                      {(onEditFertilizer || onRemoveFertilizer) && (
                        <TableCell align="right">
                          <Box sx={{ display: 'flex', justifyContent: 'flex-end', gap: 0.5 }}>
                            {onEditFertilizer && (
                              <IconButton
                                size="small"
                                onClick={() => onEditFertilizer(ch.channel_id, dosage)}
                              >
                                <EditIcon fontSize="small" />
                              </IconButton>
                            )}
                            {onRemoveFertilizer && (
                              <IconButton
                                size="small"
                                color="error"
                                onClick={() => onRemoveFertilizer(ch.channel_id, dosage.fertilizer_key)}
                              >
                                <DeleteIcon fontSize="small" />
                              </IconButton>
                            )}
                          </Box>
                        </TableCell>
                      )}
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            )}
          </AccordionDetails>
        </Accordion>
      ))}
    </Box>
  );
}
