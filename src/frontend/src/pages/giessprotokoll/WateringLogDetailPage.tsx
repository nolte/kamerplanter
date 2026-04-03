import { useEffect, useState, useCallback } from 'react';
import { useParams, useNavigate, Link as RouterLink } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import CardHeader from '@mui/material/CardHeader';
import Divider from '@mui/material/Divider';
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
import Link from '@mui/material/Link';
import Stack from '@mui/material/Stack';
import Tooltip from '@mui/material/Tooltip';
import DeleteIcon from '@mui/icons-material/Delete';
import SpaIcon from '@mui/icons-material/Spa';
import WaterDropIcon from '@mui/icons-material/WaterDrop';
import AnalyticsIcon from '@mui/icons-material/Analytics';
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
import * as wateringLogApi from '@/api/endpoints/watering-logs';
import type { WateringLog, WateringLogUpdate, RunoffResponse } from '@/api/types';

const applicationMethods = ['fertigation', 'drench', 'foliar', 'top_dress'] as const;
const waterSources = ['tank', 'tap', 'osmose', 'rainwater', 'distilled', 'well'] as const;

const editSchema = z.object({
  application_method: z.enum(applicationMethods),
  is_supplemental: z.boolean(),
  volume_liters: z.number().gt(0),
  ec_before: z.number().min(0).nullable(),
  ec_after: z.number().min(0).nullable(),
  ph_before: z.number().min(0).max(14).nullable(),
  ph_after: z.number().min(0).max(14).nullable(),
  runoff_ec: z.number().min(0).nullable(),
  runoff_ph: z.number().min(0).max(14).nullable(),
  runoff_volume_liters: z.number().min(0).nullable(),
  water_source: z.string().nullable(),
  performed_by: z.string().nullable(),
  notes: z.string().nullable(),
});

type EditFormData = z.infer<typeof editSchema>;

