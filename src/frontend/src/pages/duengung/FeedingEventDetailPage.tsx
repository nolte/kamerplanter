import { useEffect, useState, useCallback, useMemo } from 'react';
import { useParams, useNavigate, Link as RouterLink } from 'react-router-dom';
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
import Skeleton from '@mui/material/Skeleton';
import Stack from '@mui/material/Stack';
import DeleteIcon from '@mui/icons-material/Delete';
import SpaIcon from '@mui/icons-material/Spa';

const PANEL_GAP = 4;
import { useForm, useWatch } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import PageTitle from '@/components/layout/PageTitle';
import LoadingSkeleton from '@/components/common/LoadingSkeleton';
import ErrorDisplay from '@/components/common/ErrorDisplay';
import ConfirmDialog from '@/components/common/ConfirmDialog';
import Form from '@/components/form/Form';
import FormSelectField from '@/components/form/FormSelectField';
import FormNumberField from '@/components/form/FormNumberField';
import FormSwitchField from '@/components/form/FormSwitchField';
import FormTextField from '@/components/form/FormTextField';
import FormActions from '@/components/form/FormActions';
import FormRow from '@/components/form/FormRow';
import UnsavedChangesGuard from '@/components/form/UnsavedChangesGuard';
import { useNotification } from '@/hooks/useNotification';
import { useTenantPermissions } from '@/hooks/useTenantPermissions';
import { useApiError } from '@/hooks/useApiError';
import { useTabUrl } from '@/hooks/useTabUrl';
import { usePlantLabels } from '@/hooks/usePlantLabels';
import * as feedingApi from '@/api/endpoints/feeding-events';
import * as fertilizerApi from '@/api/endpoints/fertilizers';
import type { FeedingEvent, RunoffResponse } from '@/api/types';
import {
  feedingPlantKeys,
  formatFeedingDose,
  isTopDress,
  materialLabel,
  showsLiquidFields,
} from './feedingEventDose';

const applicationMethods = ['fertigation', 'drench', 'foliar', 'top_dress'] as const;

