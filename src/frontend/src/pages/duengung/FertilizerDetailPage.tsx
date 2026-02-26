import { useEffect, useState, useCallback } from 'react';
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
import TableRow from '@mui/material/TableRow';
import Tabs from '@mui/material/Tabs';
import Tab from '@mui/material/Tab';
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
import FormNumberField from '@/components/form/FormNumberField';
import FormSwitchField from '@/components/form/FormSwitchField';
import FormActions from '@/components/form/FormActions';
import UnsavedChangesGuard from '@/components/form/UnsavedChangesGuard';
import { useNotification } from '@/hooks/useNotification';
import { useApiError } from '@/hooks/useApiError';
import * as fertApi from '@/api/endpoints/fertilizers';
import type { Fertilizer, FertilizerStock } from '@/api/types';

const fertilizerTypes = ['base', 'supplement', 'booster', 'biological', 'ph_adjuster', 'organic'] as const;
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
  mixing_priority: z.number().int().min(1),
  ph_effect: z.enum(phEffects),
  recommended_application: z.enum(applicationMethods),
  bioavailability: z.enum(bioavailabilities),
  shelf_life_days: z.number().int().min(1).nullable(),
  storage_temp_min: z.number().nullable(),
  storage_temp_max: z.number().nullable(),
  notes: z.string().nullable(),
});

type EditFormData = z.infer<typeof editSchema>;

