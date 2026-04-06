import { useEffect, useState, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import Badge from '@mui/material/Badge';
import Button from '@mui/material/Button';
import Typography from '@mui/material/Typography';
import Chip from '@mui/material/Chip';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import Paper from '@mui/material/Paper';
import Stack from '@mui/material/Stack';
import Divider from '@mui/material/Divider';
import Alert from '@mui/material/Alert';
import Grid from '@mui/material/Grid';
import Tabs from '@mui/material/Tabs';
import Tab from '@mui/material/Tab';
import Tooltip from '@mui/material/Tooltip';
import IconButton from '@mui/material/IconButton';
import DeleteIcon from '@mui/icons-material/Delete';
import StarIcon from '@mui/icons-material/Star';
import StarBorderIcon from '@mui/icons-material/StarBorder';
import WarningAmberIcon from '@mui/icons-material/WarningAmber';
import ErrorOutlineIcon from '@mui/icons-material/ErrorOutline';
import AddIcon from '@mui/icons-material/Add';
import Dialog from '@mui/material/Dialog';
import useMediaQuery from '@mui/material/useMediaQuery';
import { useTheme } from '@mui/material/styles';
import DialogTitle from '@mui/material/DialogTitle';
import DialogContent from '@mui/material/DialogContent';
import DialogActions from '@mui/material/DialogActions';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import PageTitle from '@/components/layout/PageTitle';
import LoadingSkeleton from '@/components/common/LoadingSkeleton';
import ErrorDisplay from '@/components/common/ErrorDisplay';
import EmptyState from '@/components/common/EmptyState';
import ConfirmDialog from '@/components/common/ConfirmDialog';
import MobileCard from '@/components/common/MobileCard';
import DataTable, { type Column } from '@/components/common/DataTable';
import { useTableLocalState } from '@/hooks/useTableState';
import { useTabUrl } from '@/hooks/useTabUrl';
import { useLocalFavorites } from '@/hooks/useLocalFavorites';
import FormTextField from '@/components/form/FormTextField';
import FormSelectField from '@/components/form/FormSelectField';
import FormNumberField from '@/components/form/FormNumberField';
import FormSwitchField from '@/components/form/FormSwitchField';
import FormActions from '@/components/form/FormActions';
import FormRow from '@/components/form/FormRow';
import UnsavedChangesGuard from '@/components/form/UnsavedChangesGuard';
import { useNotification } from '@/hooks/useNotification';
import { useApiError } from '@/hooks/useApiError';
import { useAppDispatch } from '@/store/hooks';
import { setBreadcrumbs } from '@/store/slices/uiSlice';
import * as fertApi from '@/api/endpoints/fertilizers';
import FertilizerUsageGantt from './FertilizerUsageGantt';
import type { Fertilizer, FertilizerStock, FertilizerStockCreate, Incompatibility, NutrientPlanUsage } from '@/api/types';

const fertilizerTypes = ['base', 'supplement', 'booster', 'biological', 'ph_adjuster', 'organic', 'silicate'] as const;
const phEffects = ['acidic', 'alkaline', 'neutral'] as const;
const applicationMethods = ['fertigation', 'drench', 'foliar', 'top_dress', 'any'] as const;
const bioavailabilities = ['immediate', 'slow_release', 'microbial_dependent'] as const;

const editSchema = z.object({
  product_name: z.string().min(1).max(200),
  brand: z.string().max(200),
  fertilizer_type: z.enum(fertilizerTypes),
  is_organic: z.boolean(),
  tank_safe: z.boolean(),
  npk_n: z.number().min(0),
  npk_p: z.number().min(0),
  npk_k: z.number().min(0),
  ec_contribution_per_ml: z.number().min(0),
  ec_contribution_uncertain: z.boolean(),
  max_dose_ml_per_liter: z.number().min(0).nullable(),
  mixing_priority: z.number().int().min(1),
  ph_effect: z.enum(phEffects),
  recommended_application: z.enum(applicationMethods),
  bioavailability: z.enum(bioavailabilities),
  shelf_life_days: z.number().int().min(1).nullable(),
  storage_temp_min: z.number().nullable(),
  storage_temp_max: z.number().nullable(),
  notes: z.string().nullable(),
});

const stockSchema = z.object({
  current_volume_ml: z.number().min(0),
  purchase_date: z.string().nullable(),
  expiry_date: z.string().nullable(),
  batch_number: z.string(),
  cost_per_liter: z.number().min(0).nullable(),
});

type StockFormData = z.infer<typeof stockSchema>;

type EditFormData = z.infer<typeof editSchema>;

/** Returns color for the ph_effect value. */
function phEffectColor(effect: string): 'error' | 'primary' | 'default' {
  if (effect === 'acidic') return 'error';
  if (effect === 'alkaline') return 'primary';
  return 'default';
}

/** Returns days until date. Negative = already expired. */
function daysUntil(dateStr: string): number {
  const diff = new Date(dateStr).getTime() - Date.now();
  return Math.ceil(diff / (1000 * 60 * 60 * 24));
}

/** A labeled detail row used inside the Details tab sections. */
function DetailRow({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <Box
      sx={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        py: 0.75,
        gap: 2,
        '&:not(:last-child)': {
          borderBottom: '1px solid',
          borderColor: 'divider',
        },
      }}
    >
      <Typography variant="body2" color="text.secondary" sx={{ minWidth: 160, flexShrink: 0 }}>
        {label}
      </Typography>
      <Box sx={{ flex: 1, textAlign: 'right' }}>{children}</Box>
    </Box>
  );
}