const editSchema = z.object({
  application_method: z.enum(applicationMethods),
  is_supplemental: z.boolean(),
  // Optional for a top dress (compost, a dry fertiliser has no volume, #2903); required for a solution below.
  volume_applied_liters: z.number().gt(0).nullable(),
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

/**
 * A solution is a volume; a top dress may be saved without one, and so may a dose logged in the care log or by a
 * bed task (`loggedDose`: millilitres of a concentrate, whose water is unknown, carry no volume either).
 * UI-only rule: the server (`FeedingEventUpdate`) does not enforce it - an update without a volume keeps the old one.
 */
function volumeRequired(method: string | undefined, loggedDose: boolean): boolean {
  return method !== 'top_dress' && !loggedDose;
}

function buildEditResolver(requiredMessage: string, loggedDose: boolean) {
  return zodResolver(
    editSchema.superRefine((data, ctx) => {
      if (volumeRequired(data.application_method, loggedDose) && data.volume_applied_liters == null) {
        ctx.addIssue({ code: 'custom', path: ['volume_applied_liters'], message: requiredMessage });
      }
    }),
  );
}

export default function FeedingEventDetailPage() {
  const { key } = useParams<{ key: string }>();
  const { t } = useTranslation();
  const navigate = useNavigate();
  const notification = useNotification();
  const { handleError } = useApiError();
  // `require_permission("feeding-event", DELETE)` is lead-only (REQ-049 §2.3) (#1467).
  const { canDelete } = useTenantPermissions();

  const [event, setEvent] = useState<FeedingEvent | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [tab, setTab] = useTabUrl(['details', 'edit']);
  const [saving, setSaving] = useState(false);
  const [deleteOpen, setDeleteOpen] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [runoffResult, setRunoffResult] = useState<RunoffResponse | null>(null);
  const [productName, setProductName] = useState<string | null>(null);

  const loggedDose = event?.dose_quantity != null;
  const resolver = useMemo(() => buildEditResolver(t('validation.required'), loggedDose), [t, loggedDose]);
  const {
    control,
    handleSubmit,
    reset,
    formState: { isDirty },
  } = useForm<EditFormData>({ resolver });
  const editedMethod = useWatch({ control, name: 'application_method' });

  const plantKeys = useMemo(() => (event ? feedingPlantKeys(event) : []), [event]);
  const plantLabels = usePlantLabels(plantKeys);

  // The catalogue product a care-log dose names: its name, best effort (the key if it cannot be loaded).
  const productKey = event?.product_label ? null : (event?.product_key ?? null);
  useEffect(() => {
    if (!productKey) return;
    let cancelled = false;
    fertilizerApi
      .fetchFertilizer(productKey)
      .then((fertilizer) => {
        if (!cancelled) setProductName(fertilizer.product_name);
      })
      .catch(() => {
        if (!cancelled) setProductName(productKey);
      });
    return () => {
      cancelled = true;
    };
  }, [productKey]);

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
        // A top dress is answered as `0` L; in the form that is "no volume".
        volume_applied_liters: e.volume_applied_liters > 0 ? e.volume_applied_liters : null,
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
    setDeleting(true);
    try {
      await feedingApi.deleteFeedingEvent(key);
      notification.success(t('common.delete'));
      navigate('/duengung/feeding-events');
    } catch (err) {
      handleError(err);
    } finally {
      setDeleting(false);
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

  const topDress = isTopDress(event);
  const liquid = showsLiquidFields(event);
  const dose = formatFeedingDose(t, event);
  const material = materialLabel(t, event.material);
  const product = event.product_label || (event.product_key ? (productName ?? event.product_key) : '');
  // In the edit tab the method can change; a top dress without measurements keeps those sections hidden.
  const editLiquid = editedMethod !== 'top_dress' || liquid;

  return (
    <Box data-testid="feeding-event-detail-page">
      <UnsavedChangesGuard dirty={isDirty} />
      <PageTitle
        title={event.timestamp ? new Date(event.timestamp).toLocaleString() : t('entities.feedingEvent')}
        action={
          canDelete ? (
            <Button
              color="error"
              startIcon={<DeleteIcon />}
              onClick={() => setDeleteOpen(true)}
              data-testid="feeding-event-delete-button"
            >
              {t('common.delete')}
            </Button>
          ) : undefined
        }
      />

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
                      {plantKeys.length > 1
                        ? t('pages.feedingEvents.plants')
                        : t('pages.feedingEvents.plantKey')}
                    </TableCell>
                    <TableCell data-testid="feeding-event-plants">
                      {plantKeys.length === 0 && '—'}
                      {plantLabels.tooMany &&
                        t('pages.feedingEvents.plantCount', { count: plantKeys.length })}
                      {!plantLabels.tooMany && plantKeys.length > 0 && (
                        <Stack direction="row" spacing={1} useFlexGap sx={{ flexWrap: 'wrap' }}>
                          {plantKeys.map((plantKey) =>
                            plantLabels.loading ? (
                              <Skeleton key={plantKey} variant="rounded" width={120} height={24} />
                            ) : (
                              <Chip
                                key={plantKey}
                                icon={<SpaIcon />}
                                label={plantLabels.labels.get(plantKey) ?? plantKey}
                                size="small"
                                color="success"
                                variant="outlined"
                                component={RouterLink}
                                to={`/pflanzen/plant-instances/${plantKey}`}
                                clickable
                              />
                            ),
                          )}
                        </Stack>
                      )}
                    </TableCell>
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
                  {product && (
                    <TableRow>
                      <TableCell sx={{ fontWeight: 'bold' }}>
                        {t('pages.feedingEvents.product')}
                      </TableCell>
                      <TableCell data-testid="feeding-event-product">{product}</TableCell>
                    </TableRow>
                  )}
                  {material && (
                    <TableRow>
                      <TableCell sx={{ fontWeight: 'bold' }}>
                        {t('pages.feedingEvents.material')}
                      </TableCell>
                      <TableCell data-testid="feeding-event-material">{material}</TableCell>
                    </TableRow>
                  )}
                  {(topDress || dose) && (
                    <TableRow>
                      <TableCell sx={{ fontWeight: 'bold' }}>
                        {t('pages.feedingEvents.amount')}
                      </TableCell>
                      <TableCell data-testid="feeding-event-dose">{dose || '—'}</TableCell>
                    </TableRow>
                  )}
                  {liquid && (
                    <>
                      <TableRow>
                        <TableCell sx={{ fontWeight: 'bold' }}>
                          {t('pages.feedingEvents.volumeApplied')}
                        </TableCell>
                        <TableCell>
                          {event.volume_applied_liters > 0 ? `${event.volume_applied_liters} L` : '—'}
                        </TableCell>
                      </TableRow>
                      <TableRow>
                        <TableCell sx={{ fontWeight: 'bold' }}>
                          {t('pages.feedingEvents.ecBefore')}
                        </TableCell>
                        <TableCell>
                          {event.measured_ec_before != null ? `${event.measured_ec_before} mS/cm` : '—'}
                        </TableCell>
                      </TableRow>
                      <TableRow>
                        <TableCell sx={{ fontWeight: 'bold' }}>
                          {t('pages.feedingEvents.ecAfter')}
                        </TableCell>
                        <TableCell>
                          {event.measured_ec_after != null ? `${event.measured_ec_after} mS/cm` : '—'}
                        </TableCell>
                      </TableRow>
                      <TableRow>
                        <TableCell sx={{ fontWeight: 'bold' }}>
                          {t('pages.feedingEvents.phBefore')}
                        </TableCell>
                        <TableCell>
                          {event.measured_ph_before ?? '—'}
                        </TableCell>
                      </TableRow>
                      <TableRow>
                        <TableCell sx={{ fontWeight: 'bold' }}>
                          {t('pages.feedingEvents.phAfter')}
                        </TableCell>
                        <TableCell>
                          {event.measured_ph_after ?? '—'}
                        </TableCell>
                      </TableRow>
                      <TableRow>
                        <TableCell sx={{ fontWeight: 'bold' }}>
                          {t('pages.feedingEvents.runoffEc')}
                        </TableCell>
                        <TableCell>
                          {event.runoff_ec != null ? `${event.runoff_ec} mS/cm` : '—'}
                        </TableCell>
                      </TableRow>
                      <TableRow>
                        <TableCell sx={{ fontWeight: 'bold' }}>
                          {t('pages.feedingEvents.runoffPh')}
                        </TableCell>
                        <TableCell>
                          {event.runoff_ph ?? '—'}
                        </TableCell>
                      </TableRow>
                    </>
                  )}
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

          {liquid && (
            <Button variant="outlined" onClick={onAnalyzeRunoff} sx={{ mb: 2 }}>
              {t('pages.feedingEvents.analyzeRunoff')}
            </Button>
          )}
          {liquid && runoffResult && (
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
        <Form onSubmit={handleSubmit(onSave)} sx={{ maxWidth: 1280, display: 'flex', flexDirection: 'column', gap: PANEL_GAP }}>
          <Typography variant="body2" color="text.secondary">
            {t('pages.feedingEvents.editIntro')}
          </Typography>

          {/* Section: Application */}
          <Card variant="outlined">
            <CardContent component="fieldset" sx={{ border: 'none', p: 0, m: 0, '&:last-child': { pb: 2 }, px: 2, pt: 2 }}>
              <Typography component="legend" variant="h6" sx={{ pt: 1.5, mb: 0.5 }}>
                {t('pages.feedingEvents.sectionApplication')}
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                {t('pages.feedingEvents.sectionApplicationDesc')}
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
                  autoFocus
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
                required={volumeRequired(editedMethod, loggedDose)}
                helperText={
                  !volumeRequired(editedMethod, loggedDose)
                    ? t('pages.feedingEvents.volumeOptional')
                    : t('pages.feedingEvents.volumeAppliedHelper')
                }
              />
            </CardContent>
          </Card>

          {editLiquid && (
            <>
              {/* Section: Measurements */}
              <Card variant="outlined">
                <CardContent component="fieldset" sx={{ border: 'none', p: 0, m: 0, '&:last-child': { pb: 2 }, px: 2, pt: 2 }}>
                  <Typography component="legend" variant="h6" sx={{ pt: 1.5, mb: 0.5 }}>
                    {t('pages.feedingEvents.sectionMeasurements')}
                  </Typography>
                  <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                    {t('pages.feedingEvents.sectionMeasurementsDesc')}
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
                </CardContent>
              </Card>

              {/* Section: Runoff */}
              <Card variant="outlined">
                <CardContent component="fieldset" sx={{ border: 'none', p: 0, m: 0, '&:last-child': { pb: 2 }, px: 2, pt: 2 }}>
                  <Typography component="legend" variant="h6" sx={{ pt: 1.5, mb: 0.5 }}>
                    {t('pages.feedingEvents.sectionRunoff')}
                  </Typography>
                  <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                    {t('pages.feedingEvents.sectionRunoffDesc')}
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
                </CardContent>
              </Card>
            </>
          )}

          {/* Notes */}
          <Card variant="outlined">
            <CardContent component="fieldset" sx={{ border: 'none', p: 0, m: 0, '&:last-child': { pb: 2 }, px: 2, pt: 2 }}>
              <Typography component="legend" variant="h6" sx={{ pt: 1.5, mb: 0.5 }}>
                {t('pages.feedingEvents.notes')}
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                {t('pages.feedingEvents.sectionNotesDesc')}
              </Typography>
              <FormTextField
                name="notes"
                control={control}
                label={t('pages.feedingEvents.notes')}
                multiline
                rows={3}
              />
            </CardContent>
          </Card>

          <Typography variant="caption" color="text.secondary">* {t('common.required')}</Typography>
          <FormActions
            onCancel={() => setTab(0)}
            loading={saving}
            disabled={!isDirty}
          />
        </Form>
      )}

      <ConfirmDialog
        open={deleteOpen}
        title={t('common.delete')}
        message={t('common.deleteConfirm', { name: event.key })}
        onConfirm={onDelete}
        onCancel={() => setDeleteOpen(false)}
        destructive
        loading={deleting}
      />
    </Box>
  );
}