export default function WateringLogDetailPage() {
  const { key } = useParams<{ key: string }>();
  const { t } = useTranslation();
  const navigate = useNavigate();
  const notification = useNotification();
  const { handleError } = useApiError();

  const [log, setLog] = useState<WateringLog | null>(null);
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
      const e = await wateringLogApi.getWateringLog(key);
      setLog(e);
      reset({
        application_method: e.application_method as (typeof applicationMethods)[number],
        is_supplemental: e.is_supplemental,
        volume_liters: e.volume_liters,
        ec_before: e.ec_before,
        ec_after: e.ec_after,
        ph_before: e.ph_before,
        ph_after: e.ph_after,
        runoff_ec: e.runoff_ec,
        runoff_ph: e.runoff_ph,
        runoff_volume_liters: e.runoff_volume_liters,
        water_source: e.water_source,
        performed_by: e.performed_by,
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
      await wateringLogApi.updateWateringLog(key, data as WateringLogUpdate);
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
      await wateringLogApi.deleteWateringLog(key);
      notification.success(t('common.delete'));
      navigate('/giessprotokoll');
    } catch (err) {
      handleError(err);
    }
  };

  const onAnalyzeRunoff = async () => {
    if (!key) return;
    try {
      const result = await wateringLogApi.analyzeRunoff(key);
      setRunoffResult(result);
    } catch (err) {
      handleError(err);
    }
  };

  if (loading) return <LoadingSkeleton variant="form" />;
  if (error || !log) return <ErrorDisplay error={error ?? 'Not found'} onRetry={load} />;

  const plants = log.resolved_plants ?? [];
  const loggedAtFormatted = log.logged_at
    ? new Date(log.logged_at).toLocaleString()
    : '\u2014';

  return (
    <Box data-testid="watering-log-detail-page">
      <UnsavedChangesGuard dirty={isDirty} />
      <PageTitle
        title={`${t('pages.wateringLogs.detail')} — ${loggedAtFormatted}`}
        action={
          <Tooltip title={t('common.delete')}>
            <Button
              color="error"
              variant="outlined"
              startIcon={<DeleteIcon />}
              onClick={() => setDeleteOpen(true)}
              data-testid="delete-watering-log-button"
              size="small"
            >
              {t('common.delete')}
            </Button>
          </Tooltip>
        }
      />

      <Tabs value={tab} onChange={(_, v) => setTab(v)} sx={{ mb: 2 }} aria-label={t('pages.wateringLogs.title')}>
        <Tab label={t('pages.wateringLogs.tabDetails')} data-testid="details-tab" id="tab-details" aria-controls="tabpanel-details" />
        <Tab label={t('common.edit')} data-testid="edit-tab" id="tab-edit" aria-controls="tabpanel-edit" />
      </Tabs>

      {tab === 0 && (
        <Box role="tabpanel" id="tabpanel-details" aria-labelledby="tab-details">
          {/* Plants & Slots */}
          <Card sx={{ mb: 2 }} variant="outlined">
            <CardHeader
              avatar={<WaterDropIcon color="primary" />}
              title={
                <Typography variant="subtitle1" fontWeight={600}>
                  {loggedAtFormatted}
                </Typography>
              }
              subheader={
                <Stack direction="row" spacing={1} flexWrap="wrap" useFlexGap sx={{ mt: 0.5 }}>
                  <Chip
                    label={t(`enums.applicationMethod.${log.application_method}`)}
                    size="small"
                    color="primary"
                    variant="outlined"
                  />
                  <Chip
                    label={`${log.volume_liters} L`}
                    size="small"
                    variant="outlined"
                  />
                  {log.water_source && (
                    <Chip
                      label={t(`enums.waterSource.${log.water_source}`)}
                      size="small"
                      variant="outlined"
                    />
                  )}
                  {log.is_supplemental && (
                    <Chip
                      label={t('pages.wateringLogs.isSupplemental')}
                      size="small"
                      color="info"
                      variant="outlined"
                    />
                  )}
                </Stack>
              }
              sx={{ pb: 0 }}
            />
            <CardContent>
              {plants.length > 0 ? (
                <>
                  <Typography variant="body2" color="text.secondary" sx={{ mb: 0.75 }}>
                    {t('pages.wateringLogs.plants')}
                  </Typography>
                  <Box sx={{ display: 'flex', gap: 0.5, flexWrap: 'wrap' }}>
                    {plants.map((p) => (
                      <Chip
                        key={p.key}
                        icon={<SpaIcon />}
                        label={p.name}
                        size="small"
                        component={RouterLink}
                        to={`/pflanzen/plant-instances/${p.key}`}
                        clickable
                        color="success"
                        variant="outlined"
                      />
                    ))}
                  </Box>
                </>
              ) : (
                <Typography variant="body2" color="text.secondary" sx={{ fontStyle: 'italic' }}>
                  {t('pages.wateringLogs.noPlantsLinked')}
                </Typography>
              )}

              {(log.slot_keys ?? []).length > 0 && (
                <>
                  <Typography variant="body2" color="text.secondary" sx={{ mt: 1.5, mb: 0.75 }}>
                    {t('pages.wateringLogs.slotKeys')}
                  </Typography>
                  <Box sx={{ display: 'flex', gap: 0.5, flexWrap: 'wrap' }}>
                    {log.slot_keys.map((sk) => (
                      <Chip key={sk} label={sk} size="small" variant="outlined" />
                    ))}
                  </Box>
                </>
              )}
            </CardContent>
          </Card>

          {/* Measurements */}
          <Card sx={{ mb: 2 }} variant="outlined">
            <CardContent>
              <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                {t('pages.wateringLogs.sectionMeasurements')}
              </Typography>
              <Table size="small">
                <TableBody>
                  <TableRow>
                    <TableCell sx={{ color: 'text.secondary', width: '50%' }}>
                      {t('pages.wateringLogs.ecBefore')} / {t('pages.wateringLogs.ecAfter')}
                    </TableCell>
                    <TableCell sx={{ fontFamily: 'monospace' }}>
                      {log.ec_before ?? '\u2014'} / {log.ec_after ?? '\u2014'}
                      {(log.ec_before != null || log.ec_after != null) && (
                        <Typography component="span" variant="body2" color="text.secondary"> mS/cm</Typography>
                      )}
                    </TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell sx={{ color: 'text.secondary' }}>
                      {t('pages.wateringLogs.phBefore')} / {t('pages.wateringLogs.phAfter')}
                    </TableCell>
                    <TableCell sx={{ fontFamily: 'monospace' }}>
                      {log.ph_before ?? '\u2014'} / {log.ph_after ?? '\u2014'}
                    </TableCell>
                  </TableRow>
                </TableBody>
              </Table>

              {(log.runoff_ec != null || log.runoff_ph != null || log.runoff_volume_liters != null) && (
                <>
                  <Divider sx={{ my: 1.5 }} />
                  <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                    {t('pages.wateringLogs.sectionRunoff')}
                  </Typography>
                  <Table size="small">
                    <TableBody>
                      <TableRow>
                        <TableCell sx={{ color: 'text.secondary', width: '50%' }}>
                          {t('pages.wateringLogs.runoffEc')} / {t('pages.wateringLogs.runoffPh')}
                        </TableCell>
                        <TableCell sx={{ fontFamily: 'monospace' }}>
                          {log.runoff_ec ?? '\u2014'} / {log.runoff_ph ?? '\u2014'}
                          {log.runoff_ec != null && (
                            <Typography component="span" variant="body2" color="text.secondary"> mS/cm</Typography>
                          )}
                        </TableCell>
                      </TableRow>
                      {log.runoff_volume_liters != null && (
                        <TableRow>
                          <TableCell sx={{ color: 'text.secondary' }}>
                            {t('pages.wateringLogs.runoffVolume')}
                          </TableCell>
                          <TableCell>{log.runoff_volume_liters} L</TableCell>
                        </TableRow>
                      )}
                    </TableBody>
                  </Table>
                </>
              )}
            </CardContent>
          </Card>

          {/* Fertilizers used */}
          {log.fertilizers_used.length > 0 && (
            <Card sx={{ mb: 2 }} variant="outlined">
              <CardContent>
                <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                  {t('pages.wateringLogs.fertilizersUsed')}
                </Typography>
                <Table size="small">
                  <TableHead>
                    <TableRow>
                      <TableCell>{t('pages.wateringLogs.fertilizerKey')}</TableCell>
                      <TableCell align="right">{t('pages.wateringLogs.mlPerLiter')}</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {(log.resolved_fertilizers ?? []).map((rf, i) => (
                      <TableRow key={i}>
                        <TableCell>{rf.name}</TableCell>
                        <TableCell align="right" sx={{ fontFamily: 'monospace' }}>{rf.ml_per_liter} ml/L</TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </CardContent>
            </Card>
          )}

          {/* Meta info */}
          {(log.performed_by || log.channel_id || log.nutrient_plan_key || log.notes) && (
            <Card sx={{ mb: 2 }} variant="outlined">
              <CardContent>
                <Table size="small">
                  <TableBody>
                    {log.performed_by && (
                      <TableRow>
                        <TableCell sx={{ color: 'text.secondary', width: '40%' }}>
                          {t('pages.wateringLogs.performedBy')}
                        </TableCell>
                        <TableCell>{log.performed_by}</TableCell>
                      </TableRow>
                    )}
                    {log.channel_id && (
                      <TableRow>
                        <TableCell sx={{ color: 'text.secondary' }}>
                          {t('pages.wateringLogs.channelId')}
                        </TableCell>
                        <TableCell>{log.channel_id}</TableCell>
                      </TableRow>
                    )}
                    {log.nutrient_plan_key && (
                      <TableRow>
                        <TableCell sx={{ color: 'text.secondary' }}>
                          {t('pages.wateringLogs.nutrientPlan')}
                        </TableCell>
                        <TableCell>
                          <Link component={RouterLink} to={`/duengung/plans/${log.nutrient_plan_key}`} underline="hover">
                            {log.nutrient_plan_key}
                          </Link>
                        </TableCell>
                      </TableRow>
                    )}
                    {log.notes && (
                      <TableRow>
                        <TableCell sx={{ color: 'text.secondary' }}>
                          {t('pages.wateringLogs.notes')}
                        </TableCell>
                        <TableCell sx={{ whiteSpace: 'pre-wrap' }}>{log.notes}</TableCell>
                      </TableRow>
                    )}
                  </TableBody>
                </Table>
              </CardContent>
            </Card>
          )}

          {/* Runoff analysis */}
          <Button
            variant="outlined"
            startIcon={<AnalyticsIcon />}
            onClick={onAnalyzeRunoff}
            sx={{ mb: 2 }}
            data-testid="analyze-runoff-button"
          >
            {t('pages.wateringLogs.analyzeRunoff')}
          </Button>
          {runoffResult && (
            <Alert
              severity={runoffResult.overall_health === 'good' ? 'success' : 'warning'}
              sx={{ mb: 2 }}
              data-testid="runoff-analysis-result"
            >
              <Stack spacing={0.5}>
                {runoffResult.ec_message && <Typography variant="body2">{runoffResult.ec_message}</Typography>}
                {runoffResult.ph_message && <Typography variant="body2">{runoffResult.ph_message}</Typography>}
                {runoffResult.volume_message && <Typography variant="body2">{runoffResult.volume_message}</Typography>}
              </Stack>
            </Alert>
          )}
        </Box>
      )}

      {tab === 1 && (
        <Box
          sx={{ maxWidth: 600 }}
          role="tabpanel"
          id="tabpanel-edit"
          aria-labelledby="tab-edit"
        >
          <form onSubmit={handleSubmit(onSave)}>
            <Typography variant="subtitle2" color="text.secondary" sx={{ mb: 1, mt: 1 }}>
              {t('pages.wateringLogs.sectionApplication')}
            </Typography>
            <FormRow>
              <FormSelectField
                name="application_method"
                control={control}
                label={t('pages.wateringLogs.applicationMethod')}
                options={applicationMethods.map((v) => ({
                  value: v,
                  label: t(`enums.applicationMethod.${v}`),
                }))}
                autoFocus
              />
              <FormSwitchField
                name="is_supplemental"
                control={control}
                label={t('pages.wateringLogs.isSupplemental')}
              />
            </FormRow>
            <FormRow>
              <FormNumberField
                name="volume_liters"
                control={control}
                label={t('pages.wateringLogs.volumeLiters')}
                min={0.01}
                suffix="L"
                helperText={t('pages.wateringLogs.volumeLitersHelper')}
                inputMode="decimal"
              />
              <FormSelectField
                name="water_source"
                control={control}
                label={t('pages.wateringLogs.waterSource')}
                options={waterSources.map((v) => ({
                  value: v,
                  label: t(`enums.waterSource.${v}`),
                }))}
              />
            </FormRow>

            <Divider sx={{ my: 1.5 }} />
            <Typography variant="subtitle2" color="text.secondary" sx={{ mb: 1 }}>
              {t('pages.wateringLogs.sectionMeasurements')}
            </Typography>
            <FormRow>
              <FormNumberField
                name="ec_before"
                control={control}
                label={t('pages.wateringLogs.ecBefore')}
                min={0}
                suffix="mS/cm"
                helperText={t('pages.wateringLogs.ecHelper')}
                inputMode="decimal"
              />
              <FormNumberField
                name="ec_after"
                control={control}
                label={t('pages.wateringLogs.ecAfter')}
                min={0}
                suffix="mS/cm"
                inputMode="decimal"
              />
            </FormRow>
            <FormRow>
              <FormNumberField
                name="ph_before"
                control={control}
                label={t('pages.wateringLogs.phBefore')}
                min={0}
                max={14}
                helperText={t('pages.wateringLogs.phHelper')}
                inputMode="decimal"
              />
              <FormNumberField
                name="ph_after"
                control={control}
                label={t('pages.wateringLogs.phAfter')}
                min={0}
                max={14}
                inputMode="decimal"
              />
            </FormRow>

            <Divider sx={{ my: 1.5 }} />
            <Typography variant="subtitle2" color="text.secondary" sx={{ mb: 1 }}>
              {t('pages.wateringLogs.sectionRunoff')}
            </Typography>
            <FormRow>
              <FormNumberField
                name="runoff_ec"
                control={control}
                label={t('pages.wateringLogs.runoffEc')}
                min={0}
                suffix="mS/cm"
                helperText={t('pages.wateringLogs.runoffEcHelper')}
                inputMode="decimal"
              />
              <FormNumberField
                name="runoff_ph"
                control={control}
                label={t('pages.wateringLogs.runoffPh')}
                min={0}
                max={14}
                inputMode="decimal"
              />
            </FormRow>
            <FormNumberField
              name="runoff_volume_liters"
              control={control}
              label={t('pages.wateringLogs.runoffVolume')}
              min={0}
              suffix="L"
              inputMode="decimal"
            />

            <Divider sx={{ my: 1.5 }} />
            <FormTextField
              name="performed_by"
              control={control}
              label={t('pages.wateringLogs.performedBy')}
            />
            <FormTextField
              name="notes"
              control={control}
              label={t('pages.wateringLogs.notes')}
              multiline
              minRows={3}
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
        message={t('common.deleteConfirm', { name: log.key })}
        onConfirm={onDelete}
        onCancel={() => setDeleteOpen(false)}
        destructive
      />
    </Box>
  );
}
