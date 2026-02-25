import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Typography from '@mui/material/Typography';
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
import FormTextField from '@/components/form/FormTextField';
import FormSelectField from '@/components/form/FormSelectField';
import FormNumberField from '@/components/form/FormNumberField';
import FormChipInput from '@/components/form/FormChipInput';
import FormActions from '@/components/form/FormActions';
import UnsavedChangesGuard from '@/components/form/UnsavedChangesGuard';
import CultivarListSection from './CultivarListSection';
import LifecycleConfigSection from '@/pages/pflanzen/LifecycleConfigSection';
import { useNotification } from '@/hooks/useNotification';
import { useApiError } from '@/hooks/useApiError';
import { useAppDispatch, useAppSelector } from '@/store/hooks';
import { fetchSpecies, clearCurrent } from '@/store/slices/speciesSlice';
import * as api from '@/api/endpoints/species';
import * as familiesApi from '@/api/endpoints/botanicalFamilies';
import type { BotanicalFamily } from '@/api/types';

const schema = z.object({
  scientific_name: z.string().min(1),
  common_names: z.array(z.string()),
  family_key: z.string().nullable(),
  genus: z.string(),
  growth_habit: z.enum(['herb', 'shrub', 'tree', 'vine', 'groundcover']),
  root_type: z.enum(['fibrous', 'taproot', 'tuberous', 'bulbous']),
  hardiness_zones: z.array(z.string()),
  native_habitat: z.string(),
  allelopathy_score: z.number().min(-1).max(1),
  base_temp: z.number(),
  description: z.string(),
  synonyms: z.array(z.string()),
  taxonomic_authority: z.string(),
  taxonomic_status: z.string(),
});

type FormData = z.infer<typeof schema>;

