import { useMemo, type ReactNode } from 'react';
import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import Tooltip from '@mui/material/Tooltip';
import Typography from '@mui/material/Typography';
import HelpOutlineIcon from '@mui/icons-material/HelpOutlined';
import { useExpertiseLevel } from '@/hooks/useExpertiseLevel';

interface HelpTooltipProps {
  /** Glossary key (e.g. "vpd", "ec", "npk") — see UI-NFR-011 §3.2. */
  term: string;
  /** Element rendered next to the info icon (e.g. a field label or a header). */
  children?: ReactNode;
  /** Tooltip placement. Default: "top". */
  placement?: 'top' | 'bottom' | 'left' | 'right';
  /** When true the trigger is the icon alone — useful for table headers. */
  iconOnly?: boolean;
}

/**
 * Trigger-icon appearance. Deliberately constant across all experience levels:
 * the help affordance must stay clearly visible regardless of the active mode
 * (beginner/intermediate/expert). Only the *content* of the tooltip adapts to
 * the level — see `tooltipContent` below. Markenfarbe primary.main so the
 * question mark reads as an interactive help cue in both light and dark mode.
 */
const ICON_STYLE = { fontSize: 18, color: 'primary.main' } as const;

/** Returns true when the given i18n key resolves to a non-empty value. */
function hasKey(t: (k: string) => string, key: string): boolean {
  const value = t(key);
  return value !== key && value.trim().length > 0;
}

/**
 * UI-NFR-011 §4: contextual tooltip for domain terms.
 * - Reads short/long/beginnerTip/unit/typicalRange from i18n namespace `glossary.<term>.*`.
 * - The trigger icon looks the same in every experience level (see ICON_STYLE);
 *   only the tooltip *content* adapts to the level (REQ-021).
 * - Falls back to `term` itself if no glossary entry exists, so a missing key is visible
 *   in code review without crashing the UI.
 */
export default function HelpTooltip({
  term,
  children,
  placement = 'top',
  iconOnly,
}: HelpTooltipProps) {
  const { t } = useTranslation();
  const { level } = useExpertiseLevel();

  const tooltipContent = useMemo(() => {
    const shortKey = `glossary.${term}.short`;
    const longKey = `glossary.${term}.long`;
    const tipKey = `glossary.${term}.beginnerTip`;
    const unitKey = `glossary.${term}.unit`;
    const rangeKey = `glossary.${term}.typicalRange`;

    const short = hasKey(t, shortKey) ? t(shortKey) : term;
    const showLong = level !== 'beginner' && hasKey(t, longKey);
    const showTip = level === 'beginner' && hasKey(t, tipKey);
    const unit = hasKey(t, unitKey) ? t(unitKey) : null;
    const range = hasKey(t, rangeKey) ? t(rangeKey) : null;

    return (
      <Box sx={{ maxWidth: 320 }}>
        <Typography variant="body2" sx={{ fontWeight: 600, mb: showLong || showTip ? 0.5 : 0 }}>
          {short}
        </Typography>
        {showLong && (
          <Typography variant="body2" sx={{ mb: showTip ? 0.5 : 0 }}>
            {t(longKey)}
          </Typography>
        )}
        {showTip && (
          <Typography variant="body2" sx={{ fontStyle: 'italic' }}>
            {t(tipKey)}
          </Typography>
        )}
        {(unit ?? range) && (
          <Typography variant="caption" sx={{ display: 'block', mt: 0.5, opacity: 0.85 }}>
            {[unit && `${t('common.glossary.unit')}: ${unit}`, range && `${t('common.glossary.typical')}: ${range}`]
              .filter(Boolean)
              .join(' · ')}
          </Typography>
        )}
      </Box>
    );
  }, [term, level, t]);

  const icon = (
    <HelpOutlineIcon
      sx={{ fontSize: ICON_STYLE.fontSize, color: ICON_STYLE.color, verticalAlign: 'middle' }}
      data-testid={`help-tooltip-icon-${term}`}
    />
  );

  // The Tooltip needs a focusable / hoverable trigger. Box with tabIndex satisfies WCAG 2.1 AA.
  // WCAG 2.5.8 (Target Size Minimum) / UI-NFR-002: minWidth/minHeight guarantee at least
  // 24×24 px; the 18px icon plus 4px padding on each side actually renders at ~26×26 px,
  // comfortably above the floor even where the icon is used at its smallest size.
  const trigger = iconOnly ? (
    <Box
      component="span"
      tabIndex={0}
      sx={{
        display: 'inline-flex',
        alignItems: 'center',
        justifyContent: 'center',
        minWidth: 24,
        minHeight: 24,
        p: '4px',
        cursor: 'help',
      }}
      aria-label={t(`glossary.${term}.short`, { defaultValue: term })}
    >
      {icon}
    </Box>
  ) : (
    <Box
      component="span"
      tabIndex={0}
      sx={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: 0.5,
        minHeight: 24,
        cursor: 'help',
      }}
    >
      {children}
      {icon}
    </Box>
  );

  return (
    <Tooltip
      title={tooltipContent}
      placement={placement}
      arrow
      enterDelay={300}
      leaveDelay={100}
    >
      {trigger}
    </Tooltip>
  );
}
