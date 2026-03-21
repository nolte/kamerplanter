import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import Button from '@mui/material/Button';
import IconButton from '@mui/material/IconButton';
import Tooltip from '@mui/material/Tooltip';
import DeleteIcon from '@mui/icons-material/Delete';
import AddIcon from '@mui/icons-material/Add';
import StarIcon from '@mui/icons-material/Star';
import StarBorderIcon from '@mui/icons-material/StarBorder';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import Alert from '@mui/material/Alert';
import { useLocalFavorites } from '@/hooks/useLocalFavorites';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import MobileCard from '@/components/common/MobileCard';
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
import FormRow from '@/components/form/FormRow';
import UnsavedChangesGuard from '@/components/form/UnsavedChangesGuard';
import BatchCreateDialog from './BatchCreateDialog';
import { useNotification } from '@/hooks/useNotification';
import { useApiError } from '@/hooks/useApiError';
import * as api from '@/api/endpoints/substrates';
import Chip from '@mui/material/Chip';
import type { Substrate, Batch, ReusabilityResponse } from '@/api/types';

const schema = z.object({
  type: z.enum(['soil', 'coco', 'clay_pebbles', 'perlite', 'living_soil', 'peat', 'rockwool_slab', 'rockwool_plug', 'vermiculite', 'none', 'orchid_bark', 'pon_mineral', 'sphagnum', 'hydro_solution']),
  brand: z.string().nullable(),
  name_de: z.string(),
  name_en: z.string(),
  ph_base: z.number().min(0).max(14),
  ec_base_ms: z.number().min(0),
  water_retention: z.enum(['low', 'medium', 'high']),
  air_porosity_percent: z.number().min(0).max(100),
  buffer_capacity: z.enum(['low', 'medium', 'high']),
  reusable: z.boolean(),
  max_reuse_cycles: z.number().min(1),
});

type FormData = z.infer<typeof schema>;