/** Section card for the Details tab. */
function DetailSection({
  title,
  intro,
  children,
}: {
  title: string;
  intro: string;
  children: React.ReactNode;
}) {
  return (
    <Card sx={{ mb: 2 }}>
      <CardContent>
        <Typography variant="h6" gutterBottom>
          {title}
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
          {intro}
        </Typography>
        {children}
      </CardContent>
    </Card>
  );
}

/** Section panel for the Edit tab — Card/fieldset/legend pattern (UI-NFR-008). */
function EditSection({
  title,
  intro,
  children,
}: {
  title: string;
  intro: string;
  children: React.ReactNode;
}) {
  return (
    <Card variant="outlined">
      <CardContent component="fieldset" sx={{ border: 'none', p: 0, m: 0, '&:last-child': { pb: 2 }, px: 2, pt: 2 }}>
        <Typography component="legend" variant="h6" sx={{ pt: 1.5, mb: 0.5 }}>
          {title}
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
          {intro}
        </Typography>
        {children}
      </CardContent>
    </Card>
  );
}

export default function FertilizerDetailPage() {
  const theme = useTheme();
  const fullScreen = useMediaQuery(theme.breakpoints.down('sm'));
  const { key } = useParams<{ key: string }>();
  const { t } = useTranslation();
  const navigate = useNavigate();
  const dispatch = useAppDispatch();
  const notification = useNotification();
  const { handleError } = useApiError();

  const [fertilizer, setFertilizer] = useState<Fertilizer | null>(null);
  const [stocks, setStocks] = useState<FertilizerStock[]>([]);
  const [planUsage, setPlanUsage] = useState<NutrientPlanUsage[]>([]);
  const [incompatibilities, setIncompatibilities] = useState<Incompatibility[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [tab, setTab] = useTabUrl(['details', 'stock', 'edit']);
  const [saving, setSaving] = useState(false);
  const [deleteOpen, setDeleteOpen] = useState(false);
  const [stockDialogOpen, setStockDialogOpen] = useState(false);
  const [stockSaving, setStockSaving] = useState(false);
  const { isFavorite, toggleFavorite } = useLocalFavorites('kamerplanter-fertilizer-favorites');

  const stocksTableState = useTableLocalState({ defaultSort: { column: 'purchase_date', direction: 'desc' } });

  const {
    control,
    handleSubmit,
    reset,
    formState: { isDirty },
  } = useForm<EditFormData>({
    resolver: zodResolver(editSchema),
    defaultValues: {
      product_name: '',
      brand: '',
      fertilizer_type: 'base',
      is_organic: false,
      tank_safe: true,
      npk_n: 0,
      npk_p: 0,
      npk_k: 0,
      ec_contribution_per_ml: 0,
      ec_contribution_uncertain: false,
      max_dose_ml_per_liter: null,
      mixing_priority: 1,
      ph_effect: 'neutral',
      recommended_application: 'fertigation',
      bioavailability: 'immediate',
      shelf_life_days: null,
      storage_temp_min: null,
      storage_temp_max: null,
      notes: null,
    },
  });

  const stockForm = useForm<StockFormData>({
    resolver: zodResolver(stockSchema),
    defaultValues: {
      current_volume_ml: 1000,
      purchase_date: new Date().toISOString().split('T')[0],
      expiry_date: null,
      batch_number: '',
      cost_per_liter: null,
    },
  });

  const load = useCallback(async () => {
    if (!key) return;
    setLoading(true);
    try {
      const [f, st, pu, inc] = await Promise.all([
        fertApi.fetchFertilizer(key),
        fertApi.fetchFertilizerStocks(key),
        fertApi.fetchNutrientPlanUsage(key),
        fertApi.fetchIncompatibilities(key),
      ]);
      setFertilizer(f);
      reset({
        product_name: f.product_name,
        brand: f.brand,
        fertilizer_type: f.fertilizer_type,
        is_organic: f.is_organic,
        tank_safe: f.tank_safe,
        npk_n: f.npk_ratio[0],
        npk_p: f.npk_ratio[1],
        npk_k: f.npk_ratio[2],
        ec_contribution_per_ml: f.ec_contribution_per_ml,
        ec_contribution_uncertain: f.ec_contribution_uncertain,
        max_dose_ml_per_liter: f.max_dose_ml_per_liter,
        mixing_priority: f.mixing_priority,
        ph_effect: f.ph_effect,
        recommended_application: f.recommended_application,
        bioavailability: f.bioavailability,
        shelf_life_days: f.shelf_life_days,
        storage_temp_min: f.storage_temp_min,
        storage_temp_max: f.storage_temp_max,
        notes: f.notes,
      });
      setStocks(st);
      setPlanUsage(pu);
      setIncompatibilities(inc);
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

  // Dynamic breadcrumbs
  useEffect(() => {
    if (!fertilizer) return;
    dispatch(setBreadcrumbs([
      { label: 'nav.dashboard', path: '/dashboard' },
      { label: 'nav.fertilizers', path: '/duengung/fertilizers' },
      { label: fertilizer.product_name },
    ]));
  }, [fertilizer, dispatch]);

  // Clear dynamic breadcrumbs on unmount
  useEffect(() => () => { dispatch(setBreadcrumbs([])); }, [dispatch]);

  const onSave = async (data: EditFormData) => {
    if (!key) return;
    try {
      setSaving(true);
      await fertApi.updateFertilizer(key, {
        product_name: data.product_name,
        brand: data.brand,
        fertilizer_type: data.fertilizer_type,
        is_organic: data.is_organic,
        tank_safe: data.tank_safe,
        npk_ratio: [data.npk_n, data.npk_p, data.npk_k],
        ec_contribution_per_ml: data.ec_contribution_per_ml,
        ec_contribution_uncertain: data.ec_contribution_uncertain,
        max_dose_ml_per_liter: data.max_dose_ml_per_liter,
        mixing_priority: data.mixing_priority,
        ph_effect: data.ph_effect,
        recommended_application: data.recommended_application,
        bioavailability: data.bioavailability,
        shelf_life_days: data.shelf_life_days,
        storage_temp_min: data.storage_temp_min,
        storage_temp_max: data.storage_temp_max,
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

  const onDelete = async () => {
    if (!key) return;
    try {
      await fertApi.deleteFertilizer(key);
      notification.success(t('common.delete'));
      navigate('/duengung/fertilizers');
    } catch (err) {
      handleError(err);
    }
  };

  const onStockCreate = async (data: StockFormData) => {
    if (!key) return;
    try {
      setStockSaving(true);
      const payload: FertilizerStockCreate = {
        current_volume_ml: data.current_volume_ml,
        purchase_date: data.purchase_date || undefined,
        expiry_date: data.expiry_date || undefined,
        batch_number: data.batch_number || undefined,
        cost_per_liter: data.cost_per_liter ?? undefined,
      };
      await fertApi.createFertilizerStock(key, payload);
      notification.success(t('common.save'));
      setStockDialogOpen(false);
      stockForm.reset();
      load();
    } catch (err) {
      handleError(err);
    } finally {
      setStockSaving(false);
    }
  };

  // Stock summary calculations
  const totalVolumeMl = stocks.reduce((sum, s) => sum + s.current_volume_ml, 0);
  const costsWithValue = stocks.filter((s) => s.cost_per_liter != null);
  const avgCostPerLiter =
    costsWithValue.length > 0
      ? costsWithValue.reduce((sum, s) => sum + (s.cost_per_liter ?? 0), 0) / costsWithValue.length
      : null;
  const expiringCount = stocks.filter(
    (s) => s.expiry_date != null && daysUntil(s.expiry_date) <= 30 && daysUntil(s.expiry_date) >= 0
  ).length;

  const stockColumns: Column<FertilizerStock>[] = [
    {
      id: 'volume',
      label: t('pages.fertilizers.currentVolume'),
      render: (r) => `${r.current_volume_ml.toLocaleString()} ml`,
      align: 'right',
      searchValue: (r) => String(r.current_volume_ml),
    },
    {
      id: 'purchase_date',
      label: t('pages.fertilizers.purchaseDate'),
      render: (r) => (r.purchase_date ? new Date(r.purchase_date).toLocaleDateString() : '—'),
    },
    {
      id: 'expiry_date',
      label: t('pages.fertilizers.expiryDate'),
      render: (r) => {
        if (!r.expiry_date) return '—';
        const days = daysUntil(r.expiry_date);
        const label = new Date(r.expiry_date).toLocaleDateString();
        if (days <= 30 && days >= 0) {
          return (
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5, justifyContent: 'flex-end' }}>
              <WarningAmberIcon sx={{ fontSize: 16, color: 'warning.main' }} />
              <Typography variant="body2" color="warning.main">
                {label}
              </Typography>
            </Box>
          );
        }
        if (days < 0) {
          return (
            <Typography variant="body2" color="error.main">
              {label}
            </Typography>
          );
        }
        return label;
      },
    },
    {
      id: 'batch_number',
      label: t('pages.fertilizers.batchNumber'),
      render: (r) => r.batch_number || '—',
    },
    {
      id: 'cost',
      label: t('pages.fertilizers.costPerLiter'),
      render: (r) =>
        r.cost_per_liter != null ? `${r.cost_per_liter.toFixed(2)} €/L` : '—',
      align: 'right',
      searchValue: (r) => (r.cost_per_liter != null ? String(r.cost_per_liter) : ''),
    },
  ];

  // Storage temperature display helper
  const storageTempDisplay = (f: Fertilizer) => {
    const min = f.storage_temp_min;
    const max = f.storage_temp_max;
    if (min != null && max != null) return `${min}–${max} °C`;
    if (min != null) return `≥ ${min} °C`;
    if (max != null) return `≤ ${max} °C`;
    return '—';
  };

  if (loading) return <LoadingSkeleton variant="form" />;
  if (error) return <ErrorDisplay error={error} />;
  if (!fertilizer) return <ErrorDisplay error={t('errors.notFound')} />;

  const [npkN, npkP, npkK] = fertilizer.npk_ratio;
  const hasStorageData =
    fertilizer.shelf_life_days != null ||
    fertilizer.storage_temp_min != null ||
    fertilizer.storage_temp_max != null;

  return (
    <Box data-testid="fertilizer-detail-page">
      <UnsavedChangesGuard dirty={isDirty} />

      {/* Page header */}
      <Box
        sx={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          mb: 2,
          flexWrap: 'wrap',
          gap: 1,
        }}
      >
        <Box>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <PageTitle title={fertilizer.product_name} sx={{ mb: 0 }} />
            {key && (
              <IconButton
                onClick={() => toggleFavorite(key)}
                aria-label={isFavorite(key) ? t('common.removeFavorite') : t('common.addFavorite')}
                data-testid="favorite-toggle"
                sx={{ color: isFavorite(key) ? 'warning.main' : 'action.disabled' }}
              >
                {isFavorite(key) ? <StarIcon /> : <StarBorderIcon />}
              </IconButton>
            )}
          </Box>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, flexWrap: 'wrap', mt: 0.5 }}>
            {fertilizer.is_organic && (
              <Chip label={t('pages.fertilizers.isOrganic')} size="small" color="success" />
            )}
            {fertilizer.tank_safe && (
              <Chip label={t('pages.fertilizers.tankSafe')} size="small" color="info" />
            )}
            <Chip
              label={t(`enums.fertilizerType.${fertilizer.fertilizer_type}`)}
              size="small"
              variant="outlined"
            />
            {fertilizer.brand && (
              <Typography variant="body2" color="text.secondary">
                {fertilizer.brand}
              </Typography>
            )}
          </Box>
        </Box>
        <Button
          variant="outlined"
          color="error"
          startIcon={<DeleteIcon />}
          onClick={() => setDeleteOpen(true)}
          data-testid="delete-button"
        >
          {t('common.delete')}
        </Button>
      </Box>

      <Tabs
        value={tab}
        onChange={(_, v) => setTab(v)}
        sx={{ mb: 2 }}
        variant="scrollable"
        scrollButtons="auto"
        aria-label={fertilizer.product_name}
      >
        <Tab label={t('pages.fertilizers.tabDetails')} data-testid="tab-details" />
        <Tab
          label={
            <Badge badgeContent={stocks.length} color="primary" max={99}>
              <Box sx={{ px: 0.5 }}>{t('pages.fertilizers.tabStock')}</Box>
            </Badge>
          }
          data-testid="tab-stock"
        />
        <Tab label={t('pages.fertilizers.tabEdit')} data-testid="tab-edit" />
      </Tabs>

      {/* ── Tab 0: Details ── */}
      {tab === 0 && (
        <Box>
          {/* Incompatibilities warning */}
          {incompatibilities.length > 0 && (
            <Alert severity="warning" icon={<ErrorOutlineIcon />} sx={{ mb: 2 }}>
              <Typography variant="subtitle2" gutterBottom>
                {t('pages.fertilizers.incompatibilities')} ({incompatibilities.length})
              </Typography>
              {incompatibilities.map((inc) => (
                <Typography key={inc.fertilizer_key} variant="body2">
                  {inc.product_name ?? inc.fertilizer_key}: {inc.reason}
                  {inc.severity === 'critical' && (
                    <Chip label={t('pages.fertilizers.incompCritical')} size="small" color="error" sx={{ ml: 1 }} />
                  )}
                </Typography>
              ))}
            </Alert>
          )}

          {/* NPK Hero Block */}
          <Paper
            variant="outlined"
            sx={{
              mb: 2,
              p: 2,
              background: (theme) =>
                theme.palette.mode === 'dark'
                  ? theme.palette.grey[900]
                  : theme.palette.grey[50],
            }}
          >
            <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2} alignItems={{ sm: 'center' }}>
              {/* NPK values */}
              <Stack direction="row" spacing={1} alignItems="center" flexWrap="wrap" useFlexGap>
                <Chip
                  label={`N ${npkN}%`}
                  color="success"
                  sx={{ fontWeight: 700, fontSize: '0.95rem', minWidth: 80 }}
                />
                <Chip
                  label={`P ${npkP}%`}
                  color="warning"
                  sx={{ fontWeight: 700, fontSize: '0.95rem', minWidth: 80 }}
                />
                <Chip
                  label={`K ${npkK}%`}
                  color="secondary"
                  sx={{ fontWeight: 700, fontSize: '0.95rem', minWidth: 80 }}
                />
              </Stack>

              <Divider orientation="vertical" flexItem sx={{ display: { xs: 'none', sm: 'block' } }} />
              <Divider sx={{ display: { xs: 'block', sm: 'none' } }} />

              {/* EC & pH */}
              <Stack direction="row" spacing={3} alignItems="center" flexWrap="wrap" useFlexGap>
                <Box>
                  <Typography variant="caption" color="text.secondary" display="block">
                    {t('pages.fertilizers.ecContribution')}
                  </Typography>
                  <Stack direction="row" spacing={0.5} alignItems="center">
                    <Typography variant="body1" fontWeight={600}>
                      {fertilizer.ec_contribution_per_ml.toFixed(3)} mS/ml
                    </Typography>
                    {fertilizer.ec_contribution_uncertain && (
                      <Tooltip title={t('pages.fertilizers.ecUncertainHint')}>
                        <WarningAmberIcon sx={{ fontSize: 16, color: 'warning.main' }} />
                      </Tooltip>
                    )}
                  </Stack>
                </Box>
                <Box>
                  <Typography variant="caption" color="text.secondary" display="block">
                    {t('pages.fertilizers.phEffect')}
                  </Typography>
                  <Chip
                    label={t(`enums.phEffect.${fertilizer.ph_effect}`)}
                    size="small"
                    color={phEffectColor(fertilizer.ph_effect)}
                    variant="outlined"
                  />
                </Box>
                {fertilizer.max_dose_ml_per_liter != null && (
                  <Box>
                    <Typography variant="caption" color="text.secondary" display="block">
                      {t('pages.fertilizers.maxDose')}
                    </Typography>
                    <Typography variant="body1" fontWeight={600}>
                      {fertilizer.max_dose_ml_per_liter} ml/L
                    </Typography>
                  </Box>
                )}
              </Stack>
            </Stack>
          </Paper>

          {/* Application & Mixing section */}
          <DetailSection
            title={t('pages.fertilizers.sectionMixingDetail')}
            intro={t('pages.fertilizers.sectionMixingDetailIntro')}
          >
            <DetailRow label={t('pages.fertilizers.recommendedApplication')}>
              <Typography variant="body2">
                {t(`enums.applicationMethod.${fertilizer.recommended_application}`)}
              </Typography>
            </DetailRow>
            <DetailRow label={t('pages.fertilizers.bioavailability')}>
              <Chip
                label={t(`enums.bioavailability.${fertilizer.bioavailability}`)}
                size="small"
                variant="outlined"
              />
            </DetailRow>
            <DetailRow label={t('pages.fertilizers.mixingPriority')}>
              <Stack direction="row" spacing={1} alignItems="center" justifyContent="flex-end">
                <Chip label={fertilizer.mixing_priority} size="small" variant="outlined" />
                <Typography variant="caption" color="text.secondary">
                  {t('pages.fertilizers.mixingPriorityHelper')}
                </Typography>
              </Stack>
            </DetailRow>
          </DetailSection>

          {/* Storage section — only when data exists */}
          {hasStorageData && (
            <DetailSection
              title={t('pages.fertilizers.sectionStorageDetail')}
              intro={t('pages.fertilizers.sectionStorageDetailIntro')}
            >
              {(fertilizer.storage_temp_min != null || fertilizer.storage_temp_max != null) && (
                <DetailRow label={t('pages.fertilizers.sectionStorage')}>
                  <Typography variant="body2">{storageTempDisplay(fertilizer)}</Typography>
                </DetailRow>
              )}
              {fertilizer.shelf_life_days != null && (
                <DetailRow label={t('pages.fertilizers.shelfLifeDays')}>
                  <Typography variant="body2">
                    {fertilizer.shelf_life_days} {t('common.days')}
                  </Typography>
                </DetailRow>
              )}
            </DetailSection>
          )}

          {/* Notes */}
          {fertilizer.notes && (
            <Card sx={{ mb: 2 }}>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  {t('pages.fertilizers.notes')}
                </Typography>
                <Typography variant="body2" sx={{ whiteSpace: 'pre-line' }}>
                  {fertilizer.notes}
                </Typography>
              </CardContent>
            </Card>
          )}

          {/* Usage / Gantt */}
          <DetailSection
            title={t('pages.fertilizers.sectionUsageDetail')}
            intro={t('pages.fertilizers.sectionUsageDetailIntro')}
          >
            {planUsage.length === 0 ? (
              <Typography variant="body2" color="text.secondary">
                {t('pages.fertilizers.notUsedInAnyPlan')}
              </Typography>
            ) : (
              <FertilizerUsageGantt planUsage={planUsage} />
            )}
          </DetailSection>

          {/* Metadata */}
          {(fertilizer.created_at || fertilizer.updated_at) && (
            <Typography variant="caption" color="text.disabled" sx={{ mt: 1, display: 'block' }}>
              {fertilizer.created_at && `${t('common.createdAt')}: ${new Date(fertilizer.created_at).toLocaleDateString()}`}
              {fertilizer.created_at && fertilizer.updated_at && ' · '}
              {fertilizer.updated_at && `${t('common.updatedAt')}: ${new Date(fertilizer.updated_at).toLocaleDateString()}`}
            </Typography>
          )}
        </Box>
      )}

      {/* ── Tab 1: Stock ── */}
      {tab === 1 && (
        <Box>
          {/* Header with add button */}
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
            <Typography variant="body2" color="text.secondary">
              {t('pages.fertilizers.stockIntro')}
            </Typography>
            <Button
              variant="contained"
              size="small"
              startIcon={<AddIcon />}
              onClick={() => setStockDialogOpen(true)}
            >
              {t('pages.fertilizers.addStock')}
            </Button>
          </Box>

          {/* Summary bar */}
          {stocks.length > 0 && (
            <Grid container spacing={2} sx={{ mb: 2 }}>
              <Grid size={{ xs: 6, sm: 4 }}>
                <Paper variant="outlined" sx={{ p: 1.5, textAlign: 'center' }}>
                  <Typography variant="caption" color="text.secondary" display="block">
                    {t('pages.fertilizers.stockTotalVolume')}
                  </Typography>
                  <Typography variant="h6">
                    {totalVolumeMl >= 1000
                      ? `${(totalVolumeMl / 1000).toFixed(1)} L`
                      : `${totalVolumeMl.toLocaleString()} ml`}
                  </Typography>
                </Paper>
              </Grid>
              {avgCostPerLiter != null && (
                <Grid size={{ xs: 6, sm: 4 }}>
                  <Paper variant="outlined" sx={{ p: 1.5, textAlign: 'center' }}>
                    <Typography variant="caption" color="text.secondary" display="block">
                      {t('pages.fertilizers.stockAvgCost')}
                    </Typography>
                    <Typography variant="h6">
                      {avgCostPerLiter.toFixed(2)} &euro;/L
                    </Typography>
                  </Paper>
                </Grid>
              )}
              <Grid size={{ xs: 6, sm: 4 }}>
                <Paper variant="outlined" sx={{ p: 1.5, textAlign: 'center' }}>
                  <Typography variant="caption" color="text.secondary" display="block">
                    {t('pages.fertilizers.stockCount')}
                  </Typography>
                  <Typography variant="h6">{stocks.length}</Typography>
                </Paper>
              </Grid>
            </Grid>
          )}

          {/* Expiry warning */}
          {expiringCount > 0 && (
            <Alert severity="warning" icon={<WarningAmberIcon />} sx={{ mb: 2 }}>
              {t('pages.fertilizers.stockExpiringWarning', { count: expiringCount })}
            </Alert>
          )}

          {stocks.length === 0 ? (
            <EmptyState
              message={t('pages.fertilizers.stockEmptyTitle')}
              description={t('pages.fertilizers.stockEmptyDesc')}
              actionLabel={t('pages.fertilizers.addStock')}
              onAction={() => setStockDialogOpen(true)}
            />
          ) : (
            <DataTable
              columns={stockColumns}
              rows={stocks}
              getRowKey={(r) => r.key}
              tableState={stocksTableState}
              variant="simple"
              ariaLabel={t('pages.fertilizers.tabStock')}
              mobileCardRenderer={(r) => (
                <MobileCard
                  title={`${r.current_volume_ml.toLocaleString()} ml`}
                  subtitle={r.purchase_date ? new Date(r.purchase_date).toLocaleDateString() : undefined}
                  fields={[
                    ...(r.expiry_date
                      ? [{ label: t('pages.fertilizers.expiryDate'), value: new Date(r.expiry_date).toLocaleDateString() }]
                      : []),
                    ...(r.batch_number
                      ? [{ label: t('pages.fertilizers.batchNumber'), value: r.batch_number }]
                      : []),
                    ...(r.cost_per_liter != null
                      ? [{ label: t('pages.fertilizers.costPerLiter'), value: `${r.cost_per_liter.toFixed(2)} \u20ac/L` }]
                      : []),
                  ]}
                />
              )}
            />
          )}
        </Box>
      )}

      {/* ── Tab 2: Edit ── */}
      {tab === 2 && (
        <Box component="form" onSubmit={handleSubmit(onSave)} sx={{ maxWidth: 900, display: 'flex', flexDirection: 'column', gap: 4 }}>
          <Typography variant="body2" color="text.secondary">
            {t('pages.fertilizers.editIntro')}
          </Typography>

          {/* Section: Identification */}
          <EditSection
            title={t('pages.fertilizers.sectionIdentification')}
            intro={t('pages.fertilizers.sectionIdentificationIntro')}
          >
            <FormRow>
              <FormTextField
                name="product_name"
                control={control}
                label={t('pages.fertilizers.productName')}
                required
                autoFocus
              />
              <FormTextField
                name="brand"
                control={control}
                label={t('pages.fertilizers.brand')}
              />
            </FormRow>
            <FormSelectField
              name="fertilizer_type"
              control={control}
              label={t('pages.fertilizers.fertilizerType')}
              options={fertilizerTypes.map((v) => ({
                value: v,
                label: t(`enums.fertilizerType.${v}`),
              }))}
            />
          </EditSection>

          {/* Section: NPK & Nutrient Profile */}
          <EditSection
            title={t('pages.fertilizers.sectionNutrients')}
            intro={t('pages.fertilizers.sectionNutrientsIntro')}
          >
            <Box
              sx={{
                display: 'grid',
                gridTemplateColumns: { xs: '1fr', sm: '1fr 1fr 1fr' },
                columnGap: 2,
              }}
            >
              <FormNumberField
                name="npk_n"
                control={control}
                label={t('pages.fertilizers.npkN')}
                min={0}
                suffix="%"
                inputMode="decimal"
                helperText={t('pages.fertilizers.npkNHelper')}
              />
              <FormNumberField
                name="npk_p"
                control={control}
                label={t('pages.fertilizers.npkP')}
                min={0}
                suffix="%"
                inputMode="decimal"
              />
              <FormNumberField
                name="npk_k"
                control={control}
                label={t('pages.fertilizers.npkK')}
                min={0}
                suffix="%"
                inputMode="decimal"
              />
            </Box>
            <FormRow>
              <FormNumberField
                name="ec_contribution_per_ml"
                control={control}
                label={t('pages.fertilizers.ecContribution')}
                min={0}
                suffix="mS/ml"
                inputMode="decimal"
                helperText={t('pages.fertilizers.ecContributionHelper')}
              />
              <FormNumberField
                name="max_dose_ml_per_liter"
                control={control}
                label={t('pages.fertilizers.maxDose')}
                min={0}
                suffix="ml/L"
                inputMode="decimal"
                helperText={t('pages.fertilizers.maxDoseHelper')}
              />
            </FormRow>
            <FormSwitchField
              name="ec_contribution_uncertain"
              control={control}
              label={t('pages.fertilizers.ecUncertain')}
              helperText={t('pages.fertilizers.ecUncertainHelper')}
            />
          </EditSection>

          {/* Section: Mixing & Application */}
          <EditSection
            title={t('pages.fertilizers.sectionMixing')}
            intro={t('pages.fertilizers.sectionMixingIntro')}
          >
            <FormRow>
              <FormNumberField
                name="mixing_priority"
                control={control}
                label={t('pages.fertilizers.mixingPriority')}
                min={1}
                step={1}
                helperText={t('pages.fertilizers.mixingPriorityHelperFull')}
              />
              <FormSelectField
                name="ph_effect"
                control={control}
                label={t('pages.fertilizers.phEffect')}
                options={phEffects.map((v) => ({
                  value: v,
                  label: t(`enums.phEffect.${v}`),
                }))}
              />
            </FormRow>
            <FormRow>
              <FormSelectField
                name="recommended_application"
                control={control}
                label={t('pages.fertilizers.recommendedApplication')}
                options={applicationMethods.map((v) => ({
                  value: v,
                  label: t(`enums.applicationMethod.${v}`),
                }))}
              />
              <FormSelectField
                name="bioavailability"
                control={control}
                label={t('pages.fertilizers.bioavailability')}
                options={bioavailabilities.map((v) => ({
                  value: v,
                  label: t(`enums.bioavailability.${v}`),
                }))}
              />
            </FormRow>
          </EditSection>

          {/* Section: Properties */}
          <EditSection
            title={t('pages.fertilizers.sectionProperties')}
            intro={t('pages.fertilizers.sectionPropertiesIntro')}
          >
            <FormRow>
              <FormSwitchField
                name="is_organic"
                control={control}
                label={t('pages.fertilizers.isOrganic')}
                helperText={t('pages.fertilizers.isOrganicHelper')}
              />
              <FormSwitchField
                name="tank_safe"
                control={control}
                label={t('pages.fertilizers.tankSafe')}
                helperText={t('pages.fertilizers.tankSafeHelper')}
              />
            </FormRow>
          </EditSection>

          {/* Section: Storage */}
          <EditSection
            title={t('pages.fertilizers.sectionStorage')}
            intro={t('pages.fertilizers.sectionStorageIntro')}
          >
            <FormRow>
              <FormNumberField
                name="storage_temp_min"
                control={control}
                label={t('pages.fertilizers.storageTempMin')}
                suffix="°C"
                inputMode="decimal"
              />
              <FormNumberField
                name="storage_temp_max"
                control={control}
                label={t('pages.fertilizers.storageTempMax')}
                suffix="°C"
                inputMode="decimal"
              />
            </FormRow>
            <FormNumberField
              name="shelf_life_days"
              control={control}
              label={t('pages.fertilizers.shelfLifeDays')}
              min={1}
              step={1}
              inputMode="numeric"
              helperText={t('pages.fertilizers.shelfLifeHelper')}
            />
          </EditSection>

          {/* Notes */}
          <EditSection
            title={t('pages.fertilizers.notes')}
            intro={t('pages.fertilizers.sectionNotesIntro')}
          >
            <FormTextField
              name="notes"
              control={control}
              label={t('pages.fertilizers.notes')}
              multiline
              rows={3}
            />
          </EditSection>

          <Typography variant="caption" color="text.secondary">* {t('common.required')}</Typography>
          <FormActions
            onCancel={() => reset()}
            loading={saving}
            disabled={!isDirty}
          />
        </Box>
      )}

      {/* Stock creation dialog */}
      <Dialog fullScreen={fullScreen} open={stockDialogOpen}
        onClose={() => { setStockDialogOpen(false); stockForm.reset(); }}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>{t('pages.fertilizers.addStock')}</DialogTitle>
        <DialogContent>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 2, mt: 1 }}>
            {t('pages.fertilizers.addStockIntro')}
          </Typography>
          <FormRow>
            <FormNumberField
              name="current_volume_ml"
              control={stockForm.control}
              label={t('pages.fertilizers.currentVolumeMl')}
              min={0}
              suffix="ml"
              inputMode="numeric"
              required
            />
            <FormNumberField
              name="cost_per_liter"
              control={stockForm.control}
              label={t('pages.fertilizers.costPerLiter')}
              min={0}
              suffix={'€/L'}
              inputMode="decimal"
            />
          </FormRow>
          <FormRow>
            <FormTextField
              name="purchase_date"
              control={stockForm.control}
              label={t('pages.fertilizers.purchaseDate')}
              type="date"
            />
            <FormTextField
              name="expiry_date"
              control={stockForm.control}
              label={t('pages.fertilizers.expiryDate')}
              type="date"
            />
          </FormRow>
          <FormTextField
            name="batch_number"
            control={stockForm.control}
            label={t('pages.fertilizers.batchNumber')}
          />
        </DialogContent>
        <DialogActions>
          <Button
            onClick={() => { setStockDialogOpen(false); stockForm.reset(); }}
            disabled={stockSaving}
          >
            {t('common.cancel')}
          </Button>
          <Button
            variant="contained"
            onClick={stockForm.handleSubmit(onStockCreate)}
            disabled={stockSaving}
          >
            {t('common.save')}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Delete confirmation */}
      <ConfirmDialog
        open={deleteOpen}
        title={t('common.delete')}
        message={t('common.deleteConfirm', { name: fertilizer.product_name })}
        onConfirm={onDelete}
        onCancel={() => setDeleteOpen(false)}
        destructive
      />
    </Box>
  );
}
