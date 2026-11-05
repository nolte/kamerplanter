/**
 * The companion-planting part of the plan's layer legend (REQ-053 GP-FR-134): per status the line as the plan draws
 * it (same dash, same colour) and the words. Its own chunk (UI-NFR-003), loaded when the layer goes on.
 */
import { useId, useState } from 'react';
import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Typography from '@mui/material/Typography';
import { useTheme } from '@mui/material/styles';
import type { CompanionPairItem } from '../api/companionEdges';
import { COMPANION_LINE_CAP, COMPANION_LINE_STYLES, COMPANION_STATUSES, companionInk } from '../renderer/companionLines';

const PREFIX = 'pages.gardenPlan.editor.zones.legend';
const CARD = 'pages.gardenPlan.editor.companion';
const SWATCH_W = 40;
const SWATCH_H = 20;

interface Props {
  /** More lines were in view than the plan draws (the 500-line cap) or a bed answered only part of its pairs. */
  capped: boolean;
  /** The pairs of the lines in view, incompatible first. */
  pairs: readonly CompanionPairItem[];
}

const NUMBER_FORMAT_DIGITS = 2;

/**
 * The text twin of the lines (WCAG 2.1.1, 1.1.1): the lines are not focusable (up to 500 tab stops) and hidden for
 * assistive technology, so every pair in view is also listed here as a sentence - status as words, the two species,
 * the reason and the score. It is rendered only while the disclosure is open, and the list is one scroll region that
 * takes the keyboard focus once, not one stop per pair.
 */
function CompanionPairList({ pairs }: { pairs: readonly CompanionPairItem[] }) {
  const { t, i18n } = useTranslation();
  const format = new Intl.NumberFormat(i18n.resolvedLanguage ?? i18n.language, {
    maximumFractionDigits: NUMBER_FORMAT_DIGITS,
  });
  const unnamed = t(`${CARD}.unnamedSpecies`);
  return (
    <Box
      component="ul"
      tabIndex={0}
      aria-label={t(`${PREFIX}.companionList.label`, { count: pairs.length })}
      data-testid="garden-plan-legend-companion-list"
      sx={{ listStyle: 'none', m: 0, mt: 1, p: 0, maxHeight: 240, overflowY: 'auto', maxWidth: 480 }}
    >
      {pairs.map(({ id, edge }) => {
        const a = edge.deciding?.species_a_name ?? unnamed;
        const b = edge.deciding?.species_b_name ?? unnamed;
        const detail = edge.reason
          ? t(`${CARD}.reason`, { reason: edge.reason })
          : t(`${CARD}.reasonCode.${edge.status}`);
        return (
          <Box component="li" key={id} data-legend-companion-pair={edge.status} sx={{ py: 0.5 }}>
            <Typography variant="body2" component="span">
              {t(`${CARD}.listItem`, { status: t(`${CARD}.status.${edge.status}`), pair: t(`${CARD}.pair`, { a, b }), detail })}
              {edge.score !== null ? ` ${t(`${CARD}.score`, { score: format.format(edge.score) })}` : ''}
            </Typography>
          </Box>
        );
      })}
    </Box>
  );
}

export default function CompanionLegendSection({ capped, pairs }: Props) {
  const { t } = useTranslation();
  const [listOpen, setListOpen] = useState(false);
  const listId = useId();
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
      <Button
        size="small"
        onClick={() => setListOpen((open) => !open)}
        aria-expanded={listOpen}
        aria-controls={listId}
        data-testid="garden-plan-legend-companion-list-toggle"
        sx={{ minHeight: 44, alignSelf: 'flex-start' }}
      >
        {t(`${PREFIX}.companionList.${listOpen ? 'hide' : 'show'}`, { count: pairs.length })}
      </Button>
      <Box id={listId}>
        {listOpen ? (
          pairs.length > 0 ? (
            <CompanionPairList pairs={pairs} />
          ) : (
            <Typography variant="body2" color="text.secondary" data-testid="garden-plan-legend-companion-list-empty">
              {t(`${PREFIX}.companionList.empty`)}
            </Typography>
          )
        ) : null}
      </Box>
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
