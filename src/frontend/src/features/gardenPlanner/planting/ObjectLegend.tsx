/**
 * The object legend of the tab "Ebenen" (REQ-053 GP-FR-180, GP-UX-005, WP 10.6): one entry per object class the plan
 * holds - garden objects and the indoor classes window, door, furniture and lamp alike - drawn with the fill and the
 * glyph the renderer uses (`objectTypeFill`, `OBJECT_ICON_PATHS`), so legend and plan cannot drift apart. Every
 * entry pairs the swatch with TEXT (the class and how many there are, and how many of them lie outside the property),
 * so it works without seeing colour (WCAG 1.4.1).
 */
import { useMemo } from 'react';
import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import { useTheme } from '@mui/material/styles';
import type { GardenObject, GardenObjectType } from '../model/types';
import { OBJECT_ICON_PATHS } from '../renderer/icons';
import { objectTypeFill, planPalette } from '../renderer/planDrawing';
import { OBJECT_TYPES } from '../editor/tools/objectTypes';

const PREFIX = 'pages.gardenPlan.editor.objectLegend';
const SWATCH = 24;

interface ObjectLegendProps {
  objects: Readonly<Record<string, GardenObject>>;
  /** The display name of a class ("Fenster"), the renderer's label. */
  objectTypeLabel: (type: GardenObjectType) => string;
}

interface LegendEntry {
  type: GardenObjectType;
  count: number;
  offSite: number;
}

/** The classes the plan holds, in the order of the object menu, with their counts. */
function legendEntries(objects: Readonly<Record<string, GardenObject>>): LegendEntry[] {
  const counts = new Map<GardenObjectType, LegendEntry>();
  for (const object of Object.values(objects)) {
    const entry = counts.get(object.object_type) ?? { type: object.object_type, count: 0, offSite: 0 };
    entry.count += 1;
    if (object.off_site) entry.offSite += 1;
    counts.set(object.object_type, entry);
  }
  return OBJECT_TYPES.flatMap((type) => counts.get(type) ?? []);
}

export default function ObjectLegend({ objects, objectTypeLabel }: ObjectLegendProps) {
  const { t } = useTranslation();
  const theme = useTheme();
  const palette = useMemo(() => planPalette(theme), [theme]);
  const entries = useMemo(() => legendEntries(objects), [objects]);
  return (
    <Box
      component="section"
      aria-labelledby="garden-plan-legend-objects-title"
      data-testid="garden-plan-legend-objects"
      sx={{ p: 1, border: 1, borderColor: 'divider', borderRadius: 1 }}
    >
      <Typography variant="subtitle2" component="h4" id="garden-plan-legend-objects-title">
        {t(`${PREFIX}.title`)}
      </Typography>
      {entries.length === 0 ? (
        <Typography variant="body2" color="text.secondary">
          {t(`${PREFIX}.none`)}
        </Typography>
      ) : (
        <Box component="ul" sx={{ listStyle: 'none', m: 0, p: 0 }}>
          {entries.map((entry) => (
            <Box
              component="li"
              key={entry.type}
              data-testid={`garden-plan-legend-object-${entry.type}`}
              sx={{ display: 'flex', alignItems: 'center', gap: 1, minHeight: 32 }}
            >
              <svg width={SWATCH} height={SWATCH} viewBox="0 0 24 24" aria-hidden="true" focusable="false">
                <rect
                  x="0.5"
                  y="0.5"
                  width="23"
                  height="23"
                  fill={objectTypeFill(entry.type, palette)}
                  stroke={palette.stroke}
                />
                <path
                  d={OBJECT_ICON_PATHS[entry.type]}
                  fill="none"
                  stroke={palette.text}
                  strokeWidth={2}
                  strokeLinecap="round"
                  strokeLinejoin="round"
                />
              </svg>
              <Typography variant="body2">
                {t(`${PREFIX}.entry`, { type: objectTypeLabel(entry.type), count: entry.count })}
                {entry.offSite > 0 ? ` ${t(`${PREFIX}.offSite`, { count: entry.offSite })}` : ''}
              </Typography>
            </Box>
          ))}
        </Box>
      )}
    </Box>
  );
}
