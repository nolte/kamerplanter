import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import IconButton from '@mui/material/IconButton';
import Paper from '@mui/material/Paper';
import Typography from '@mui/material/Typography';
import { useTheme } from '@mui/material/styles';
import CloseIcon from '@mui/icons-material/Close';
import type { CompanionEdgeWire } from '../api/companionEdges';
import { COMPANION_LINE_STYLES, COMPANION_SPECIES_CAP, companionInk } from '../renderer/companionLines';

/**
 * The info card of one companion line (REQ-053 GP-FR-134): status in words, the two species that decided it, the
 * reason and the score. Opened by hovering a line (transient) or by tapping it (pinned, with a close button and Esc).
 * Its own chunk (UI-NFR-003). The card stops its own pointer and key events, so pressing it never starts a gesture
 * on the plan below.
 */
const PREFIX = 'pages.gardenPlan.editor.companion';
const CARD_WIDTH_PX = 280;
const CARD_HEIGHT_PX = 190;
const GAP_PX = 12;

interface Props {
  edge: CompanionEdgeWire;
  /** The line's midpoint on screen; the card sits next to it, inside the canvas. */
  x: number;
  y: number;
  canvasWidthPx: number;
  canvasHeightPx: number;
  /** A tapped line keeps its card until it is closed; a hovered one closes when the pointer leaves. */
  pinned: boolean;
  onClose: () => void;
}

function clamp(value: number, min: number, max: number): number {
  return Math.max(min, Math.min(value, Math.max(min, max)));
}

export default function CompanionEdgeInfo({ edge, x, y, canvasWidthPx, canvasHeightPx, pinned, onClose }: Props) {
  const { t, i18n } = useTranslation();
  const theme = useTheme();
  const format = new Intl.NumberFormat(i18n.resolvedLanguage ?? i18n.language, { maximumFractionDigits: 2 });
  const { deciding } = edge;
  const names = deciding
    ? {
        a: deciding.species_a_name ?? t(`${PREFIX}.unnamedSpecies`),
        b: deciding.species_b_name ?? t(`${PREFIX}.unnamedSpecies`),
      }
    : null;
  const left = clamp(x + GAP_PX, GAP_PX / 2, canvasWidthPx - CARD_WIDTH_PX - GAP_PX / 2);
  const top = clamp(y + GAP_PX, GAP_PX / 2, canvasHeightPx - CARD_HEIGHT_PX - GAP_PX / 2);
  const style = COMPANION_LINE_STYLES[edge.status];
  const ink = companionInk(theme, edge.status);
  return (
    <Paper
      elevation={4}
      role="status"
      data-testid="garden-plan-companion-info"
      data-companion-status={edge.status}
      onPointerDown={(event) => event.stopPropagation()}
      onClick={(event) => event.stopPropagation()}
      onKeyDown={(event) => {
        event.stopPropagation();
        if (event.key === 'Escape') onClose();
      }}
      sx={{
        position: 'absolute',
        left,
        top,
        width: CARD_WIDTH_PX,
        maxWidth: 'calc(100% - 12px)',
        p: 1.5,
        zIndex: 2,
        pointerEvents: pinned ? 'auto' : 'none',
      }}
    >
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
        <svg width={28} height={12} aria-hidden="true" focusable="false">
          <line
            x1={2}
            y1={6}
            x2={26}
            y2={6}
            stroke={ink}
            strokeWidth={style.widthPx}
            strokeDasharray={style.dash}
            strokeLinecap="round"
          />
        </svg>
        <Typography variant="subtitle2" component="p" sx={{ flexGrow: 1 }}>
          {t(`${PREFIX}.status.${edge.status}`)}
        </Typography>
        {pinned ? (
          <IconButton
            size="small"
            onClick={onClose}
            aria-label={t(`${PREFIX}.close`)}
            sx={{ minWidth: 44, minHeight: 44, mr: -1, my: -1 }}
            data-testid="garden-plan-companion-info-close"
          >
            <CloseIcon fontSize="small" />
          </IconButton>
        ) : null}
      </Box>
      {names ? (
        <Typography variant="body2" data-testid="garden-plan-companion-info-pair">
          {t(`${PREFIX}.pair`, { a: names.a, b: names.b })}
        </Typography>
      ) : null}
      <Typography variant="body2" color="text.secondary" data-testid="garden-plan-companion-info-reason">
        {edge.reason
          ? t(`${PREFIX}.reason`, { reason: edge.reason })
          : t(`${PREFIX}.reasonCode.${edge.status}`)}
      </Typography>
      {edge.score !== null ? (
        <Typography variant="body2" data-testid="garden-plan-companion-info-score">
          {t(`${PREFIX}.score`, { score: format.format(edge.score) })}
        </Typography>
      ) : null}
      {edge.distance_cm !== null ? (
        <Typography variant="body2" color="text.secondary">
          {t(`${PREFIX}.distance`, { distance: format.format(edge.distance_cm) })}
        </Typography>
      ) : null}
      {edge.slot_a.species_truncated || edge.slot_b.species_truncated ? (
        <Typography variant="caption" color="text.secondary" component="p" data-testid="garden-plan-companion-info-truncated">
          {t(`${PREFIX}.speciesTruncated`, { count: COMPANION_SPECIES_CAP })}
        </Typography>
      ) : null}
    </Paper>
  );
}