export default function FertilizerDetailPage() {
  const { key } = useParams<{ key: string }>();
  const { t } = useTranslation();
  const navigate = useNavigate();
  const notification = useNotification();
  const { handleError } = useApiError();

  const [fertilizer, setFertilizer] = useState<Fertilizer | null>(null);
  const [stocks, setStocks] = useState<FertilizerStock[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [tab, setTab] = useState(0);
  const [saving, setSaving] = useState(false);
  const [deleteOpen, setDeleteOpen] = useState(false);

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

  const load = useCallback(async () => {
    if (!key) return;
    setLoading(true);
    try {
      const f = await fertApi.fetchFertilizer(key);
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
        mixing_priority: f.mixing_priority,
        ph_effect: f.ph_effect,
        recommended_application: f.recommended_application,
        bioavailability: f.bioavailability,
        shelf_life_days: f.shelf_life_days,
        storage_temp_min: f.storage_temp_min,
        storage_temp_max: f.storage_temp_max,
        notes: f.notes,
      });
      const st = await fertApi.fetchFertilizerStocks(key);
      setStocks(st);
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

  const stockColumns: Column<FertilizerStock>[] = [
    {
      id: 'volume',
      label: t('pages.fertilizers.currentVolume'),
      render: (r) => `${r.current_volume_ml} ml`,
      align: 'right',
      searchValue: (r) => String(r.current_volume_ml),
    },
    {
      id: 'purchase_date',
      label: t('pages.fertilizers.purchaseDate'),
      render: (r) => r.purchase_date ? new Date(r.purchase_date).toLocaleDateString() : '-',
    },
    {
      id: 'expiry_date',
      label: t('pages.fertilizers.expiryDate'),
      render: (r) => r.expiry_date ? new Date(r.expiry_date).toLocaleDateString() : '-',
    },
    {
      id: 'batch_number',
      label: t('pages.fertilizers.batchNumber'),
      render: (r) => r.batch_number || '-',
    },
    {
      id: 'cost',
      label: t('pages.fertilizers.costPerLiter'),
      render: (r) => r.cost_per_liter != null ? `${r.cost_per_liter.toFixed(2)} EUR/L` : '-',
      align: 'right',
      searchValue: (r) => r.cost_per_liter != null ? String(r.cost_per_liter) : '',
    },
  ];

  if (loading) return <LoadingSkeleton variant="form" />;
  if (error) return <ErrorDisplay error={error} />;
  if (!fertilizer) return <ErrorDisplay error={t('errors.notFound')} />;

  return (
    <Box data-testid="fertilizer-detail-page">
      <UnsavedChangesGuard dirty={isDirty} />
      <Box
        sx={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          mb: 2,
        }}
      >
        <PageTitle title={fertilizer.product_name} />
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
        <Tab label={t('pages.fertilizers.tabDetails')} />
        <Tab label={t('pages.fertilizers.tabStock')} />
        <Tab label={t('common.edit')} />
      </Tabs>

      {/* Tab 0: Details */}
      {tab === 0 && (
        <Box>
          <Card sx={{ mb: 2 }}>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                {t('pages.fertilizers.tabDetails')}
              </Typography>
              <Table size="small" aria-label={t('pages.fertilizers.tabDetails')}>
                <TableBody>
                  <TableRow>
                    <TableCell component="th">{t('pages.fertilizers.productName')}</TableCell>
                    <TableCell>{fertilizer.product_name}</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell component="th">{t('pages.fertilizers.brand')}</TableCell>
                    <TableCell>{fertilizer.brand || '-'}</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell component="th">{t('pages.fertilizers.fertilizerType')}</TableCell>
                    <TableCell>{t(`enums.fertilizerType.${fertilizer.fertilizer_type}`)}</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell component="th">NPK</TableCell>
                    <TableCell>
                      {fertilizer.npk_ratio[0]}-{fertilizer.npk_ratio[1]}-{fertilizer.npk_ratio[2]}
                    </TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell component="th">{t('pages.fertilizers.ecContribution')}</TableCell>
                    <TableCell>{fertilizer.ec_contribution_per_ml.toFixed(3)} mS/ml</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell component="th">{t('pages.fertilizers.phEffect')}</TableCell>
                    <TableCell>{t(`enums.phEffect.${fertilizer.ph_effect}`)}</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell component="th">{t('pages.fertilizers.mixingPriority')}</TableCell>
                    <TableCell>{fertilizer.mixing_priority}</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell component="th">{t('pages.fertilizers.recommendedApplication')}</TableCell>
                    <TableCell>{t(`enums.applicationMethod.${fertilizer.recommended_application}`)}</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell component="th">{t('pages.fertilizers.bioavailability')}</TableCell>
                    <TableCell>{t(`enums.bioavailability.${fertilizer.bioavailability}`)}</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell component="th">{t('pages.fertilizers.badges')}</TableCell>
                    <TableCell>
                      {fertilizer.is_organic && (
                        <Chip label={t('pages.fertilizers.isOrganic')} size="small" color="success" sx={{ mr: 0.5 }} />
                      )}
                      {fertilizer.tank_safe && (
                        <Chip label={t('pages.fertilizers.tankSafe')} size="small" color="info" sx={{ mr: 0.5 }} />
                      )}
                    </TableCell>
                  </TableRow>
                  {fertilizer.notes && (
                    <TableRow>
                      <TableCell component="th">{t('pages.fertilizers.notes')}</TableCell>
                      <TableCell>{fertilizer.notes}</TableCell>
                    </TableRow>
                  )}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </Box>
      )}

      {/* Tab 1: Stock */}
      {tab === 1 && (
        <Box>
          <DataTable
            columns={stockColumns}
            rows={stocks}
            getRowKey={(r) => r.key}
            tableState={stocksTableState}
            variant="simple"
            ariaLabel={t('pages.fertilizers.tabStock')}
          />
        </Box>
      )}

      {/* Tab 2: Edit */}
      {tab === 2 && (
        <Card>
          <CardContent>
            <form onSubmit={handleSubmit(onSave)}>
              <FormTextField
                name="product_name"
                control={control}
                label={t('pages.fertilizers.productName')}
                required
              />
              <FormTextField
                name="brand"
                control={control}
                label={t('pages.fertilizers.brand')}
              />
              <FormSelectField
                name="fertilizer_type"
                control={control}
                label={t('pages.fertilizers.fertilizerType')}
                options={fertilizerTypes.map((v) => ({
                  value: v,
                  label: t(`enums.fertilizerType.${v}`),
                }))}
              />
              <FormSwitchField
                name="is_organic"
                control={control}
                label={t('pages.fertilizers.isOrganic')}
              />
              <FormSwitchField
                name="tank_safe"
                control={control}
                label={t('pages.fertilizers.tankSafe')}
              />
              <FormNumberField
                name="npk_n"
                control={control}
                label={t('pages.fertilizers.npkN')}
                min={0}
              />
              <FormNumberField
                name="npk_p"
                control={control}
                label={t('pages.fertilizers.npkP')}
                min={0}
              />
              <FormNumberField
                name="npk_k"
                control={control}
                label={t('pages.fertilizers.npkK')}
                min={0}
              />
              <FormNumberField
                name="ec_contribution_per_ml"
                control={control}
                label={t('pages.fertilizers.ecContribution')}
                min={0}
              />
              <FormNumberField
                name="mixing_priority"
                control={control}
                label={t('pages.fertilizers.mixingPriority')}
                min={1}
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
              <FormNumberField
                name="shelf_life_days"
                control={control}
                label={t('pages.fertilizers.shelfLifeDays')}
                min={1}
              />
              <FormNumberField
                name="storage_temp_min"
                control={control}
                label={t('pages.fertilizers.storageTempMin')}
              />
              <FormNumberField
                name="storage_temp_max"
                control={control}
                label={t('pages.fertilizers.storageTempMax')}
              />
              <FormTextField
                name="notes"
                control={control}
                label={t('pages.fertilizers.notes')}
                multiline
                rows={3}
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
        message={t('common.deleteConfirm', { name: fertilizer.product_name })}
        onConfirm={onDelete}
        onCancel={() => setDeleteOpen(false)}
      />
    </Box>
  );
}
