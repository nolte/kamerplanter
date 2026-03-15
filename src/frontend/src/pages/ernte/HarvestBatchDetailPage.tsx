import { useEffect, useState, useCallback } from 'react';
import { useTabUrl } from '@/hooks/useTabUrl';
import { useParams } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import Chip from '@mui/material/Chip';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import Table from '@mui/material/Table';
import TableBody from '@mui/material/TableBody';
import TableCell from '@mui/material/TableCell';
import TableRow from '@mui/material/TableRow';
import Tabs from '@mui/material/Tabs';
import Tab from '@mui/material/Tab';
import LinearProgress from '@mui/material/LinearProgress';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import PageTitle from '@/components/layout/PageTitle';
import LoadingSkeleton from '@/components/common/LoadingSkeleton';
import ErrorDisplay from '@/components/common/ErrorDisplay';
import UnsavedChangesGuard from '@/components/form/UnsavedChangesGuard';
import FormTextField from '@/components/form/FormTextField';
import FormSelectField from '@/components/form/FormSelectField';
import FormNumberField from '@/components/form/FormNumberField';
import FormActions from '@/components/form/FormActions';
import FormRow from '@/components/form/FormRow';
import FormChipInput from '@/components/form/FormChipInput';
import { useNotification } from '@/hooks/useNotification';
import { useApiError } from '@/hooks/useApiError';
import * as harvestApi from '@/api/endpoints/harvest';
import type {
  HarvestBatch,
  QualityAssessment,
  YieldMetric,
} from '@/api/types';

const harvestTypes = ['partial', 'final', 'continuous'] as const;
const qualityGrades = ['a_plus', 'a', 'b', 'c', 'd'] as const;

const editSchema = z.object({
  harvest_type: z.enum(harvestTypes),
  wet_weight_g: z.number().min(0).nullable(),
  estimated_dry_weight_g: z.number().min(0).nullable(),
  actual_dry_weight_g: z.number().min(0).nullable(),
  quality_grade: z.string().nullable(),
  harvester: z.string().max(200),
  notes: z.string().nullable(),
});

type EditFormData = z.infer<typeof editSchema>;

const qualitySchema = z.object({
  assessed_by: z.string().min(1).max(200),
  appearance_score: z.number().min(0).max(100),
  aroma_score: z.number().min(0).max(100),
  color_score: z.number().min(0).max(100),
  defects: z.array(z.string()),
  notes: z.string().nullable(),
});

type QualityFormData = z.infer<typeof qualitySchema>;

const yieldSchema = z.object({
  yield_per_plant_g: z.number().min(0),
  yield_per_m2_g: z.number().min(0),
  total_yield_g: z.number().min(0),
  trim_waste_percent: z.number().min(0).max(100),
  usable_yield_g: z.number().min(0),
});

type YieldFormData = z.infer<typeof yieldSchema>;