export default function SpeciesDetailPage() {
  const { key } = useParams<{ key: string }>();
  const { t } = useTranslation();
  const dispatch = useAppDispatch();
  const navigate = useNavigate();
  const notification = useNotification();
  const { handleError } = useApiError();
  const { current, loading, error } = useAppSelector((s) => s.species);
  const [saving, setSaving] = useState(false);
  const [deleteOpen, setDeleteOpen] = useState(false);
  const [tab, setTab] = useState(0);
  const [families, setFamilies] = useState<BotanicalFamily[]>([]);

  const {
    control,
    handleSubmit,
    reset,
    formState: { isDirty },
  } = useForm<FormData>({
    resolver: zodResolver(schema),
    defaultValues: {
      scientific_name: '',
      common_names: [],
      family_key: null,
      genus: '',
      growth_habit: 'herb',
      root_type: 'fibrous',
      hardiness_zones: [],
      native_habitat: '',
      allelopathy_score: 0,
      base_temp: 10,
      description: '',
      synonyms: [],
      taxonomic_authority: '',
      taxonomic_status: '',
    },
  });

  useEffect(() => {
    if (key) dispatch(fetchSpecies(key));
    familiesApi.listBotanicalFamilies().then(setFamilies).catch(() => {});
    return () => { dispatch(clearCurrent()); };
  }, [key, dispatch]);

  useEffect(() => {
    if (current) {
      reset({
        scientific_name: current.scientific_name,
        common_names: current.common_names,
        family_key: current.family_key,
        genus: current.genus,
        growth_habit: current.growth_habit,
        root_type: current.root_type,
        hardiness_zones: current.hardiness_zones,
        native_habitat: current.native_habitat,
        allelopathy_score: current.allelopathy_score,
        base_temp: current.base_temp,
        description: current.description ?? '',
        synonyms: current.synonyms ?? [],
        taxonomic_authority: current.taxonomic_authority ?? '',
        taxonomic_status: current.taxonomic_status ?? '',
      });
    }
  }, [current, reset]);

  const onSubmit = async (data: FormData) => {
    if (!key) return;
    try {
      setSaving(true);
      await api.updateSpecies(key, data);
      notification.success(t('common.save'));
      dispatch(fetchSpecies(key));
    } catch (err) {
      handleError(err);
    } finally {
      setSaving(false);
    }
  };

  const onDelete = async () => {
    if (!key) return;
    try {
      await api.deleteSpecies(key);
      notification.success(t('common.delete'));
      navigate('/stammdaten/species');
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
        <PageTitle title={current?.scientific_name ?? t('entities.species')} />
        <Button color="error" startIcon={<DeleteIcon />} onClick={() => setDeleteOpen(true)}>
          {t('common.delete')}
        </Button>
      </Box>

      <Tabs value={tab} onChange={(_, v) => setTab(v)} sx={{ mb: 3 }}>
        <Tab label={t('common.edit')} />
        <Tab label={t('pages.cultivars.title')} />
        <Tab label={t('pages.lifecycle.title')} />
      </Tabs>

      {tab === 0 && (
        <Box component="form" onSubmit={handleSubmit(onSubmit)} sx={{ maxWidth: 600 }}>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
            {t('pages.species.editIntro')}
          </Typography>
          <FormTextField
            name="scientific_name"
            control={control}
            label={t('pages.species.scientificName')}
            helperText={t('pages.species.scientificNameHelper')}
            required
          />
          <FormChipInput
            name="common_names"
            control={control}
            label={t('pages.species.commonNames')}
            helperText={t('pages.species.commonNamesHelper')}
          />
          <FormSelectField
            name="family_key"
            control={control}
            label={t('pages.species.family')}
            helperText={t('pages.species.familyHelper')}
            options={[
              { value: '', label: '-' },
              ...families.map((f) => ({ value: f.key, label: f.name })),
            ]}
          />
          <FormTextField
            name="genus"
            control={control}
            label={t('pages.species.genus')}
            helperText={t('pages.species.genusHelper')}
          />
          <FormTextField
            name="description"
            control={control}
            label={t('pages.species.description')}
            helperText={t('pages.species.descriptionHelper')}
            multiline
            rows={3}
          />
          <FormSelectField
            name="growth_habit"
            control={control}
            label={t('pages.species.growthHabit')}
            helperText={t('pages.species.growthHabitHelper')}
            options={['herb', 'shrub', 'tree', 'vine', 'groundcover'].map((v) => ({
              value: v,
              label: t(`enums.growthHabit.${v}`),
            }))}
          />
          <FormSelectField
            name="root_type"
            control={control}
            label={t('pages.species.rootType')}
            helperText={t('pages.species.rootTypeHelper')}
            options={['fibrous', 'taproot', 'tuberous', 'bulbous'].map((v) => ({
              value: v,
              label: t(`enums.rootType.${v}`),
            }))}
          />
          <FormChipInput
            name="hardiness_zones"
            control={control}
            label={t('pages.species.hardinessZones')}
            helperText={t('pages.species.hardinessZonesHelper')}
          />
          <FormTextField
            name="native_habitat"
            control={control}
            label={t('pages.species.nativeHabitat')}
            helperText={t('pages.species.nativeHabitatHelper')}
          />
          <FormNumberField
            name="allelopathy_score"
            control={control}
            label={t('pages.species.allelopathyScore')}
            helperText={t('pages.species.allelopathyScoreHelper')}
            min={-1}
            max={1}
            step={0.1}
          />
          <FormNumberField
            name="base_temp"
            control={control}
            label={t('pages.species.baseTemp')}
            helperText={t('pages.species.baseTempHelper')}
          />
          <FormChipInput
            name="synonyms"
            control={control}
            label={t('pages.species.synonyms')}
            helperText={t('pages.species.synonymsHelper')}
          />
          <FormTextField
            name="taxonomic_authority"
            control={control}
            label={t('pages.species.taxonomicAuthority')}
            helperText={t('pages.species.taxonomicAuthorityHelper')}
          />
          <FormTextField
            name="taxonomic_status"
            control={control}
            label={t('pages.species.taxonomicStatus')}
            helperText={t('pages.species.taxonomicStatusHelper')}
          />
          <FormActions onCancel={() => navigate(-1)} loading={saving} />
        </Box>
      )}

      {tab === 1 && key && <CultivarListSection speciesKey={key} />}
      {tab === 2 && key && <LifecycleConfigSection speciesKey={key} />}

      <ConfirmDialog
        open={deleteOpen}
        title={t('common.delete')}
        message={t('common.deleteConfirm', { name: current?.scientific_name })}
        onConfirm={onDelete}
        onCancel={() => setDeleteOpen(false)}
        destructive
      />
    </>
  );
}
