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
import FormActions from '@/components/form/FormActions';
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
      await speciesApi.createSpecies(data);
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
          {/* intermediate fields (F-004: all Species fields are intermediate+) */}
          <ExpertiseFieldWrapper minLevel={fc.common_names.level}>
            <FormChipInput
              name="common_names"
              control={control}
              label={t('pages.species.commonNames')}
              helperText={t('pages.species.commonNamesHelper')}
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
          <ExpertiseFieldWrapper minLevel={fc.scientific_name.level}>
            <FormTextField
              name="scientific_name"
              control={control}
              label={t('pages.species.scientificName')}
              helperText={t('pages.species.scientificNameHelper')}
              required
            />
          </ExpertiseFieldWrapper>
          <ExpertiseFieldWrapper minLevel={fc.family_key.level}>
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
          </ExpertiseFieldWrapper>
          <ExpertiseFieldWrapper minLevel={fc.genus.level}>
            <FormTextField
              name="genus"
              control={control}
              label={t('pages.species.genus')}
              helperText={t('pages.species.genusHelper')}
            />
          </ExpertiseFieldWrapper>

          {/* expert fields */}
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

          {level !== 'expert' && (
            <ShowAllFieldsToggle showAll={showAllOverride} onToggle={toggleShowAll} />
          )}
          <FormActions onCancel={onClose} loading={saving} saveLabel={t('common.create')} />
        </form>
      </DialogContent>
    </Dialog>
  );
}
