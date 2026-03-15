import { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import Dialog from '@mui/material/Dialog';
import DialogTitle from '@mui/material/DialogTitle';
import DialogContent from '@mui/material/DialogContent';
import Typography from '@mui/material/Typography';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import FormTextField from '@/components/form/FormTextField';
import FormSelectField from '@/components/form/FormSelectField';
import FormNumberField from '@/components/form/FormNumberField';
import FormChipInput from '@/components/form/FormChipInput';
import FormSwitchField from '@/components/form/FormSwitchField';
import FormActions from '@/components/form/FormActions';
import FormRow from '@/components/form/FormRow';
import ExpertiseFieldWrapper from '@/components/common/ExpertiseFieldWrapper';
import ShowAllFieldsToggle from '@/components/common/ShowAllFieldsToggle';
import { useExpertiseLevel } from '@/hooks/useExpertiseLevel';
import { useNotification } from '@/hooks/useNotification';
import { useApiError } from '@/hooks/useApiError';
import { speciesFieldConfig } from '@/config/fieldConfigs';
import * as speciesApi from '@/api/endpoints/species';
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
  container_suitable: z.enum(['yes', 'limited', 'no', '']).nullable(),
  recommended_container_volume_l: z.string(),
  min_container_depth_cm: z.number().min(1).max(200).nullable(),
  mature_height_cm: z.string(),
  mature_width_cm: z.string(),
  spacing_cm: z.string(),
  indoor_suitable: z.enum(['yes', 'limited', 'no', '']).nullable(),
  balcony_suitable: z.enum(['yes', 'limited', 'no', '']).nullable(),
  greenhouse_recommended: z.boolean(),
  support_required: z.boolean(),
});

type FormData = z.infer<typeof schema>;

interface Props {
  open: boolean;
  onClose: () => void;
  onCreated: () => void;
}

