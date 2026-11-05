/**
 * The companion-planting part of the plan's layer legend (REQ-053 GP-FR-134): per status the line as the plan draws
 * it (same dash, same colour) and the words. Its own chunk (UI-NFR-003), loaded when the layer goes on.
 */
import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import { useTheme } from '@mui/material/styles';
import { COMPANION_LINE_CAP, COMPANION_LINE_STYLES, COMPANION_STATUSES, companionInk } from '../renderer/companionLines';

const PREFIX = 'pages.gardenPlan.editor.zones.legend';
const SWATCH_W = 40;
const SWATCH_H = 20;

interface Props {
  /** More lines were in view than the plan draws (the 500-line cap) or a bed answered only part of its pairs. */
  capped: boolean;
}

export default function CompanionLegendSection({ capped }: Props) {
  const { t } = useTranslation();
  const theme = useTheme();
  return (
    <>
      <Box component="ul" sx={{ listStyle: 'none', m: 0, p: 0 }}>
        {COMPANION_STATUSES.map((status) => {
          const style = COMPANION_LINE_STYLES[status];
          return (
            <Box
              component="li"
              key={status}
              data-legend-companion={status}
              sx={{ display: 'flex', alignItems: 'center', gap: 1, minHeight: 28 }}
            >
              <svg width={SWATCH_W} height={SWATCH_H} aria-hidden="true" focusable="false">
                <line
                  x1={4}
                  y1={SWATCH_H / 2}
                  x2={SWATCH_W - 4}
                  y2={SWATCH_H / 2}
                  stroke={companionInk(theme, status)}
                  strokeWidth={style.widthPx}
                  strokeDasharray={style.dash}
                  strokeLinecap="round"
                />
              </svg>
              <Typography variant="body2">{t(`${PREFIX}.companion.${status}`)}</Typography>
            </Box>
          );
        })}
      </Box>
      <Typography variant="caption" color="text.secondary" component="p" sx={{ maxWidth: 360 }}>
        {t(`${PREFIX}.companionNote`)}
      </Typography>
      {capped ? (
        <Typography
          variant="caption"
          color="text.secondary"
          component="p"
          sx={{ maxWidth: 360 }}
          data-testid="garden-plan-legend-companion-capped"
        >
          {t(`${PREFIX}.companionCapped`, { count: COMPANION_LINE_CAP })}
        </Typography>
      ) : null}
    </>
  );
}
