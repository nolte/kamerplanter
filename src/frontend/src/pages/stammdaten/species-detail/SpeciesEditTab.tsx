import type { FormEventHandler } from 'react';
import { useTranslation } from 'react-i18next';
import { Link as RouterLink } from 'react-router-dom';
import Box from '@mui/material/Box';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import Chip from '@mui/material/Chip';
import Link from '@mui/material/Link';
import Typography from '@mui/material/Typography';
import AccountTreeIcon from '@mui/icons-material/AccountTree';
import { type Control } from 'react-hook-form';
import ExpertiseFieldWrapper from '@/components/common/ExpertiseFieldWrapper';
import FormTextField from '@/components/form/FormTextField';
import FormSelectField from '@/components/form/FormSelectField';
import FormNumberField from '@/components/form/FormNumberField';
import FormChipInput from '@/components/form/FormChipInput';
import FormActions from '@/components/form/FormActions';
import FormRow from '@/components/form/FormRow';
import type { BotanicalFamily, NutrientPlan } from '@/api/types';
import SpeciesGrowthPanel from './SpeciesGrowthPanel';
import SpeciesCultivationPanel from './SpeciesCultivationPanel';
import {
  PANEL_GAP,
  FORM_MAX_WIDTH,
  READING_COL_MAX,
  type SpeciesFormData,
} from './speciesDetailSchema';

interface SpeciesEditTabProps {
  control: Control<SpeciesFormData>;
  /** Pre-bound react-hook-form submit handler (handleSubmit(onValid)). */
  onSubmit: FormEventHandler<HTMLFormElement>;
  families: BotanicalFamily[];
  nutrientPlans: NutrientPlan[];
  isReadOnly: boolean;
  saving: boolean;
  phaseSequenceKey: string | null;
  currentFamilyKey: string | null | undefined;
  onCancel: () => void;
}

/**
 * Species master-data edit form (REQ-001). Presentational RHF section — it owns
 * no data of its own; the parent supplies the `control`, option lists and the
 * bound submit handler. Composes the growth/cultivation sub-panels, which take
 * the same `control` prop.
 */
