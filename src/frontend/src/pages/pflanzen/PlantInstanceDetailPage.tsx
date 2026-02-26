import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Typography from '@mui/material/Typography';
import Chip from '@mui/material/Chip';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import Table from '@mui/material/Table';
import TableBody from '@mui/material/TableBody';
import TableCell from '@mui/material/TableCell';
import TableHead from '@mui/material/TableHead';
import TableRow from '@mui/material/TableRow';
import Tabs from '@mui/material/Tabs';
import Tab from '@mui/material/Tab';
import RemoveCircleIcon from '@mui/icons-material/RemoveCircle';
import SwapHorizIcon from '@mui/icons-material/SwapHoriz';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import PageTitle from '@/components/layout/PageTitle';
import LoadingSkeleton from '@/components/common/LoadingSkeleton';
import ErrorDisplay from '@/components/common/ErrorDisplay';
import ConfirmDialog from '@/components/common/ConfirmDialog';
import FormTextField from '@/components/form/FormTextField';
import FormActions from '@/components/form/FormActions';
import UnsavedChangesGuard from '@/components/form/UnsavedChangesGuard';
import PhaseTransitionDialog from './PhaseTransitionDialog';
import { useNotification } from '@/hooks/useNotification';
import { useApiError } from '@/hooks/useApiError';
import * as plantApi from '@/api/endpoints/plantInstances';
import * as phasesApi from '@/api/endpoints/phases';
import type { PlantInstance, CurrentPhaseResponse, PhaseHistoryEntry } from '@/api/types';

const editSchema = z.object({
  plant_name: z.string().nullable(),
  cultivar_key: z.string().nullable(),
  slot_key: z.string().nullable(),
  substrate_batch_key: z.string().nullable(),
  planted_on: z.string().min(1),
});

type EditFormData = z.infer<typeof editSchema>;

