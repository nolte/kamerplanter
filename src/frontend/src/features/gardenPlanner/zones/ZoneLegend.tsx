import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import { useTheme } from '@mui/material/styles';
import { WATERED_CLASSES } from './lastWatered';
import { WATERED_PATTERNS, WateredPatternTile, ZONE_VARIANTS } from '../renderer/ZoneOverlays';
import {
  CONDITION_SPECS,
  ConditionGlyph,
  ConditionPatternTile,
  conditionInk,
  type ConditionLayerId,
  type ConditionSpec,
} from '../renderer/ConditionOverlays';
import type { PlanZone } from './zoneTypes';

const PREFIX = 'pages.gardenPlan.editor.zones';
const SWATCH_W = 32;
const SWATCH_H = 20;
const CONDITION_SWATCH_W = 48;
const CONDITION_PATTERN_W = 28;
const GLYPH_SIZE = 16;

/** The enum whose labels word a condition layer's values. */
const CONDITION_ENUMS: Record<ConditionLayerId, string> = {
  sun: 'sunWindow',
  moisture: 'soilDrainage',
  frost: 'frostRisk',
};

interface Props {
  zones: readonly PlanZone[];
  showZones: boolean;
  showLastWatered: boolean;
  /** The site-condition layers (GP-FR-169); each adds its own section while it is on. */
  showSun?: boolean;
  showMoisture?: boolean;
  showFrost?: boolean;
}

/** One section of a site-condition layer: per value the pattern, the glyph and the words. */
function ConditionSection({ spec }: { spec: ConditionSpec<string> }) {
  const { t } = useTranslation();
  const theme = useTheme();
  const ink = conditionInk(theme, spec.tone);
  const enumName = CONDITION_ENUMS[spec.id];
  return (
    <Box data-testid={`garden-plan-legend-${spec.id}`}>
      <Typography variant="subtitle2" component="h4">
        {t(`${PREFIX}.legend.${spec.id}Title`)}
      </Typography>
      <Box component="ul" sx={{ listStyle: 'none', m: 0, p: 0 }}>
        {spec.values.map((value) => {
          const id = `gp-legend-${spec.id}-${value}`;
          return (
            <Box
              component="li"
              key={value}
              data-legend-value={value}
              sx={{ display: 'flex', alignItems: 'center', gap: 1, minHeight: 28 }}
            >
              <svg width={CONDITION_SWATCH_W} height={SWATCH_H} aria-hidden="true" focusable="false">
                <defs>
                  <pattern id={id} width="10" height="10" patternUnits="userSpaceOnUse">
                    <ConditionPatternTile kind={spec.patterns[value]} tile={10} line={1.4} color={ink} />
                  </pattern>
                </defs>
                <rect width={CONDITION_PATTERN_W} height={SWATCH_H} fill={`url(#${id})`} stroke={ink} />
                <ConditionGlyph
                  parts={spec.glyphs[value]}
                  x={CONDITION_SWATCH_W - GLYPH_SIZE - 2}
                  y={(SWATCH_H - GLYPH_SIZE) / 2}
                  size={GLYPH_SIZE}
                  color={ink}
                  backdrop={theme.palette.background.paper}
                  value={value}
                />
              </svg>
              <Typography variant="body2">{t(`enums.${enumName}.${value}`)}</Typography>
            </Box>
          );
        })}
      </Box>
      <Typography variant="caption" color="text.secondary" component="p">
        {t(`${PREFIX}.legend.conditionNone`)}
      </Typography>
    </Box>
  );
}

/**
 * The legend of the plan's layers (GP-FR-031): zones, "last watered" and the site-condition layers (GP-FR-169).
 * Every entry pairs a swatch with TEXT - the swatch shows the pattern (and, for the site conditions, the glyph) the
 * layer uses, the words say what it means, so the legend works without seeing colour (WCAG 1.4.1).
 */