export default function SpeciesCreateDialog({ open, onClose, onCreated }: Props) {
  const { t } = useTranslation();
  const notification = useNotification();
  const { handleError } = useApiError();
  const [saving, setSaving] = useState(false);
  const [families, setFamilies] = useState<BotanicalFamily[]>([]);
  const { showAllOverride, toggleShowAll, level } = useExpertiseLevel();

  const { control, handleSubmit, reset } = useForm<FormData>({
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
      container_suitable: null,
      recommended_container_volume_l: '',
      min_container_depth_cm: null,
      mature_height_cm: '',
      mature_width_cm: '',
      spacing_cm: '',
      indoor_suitable: null,
      balcony_suitable: null,
      greenhouse_recommended: false,
      support_required: false,
    },
  });

  useEffect(() => {
    if (open) {
      familiesApi.listBotanicalFamilies().then(setFamilies).catch(() => {});
    }
  }, [open]);

  const onSubmit = async (data: FormData) => {
    try {
      setSaving(true);
      const payload = {
        ...data,
        container_suitable: data.container_suitable || null,
        indoor_suitable: data.indoor_suitable || null,
        balcony_suitable: data.balcony_suitable || null,
      };
      await speciesApi.createSpecies(payload);
      notification.success(t('common.create'));
      reset();
      onCreated();
    } catch (err) {
      handleError(err);
    } finally {
      setSaving(false);
    }
  };

  const fc = speciesFieldConfig;

  return (
    <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth data-testid="create-dialog">
      <DialogTitle>{t('pages.species.create')}</DialogTitle>
      <DialogContent>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
          {t('pages.species.createIntro')}
        </Typography>
        <form onSubmit={handleSubmit(onSubmit)}>
          {/* --- Taxonomy section --- */}
          <Typography variant="subtitle2" color="text.secondary" sx={{ mb: 1, mt: 2 }}>
            {t('pages.species.sectionTaxonomy')}
          </Typography>
          <ExpertiseFieldWrapper minLevel={fc.scientific_name.level}>
            <FormTextField
              name="scientific_name"
              control={control}
              label={t('pages.species.scientificName')}
              helperText={t('pages.species.scientificNameHelper')}
              required
            />
          </ExpertiseFieldWrapper>
          <ExpertiseFieldWrapper minLevel={fc.common_names.level}>
            <FormChipInput
              name="common_names"
              control={control}
              label={t('pages.species.commonNames')}
              helperText={t('pages.species.commonNamesHelper')}
            />
          </ExpertiseFieldWrapper>
          <ExpertiseFieldWrapper minLevel={fc.family_key.level}>
            <FormSelectField
              name="family_key"
              control={control}
              label={t('pages.species.family')}
              helperText={t('pages.species.familyHelper')}
              options={[
                { value: '', label: '\u2014' },
                ...families.map((f) => ({ value: f.key, label: f.name })),
              ]}
            />
          </ExpertiseFieldWrapper>
          <ExpertiseFieldWrapper minLevel={fc.genus.level}>
            <FormTextField
              name="genus"
              control={control}
              label={t('pages.species.genus')}
              helperText={t('pages.species.genusHelper')}
            />
          </ExpertiseFieldWrapper>
          <ExpertiseFieldWrapper minLevel={fc.description.level}>
            <FormTextField
              name="description"
              control={control}
              label={t('pages.species.description')}
              helperText={t('pages.species.descriptionHelper')}
              multiline
              rows={3}
            />
          </ExpertiseFieldWrapper>

          {/* --- Growth section --- */}
          <Typography variant="subtitle2" color="text.secondary" sx={{ mb: 1, mt: 2 }}>
            {t('pages.species.sectionGrowth')}
          </Typography>
          <ExpertiseFieldWrapper minLevel={fc.growth_habit.level}>
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
          </ExpertiseFieldWrapper>
          <ExpertiseFieldWrapper minLevel={fc.root_type.level}>
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
          </ExpertiseFieldWrapper>

          {/* --- Environment section --- */}
          <Typography variant="subtitle2" color="text.secondary" sx={{ mb: 1, mt: 2 }}>
            {t('pages.species.sectionEnvironment')}
          </Typography>
          <ExpertiseFieldWrapper minLevel={fc.hardiness_zones.level}>
            <FormChipInput
              name="hardiness_zones"
              control={control}
              label={t('pages.species.hardinessZones')}
              helperText={t('pages.species.hardinessZonesHelper')}
            />
          </ExpertiseFieldWrapper>
          <ExpertiseFieldWrapper minLevel={fc.native_habitat.level}>
            <FormTextField
              name="native_habitat"
              control={control}
              label={t('pages.species.nativeHabitat')}
              helperText={t('pages.species.nativeHabitatHelper')}
            />
          </ExpertiseFieldWrapper>
          <ExpertiseFieldWrapper minLevel={fc.allelopathy_score.level}>
            <FormNumberField
              name="allelopathy_score"
              control={control}
              label={t('pages.species.allelopathyScore')}
              helperText={t('pages.species.allelopathyScoreHelper')}
              min={-1}
              max={1}
              step={0.1}
            />
          </ExpertiseFieldWrapper>
          <ExpertiseFieldWrapper minLevel={fc.base_temp.level}>
            <FormNumberField
              name="base_temp"
              control={control}
              label={t('pages.species.baseTemp')}
              helperText={t('pages.species.baseTempHelper')}
            />
          </ExpertiseFieldWrapper>

          {/* --- Classification section --- */}
          <Typography variant="subtitle2" color="text.secondary" sx={{ mb: 1, mt: 2 }}>
            {t('pages.species.sectionClassification')}
          </Typography>
          <ExpertiseFieldWrapper minLevel={fc.synonyms.level}>
            <FormChipInput
              name="synonyms"
              control={control}
              label={t('pages.species.synonyms')}
              helperText={t('pages.species.synonymsHelper')}
            />
          </ExpertiseFieldWrapper>
          <ExpertiseFieldWrapper minLevel={fc.taxonomic_authority.level}>
            <FormTextField
              name="taxonomic_authority"
              control={control}
              label={t('pages.species.taxonomicAuthority')}
              helperText={t('pages.species.taxonomicAuthorityHelper')}
            />
          </ExpertiseFieldWrapper>
          <ExpertiseFieldWrapper minLevel={fc.taxonomic_status.level}>
            <FormTextField
              name="taxonomic_status"
              control={control}
              label={t('pages.species.taxonomicStatus')}
              helperText={t('pages.species.taxonomicStatusHelper')}
            />
          </ExpertiseFieldWrapper>

          {/* --- Cultivation conditions section --- */}
          <Typography variant="subtitle2" color="text.secondary" sx={{ mb: 1, mt: 2 }}>
            {t('pages.species.sectionCultivation')}
          </Typography>
          <ExpertiseFieldWrapper minLevel={fc.container_suitable.level}>
            <FormRow>
              <FormSelectField
                name="container_suitable"
                control={control}
                label={t('pages.species.containerSuitable')}
                helperText={t('pages.species.containerSuitableHelper')}
                options={[
                  { value: '', label: '\u2014' },
                  ...['yes', 'limited', 'no'].map((v) => ({
                    value: v,
                    label: t(`enums.suitability.${v}`),
                  })),
                ]}
              />
              <FormSelectField
                name="indoor_suitable"
                control={control}
                label={t('pages.species.indoorSuitable')}
                helperText={t('pages.species.indoorSuitableHelper')}
                options={[
                  { value: '', label: '\u2014' },
                  ...['yes', 'limited', 'no'].map((v) => ({
                    value: v,
                    label: t(`enums.suitability.${v}`),
                  })),
                ]}
              />
            </FormRow>
          </ExpertiseFieldWrapper>
          <ExpertiseFieldWrapper minLevel={fc.balcony_suitable.level}>
            <FormSelectField
              name="balcony_suitable"
              control={control}
              label={t('pages.species.balconySuitable')}
              helperText={t('pages.species.balconySuitableHelper')}
              options={[
                { value: '', label: '\u2014' },
                ...['yes', 'limited', 'no'].map((v) => ({
                  value: v,
                  label: t(`enums.suitability.${v}`),
                })),
              ]}
            />
          </ExpertiseFieldWrapper>
          <ExpertiseFieldWrapper minLevel={fc.recommended_container_volume_l.level}>
            <FormRow>
              <FormTextField
                name="recommended_container_volume_l"
                control={control}
                label={t('pages.species.recommendedContainerVolumeL')}
                helperText={t('pages.species.recommendedContainerVolumeLHelper')}
              />
              <FormNumberField
                name="min_container_depth_cm"
                control={control}
                label={t('pages.species.minContainerDepthCm')}
                helperText={t('pages.species.minContainerDepthCmHelper')}
                min={1}
                max={200}
              />
            </FormRow>
          </ExpertiseFieldWrapper>
          <ExpertiseFieldWrapper minLevel={fc.mature_height_cm.level}>
            <FormRow>
              <FormTextField
                name="mature_height_cm"
                control={control}
                label={t('pages.species.matureHeightCm')}
                helperText={t('pages.species.matureHeightCmHelper')}
              />
              <FormTextField
                name="mature_width_cm"
                control={control}
                label={t('pages.species.matureWidthCm')}
                helperText={t('pages.species.matureWidthCmHelper')}
              />
            </FormRow>
          </ExpertiseFieldWrapper>
          <ExpertiseFieldWrapper minLevel={fc.spacing_cm.level}>
            <FormTextField
              name="spacing_cm"
              control={control}
              label={t('pages.species.spacingCm')}
              helperText={t('pages.species.spacingCmHelper')}
            />
          </ExpertiseFieldWrapper>
          <ExpertiseFieldWrapper minLevel={fc.greenhouse_recommended.level}>
            <FormRow>
              <FormSwitchField
                name="greenhouse_recommended"
                control={control}
                label={t('pages.species.greenhouseRecommended')}
                helperText={t('pages.species.greenhouseRecommendedHelper')}
              />
              <FormSwitchField
                name="support_required"
                control={control}
                label={t('pages.species.supportRequired')}
                helperText={t('pages.species.supportRequiredHelper')}
              />
            </FormRow>
          </ExpertiseFieldWrapper>

          {level !== 'expert' && (
            <ShowAllFieldsToggle showAll={showAllOverride} onToggle={toggleShowAll} />
          )}
          <FormActions onCancel={onClose} loading={saving} saveLabel={t('common.create')} />
        </form>
      </DialogContent>
    </Dialog>
  );
}
