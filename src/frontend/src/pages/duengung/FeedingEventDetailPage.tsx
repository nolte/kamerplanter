import { useEffect, useState, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import Table from '@mui/material/Table';
import TableBody from '@mui/material/TableBody';
import TableCell from '@mui/material/TableCell';
import TableHead from '@mui/material/TableHead';
import TableRow from '@mui/material/TableRow';
import Typography from '@mui/material/Typography';
import Chip from '@mui/material/Chip';
import Tabs from '@mui/material/Tabs';
import Tab from '@mui/material/Tab';
import Alert from '@mui/material/Alert';
import DeleteIcon from '@mui/icons-material/Delete';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import PageTitle from '@/components/layout/PageTitle';
import LoadingSkeleton from '@/components/common/LoadingSkeleton';
import ErrorDisplay from '@/components/common/ErrorDisplay';
import ConfirmDialog from '@/components/common/ConfirmDialog';
import FormSelectField from '@/components/form/FormSelectField';
import FormNumberField from '@/components/form/FormNumberField';
import FormSwitchField from '@/components/form/FormSwitchField';
import FormTextField from '@/components/form/FormTextField';
import FormActions from '@/components/form/FormActions';
import FormRow from '@/components/form/FormRow';
import UnsavedChangesGuard from '@/components/form/UnsavedChangesGuard';
import { useNotification } from '@/hooks/useNotification';
import { useApiError } from '@/hooks/useApiError';
import { useTabUrl } from '@/hooks/useTabUrl';
import * as feedingApi from '@/api/endpoints/feeding-events';
import type { FeedingEvent, RunoffResponse } from '@/api/types';

const applicationMethods = ['fertigation', 'drench', 'foliar', 'top_dress'] as const;

const editSchema = z.object({
  application_method: z.enum(applicationMethods),
  is_supplemental: z.boolean(),
  volume_applied_liters: z.number().gt(0),
  measured_ec_before: z.number().min(0).nullable(),
  measured_ec_after: z.number().min(0).nullable(),
  measured_ph_before: z.number().min(0).max(14).nullable(),
  measured_ph_after: z.number().min(0).max(14).nullable(),
  runoff_ec: z.number().min(0).nullable(),
  runoff_ph: z.number().min(0).max(14).nullable(),
  runoff_volume_liters: z.number().min(0).nullable(),
  notes: z.string().nullable(),
});

type EditFormData = z.infer<typeof editSchema>;

export default function FeedingEventDetailPage() {
  const { key } = useParams<{ key: string }>();
  const { t } = useTranslation();
  const navigate = useNavigate();
  const notification = useNotification();
  const { handleError } = useApiError();

  const [event, setEvent] = useState<FeedingEvent | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [tab, setTab] = useTabUrl(['details', 'edit']);
  const [saving, setSaving] = useState(false);
  const [deleteOpen, setDeleteOpen] = useState(false);
  const [runoffResult, setRunoffResult] = useState<RunoffResponse | null>(null);

  const {
    control,
    handleSubmit,
    reset,
    formState: { isDirty },
  } = useForm<EditFormData>({
    resolver: zodResolver(editSchema),
  });

  const load = useCallback(async () => {
    if (!key) return;
    try {
      setLoading(true);
      setError(null);
      const e = await feedingApi.getFeedingEvent(key);
      setEvent(e);
      reset({
        application_method: e.application_method as (typeof applicationMethods)[number],
        is_supplemental: e.is_supplemental,
        volume_applied_liters: e.volume_applied_liters,
        measured_ec_before: e.measured_ec_before,
        measured_ec_after: e.measured_ec_after,
        measured_ph_before: e.measured_ph_before,
        measured_ph_after: e.measured_ph_after,
        runoff_ec: e.runoff_ec,
        runoff_ph: e.runoff_ph,
        runoff_volume_liters: e.runoff_volume_liters,
        notes: e.notes,
      });
    } catch (err) {
      setError(String(err));
    } finally {
      setLoading(false);
    }
  }, [key, reset]);

  useEffect(() => {
    load();
  }, [load]);

  const onSave = async (data: EditFormData) => {
    if (!key) return;
    try {
      setSaving(true);
      await feedingApi.updateFeedingEvent(key, data);
      notification.success(t('common.save'));
      load();
    } catch (err) {
      handleError(err);
    } finally {
      setSaving(false);
    }
  };

  const onDelete = async () => {
    if (!key) return;
    try {
      await feedingApi.deleteFeedingEvent(key);
      notification.success(t('common.delete'));
      navigate('/duengung/feeding-events');
    } catch (err) {
      handleError(err);
    }
  };

  const onAnalyzeRunoff = async () => {
    if (!key) return;
    try {
      const result = await feedingApi.analyzeRunoff(key);
      setRunoffResult(result);
    } catch (err) {
      handleError(err);
    }
  };

  if (loading) return <LoadingSkeleton variant="form" />;
  if (error || !event) return <ErrorDisplay error={error ?? 'Not found'} />;

  return (
    <Box>
      <UnsavedChangesGuard dirty={isDirty} />
      <Box
        sx={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
        }}
      >
        <PageTitle title={event.timestamp ? new Date(event.timestamp).toLocaleString() : t('entities.feedingEvent')} />
        <Button
          color="error"
          startIcon={<DeleteIcon />}
          onClick={() => setDeleteOpen(true)}
        >
          {t('common.delete')}
        </Button>
      </Box>

      <Tabs value={tab} onChange={(_, v) => setTab(v)} sx={{ mb: 2 }}>
        <Tab label={t('pages.feedingEvents.tabDetails')} />
        <Tab label={t('common.edit')} />
      </Tabs>

      {tab === 0 && (
        <Box>
          <Card sx={{ mb: 2 }}>
            <CardContent>
              <Table size="small">
                <TableBody>
                  <TableRow>
                    <TableCell sx={{ fontWeight: 'bold' }}>
                      {t('pages.feedingEvents.plantKey')}
                    </TableCell>
                    <TableCell>{event.plant_key}</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell sx={{ fontWeight: 'bold' }}>
                      {t('pages.feedingEvents.timestamp')}
                    </TableCell>
                    <TableCell>
                      {event.timestamp
                        ? new Date(event.timestamp).toLocaleString()
                        : '—'}
                    </TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell sx={{ fontWeight: 'bold' }}>
                      {t('pages.feedingEvents.applicationMethod')}
                    </TableCell>
                    <TableCell>
                      {t(
                        `enums.applicationMethod.${event.application_method}`,
                      )}
                    </TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell sx={{ fontWeight: 'bold' }}>
                      {t('pages.feedingEvents.isSupplemental')}
                    </TableCell>
                    <TableCell>
                      {event.is_supplemental ? (
                        <Chip
                          label={t('common.yes')}
                          size="small"
                          color="info"
                        />
                      ) : (
                        t('common.no')
                      )}
                    </TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell sx={{ fontWeight: 'bold' }}>
                      {t('pages.feedingEvents.volumeApplied')}
                    </TableCell>
                    <TableCell>{event.volume_applied_liters} L</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell sx={{ fontWeight: 'bold' }}>
                      {t('pages.feedingEvents.ecBefore')}
                    </TableCell>
                    <TableCell>
                      {event.measured_ec_before != null ? `${event.measured_ec_before} mS/cm` : '\u2014'}
                    </TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell sx={{ fontWeight: 'bold' }}>
                      {t('pages.feedingEvents.ecAfter')}
                    </TableCell>
                    <TableCell>
                      {event.measured_ec_after != null ? `${event.measured_ec_after} mS/cm` : '\u2014'}
                    </TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell sx={{ fontWeight: 'bold' }}>
                      {t('pages.feedingEvents.phBefore')}
                    </TableCell>
                    <TableCell>
                      {event.measured_ph_before ?? '\u2014'}
                    </TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell sx={{ fontWeight: 'bold' }}>
                      {t('pages.feedingEvents.phAfter')}
                    </TableCell>
                    <TableCell>
                      {event.measured_ph_after ?? '\u2014'}
                    </TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell sx={{ fontWeight: 'bold' }}>
                      {t('pages.feedingEvents.runoffEc')}
                    </TableCell>
                    <TableCell>
                      {event.runoff_ec != null ? `${event.runoff_ec} mS/cm` : '\u2014'}
                    </TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell sx={{ fontWeight: 'bold' }}>
                      {t('pages.feedingEvents.runoffPh')}
                    </TableCell>
                    <TableCell>
                      {event.runoff_ph ?? '\u2014'}
                    </TableCell>
                  </TableRow>
                  {event.notes && (
                    <TableRow>
                      <TableCell sx={{ fontWeight: 'bold' }}>
                        {t('pages.feedingEvents.notes')}
                      </TableCell>
                      <TableCell>{event.notes}</TableCell>
                    </TableRow>
                  )}
                </TableBody>
              </Table>
            </CardContent>
          </Card>

          {event.fertilizers_used.length > 0 && (
            <Card sx={{ mb: 2 }}>
              <CardContent>
                <Typography variant="subtitle1" sx={{ mb: 1 }}>
                  {t('pages.feedingEvents.fertilizersUsed')}
                </Typography>
                <Table size="small">
                  <TableHead>
                    <TableRow>
                      <TableCell>
                        {t('pages.feedingEvents.fertilizerKey')}
                      </TableCell>
                      <TableCell align="right">
                        {t('pages.feedingEvents.mlApplied')}
                      </TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {event.fertilizers_used.map((f) => (
                      <TableRow key={f.fertilizer_key}>
                        <TableCell>{f.fertilizer_key}</TableCell>
                        <TableCell align="right">{f.ml_applied} ml</TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </CardContent>
            </Card>
          )}

          <Button variant="outlined" onClick={onAnalyzeRunoff} sx={{ mb: 2 }}>
            {t('pages.feedingEvents.analyzeRunoff')}
          </Button>
          {runoffResult && (
            <Alert
              severity={
                runoffResult.overall_health === 'good' ? 'success' : 'warning'
              }
              sx={{ mb: 2 }}
            >
              {runoffResult.ec_message} | {runoffResult.ph_message} |{' '}
              {runoffResult.volume_message}
            </Alert>
          )}
        </Box>
      )}

      {tab === 1 && (
        <Box sx={{ maxWidth: 900 }}>
          <form onSubmit={handleSubmit(onSave)}>
            <Typography variant="subtitle2" color="text.secondary" sx={{ mb: 1, mt: 1 }}>
              {t('pages.feedingEvents.sectionApplication')}
            </Typography>
            <FormRow>
              <FormSelectField
                name="application_method"
                control={control}
                label={t('pages.feedingEvents.applicationMethod')}
                options={applicationMethods.map((v) => ({
                  value: v,
                  label: t(`enums.applicationMethod.${v}`),
                }))}
              />
              <FormSwitchField
                name="is_supplemental"
                control={control}
                label={t('pages.feedingEvents.isSupplemental')}
              />
            </FormRow>
            <FormNumberField
              name="volume_applied_liters"
              control={control}
              label={t('pages.feedingEvents.volumeApplied')}
              min={0.01}
              suffix="L"
              inputMode="decimal"
              helperText={t('pages.feedingEvents.volumeAppliedHelper')}
            />

            <Typography variant="subtitle2" color="text.secondary" sx={{ mb: 1, mt: 2 }}>
              {t('pages.feedingEvents.sectionMeasurements')}
            </Typography>
            <FormRow>
              <FormNumberField
                name="measured_ec_before"
                control={control}
                label={t('pages.feedingEvents.ecBefore')}
                min={0}
                suffix="mS/cm"
                inputMode="decimal"
                helperText={t('pages.feedingEvents.ecHelper')}
              />
              <FormNumberField
                name="measured_ec_after"
                control={control}
                label={t('pages.feedingEvents.ecAfter')}
                min={0}
                suffix="mS/cm"
                inputMode="decimal"
              />
            </FormRow>
            <FormRow>
              <FormNumberField
                name="measured_ph_before"
                control={control}
                label={t('pages.feedingEvents.phBefore')}
                min={0}
                max={14}
                inputMode="decimal"
                helperText={t('pages.feedingEvents.phHelper')}
              />
              <FormNumberField
                name="measured_ph_after"
                control={control}
                label={t('pages.feedingEvents.phAfter')}
                min={0}
                max={14}
                inputMode="decimal"
              />
            </FormRow>

            <Typography variant="subtitle2" color="text.secondary" sx={{ mb: 1, mt: 2 }}>
              {t('pages.feedingEvents.sectionRunoff')}
            </Typography>
            <FormRow>
              <FormNumberField
                name="runoff_ec"
                control={control}
                label={t('pages.feedingEvents.runoffEc')}
                min={0}
                suffix="mS/cm"
                inputMode="decimal"
                helperText={t('pages.feedingEvents.ecHelper')}
              />
              <FormNumberField
                name="runoff_ph"
                control={control}
                label={t('pages.feedingEvents.runoffPh')}
                min={0}
                max={14}
                inputMode="decimal"
              />
            </FormRow>
            <FormNumberField
              name="runoff_volume_liters"
              control={control}
              label={t('pages.feedingEvents.runoffVolume')}
              min={0}
              suffix="L"
              inputMode="decimal"
            />
            <FormTextField
              name="notes"
              control={control}
              label={t('pages.feedingEvents.notes')}
              multiline
              rows={3}
            />
            <FormActions
              onCancel={() => setTab(0)}
              loading={saving}
              disabled={!isDirty}
            />
          </form>
        </Box>
      )}

      <ConfirmDialog
        open={deleteOpen}
        title={t('common.delete')}
        message={t('common.deleteConfirm', { name: event.key })}
        onConfirm={onDelete}
        onCancel={() => setDeleteOpen(false)}
        destructive
      />
    </Box>
  );
}