export function ZoneLegend({
  zones,
  showZones,
  showLastWatered,
  showSun = false,
  showMoisture = false,
  showFrost = false,
}: Props) {
  const { t } = useTranslation();
  const theme = useTheme();
  const shownConditions: Record<ConditionLayerId, boolean> = { sun: showSun, moisture: showMoisture, frost: showFrost };
  const conditions = CONDITION_SPECS.filter((spec) => shownConditions[spec.id]);
  if (!showZones && !showLastWatered && conditions.length === 0) return null;
  const ink = theme.palette.mode === 'dark' ? theme.palette.info.light : theme.palette.info.dark;
  return (
    <Box
      component="section"
      aria-label={t(`${PREFIX}.legend.title`)}
      data-testid="garden-plan-layer-legend"
      sx={{ display: 'flex', flexWrap: 'wrap', gap: 3, p: 1, border: 1, borderColor: 'divider', borderRadius: 1 }}
    >
      {showZones && (
        <Box data-testid="garden-plan-legend-zones">
          <Typography variant="subtitle2" component="h4">
            {t(`${PREFIX}.legend.zonesTitle`)}
          </Typography>
          {zones.length === 0 ? (
            <Typography variant="body2" color="text.secondary">
              {t(`${PREFIX}.legend.zonesNone`)}
            </Typography>
          ) : (
            <Box component="ul" sx={{ listStyle: 'none', m: 0, p: 0 }}>
              {zones.map((zone, index) => {
                const variant = ZONE_VARIANTS[index % ZONE_VARIANTS.length];
                const id = `gp-legend-zone-${zone.key}`;
                return (
                  <Box component="li" key={zone.key} sx={{ display: 'flex', alignItems: 'center', gap: 1, minHeight: 28 }}>
                    <svg width={SWATCH_W} height={SWATCH_H} aria-hidden="true" focusable="false">
                      <defs>
                        <pattern id={id} width="8" height="8" patternUnits="userSpaceOnUse" patternTransform={`rotate(${variant.angle})`}>
                          <line x1="0" y1="0" x2="0" y2="8" stroke={zone.color} strokeWidth="1.6" />
                        </pattern>
                      </defs>
                      <rect width={SWATCH_W} height={SWATCH_H} fill={`url(#${id})`} />
                      <rect
                        x="1.5"
                        y="1.5"
                        width={SWATCH_W - 3}
                        height={SWATCH_H - 3}
                        fill="none"
                        stroke={zone.color}
                        strokeWidth="3"
                        strokeDasharray={variant.dash}
                      />
                    </svg>
                    <Typography variant="body2">
                      {t(`${PREFIX}.legend.zoneEntry`, {
                        number: index + 1,
                        name: zone.name,
                        type: t(`enums.irrigationType.${zone.irrigation_type}`),
                      })}
                    </Typography>
                  </Box>
                );
              })}
            </Box>
          )}
        </Box>
      )}
      {showLastWatered && (
        <Box data-testid="garden-plan-legend-watered">
          <Typography variant="subtitle2" component="h4">
            {t(`${PREFIX}.legend.wateredTitle`)}
          </Typography>
          <Box component="ul" sx={{ listStyle: 'none', m: 0, p: 0 }}>
            {WATERED_CLASSES.map((wateredClass) => (
              <Box component="li" key={wateredClass} sx={{ display: 'flex', alignItems: 'center', gap: 1, minHeight: 28 }}>
                <svg width={SWATCH_W} height={SWATCH_H} aria-hidden="true" focusable="false">
                  <defs>
                    <pattern id={`gp-legend-${wateredClass}`} width="10" height="10" patternUnits="userSpaceOnUse">
                      <WateredPatternTile kind={WATERED_PATTERNS[wateredClass]} tile={10} line={1.6} color={ink} />
                    </pattern>
                  </defs>
                  <rect width={SWATCH_W} height={SWATCH_H} fill={`url(#gp-legend-${wateredClass})`} stroke={ink} />
                </svg>
                <Typography variant="body2">{t(`${PREFIX}.legend.class.${wateredClass}`)}</Typography>
              </Box>
            ))}
          </Box>
          <Typography variant="caption" color="text.secondary" component="p">
            {t(`${PREFIX}.legend.wateredNone`)}
          </Typography>
          <Typography variant="caption" color="text.secondary" component="p" sx={{ maxWidth: 360 }}>
            {t(`${PREFIX}.legend.wateredNote`)}
          </Typography>
        </Box>
      )}
      {conditions.map((spec) => (
        <ConditionSection key={spec.id} spec={spec as ConditionSpec<string>} />
      ))}
    </Box>
  );
}
