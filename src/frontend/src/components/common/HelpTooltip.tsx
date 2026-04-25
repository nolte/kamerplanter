import { useMemo, type ReactNode } from 'react';
import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import Tooltip from '@mui/material/Tooltip';
import Typography from '@mui/material/Typography';
import HelpOutlineIcon from '@mui/icons-material/HelpOutlined';
import { useExpertiseLevel } from '@/hooks/useExpertiseLevel';
import type { ExperienceLevel } from '@/api/types';

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

interface IconStyle {
  fontSize: number;
  color: string;
}

const ICON_STYLE: Record<ExperienceLevel, IconStyle> = {
  beginner: { fontSize: 16, color: 'primary.main' },
  intermediate: { fontSize: 14, color: 'text.secondary' },
  expert: { fontSize: 12, color: 'action.disabled' },
};

/** Returns true when the given i18n key resolves to a non-empty value. */
function hasKey(t: (k: string) => string, key: string): boolean {
  const value = t(key);
  return value !== key && value.trim().length > 0;
}

/**
 * UI-NFR-011 §4: contextual tooltip for domain terms.
 * - Reads short/long/beginnerTip/unit/typicalRange from i18n namespace `glossary.<term>.*`.
 * - Visual prominence of the trigger icon depends on the user's experience level (REQ-021).
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

  const iconStyle = ICON_STYLE[level];

  const icon = (
    <HelpOutlineIcon
      sx={{ fontSize: iconStyle.fontSize, color: iconStyle.color, verticalAlign: 'middle' }}
      data-testid={`help-tooltip-icon-${term}`}
    />
  );

  // The Tooltip needs a focusable / hoverable trigger. Box with tabIndex satisfies WCAG 2.1 AA.
  // WCAG 2.5.5 / UI-NFR-002: minimum touch-target of 24×24 px (32 px effective via padding)
  // even on the smallest expert-level icon.
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
