/**
 * The garden-planning thresholds of a site (REQ-053 GP-FR-164/166, WP 8.24): where the sun classes begin, the day
 * they refer to, how wide a bed may be before it is out of reach, and how close a path must come to a bed edge to
 * give access from that side (#2703). Part of the site edit form; the values feed the help texts of the sun tiles
 * and the `bed.reach_too_wide` hint. Nothing is computed from them beyond that.
 */
import { useTranslation } from 'react-i18next';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import Button from '@mui/material/Button';
import Typography from '@mui/material/Typography';
import type { Control } from 'react-hook-form';
import FormNumberField from '@/components/form/FormNumberField';
import FormRow from '@/components/form/FormRow';
import { MAX_PATH_ACCESS_DISTANCE_M, type SiteFormData } from './siteForm';

const PREFIX = 'pages.sites.thresholds';

interface SiteThresholdsSectionProps {
  control: Control<SiteFormData>;
  /** Puts the default thresholds back into the form (not saved until the form is). */
  onResetDefaults?: () => void;
}

export default function SiteThresholdsSection({ control, onResetDefaults }: SiteThresholdsSectionProps) {
  const { t } = useTranslation();
  const hours = t(`${PREFIX}.hoursUnit`);
  return (
    <Card variant="outlined" data-testid="site-thresholds-section">
      <CardContent component="fieldset" sx={{ border: 'none', p: 0, m: 0, '&:last-child': { pb: 2 }, px: 2, pt: 2 }}>
        <Typography component="legend" variant="h6" sx={{ pt: 1.5, mb: 0.5 }}>
          {t(`${PREFIX}.title`)}
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
          {t(`${PREFIX}.intro`)}
        </Typography>

        <Typography variant="subtitle2" component="h3" sx={{ mb: 0.5 }}>
          {t(`${PREFIX}.sunTitle`)}
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
          {t(`${PREFIX}.sunHint`)}
        </Typography>
        <FormRow>
          <FormNumberField
            name="sun_class_thresholds.full_sun_min_hours"
            control={control}
            label={t(`${PREFIX}.fullSun`)}
            helperText={t(`${PREFIX}.fullSunHelper`)}
            min={0}
            max={24}
            step="any"
            inputMode="decimal"
            suffix={hours}
            required
          />
          <FormNumberField
            name="sun_class_thresholds.partial_shade_min_hours"
            control={control}
            label={t(`${PREFIX}.partialShade`)}
            helperText={t(`${PREFIX}.partialShadeHelper`)}
            min={0}
            max={24}
            step="any"
            inputMode="decimal"
            suffix={hours}
            required
          />
          <FormNumberField
            name="sun_class_thresholds.shade_min_hours"
            control={control}
            label={t(`${PREFIX}.shade`)}
            helperText={t(`${PREFIX}.shadeHelper`)}
            min={0}
            max={24}
            step="any"
            inputMode="decimal"
            suffix={hours}
            required
          />
        </FormRow>
        <FormRow>
          <FormNumberField
            name="sun_class_thresholds.reference_day"
            control={control}
            label={t(`${PREFIX}.referenceDay`)}
            helperText={t(`${PREFIX}.referenceHelper`)}
            min={1}
            max={31}
            inputMode="numeric"
            required
          />
          <FormNumberField
            name="sun_class_thresholds.reference_month"
            control={control}
            label={t(`${PREFIX}.referenceMonth`)}
            helperText={t(`${PREFIX}.referenceMonthHelper`)}
            min={1}
            max={12}
            inputMode="numeric"
            required
          />
        </FormRow>

        <Typography variant="subtitle2" component="h3" sx={{ mt: 2, mb: 0.5 }}>
          {t(`${PREFIX}.reachTitle`)}
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
          {t(`${PREFIX}.reachHint`)}
        </Typography>
        <FormRow>
          <FormNumberField
            name="reach_thresholds.both_sides_m"
            control={control}
            label={t(`${PREFIX}.bothSides`)}
            helperText={t(`${PREFIX}.bothSidesHelper`)}
            min={0}
            step="any"
            inputMode="decimal"
            suffix="m"
            required
          />
          <FormNumberField
            name="reach_thresholds.one_side_m"
            control={control}
            label={t(`${PREFIX}.oneSide`)}
            helperText={t(`${PREFIX}.oneSideHelper`)}
            min={0}
            step="any"
            inputMode="decimal"
            suffix="m"
            required
          />
        </FormRow>
        <FormRow>
          <FormNumberField
            name="reach_thresholds.path_access_max_distance_m"
            control={control}
            label={t(`${PREFIX}.pathDistance`)}
            helperText={t(`${PREFIX}.pathDistanceHelper`)}
            min={0}
            max={MAX_PATH_ACCESS_DISTANCE_M}
            step="any"
            inputMode="decimal"
            suffix="m"
            required
          />
        </FormRow>
        {onResetDefaults && (
          <Button
            variant="text"
            onClick={onResetDefaults}
            sx={{ mt: 1, minHeight: 44 }}
            data-testid="site-thresholds-reset"
          >
            {t(`${PREFIX}.resetDefaults`)}
          </Button>
        )}
      </CardContent>
    </Card>
  );
}