export default function SubstrateDetailPage() {
  const { key } = useParams<{ key: string }>();
  const { t, i18n } = useTranslation();
  const navigate = useNavigate();
  const notification = useNotification();
  const { handleError } = useApiError();
  const [substrate, setSubstrate] = useState<Substrate | null>(null);
  const [batches, setBatches] = useState<Batch[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [deleteOpen, setDeleteOpen] = useState(false);
  const [deleteBatchTarget, setDeleteBatchTarget] = useState<Batch | null>(null);
  const [batchCreateOpen, setBatchCreateOpen] = useState(false);
  const [reusability, setReusability] = useState<Record<string, ReusabilityResponse>>({});
  const [allSubstrates, setAllSubstrates] = useState<Substrate[]>([]);
  const { isFavorite, toggleFavorite } = useLocalFavorites('kamerplanter-substrate-favorites');
  const batchTableState = useTableLocalState({ defaultSort: { column: 'mixedOn', direction: 'desc' } });

  const {
    control,
    handleSubmit,
    reset,
    formState: { isDirty },
  } = useForm<FormData>({
    resolver: zodResolver(schema),
    defaultValues: {
      type: 'soil',
      brand: null,
      name_de: '',
      name_en: '',
      ph_base: 6.5,
      ec_base_ms: 0.5,
      water_retention: 'medium',
      air_porosity_percent: 25.0,
      buffer_capacity: 'medium',
      reusable: false,
      max_reuse_cycles: 3,
    },
  });

  const load = async () => {
    if (!key) return;
    setLoading(true);
    try {
      const s = await api.getSubstrate(key);
      setSubstrate(s);
      reset({
        type: s.type,
        brand: s.brand,
        name_de: s.name_de ?? '',
        name_en: s.name_en ?? '',
        ph_base: s.ph_base,
        ec_base_ms: s.ec_base_ms,
        water_retention: s.water_retention,
        air_porosity_percent: s.air_porosity_percent,
        buffer_capacity: s.buffer_capacity,
        reusable: s.reusable,
        max_reuse_cycles: s.max_reuse_cycles,
      });
      setBatches(await api.listBatches(key));
      if (s.is_mix && s.mix_components?.length) {
        api.listSubstrates(0, 200).then(setAllSubstrates).catch(() => {});
      }
    } catch (err) {
      setError(String(err));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, [key]); // eslint-disable-line react-hooks/exhaustive-deps

  const onSubmit = async (data: FormData) => {
    if (!key) return;
    try {
      setSaving(true);
      await api.updateSubstrate(key, data);
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
      await api.deleteSubstrate(key);
      notification.success(t('common.delete'));
      navigate('/standorte/substrates');
    } catch (err) {
      handleError(err);
    }
    setDeleteOpen(false);
  };

  const onDeleteBatch = async () => {
    if (!deleteBatchTarget) return;
    try {
      await api.deleteBatch(deleteBatchTarget.key);
      notification.success(t('common.delete'));
      load();
    } catch (err) {
      handleError(err);
    }
    setDeleteBatchTarget(null);
  };

  const checkReusability = async (batchKey: string) => {
    try {
      const result = await api.checkReusability(batchKey);
      setReusability((prev) => ({ ...prev, [batchKey]: result }));
      if (result.can_reuse) {
        notification.success(t('pages.substrates.checkReusability') + ': OK');
      } else {
        notification.warning(t('pages.substrates.checkReusability') + ': ' + result.treatments.join(', '));
      }
    } catch (err) {
      handleError(err);
    }
  };

  const batchColumns: Column<Batch>[] = [
    { id: 'batchId', label: t('pages.batches.batchId'), render: (r) => r.batch_id },
    { id: 'volume', label: t('pages.batches.volume'), render: (r) => `${r.volume_liters} L`, align: 'right' as const, searchValue: (r: Batch) => String(r.volume_liters) },
    { id: 'mixedOn', label: t('pages.batches.mixedOn'), render: (r) => r.mixed_on },
    { id: 'cycles', label: t('pages.batches.cyclesUsed'), render: (r) => r.cycles_used, align: 'right' as const },
    {
      id: 'actions',
      label: t('common.actions'),
      sortable: false,
      searchable: false,
      render: (r) => (
        <Box sx={{ display: 'flex', gap: 0.5 }}>
          <Button size="small" onClick={(e) => { e.stopPropagation(); checkReusability(r.key); }}>
            {t('pages.substrates.checkReusability')}
          </Button>
          <IconButton size="small" onClick={(e) => { e.stopPropagation(); setDeleteBatchTarget(r); }}>
            <DeleteIcon fontSize="small" />
          </IconButton>
        </Box>
      ),
    },
  ];

  if (loading) return <LoadingSkeleton variant="form" />;
  if (error) return <ErrorDisplay error={error} onRetry={() => navigate(-1)} />;

  const PANEL_GAP = 4;

  return (
    <Box data-testid="substrate-detail-page">
      <UnsavedChangesGuard dirty={isDirty} />
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <PageTitle title={substrate ? ((i18n.language?.startsWith('en') ? substrate.name_en : substrate.name_de) || `${t(`enums.substrateType.${substrate.type}`)} ${substrate.brand ?? ''}`) : t('entities.substrate')} />
          {key && (
            <Tooltip title={t('pages.plantInstances.substrateFavToggle')}>
              <IconButton
                onClick={() => toggleFavorite(key)}
                sx={{ color: isFavorite(key) ? 'warning.main' : 'action.disabled' }}
              >
                {isFavorite(key) ? <StarIcon /> : <StarBorderIcon />}
              </IconButton>
            </Tooltip>
          )}
        </Box>
        <Button color="error" startIcon={<DeleteIcon />} onClick={() => setDeleteOpen(true)}>
          {t('common.delete')}
        </Button>
      </Box>

      {substrate?.is_mix && substrate.mix_components?.length > 0 && (
        <Box sx={{ mb: 3, p: 2, borderRadius: 1, bgcolor: 'action.hover' }}>
          <Typography variant="subtitle2" color="text.secondary" sx={{ mb: 1 }}>
            {t('pages.substrates.mixComponents')}
          </Typography>
          <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
            {substrate.mix_components.map((comp) => {
              const compSub = allSubstrates.find((s) => s.key === comp.substrate_key);
              const label = compSub
                ? (i18n.language?.startsWith('en') ? compSub.name_en : compSub.name_de) || `${t(`enums.substrateType.${compSub.type}`)} ${compSub.brand ?? ''}`
                : comp.substrate_key;
              return (
                <Chip
                  key={comp.substrate_key}
                  label={`${label}: ${Math.round(comp.fraction * 100)}%`}
                  color="info"
                  variant="outlined"
                />
              );
            })}
          </Box>
        </Box>
      )}

      <Box component="form" onSubmit={handleSubmit(onSubmit)} sx={{ maxWidth: 900, display: 'flex', flexDirection: 'column', gap: PANEL_GAP }}>
        <Typography variant="body2" color="text.secondary">
          {t('pages.substrates.editIntro')}
        </Typography>

        <Card variant="outlined">
          <CardContent component="fieldset" sx={{ border: 'none', p: 0, m: 0, '&:last-child': { pb: 2 }, px: 2, pt: 2 }}>
            <Typography component="legend" variant="h6" sx={{ pt: 1.5, mb: 0.5 }}>
              {t('pages.substrates.sectionIdentification')}
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
              {t('pages.substrates.sectionIdentificationDesc')}
            </Typography>
            <FormRow>
              <FormSelectField
                name="type"
                control={control}
                label={t('pages.substrates.type')}
                helperText={t('pages.substrates.typeHelper')}
                autoFocus
                options={['soil', 'coco', 'clay_pebbles', 'perlite', 'living_soil', 'peat', 'rockwool_slab', 'rockwool_plug', 'vermiculite', 'none', 'orchid_bark', 'pon_mineral', 'sphagnum', 'hydro_solution'].map((v) => ({
                  value: v, label: t(`enums.substrateType.${v}`),
                }))}
              />
              <FormTextField name="brand" control={control} label={t('pages.substrates.brand')} helperText={t('pages.substrates.brandHelper')} />
            </FormRow>
            <FormRow>
              <FormTextField name="name_de" control={control} label={`${t('pages.substrates.name')} (DE)`} helperText={t('pages.substrates.nameHelper')} />
              <FormTextField name="name_en" control={control} label={`${t('pages.substrates.name')} (EN)`} helperText={t('pages.substrates.nameHelper')} />
            </FormRow>
          </CardContent>
        </Card>

        <Card variant="outlined">
          <CardContent component="fieldset" sx={{ border: 'none', p: 0, m: 0, '&:last-child': { pb: 2 }, px: 2, pt: 2 }}>
            <Typography component="legend" variant="h6" sx={{ pt: 1.5, mb: 0.5 }}>
              {t('pages.substrates.sectionChemistry')}
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
              {t('pages.substrates.sectionChemistryDesc')}
            </Typography>
            <Box sx={{ display: 'flex', gap: 2 }}>
              <FormNumberField name="ph_base" control={control} label={t('pages.substrates.phBase')} helperText={t('pages.substrates.phBaseHelper')} min={0} max={14} step={0.1} />
              <FormNumberField name="ec_base_ms" control={control} label={t('pages.substrates.ecBase')} helperText={t('pages.substrates.ecBaseHelper')} min={0} step={0.1} />
            </Box>
          </CardContent>
        </Card>

        <Card variant="outlined">
          <CardContent component="fieldset" sx={{ border: 'none', p: 0, m: 0, '&:last-child': { pb: 2 }, px: 2, pt: 2 }}>
            <Typography component="legend" variant="h6" sx={{ pt: 1.5, mb: 0.5 }}>
              {t('pages.substrates.sectionPhysical')}
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
              {t('pages.substrates.sectionPhysicalDesc')}
            </Typography>
            <FormRow>
              <FormSelectField
                name="water_retention"
                control={control}
                label={t('pages.substrates.waterRetention')}
                helperText={t('pages.substrates.waterRetentionHelper')}
                options={['low', 'medium', 'high'].map((v) => ({
                  value: v, label: t(`enums.waterRetention.${v}`),
                }))}
              />
              <FormNumberField name="air_porosity_percent" control={control} label={t('pages.substrates.airPorosity')} helperText={t('pages.substrates.airPorosityHelper')} min={0} max={100} step={1} />
            </FormRow>
            <FormSelectField
              name="buffer_capacity"
              control={control}
              label={t('pages.substrates.bufferCapacity')}
              helperText={t('pages.substrates.bufferCapacityHelper')}
              options={['low', 'medium', 'high'].map((v) => ({
                value: v, label: t(`enums.bufferCapacity.${v}`),
              }))}
            />
          </CardContent>
        </Card>

        <Card variant="outlined">
          <CardContent component="fieldset" sx={{ border: 'none', p: 0, m: 0, '&:last-child': { pb: 2 }, px: 2, pt: 2 }}>
            <Typography component="legend" variant="h6" sx={{ pt: 1.5, mb: 0.5 }}>
              {t('pages.substrates.sectionReuse')}
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
              {t('pages.substrates.sectionReuseDesc')}
            </Typography>
            <FormRow>
              <FormSwitchField name="reusable" control={control} label={t('pages.substrates.reusable')} helperText={t('pages.substrates.reusableHelper')} />
              <FormNumberField name="max_reuse_cycles" control={control} label={t('pages.substrates.maxReuseCycles')} helperText={t('pages.substrates.maxReuseCyclesHelper')} min={1} />
            </FormRow>
          </CardContent>
        </Card>

        <Typography variant="caption" color="text.secondary">* {t('common.required')}</Typography>
        <FormActions onCancel={() => navigate(-1)} loading={saving} />
      </Box>

      {Object.entries(reusability).map(([batchKey, result]) => (
        <Alert key={batchKey} severity={result.can_reuse ? 'success' : 'warning'} sx={{ mb: 1, mt: 2 }}>
          {result.can_reuse
            ? t('pages.substrates.reusabilityOk', { batch: batchKey })
            : t('pages.substrates.reusabilityRequired', { batch: batchKey, treatments: result.treatments.join(', ') })}
        </Alert>
      ))}

      <Box sx={{ mt: 4 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
          <Typography variant="h6">{t('pages.batches.title')}</Typography>
          <Button startIcon={<AddIcon />} onClick={() => setBatchCreateOpen(true)}>
            {t('pages.batches.create')}
          </Button>
        </Box>
        <DataTable
          columns={batchColumns}
          rows={batches}
          getRowKey={(r) => r.key}
          onRowClick={(r) => navigate(`/standorte/substrates/batches/${r.key}`)}
          tableState={batchTableState}
          ariaLabel={t('pages.batches.title')}
          mobileCardRenderer={(r) => (
            <MobileCard
              title={r.batch_id}
              subtitle={r.mixed_on}
              fields={[
                { label: t('pages.batches.volume'), value: `${r.volume_liters} L` },
                { label: t('pages.batches.cyclesUsed'), value: String(r.cycles_used) },
              ]}
            />
          )}
        />
      </Box>

      {key && (
        <BatchCreateDialog
          substrateKey={key}
          open={batchCreateOpen}
          onClose={() => setBatchCreateOpen(false)}
          onCreated={() => { setBatchCreateOpen(false); load(); } }
        />
      )}

      <ConfirmDialog
        open={deleteOpen}
        title={t('common.delete')}
        message={t('common.deleteConfirm', { name: substrate ? ((i18n.language?.startsWith('en') ? substrate.name_en : substrate.name_de) || `${t(`enums.substrateType.${substrate.type}`)} ${substrate.brand ?? ''}`) : '' })}
        onConfirm={onDelete}
        onCancel={() => setDeleteOpen(false)}
        destructive
      />

      <ConfirmDialog
        open={!!deleteBatchTarget}
        title={t('common.delete')}
        message={t('common.deleteConfirm', { name: deleteBatchTarget?.batch_id })}
        onConfirm={onDeleteBatch}
        onCancel={() => setDeleteBatchTarget(null)}
        destructive
      />
    </Box>
  );
}
