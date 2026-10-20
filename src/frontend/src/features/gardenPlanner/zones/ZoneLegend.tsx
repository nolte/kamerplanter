import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import { useTheme } from '@mui/material/styles';
import { WATERED_CLASSES } from './lastWatered';
import { WATERED_PATTERNS, WateredPatternTile, ZONE_VARIANTS } from '../renderer/ZoneOverlays';
import type { PlanZone } from './zoneTypes';

const PREFIX = 'pages.gardenPlan.editor.zones';
const SWATCH_W = 32;
const SWATCH_H = 20;

interface Props {
  zones: readonly PlanZone[];
  showZones: boolean;
  showLastWatered: boolean;
}

/**
 * The legend of the two layers (GP-FR-031): every entry pairs a swatch with TEXT - the swatch shows the pattern the
 * layer uses, the words say what it means, so the legend works without seeing colour (WCAG 1.4.1).
 */
export function ZoneLegend({ zones, showZones, showLastWatered }: Props) {
  const { t } = useTranslation();
  const theme = useTheme();
  if (!showZones && !showLastWatered) return null;
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
    </Box>
  );
}