export default function SpeciesEditTab({
  control,
  onSubmit,
  families,
  nutrientPlans,
  isReadOnly,
  saving,
  phaseSequenceKey,
  currentFamilyKey,
  onCancel,
}: SpeciesEditTabProps) {
  const { t } = useTranslation();

  return (
    /* UI-NFR-018 R-027: when read-only the whole form must reject input,
      not just hide the save button. fieldset[disabled] grays out and
      disables every native form control beneath it (HTML5 spec). */
    <Box
      component="form"
      onSubmit={onSubmit}
      sx={{
        maxWidth: FORM_MAX_WIDTH,
        display: 'flex',
        flexDirection: 'column',
        gap: PANEL_GAP,
      }}
    >
      <Box
        component="fieldset"
        disabled={isReadOnly}
        sx={{
          border: 'none',
          p: 0,
          m: 0,
          minWidth: 0,
          display: 'flex',
          flexDirection: 'column',
          gap: PANEL_GAP,
        }}
      >
        <Box
          sx={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            flexWrap: 'wrap',
            gap: 1,
          }}
        >
          <Typography variant="body2" color="text.secondary">
            {t('pages.species.editIntro')}
          </Typography>
          {phaseSequenceKey && (
            <Chip
              component={RouterLink}
              to={`/phasen/ablaeufe/${phaseSequenceKey}`}
              icon={<AccountTreeIcon />}
              label={t('pages.phaseSequences.viewPhaseSequence')}
              clickable
              variant="outlined"
              size="small"
            />
          )}
        </Box>

        {/* QW-3 / UI-NFR-008 R-025: Required-field legend leads the form, so the
          meaning of the "*" marker is established before any required field. */}
        <Typography variant="caption" color="text.secondary">
          * {t('common.required')}
        </Typography>

        {/* UI-NFR-008 R-061: Master-detail layout — left column = reading-width prose
          panel (Taxonomy + Description), right column = stacked compact meta panels
          (Growth + Cultivation). On xs/sm everything stacks vertically. R-063: DOM
          order matches visual reading order (left-column first, then right-column). */}
        <Box
          sx={{
            display: 'grid',
            gridTemplateColumns: { xs: '1fr', md: `minmax(0, ${READING_COL_MAX}px) 1fr` },
            gap: PANEL_GAP,
            alignItems: 'start',
          }}
        >
          {/* ── Panel 1: Taxonomie (master column, reading-width) ── */}
          {/* UI-NFR-008 R-037/R-038/R-040: Card panel, h6 heading, required fields first */}
          <Card variant="outlined">
            <CardContent
              component="fieldset"
              sx={{ border: 'none', p: 0, m: 0, '&:last-child': { pb: 2 }, px: 2, pt: 2 }}
            >
              <Typography component="legend" variant="h6" sx={{ pt: 1.5, mb: 0.5 }}>
                {t('pages.species.sectionTaxonomy')}
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                {t('pages.species.sectionTaxonomyDesc')}
              </Typography>
              <FormTextField
                name="scientific_name"
                control={control}
                label={t('pages.species.scientificName')}
                helperText={t('pages.species.scientificNameHelper')}
                required
                autoFocus
              />
              <FormChipInput
                name="common_names"
                control={control}
                label={t('pages.species.commonNames')}
                helperText={t('pages.species.commonNamesHelper')}
              />
              <FormRow>
                <Box>
                  <FormSelectField
                    name="family_key"
                    control={control}
                    label={t('pages.species.family')}
                    helperText={t('pages.species.familyHelper')}
                    options={[
                      { value: '', label: '—' },
                      ...families.map((f) => ({ value: f.key, label: f.name })),
                    ]}
                  />
                  {currentFamilyKey && (
                    <Link
                      component={RouterLink}
                      to={`/stammdaten/botanical-families/${currentFamilyKey}`}
                      variant="body2"
                      sx={{ display: 'inline-block', mt: -1, mb: 1 }}
                    >
                      {t('pages.species.viewFamily')}
                    </Link>
                  )}
                </Box>
                <FormTextField
                  name="genus"
                  control={control}
                  label={t('pages.species.genus')}
                  helperText={t('pages.species.genusHelper')}
                />
              </FormRow>
              {/* UI-NFR-008 R-054 + R-055: prose field capped at reading width */}
              <Box sx={{ maxWidth: READING_COL_MAX }}>
                <FormTextField
                  name="description"
                  control={control}
                  label={t('pages.species.description')}
                  helperText={t('pages.species.descriptionHelper')}
                  multiline
                  minRows={4}
                  maxRows={14}
                />
              </Box>
            </CardContent>
          </Card>

          {/* ── Detail column: stacked compact panels (Growth + Cultivation) ── */}
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: PANEL_GAP }}>
            {/* ── Panel 2: Wachstum (compact, R-057) ── */}
            <SpeciesGrowthPanel control={control} />
          </Box>
        </Box>

        {/* ── Panel 3: Anbaubedingungen (full-width below master-detail, R-058) ── */}
        <SpeciesCultivationPanel control={control} nutrientPlans={nutrientPlans} />

        {/* ── Panel 4: Umgebung (expert) ── */}
        {/* UI-NFR-008 R-041: Expert-only panel hidden as a whole */}
        <ExpertiseFieldWrapper minLevel="expert">
          <Card variant="outlined">
            <CardContent
              component="fieldset"
              sx={{ border: 'none', p: 0, m: 0, '&:last-child': { pb: 2 }, px: 2, pt: 2 }}
            >
              <Typography component="legend" variant="h6" sx={{ pt: 1.5, mb: 2 }}>
                {t('pages.species.sectionEnvironment')}
              </Typography>
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
              <FormRow>
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
              </FormRow>
            </CardContent>
          </Card>
        </ExpertiseFieldWrapper>

        {/* ── Panel 5: Klassifikation (expert) ── */}
        {/* UI-NFR-008 R-041: Expert-only panel hidden as a whole */}
        <ExpertiseFieldWrapper minLevel="expert">
          <Card variant="outlined">
            <CardContent
              component="fieldset"
              sx={{ border: 'none', p: 0, m: 0, '&:last-child': { pb: 2 }, px: 2, pt: 2 }}
            >
              <Typography component="legend" variant="h6" sx={{ pt: 1.5, mb: 2 }}>
                {t('pages.species.sectionClassification')}
              </Typography>
              <FormChipInput
                name="synonyms"
                control={control}
                label={t('pages.species.synonyms')}
                helperText={t('pages.species.synonymsHelper')}
              />
              <FormRow>
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
              </FormRow>
            </CardContent>
          </Card>
        </ExpertiseFieldWrapper>

        {/* QW-4: the read-only watering guide moved to the Overview tab — the
          Edit form holds editable fields only (single source of edit). */}

        {/* UI-NFR-018 R-011: hide save/cancel actions for read-only system/enrichment data */}
        {!isReadOnly && <FormActions onCancel={onCancel} loading={saving} />}
        {isReadOnly && (
          <Typography variant="body2" color="text.secondary">
            {t('common.origin.readOnlyHint')}
          </Typography>
        )}
      </Box>
    </Box>
  );
}
