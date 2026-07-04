import { useTranslation } from 'react-i18next';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import Typography from '@mui/material/Typography';
import { type Control } from 'react-hook-form';
import ExpertiseFieldWrapper from '@/components/common/ExpertiseFieldWrapper';
import FormSelectField from '@/components/form/FormSelectField';
import FormTextField from '@/components/form/FormTextField';
import FormNumberField from '@/components/form/FormNumberField';
import FormSwitchField from '@/components/form/FormSwitchField';
import FormRow from '@/components/form/FormRow';
import type { NutrientPlan } from '@/api/types';
import {
  HARVEST_PATTERNS,
  HARVESTED_PARTS,
  CLIMACTERIC_CLASSES,
  type SpeciesFormData,
} from './speciesDetailSchema';

interface SpeciesCultivationPanelProps {
  control: Control<SpeciesFormData>;
  nutrientPlans: NutrientPlan[];
}

/**
 * Cultivation panel of the species edit form (UI-NFR-008 R-058): container/site
 * suitability, harvest properties (REQ-007/008), growth flags and expert sizing
 * details. Full-width below the master-detail grid because the expert expansion
 * makes it tall.
 */
export default function SpeciesCultivationPanel({
  control,
  nutrientPlans,
}: SpeciesCultivationPanelProps) {
  const { t } = useTranslation();

  return (
    <Card variant="outlined">
      <CardContent
        component="fieldset"
        sx={{ border: 'none', p: 0, m: 0, '&:last-child': { pb: 2 }, px: 2, pt: 2 }}
      >
        <Typography component="legend" variant="h6" sx={{ pt: 1.5, mb: 2 }}>
          {t('pages.species.sectionCultivation')}
        </Typography>
        <FormRow>
          <FormSelectField
            name="container_suitable"
            control={control}
            label={t('pages.species.containerSuitable')}
            helperText={t('pages.species.containerSuitableHelper')}
            options={[
              { value: '', label: '—' },
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
              { value: '', label: '—' },
              ...['yes', 'limited', 'no'].map((v) => ({
                value: v,
                label: t(`enums.suitability.${v}`),
              })),
            ]}
          />
        </FormRow>
        <FormRow>
          <FormSelectField
            name="balcony_suitable"
            control={control}
            label={t('pages.species.balconySuitable')}
            helperText={t('pages.species.balconySuitableHelper')}
            options={[
              { value: '', label: '—' },
              ...['yes', 'limited', 'no'].map((v) => ({
                value: v,
                label: t(`enums.suitability.${v}`),
              })),
            ]}
          />
          <FormSelectField
            name="default_nutrient_plan_key"
            control={control}
            label={t('pages.species.defaultNutrientPlan')}
            helperText={t('pages.species.defaultNutrientPlanHelper')}
            options={[
              { value: '', label: '—' },
              ...nutrientPlans.map((p) => ({
                value: p.key,
                label: `${p.name}${p.is_template ? ` (${t('pages.nutrientPlans.isTemplate')})` : ''}`,
              })),
            ]}
          />
        </FormRow>
        {/* Phase A harvest properties (REQ-007/008). intermediate: pattern + part;
          expert: climacteric ripening class. Empty select → null on submit. */}
        <FormRow>
          <ExpertiseFieldWrapper minLevel="intermediate">
            <FormSelectField
              name="harvest_pattern"
              control={control}
              label={t('pages.species.harvestPattern')}
              helperText={t('pages.species.harvestPatternHelper')}
              options={[
                { value: '', label: '—' },
                ...HARVEST_PATTERNS.map((v) => ({
                  value: v,
                  label: t(`enums.harvestPattern.${v}`),
                })),
              ]}
            />
          </ExpertiseFieldWrapper>
          <ExpertiseFieldWrapper minLevel="intermediate">
            <FormSelectField
              name="harvested_part"
              control={control}
              label={t('pages.species.harvestedPart')}
              helperText={t('pages.species.harvestedPartHelper')}
              options={[
                { value: '', label: '—' },
                ...HARVESTED_PARTS.map((v) => ({
                  value: v,
                  label: t(`enums.harvestedPart.${v}`),
                })),
              ]}
            />
          </ExpertiseFieldWrapper>
        </FormRow>
        <ExpertiseFieldWrapper minLevel="expert">
          <FormRow>
            <FormSelectField
              name="climacteric"
              control={control}
              label={t('pages.species.climacteric')}
              helperText={t('pages.species.climactericHelper')}
              options={[
                { value: '', label: '—' },
                ...CLIMACTERIC_CLASSES.map((v) => ({
                  value: v,
                  label: t(`enums.climacteric.${v}`),
                })),
              ]}
            />
          </FormRow>
        </ExpertiseFieldWrapper>
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

        {/* Expert: Sizing & spacing details */}
        <ExpertiseFieldWrapper minLevel="expert">
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
          <FormRow>
            <FormTextField
              name="spacing_cm"
              control={control}
              label={t('pages.species.spacingCm')}
              helperText={t('pages.species.spacingCmHelper')}
            />
          </FormRow>
        </ExpertiseFieldWrapper>
      </CardContent>
    </Card>
  );
}