export default function PlantInstanceDetailPage() {
  const { key } = useParams<{ key: string }>();
  const { t } = useTranslation();
  const navigate = useNavigate();
  const notification = useNotification();
  const { handleError } = useApiError();
  const [plant, setPlant] = useState<PlantInstance | null>(null);
  const [currentPhase, setCurrentPhase] = useState<CurrentPhaseResponse | null>(null);
  const [history, setHistory] = useState<PhaseHistoryEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [removeOpen, setRemoveOpen] = useState(false);
  const [transitionOpen, setTransitionOpen] = useState(false);
  const [tab, setTab] = useState(0);
  const [saving, setSaving] = useState(false);

  const {
    control,
    handleSubmit,
    reset,
    formState: { isDirty },
  } = useForm<EditFormData>({
    resolver: zodResolver(editSchema),
    defaultValues: {
      plant_name: null,
      cultivar_key: null,
      slot_key: null,
      substrate_batch_key: null,
      planted_on: '',
    },
  });

  const load = async () => {
    if (!key) return;
    setLoading(true);
    try {
      const p = await plantApi.getPlantInstance(key);
      setPlant(p);
      reset({
        plant_name: p.plant_name,
        cultivar_key: p.cultivar_key,
        slot_key: p.slot_key,
        substrate_batch_key: p.substrate_batch_key,
        planted_on: p.planted_on,
      });
      try {
        const cp = await phasesApi.getCurrentPhase(key);
        setCurrentPhase(cp);
      } catch {
        // Phase control may not be configured
      }
      try {
        const h = await phasesApi.getPhaseHistory(key);
        setHistory(h);
      } catch {
        // History may be empty
      }
    } catch (err) {
      setError(String(err));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, [key]); // eslint-disable-line react-hooks/exhaustive-deps

  const onRemove = async () => {
    if (!key) return;
    try {
      const updated = await plantApi.removePlantInstance(key);
      setPlant(updated);
      notification.success(t('pages.plantInstances.remove'));
    } catch (err) {
      handleError(err);
    }
    setRemoveOpen(false);
  };

  const onEditSubmit = async (data: EditFormData) => {
    if (!key || !plant) return;
    try {
      setSaving(true);
      await plantApi.updatePlantInstance(key, {
        instance_id: plant.instance_id,
        species_key: plant.species_key,
        ...data,
      });
      notification.success(t('common.save'));
      load();
    } catch (err) {
      handleError(err);
    } finally {
      setSaving(false);
    }
  };

  if (loading) return <LoadingSkeleton variant="form" />;
  if (error) return <ErrorDisplay error={error} onRetry={() => navigate(-1)} />;

  return (
    <Box data-testid="plant-instance-detail-page">
      <UnsavedChangesGuard dirty={isDirty} />
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <PageTitle title={plant?.plant_name ?? plant?.instance_id ?? t('entities.plantInstance')} />
        <Box sx={{ display: 'flex', gap: 1 }}>
          <Button
            startIcon={<SwapHorizIcon />}
            onClick={() => setTransitionOpen(true)}
            disabled={!!plant?.removed_on}
            data-testid="transition-button"
          >
            {t('pages.phases.transition')}
          </Button>
          <Button
            color="error"
            startIcon={<RemoveCircleIcon />}
            onClick={() => setRemoveOpen(true)}
            disabled={!!plant?.removed_on}
            data-testid="remove-button"
          >
            {t('pages.plantInstances.remove')}
          </Button>
        </Box>
      </Box>

      <Tabs value={tab} onChange={(_, v) => setTab(v)} sx={{ mb: 3 }}>
        <Tab label={t('pages.plantInstances.info')} />
        <Tab label={t('common.edit')} />
      </Tabs>

      {tab === 0 && (
        <>
          {plant && (
            <Box sx={{ display: 'flex', gap: 3, flexWrap: 'wrap', mb: 4 }}>
              <Card sx={{ minWidth: 250 }} data-testid="plant-info-card">
                <CardContent>
                  <Typography variant="subtitle2" color="text.secondary">
                    {t('pages.plantInstances.instanceId')}
                  </Typography>
                  <Typography>{plant.instance_id}</Typography>
                  <Typography variant="subtitle2" color="text.secondary" sx={{ mt: 1 }}>
                    {t('pages.plantInstances.plantedOn')}
                  </Typography>
                  <Typography>{plant.planted_on}</Typography>
                  {plant.removed_on && (
                    <>
                      <Typography variant="subtitle2" color="text.secondary" sx={{ mt: 1 }}>
                        {t('pages.plantInstances.removedOn')}
                      </Typography>
                      <Typography>{plant.removed_on}</Typography>
                    </>
                  )}
                </CardContent>
              </Card>

              <Card sx={{ minWidth: 250 }} data-testid="phase-info-card">
                <CardContent>
                  <Typography variant="subtitle2" color="text.secondary">
                    {t('pages.phases.current')}
                  </Typography>
                  <Chip label={plant.current_phase} color="primary" sx={{ mt: 0.5 }} data-testid="current-phase" />
                  {currentPhase && (
                    <>
                      <Typography variant="subtitle2" color="text.secondary" sx={{ mt: 1 }}>
                        {t('pages.phases.daysInPhase')}
                      </Typography>
                      <Typography>{currentPhase.days_in_phase}</Typography>
                      {currentPhase.next_phase && (
                        <>
                          <Typography variant="subtitle2" color="text.secondary" sx={{ mt: 1 }}>
                            {t('pages.phases.nextPhase')}
                          </Typography>
                          <Typography>{currentPhase.next_phase}</Typography>
                        </>
                      )}
                    </>
                  )}
                </CardContent>
              </Card>
            </Box>
          )}

          {history.length > 0 && (
            <Box data-testid="phase-history">
              <Typography variant="h6" sx={{ mb: 2 }}>
                {t('pages.phases.history')}
              </Typography>
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell>{t('pages.phases.current')}</TableCell>
                    <TableCell>{t('pages.phases.enteredAt')}</TableCell>
                    <TableCell>{t('pages.phases.exitedAt')}</TableCell>
                    <TableCell>{t('pages.phases.duration')}</TableCell>
                    <TableCell>{t('pages.phases.transitionReason')}</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {history.map((h) => (
                    <TableRow key={h.key}>
                      <TableCell>{h.phase_name}</TableCell>
                      <TableCell>{new Date(h.entered_at).toLocaleDateString()}</TableCell>
                      <TableCell>{h.exited_at ? new Date(h.exited_at).toLocaleDateString() : '-'}</TableCell>
                      <TableCell>{h.actual_duration_days ?? '-'}</TableCell>
                      <TableCell>{h.transition_reason}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </Box>
          )}
        </>
      )}

      {tab === 1 && (
        <Box component="form" onSubmit={handleSubmit(onEditSubmit)} sx={{ maxWidth: 600 }}>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
            {t('pages.plantInstances.editIntro')}
          </Typography>
          <FormTextField name="plant_name" control={control} label={t('pages.plantInstances.plantName')} helperText={t('pages.plantInstances.plantNameHelper')} />
          <FormTextField name="cultivar_key" control={control} label={t('pages.plantInstances.cultivarKey')} helperText={t('pages.plantInstances.cultivarKeyHelper')} />
          <FormTextField name="slot_key" control={control} label={t('pages.plantInstances.slotKey')} helperText={t('pages.plantInstances.slotKeyHelper')} />
          <FormTextField name="substrate_batch_key" control={control} label={t('pages.plantInstances.substrateBatchKey')} helperText={t('pages.plantInstances.substrateBatchKeyHelper')} />
          <FormTextField name="planted_on" control={control} label={t('pages.plantInstances.plantedOn')} helperText={t('pages.plantInstances.plantedOnHelper')} type="date" required />
          <FormActions onCancel={() => setTab(0)} loading={saving} />
        </Box>
      )}

      <ConfirmDialog
        open={removeOpen}
        title={t('pages.plantInstances.remove')}
        message={t('common.deleteConfirm', { name: plant?.plant_name ?? plant?.instance_id })}
        onConfirm={onRemove}
        onCancel={() => setRemoveOpen(false)}
        destructive
      />

      {key && (
        <PhaseTransitionDialog
          plantKey={key}
          lifecycleKey={plant?.current_phase_key ?? null}
          open={transitionOpen}
          onClose={() => setTransitionOpen(false)}
          onTransitioned={(updated) => {
            setPlant(updated);
            setTransitionOpen(false);
            load();
          }}
        />
      )}
    </Box>
  );
}
