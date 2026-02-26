import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Typography from '@mui/material/Typography';
import DeleteIcon from '@mui/icons-material/Delete';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import PageTitle from '@/components/layout/PageTitle';
import LoadingSkeleton from '@/components/common/LoadingSkeleton';
import ErrorDisplay from '@/components/common/ErrorDisplay';
import ConfirmDialog from '@/components/common/ConfirmDialog';
import FormTextField from '@/components/form/FormTextField';
import FormNumberField from '@/components/form/FormNumberField';
import FormChipInput from '@/components/form/FormChipInput';
import FormActions from '@/components/form/FormActions';
import UnsavedChangesGuard from '@/components/form/UnsavedChangesGuard';
import { useNotification } from '@/hooks/useNotification';
import { useApiError } from '@/hooks/useApiError';
import * as api from '@/api/endpoints/species';
import type { Cultivar, CultivarCreate, PlantTrait } from '@/api/types';

const schema = z.object({
  name: z.string().min(1),
  breeder: z.string().nullable(),
  breeding_year: z.number().nullable(),
  traits: z.array(z.string()),
  patent_status: z.string(),
  days_to_maturity: z.number().min(1).max(365).nullable(),
  disease_resistances: z.array(z.string()),
});

type FormData = z.infer<typeof schema>;

export default function CultivarDetailPage() {
  const { speciesKey, cultivarKey } = useParams<{ speciesKey: string; cultivarKey: string }>();
  const { t } = useTranslation();
  const navigate = useNavigate();
  const notification = useNotification();
  const { handleError } = useApiError();
  const [cultivar, setCultivar] = useState<Cultivar | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [deleteOpen, setDeleteOpen] = useState(false);

  const {
    control,
    handleSubmit,
    reset,
    formState: { isDirty },
  } = useForm<FormData>({
    resolver: zodResolver(schema),
    defaultValues: {
      name: '',
      breeder: null,
      breeding_year: null,
      traits: [],
      patent_status: '',
      days_to_maturity: null,
      disease_resistances: [],
    },
  });

  const load = async () => {
    if (!speciesKey || !cultivarKey) return;
    setLoading(true);
    try {
      const c = await api.getCultivar(speciesKey, cultivarKey);
      setCultivar(c);
      reset({
        name: c.name,
        breeder: c.breeder,
        breeding_year: c.breeding_year,
        traits: c.traits,
        patent_status: c.patent_status,
        days_to_maturity: c.days_to_maturity,
        disease_resistances: c.disease_resistances,
      });
    } catch (err) {
      setError(String(err));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, [speciesKey, cultivarKey]); // eslint-disable-line react-hooks/exhaustive-deps

  const onSubmit = async (data: FormData) => {
    if (!speciesKey || !cultivarKey) return;
    try {
      setSaving(true);
      await api.updateCultivar(speciesKey, cultivarKey, {
        ...data,
        traits: data.traits as PlantTrait[],
      } as Omit<CultivarCreate, 'species_key'>);
      notification.success(t('common.save'));
      load();
    } catch (err) {
      handleError(err);
    } finally {
      setSaving(false);
    }
  };

  const onDelete = async () => {
    if (!speciesKey || !cultivarKey) return;
    try {
      await api.deleteCultivar(speciesKey, cultivarKey);
      notification.success(t('common.delete'));
      navigate(`/stammdaten/species/${speciesKey}`);
    } catch (err) {
      handleError(err);
    }
    setDeleteOpen(false);
  };

  if (loading) return <LoadingSkeleton variant="form" />;
  if (error) return <ErrorDisplay error={error} onRetry={() => navigate(-1)} />;

  return (
    <>
      <UnsavedChangesGuard dirty={isDirty} />
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <PageTitle title={cultivar?.name ?? t('entities.cultivar')} />
        <Button color="error" startIcon={<DeleteIcon />} onClick={() => setDeleteOpen(true)}>
          {t('common.delete')}
        </Button>
      </Box>

      <Box component="form" onSubmit={handleSubmit(onSubmit)} sx={{ maxWidth: 600 }}>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
          {t('pages.cultivars.editIntro')}
        </Typography>
        <FormTextField name="name" control={control} label={t('pages.cultivars.name')} helperText={t('pages.cultivars.nameHelper')} required />
        <FormTextField name="breeder" control={control} label={t('pages.cultivars.breeder')} helperText={t('pages.cultivars.breederHelper')} />
        <FormNumberField name="breeding_year" control={control} label={t('pages.cultivars.breedingYear')} helperText={t('pages.cultivars.breedingYearHelper')} />
        <FormChipInput name="traits" control={control} label={t('pages.cultivars.traits')} helperText={t('pages.cultivars.traitsHelper')} />
        <FormTextField name="patent_status" control={control} label={t('pages.cultivars.patentStatus')} helperText={t('pages.cultivars.patentStatusHelper')} />
        <FormNumberField name="days_to_maturity" control={control} label={t('pages.cultivars.daysToMaturity')} helperText={t('pages.cultivars.daysToMaturityHelper')} min={1} max={365} />
        <FormChipInput name="disease_resistances" control={control} label={t('pages.cultivars.diseaseResistances')} helperText={t('pages.cultivars.diseaseResistancesHelper')} />
        <FormActions onCancel={() => navigate(-1)} loading={saving} />
      </Box>

      <ConfirmDialog
        open={deleteOpen}
        title={t('common.delete')}
        message={t('common.deleteConfirm', { name: cultivar?.name })}
        onConfirm={onDelete}
        onCancel={() => setDeleteOpen(false)}
        destructive
      />
    </>
  );
}
