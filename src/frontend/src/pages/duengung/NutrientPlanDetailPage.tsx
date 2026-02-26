import { useEffect, useState, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Typography from '@mui/material/Typography';
import Chip from '@mui/material/Chip';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import Tabs from '@mui/material/Tabs';
import Tab from '@mui/material/Tab';
import Alert from '@mui/material/Alert';
import CircularProgress from '@mui/material/CircularProgress';
import DeleteIcon from '@mui/icons-material/Delete';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import PageTitle from '@/components/layout/PageTitle';
import LoadingSkeleton from '@/components/common/LoadingSkeleton';
import ErrorDisplay from '@/components/common/ErrorDisplay';
import ConfirmDialog from '@/components/common/ConfirmDialog';
import DataTable, { type Column } from '@/components/common/DataTable';
import { useTableLocalState } from '@/hooks/useTableState';
import FormTextField from '@/components/form/FormTextField';
import FormSelectField from '@/components/form/FormSelectField';
import FormSwitchField from '@/components/form/FormSwitchField';
import FormChipInput from '@/components/form/FormChipInput';
import FormActions from '@/components/form/FormActions';
import UnsavedChangesGuard from '@/components/form/UnsavedChangesGuard';
import { useNotification } from '@/hooks/useNotification';
import { useApiError } from '@/hooks/useApiError';
import * as planApi from '@/api/endpoints/nutrient-plans';
import type { NutrientPlan, NutrientPlanPhaseEntry, PlanValidationResult } from '@/api/types';

const substrateTypes = [
  'soil',
  'coco',
  'rockwool',
  'clay_pebbles',
  'perlite',
  'living_soil',
  'hydro_solution',
] as const;

const editSchema = z.object({
  name: z.string().min(1).max(200),
  description: z.string().max(2000),
  recommended_substrate_type: z.enum(substrateTypes).nullable(),
  author: z.string().max(200),
  is_template: z.boolean(),
  version: z.string().max(50),
  tags: z.array(z.string()),
});

type EditFormData = z.infer<typeof editSchema>;

export default function NutrientPlanDetailPage() {
  const { key } = useParams<{ key: string }>();
  const { t } = useTranslation();
  const navigate = useNavigate();
  const notification = useNotification();
  const { handleError } = useApiError();

  const [plan, setPlan] = useState<NutrientPlan | null>(null);
  const [entries, setEntries] = useState<NutrientPlanPhaseEntry[]>([]);
  const [validation, setValidation] = useState<PlanValidationResult | null>(null);
  const [validating, setValidating] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [tab, setTab] = useState(0);
  const [saving, setSaving] = useState(false);
  const [deleteOpen, setDeleteOpen] = useState(false);

  const entriesTableState = useTableLocalState({ defaultSort: { column: 'sequence_order', direction: 'asc' } });

  const {
    control,
    handleSubmit,
    reset,
    formState: { isDirty },
  } = useForm<EditFormData>({
    resolver: zodResolver(editSchema),
    defaultValues: {
      name: '',
      description: '',
      recommended_substrate_type: null,
      author: '',
      is_template: false,
      version: '',
      tags: [],
    },
  });

  const load = useCallback(async () => {
    if (!key) return;
    setLoading(true);
    try {
      const [p, e] = await Promise.all([
        planApi.fetchNutrientPlan(key),
        planApi.fetchPhaseEntries(key),
      ]);
      setPlan(p);
      setEntries(e);
      reset({
        name: p.name,
        description: p.description,
        recommended_substrate_type: p.recommended_substrate_type as typeof substrateTypes[number] | null,
        author: p.author,
        is_template: p.is_template,
        version: p.version,
        tags: p.tags,
      });
      setError(null);
    } catch (err) {
      setError(String(err));
    } finally {
      setLoading(false);
    }
  }, [key, reset]);

  useEffect(() => {
    load();
  }, [load]);

  const loadValidation = useCallback(async () => {
    if (!key) return;
    setValidating(true);
    try {
      const result = await planApi.validateNutrientPlan(key);
      setValidation(result);
    } catch (err) {
      handleError(err);
    } finally {
      setValidating(false);
    }
  }, [key, handleError]);

  useEffect(() => {
    if (tab === 1) {
      loadValidation();
    }
  }, [tab, loadValidation]);

  const onSave = async (data: EditFormData) => {
    if (!key) return;
    try {
      setSaving(true);
      await planApi.updateNutrientPlan(key, {
        name: data.name,
        description: data.description,
        recommended_substrate_type: data.recommended_substrate_type,
        author: data.author,
        is_template: data.is_template,
        version: data.version,
        tags: data.tags,
      });
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
      await planApi.deleteNutrientPlan(key);
      notification.success(t('common.delete'));
      navigate('/duengung/plans');
    } catch (err) {
      handleError(err);
    }
  };

  const entryColumns: Column<NutrientPlanPhaseEntry>[] = [
    {
      id: 'sequence_order',
      label: '#',
      render: (r) => r.sequence_order,
      align: 'right',
    },
    {
      id: 'phase_name',
      label: t('pages.nutrientPlans.phaseName'),
      render: (r) => t(`enums.phaseName.${r.phase_name}`),
      searchValue: (r) => t(`enums.phaseName.${r.phase_name}`),
    },
    {
      id: 'weeks',
      label: t('pages.nutrientPlans.weeks'),
      render: (r) => `${r.week_start}-${r.week_end}`,
    },
    {
      id: 'npk',
      label: 'NPK',
      render: (r) => `${r.npk_ratio[0]}-${r.npk_ratio[1]}-${r.npk_ratio[2]}`,
    },
    {
      id: 'target_ec',
      label: t('pages.nutrientPlans.targetEc'),
      render: (r) => `${r.target_ec_ms} mS`,
      align: 'right',
      searchValue: (r) => String(r.target_ec_ms),
    },
    {
      id: 'target_ph',
      label: t('pages.nutrientPlans.targetPh'),
      render: (r) => r.target_ph.toFixed(1),
      align: 'right',
      searchValue: (r) => String(r.target_ph),
    },
    {
      id: 'feeding_frequency',
      label: t('pages.nutrientPlans.feedingFrequency'),
      render: (r) => `${r.feeding_frequency_per_week}x / ${t('pages.nutrientPlans.week')}`,
      align: 'right',
    },
  ];

  if (loading) return <LoadingSkeleton variant="form" />;
  if (error) return <ErrorDisplay error={error} />;
  if (!plan) return <ErrorDisplay error={t('errors.notFound')} />;

  return (
    <Box data-testid="nutrient-plan-detail-page">
      <UnsavedChangesGuard dirty={isDirty} />
      <Box
        sx={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          mb: 2,
        }}
      >
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <PageTitle title={plan.name} />
          {plan.is_template && (
            <Chip label={t('pages.nutrientPlans.isTemplate')} size="small" color="primary" />
          )}
        </Box>
        <Button
          variant="outlined"
          color="error"
          startIcon={<DeleteIcon />}
          onClick={() => setDeleteOpen(true)}
        >
          {t('common.delete')}
        </Button>
      </Box>

      <Tabs value={tab} onChange={(_, v) => setTab(v)} sx={{ mb: 2 }}>
        <Tab label={t('pages.nutrientPlans.tabPhaseEntries')} />
        <Tab label={t('pages.nutrientPlans.tabValidation')} />
        <Tab label={t('common.edit')} />
      </Tabs>

      {/* Tab 0: Phase Entries */}
      {tab === 0 && (
        <Box>
          <DataTable
            columns={entryColumns}
            rows={entries}
            getRowKey={(r) => r.key}
            tableState={entriesTableState}
            variant="simple"
            ariaLabel={t('pages.nutrientPlans.tabPhaseEntries')}
          />
        </Box>
      )}

      {/* Tab 1: Validation */}
      {tab === 1 && (
        <Box>
          {validating && (
            <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
              <CircularProgress />
            </Box>
          )}
          {!validating && validation && (
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
                  {validation.completeness.issues.map((issue, i) => (
                    <Alert key={i} severity="warning" sx={{ mb: 0.5 }}>
                      {issue}
                    </Alert>
                  ))}
                </CardContent>
              </Card>

              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    {t('pages.nutrientPlans.ecBudgets')}
                  </Typography>
                  {validation.ec_budgets.map((budget, i) => (
                    <Alert
                      key={i}
                      severity={budget.valid ? 'success' : 'error'}
                      sx={{ mb: 0.5 }}
                    >
                      <strong>{t(`enums.phaseName.${budget.phase_name}`)}</strong>:{' '}
                      {budget.message} ({t('pages.nutrientPlans.targetEc')}: {budget.target_ec},{' '}
                      {t('pages.nutrientPlans.calculatedEc')}: {budget.calculated_ec.toFixed(2)},{' '}
                      {t('pages.nutrientPlans.delta')}: {budget.delta.toFixed(2)})
                    </Alert>
                  ))}
                </CardContent>
              </Card>
            </>
          )}
        </Box>
      )}

      {/* Tab 2: Edit */}
      {tab === 2 && (
        <Card>
          <CardContent>
            <form onSubmit={handleSubmit(onSave)}>
              <FormTextField
                name="name"
                control={control}
                label={t('pages.nutrientPlans.name')}
                required
              />
              <FormTextField
                name="description"
                control={control}
                label={t('pages.nutrientPlans.description')}
                multiline
                rows={3}
              />
              <FormSelectField
                name="recommended_substrate_type"
                control={control}
                label={t('pages.nutrientPlans.substrateType')}
                options={substrateTypes.map((v) => ({
                  value: v,
                  label: t(`enums.substrateType.${v}`),
                }))}
              />
              <FormTextField
                name="author"
                control={control}
                label={t('pages.nutrientPlans.author')}
              />
              <FormSwitchField
                name="is_template"
                control={control}
                label={t('pages.nutrientPlans.isTemplate')}
              />
              <FormTextField
                name="version"
                control={control}
                label={t('pages.nutrientPlans.version')}
              />
              <FormChipInput
                name="tags"
                control={control}
                label={t('pages.nutrientPlans.tags')}
                placeholder={t('pages.nutrientPlans.tagsPlaceholder')}
              />
              <FormActions
                onCancel={() => reset()}
                loading={saving}
                disabled={!isDirty}
              />
            </form>
          </CardContent>
        </Card>
      )}

      <ConfirmDialog
        open={deleteOpen}
        title={t('common.delete')}
        message={t('common.deleteConfirm', { name: plan.name })}
        onConfirm={onDelete}
        onCancel={() => setDeleteOpen(false)}
      />
    </Box>
  );
}