export default function HarvestBatchDetailPage() {
  const { key } = useParams<{ key: string }>();
  const { t } = useTranslation();
  const notification = useNotification();
  const { handleError } = useApiError();

  const [batch, setBatch] = useState<HarvestBatch | null>(null);
  const [quality, setQuality] = useState<QualityAssessment | null>(null);
  const [yieldMetric, setYieldMetric] = useState<YieldMetric | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [tab, setTab] = useTabUrl(['details', 'quality', 'yield', 'edit']);
  const [saving, setSaving] = useState(false);
  const [savingQuality, setSavingQuality] = useState(false);
  const [savingYield, setSavingYield] = useState(false);

  const {
    control: editControl,
    handleSubmit: handleEditSubmit,
    reset: resetEdit,
    formState: { isDirty },
  } = useForm<EditFormData>({
    resolver: zodResolver(editSchema),
    defaultValues: {
      harvest_type: 'final',
      wet_weight_g: null,
      estimated_dry_weight_g: null,
      actual_dry_weight_g: null,
      quality_grade: null,
      harvester: '',
      notes: null,
    },
  });

  const {
    control: qualityControl,
    handleSubmit: handleQualitySubmit,
    reset: resetQuality,
  } = useForm<QualityFormData>({
    resolver: zodResolver(qualitySchema),
    defaultValues: {
      assessed_by: '',
      appearance_score: 0,
      aroma_score: 0,
      color_score: 0,
      defects: [],
      notes: null,
    },
  });

  const {
    control: yieldControl,
    handleSubmit: handleYieldSubmit,
    reset: resetYield,
  } = useForm<YieldFormData>({
    resolver: zodResolver(yieldSchema),
    defaultValues: {
      yield_per_plant_g: 0,
      yield_per_m2_g: 0,
      total_yield_g: 0,
      trim_waste_percent: 0,
      usable_yield_g: 0,
    },
  });

  const load = useCallback(async () => {
    if (!key) return;
    setLoading(true);
    try {
      const b = await harvestApi.getBatch(key);
      setBatch(b);
      resetEdit({
        harvest_type: b.harvest_type,
        wet_weight_g: b.wet_weight_g,
        estimated_dry_weight_g: b.estimated_dry_weight_g,
        actual_dry_weight_g: b.actual_dry_weight_g,
        quality_grade: b.quality_grade,
        harvester: b.harvester,
        notes: b.notes,
      });

      const [q, y] = await Promise.all([
        harvestApi.getQuality(key),
        harvestApi.getYield(key),
      ]);
      setQuality(q);
      setYieldMetric(y);
      setError(null);
    } catch (err) {
      setError(String(err));
    } finally {
      setLoading(false);
    }
  }, [key, resetEdit]);

  useEffect(() => {
    load();
  }, [load]);

  const onSave = async (data: EditFormData) => {
    if (!key) return;
    try {
      setSaving(true);
      await harvestApi.updateBatch(key, {
        harvest_type: data.harvest_type,
        wet_weight_g: data.wet_weight_g,
        estimated_dry_weight_g: data.estimated_dry_weight_g,
        actual_dry_weight_g: data.actual_dry_weight_g,
        quality_grade: (data.quality_grade as QualityAssessment['grade']) || undefined,
        harvester: data.harvester || undefined,
        notes: data.notes,
      });
      notification.success(t('common.save'));
      load();
    } catch (err) {
      handleError(err);
    } finally {
      setSaving(false);
    }
  };

  const onSaveQuality = async (data: QualityFormData) => {
    if (!key) return;
    try {
      setSavingQuality(true);
      const created = await harvestApi.createQualityAssessment(key, {
        assessed_by: data.assessed_by,
        appearance_score: data.appearance_score,
        aroma_score: data.aroma_score,
        color_score: data.color_score,
        defects: data.defects,
        notes: data.notes,
      });
      setQuality(created);
      notification.success(t('pages.harvest.qualityCreated'));
    } catch (err) {
      handleError(err);
    } finally {
      setSavingQuality(false);
    }
  };

  const onSaveYield = async (data: YieldFormData) => {
    if (!key) return;
    try {
      setSavingYield(true);
      const created = await harvestApi.createYieldMetric(key, data);
      setYieldMetric(created);
      notification.success(t('pages.harvest.yieldCreated'));
    } catch (err) {
      handleError(err);
    } finally {
      setSavingYield(false);
    }
  };

  if (loading) return <LoadingSkeleton variant="form" />;
  if (error) return <ErrorDisplay error={error} />;
  if (!batch) return <ErrorDisplay error={t('errors.notFound')} />;

  return (
    <Box data-testid="harvest-batch-detail-page">
      <UnsavedChangesGuard dirty={isDirty} />
      <Box
        sx={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          mb: 2,
        }}
      >
        <PageTitle
          title={batch.batch_id || t('pages.harvest.batchFallbackTitle')}
        />
        {batch.quality_grade && (
          <Chip
            label={t(`enums.qualityGrade.${batch.quality_grade}`)}
            color="primary"
          />
        )}
      </Box>

      <Tabs value={tab} onChange={(_, v) => setTab(v)} sx={{ mb: 2 }}>
        <Tab label={t('pages.harvest.tabDetails')} />
        <Tab label={t('pages.harvest.tabQuality')} />
        <Tab label={t('pages.harvest.tabYield')} />
        <Tab label={t('common.edit')} />
      </Tabs>

      {/* Tab 0: Details */}
      {tab === 0 && (
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              {t('pages.harvest.tabDetails')}
            </Typography>
            <Table size="small" aria-label={t('pages.harvest.tabDetails')}>
              <TableBody>
                <TableRow>
                  <TableCell component="th">
                    {t('pages.harvest.batchId')}
                  </TableCell>
                  <TableCell>{batch.batch_id || '\u2014'}</TableCell>
                </TableRow>
                <TableRow>
                  <TableCell component="th">
                    {t('pages.harvest.plantKey')}
                  </TableCell>
                  <TableCell>{batch.plant_key}</TableCell>
                </TableRow>
                <TableRow>
                  <TableCell component="th">
                    {t('pages.harvest.harvestDate')}
                  </TableCell>
                  <TableCell>
                    {batch.harvest_date
                      ? new Date(batch.harvest_date).toLocaleDateString()
                      : '\u2014'}
                  </TableCell>
                </TableRow>
                <TableRow>
                  <TableCell component="th">
                    {t('pages.harvest.harvestType')}
                  </TableCell>
                  <TableCell>
                    {t(`enums.harvestType.${batch.harvest_type}`)}
                  </TableCell>
                </TableRow>
                <TableRow>
                  <TableCell component="th">
                    {t('pages.harvest.wetWeightG')}
                  </TableCell>
                  <TableCell>
                    {batch.wet_weight_g != null
                      ? `${batch.wet_weight_g} g`
                      : '\u2014'}
                  </TableCell>
                </TableRow>
                <TableRow>
                  <TableCell component="th">
                    {t('pages.harvest.estimatedDryWeightG')}
                  </TableCell>
                  <TableCell>
                    {batch.estimated_dry_weight_g != null
                      ? `${batch.estimated_dry_weight_g} g`
                      : '\u2014'}
                  </TableCell>
                </TableRow>
                <TableRow>
                  <TableCell component="th">
                    {t('pages.harvest.actualDryWeightG')}
                  </TableCell>
                  <TableCell>
                    {batch.actual_dry_weight_g != null
                      ? `${batch.actual_dry_weight_g} g`
                      : '\u2014'}
                  </TableCell>
                </TableRow>
                <TableRow>
                  <TableCell component="th">
                    {t('pages.harvest.qualityGrade')}
                  </TableCell>
                  <TableCell>
                    {batch.quality_grade ? (
                      <Chip
                        label={t(`enums.qualityGrade.${batch.quality_grade}`)}
                        size="small"
                        color="primary"
                      />
                    ) : '\u2014'}
                  </TableCell>
                </TableRow>
                <TableRow>
                  <TableCell component="th">
                    {t('pages.harvest.harvester')}
                  </TableCell>
                  <TableCell>{batch.harvester || '\u2014'}</TableCell>
                </TableRow>
                {batch.notes && (
                  <TableRow>
                    <TableCell component="th">
                      {t('pages.harvest.notes')}
                    </TableCell>
                    <TableCell>{batch.notes}</TableCell>
                  </TableRow>
                )}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      )}

      {/* Tab 1: Quality */}
      {tab === 1 && (
        <Box>
          {quality ? (
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  {t('pages.harvest.qualityAssessment')}
                </Typography>
                <Table
                  size="small"
                  aria-label={t('pages.harvest.qualityAssessment')}
                >
                  <TableBody>
                    <TableRow>
                      <TableCell component="th">
                        {t('pages.harvest.assessedBy')}
                      </TableCell>
                      <TableCell>{quality.assessed_by}</TableCell>
                    </TableRow>
                    <TableRow>
                      <TableCell component="th">
                        {t('pages.harvest.assessedAt')}
                      </TableCell>
                      <TableCell>
                        {quality.assessed_at
                          ? new Date(quality.assessed_at).toLocaleString()
                          : '\u2014'}
                      </TableCell>
                    </TableRow>
                    <TableRow>
                      <TableCell component="th">
                        {t('pages.harvest.appearanceScore')}
                      </TableCell>
                      <TableCell>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                          <LinearProgress
                            variant="determinate"
                            value={quality.appearance_score}
                            sx={{ flexGrow: 1 }}
                          />
                          <Typography variant="body2">
                            {quality.appearance_score}
                          </Typography>
                        </Box>
                      </TableCell>
                    </TableRow>
                    <TableRow>
                      <TableCell component="th">
                        {t('pages.harvest.aromaScore')}
                      </TableCell>
                      <TableCell>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                          <LinearProgress
                            variant="determinate"
                            value={quality.aroma_score}
                            sx={{ flexGrow: 1 }}
                          />
                          <Typography variant="body2">
                            {quality.aroma_score}
                          </Typography>
                        </Box>
                      </TableCell>
                    </TableRow>
                    <TableRow>
                      <TableCell component="th">
                        {t('pages.harvest.colorScore')}
                      </TableCell>
                      <TableCell>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                          <LinearProgress
                            variant="determinate"
                            value={quality.color_score}
                            sx={{ flexGrow: 1 }}
                          />
                          <Typography variant="body2">
                            {quality.color_score}
                          </Typography>
                        </Box>
                      </TableCell>
                    </TableRow>
                    <TableRow>
                      <TableCell component="th">
                        {t('pages.harvest.overallScore')}
                      </TableCell>
                      <TableCell>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                          <LinearProgress
                            variant="determinate"
                            value={quality.overall_score}
                            sx={{ flexGrow: 1 }}
                            color={
                              quality.overall_score >= 80
                                ? 'success'
                                : quality.overall_score >= 60
                                  ? 'warning'
                                  : 'error'
                            }
                          />
                          <Typography variant="body2">
                            {quality.overall_score}
                          </Typography>
                        </Box>
                      </TableCell>
                    </TableRow>
                    {quality.grade && (
                      <TableRow>
                        <TableCell component="th">
                          {t('pages.harvest.grade')}
                        </TableCell>
                        <TableCell>
                          <Chip
                            label={t(`enums.qualityGrade.${quality.grade}`)}
                            size="small"
                            color="primary"
                          />
                        </TableCell>
                      </TableRow>
                    )}
                    {quality.defects.length > 0 && (
                      <TableRow>
                        <TableCell component="th">
                          {t('pages.harvest.defects')}
                        </TableCell>
                        <TableCell>
                          <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                            {quality.defects.map((d) => (
                              <Chip key={d} label={d} size="small" color="error" />
                            ))}
                          </Box>
                        </TableCell>
                      </TableRow>
                    )}
                    {quality.notes && (
                      <TableRow>
                        <TableCell component="th">
                          {t('pages.harvest.notes')}
                        </TableCell>
                        <TableCell>{quality.notes}</TableCell>
                      </TableRow>
                    )}
                  </TableBody>
                </Table>
              </CardContent>
            </Card>
          ) : (
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  {t('pages.harvest.createQuality')}
                </Typography>
                <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                  {t('pages.harvest.createQualityIntro')}
                </Typography>
                <form onSubmit={handleQualitySubmit(onSaveQuality)}>
                  <FormTextField
                    name="assessed_by"
                    control={qualityControl}
                    label={t('pages.harvest.assessedBy')}
                    required
                  />
                  <FormRow>
                    <FormNumberField
                      name="appearance_score"
                      control={qualityControl}
                      label={t('pages.harvest.appearanceScore')}
                      min={0}
                      max={100}
                      inputMode="numeric"
                      helperText={t('pages.harvest.scoreHelper')}
                    />
                    <FormNumberField
                      name="aroma_score"
                      control={qualityControl}
                      label={t('pages.harvest.aromaScore')}
                      min={0}
                      max={100}
                      inputMode="numeric"
                    />
                  </FormRow>
                  <FormNumberField
                    name="color_score"
                    control={qualityControl}
                    label={t('pages.harvest.colorScore')}
                    min={0}
                    max={100}
                    inputMode="numeric"
                  />
                  <FormChipInput
                    name="defects"
                    control={qualityControl}
                    label={t('pages.harvest.defects')}
                    helperText={t('pages.harvest.defectsHelper')}
                  />
                  <FormTextField
                    name="notes"
                    control={qualityControl}
                    label={t('pages.harvest.notes')}
                    multiline
                    rows={3}
                  />
                  <FormActions
                    onCancel={() => resetQuality()}
                    loading={savingQuality}
                    saveLabel={t('common.create')}
                  />
                </form>
              </CardContent>
            </Card>
          )}
        </Box>
      )}

      {/* Tab 2: Yield */}
      {tab === 2 && (
        <Box>
          {yieldMetric ? (
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  {t('pages.harvest.yieldMetrics')}
                </Typography>
                <Table
                  size="small"
                  aria-label={t('pages.harvest.yieldMetrics')}
                >
                  <TableBody>
                    <TableRow>
                      <TableCell component="th">
                        {t('pages.harvest.yieldPerPlant')}
                      </TableCell>
                      <TableCell>
                        {yieldMetric.yield_per_plant_g} g
                      </TableCell>
                    </TableRow>
                    <TableRow>
                      <TableCell component="th">
                        {t('pages.harvest.yieldPerM2')}
                      </TableCell>
                      <TableCell>
                        {yieldMetric.yield_per_m2_g} g/m2
                      </TableCell>
                    </TableRow>
                    <TableRow>
                      <TableCell component="th">
                        {t('pages.harvest.totalYield')}
                      </TableCell>
                      <TableCell>{yieldMetric.total_yield_g} g</TableCell>
                    </TableRow>
                    <TableRow>
                      <TableCell component="th">
                        {t('pages.harvest.trimWaste')}
                      </TableCell>
                      <TableCell>
                        {yieldMetric.trim_waste_percent}%
                      </TableCell>
                    </TableRow>
                    <TableRow>
                      <TableCell component="th">
                        {t('pages.harvest.usableYield')}
                      </TableCell>
                      <TableCell>{yieldMetric.usable_yield_g} g</TableCell>
                    </TableRow>
                  </TableBody>
                </Table>
              </CardContent>
            </Card>
          ) : (
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  {t('pages.harvest.createYield')}
                </Typography>
                <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                  {t('pages.harvest.createYieldIntro')}
                </Typography>
                <form onSubmit={handleYieldSubmit(onSaveYield)}>
                  <FormRow>
                    <FormNumberField
                      name="yield_per_plant_g"
                      control={yieldControl}
                      label={t('pages.harvest.yieldPerPlant')}
                      min={0}
                      inputMode="decimal"
                      suffix="g"
                      helperText={t('pages.harvest.weightHelper')}
                    />
                    <FormNumberField
                      name="yield_per_m2_g"
                      control={yieldControl}
                      label={t('pages.harvest.yieldPerM2')}
                      min={0}
                      inputMode="decimal"
                      suffix="g/m\u00b2"
                    />
                  </FormRow>
                  <FormRow>
                    <FormNumberField
                      name="total_yield_g"
                      control={yieldControl}
                      label={t('pages.harvest.totalYield')}
                      min={0}
                      inputMode="decimal"
                      suffix="g"
                    />
                    <FormNumberField
                      name="usable_yield_g"
                      control={yieldControl}
                      label={t('pages.harvest.usableYield')}
                      min={0}
                      inputMode="decimal"
                      suffix="g"
                    />
                  </FormRow>
                  <FormNumberField
                    name="trim_waste_percent"
                    control={yieldControl}
                    label={t('pages.harvest.trimWaste')}
                    min={0}
                    max={100}
                    inputMode="decimal"
                    suffix="%"
                    helperText={t('pages.harvest.trimWasteHelper')}
                  />
                  <FormActions
                    onCancel={() => resetYield()}
                    loading={savingYield}
                    saveLabel={t('common.create')}
                  />
                </form>
              </CardContent>
            </Card>
          )}
        </Box>
      )}

      {/* Tab 3: Edit */}
      {tab === 3 && (
        <Card sx={{ maxWidth: 900 }}>
          <CardContent>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
              {t('pages.harvest.editIntro')}
            </Typography>
            <form onSubmit={handleEditSubmit(onSave)}>
              <FormSelectField
                name="harvest_type"
                control={editControl}
                label={t('pages.harvest.harvestType')}
                options={harvestTypes.map((v) => ({
                  value: v,
                  label: t(`enums.harvestType.${v}`),
                }))}
              />

              <Typography variant="subtitle2" color="text.secondary" sx={{ mb: 1, mt: 2 }}>
                {t('pages.harvest.sectionWeights')}
              </Typography>
              <FormNumberField
                name="wet_weight_g"
                control={editControl}
                label={t('pages.harvest.wetWeightG')}
                min={0}
                inputMode="decimal"
                suffix="g"
                helperText={t('pages.harvest.weightHelper')}
              />
              <FormRow>
                <FormNumberField
                  name="estimated_dry_weight_g"
                  control={editControl}
                  label={t('pages.harvest.estimatedDryWeightG')}
                  min={0}
                  inputMode="decimal"
                  suffix="g"
                />
                <FormNumberField
                  name="actual_dry_weight_g"
                  control={editControl}
                  label={t('pages.harvest.actualDryWeightG')}
                  min={0}
                  inputMode="decimal"
                  suffix="g"
                />
              </FormRow>
              <FormRow>
                <FormSelectField
                  name="quality_grade"
                  control={editControl}
                  label={t('pages.harvest.qualityGrade')}
                  options={[
                    { value: '', label: '\u2014' },
                    ...qualityGrades.map((v) => ({
                      value: v,
                      label: t(`enums.qualityGrade.${v}`),
                    })),
                  ]}
                />
                <FormTextField
                  name="harvester"
                  control={editControl}
                  label={t('pages.harvest.harvester')}
                />
              </FormRow>
              <FormTextField
                name="notes"
                control={editControl}
                label={t('pages.harvest.notes')}
                multiline
                rows={3}
              />
              <FormActions
                onCancel={() => resetEdit()}
                loading={saving}
                disabled={!isDirty}
              />
            </form>
          </CardContent>
        </Card>
      )}
    </Box>
  );
}
