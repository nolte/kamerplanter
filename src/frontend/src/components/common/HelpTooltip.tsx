import { useMemo, type MouseEvent, type ReactNode } from 'react';
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

  // Keep an activation of this trigger from reaching an ancestor link: a header
  // title carrying it (e.g. GenericWidget's `ipm_alerts` glossary icon) can sit
  // inside an ancestor navigation link (issue #439 panel-level CardActionArea).
  // Without this, tapping the tiny help icon would both toggle the tooltip *and*
  // fire the ancestor link's navigation — on touch devices the click reaches the
  // ancestor well before any touch-hold tooltip delay, so the help affordance
  // would silently stop working the moment it is nested inside a link.
  //
  // `preventDefault` next to `stopPropagation`, because stopping propagation
  // alone never delivered that. Measured on the dashboard, where the
  // `ipm_alerts` trigger really does sit inside `<a href="/pflanzenschutz/pests">`:
  // a click on the help icon navigated away — with the previous
  // `stopPropagation`-only version too, so the guard this comment describes has
  // been inert. Two independent routes get past propagation control: an <a>
  // follows its href as the *default action* of a click that merely passed
  // through it, and react-router's link handler runs off React's delegated root
  // listener. `defaultPrevented` closes both — the browser skips the default
  // navigation, and `useLinkClickHandler` returns early on an already-prevented
  // event.
  const swallowActivation = (e: MouseEvent<HTMLElement>) => {
    e.preventDefault();
    e.stopPropagation();
  };

  // A real <button>, not a span carrying `tabIndex` (#1290). A <span> maps to
  // the `generic` role, ARIA forbids naming a generic element, so the accessible
  // name was *discarded* — screen-reader users reached a focus stop with no name
  // at all. The button carries role, keyboard activation and focus handling
  // natively, which retires the tabIndex/role/keyboard trio the span had to
  // re-implement by hand.
  //
  // `type="button"` is load-bearing rather than boilerplate: several call sites
  // place this trigger next to a field inside a <form>, and a bare <button>
  // defaults to `type="submit"` — it would submit the form on every help click.
  //
  // WCAG 2.5.8 (Target Size Minimum) / UI-NFR-002: minWidth/minHeight guarantee
  // at least 24×24 px; the 18px icon plus 4px padding on each side renders at
  // ~26×26 px. The UA button styling (border, background, font) is reset so the
  // trigger looks exactly as the span did.
  const iconTrigger = (
    <Box
      component="button"
      type="button"
      onClick={swallowActivation}
      sx={{
        display: 'inline-flex',
        alignItems: 'center',
        justifyContent: 'center',
        minWidth: 24,
        minHeight: 24,
        p: '4px',
        m: 0,
        border: 0,
        background: 'none',
        color: 'inherit',
        font: 'inherit',
        lineHeight: 0,
        cursor: 'help',
      }}
      aria-label={t(`glossary.${term}.short`, { defaultValue: term })}
    >
      {icon}
    </Box>
  );

  const trigger = iconOnly ? (
    iconTrigger
  ) : (
    // The labelled variant keeps a plain <span> as the Tooltip anchor and moves
    // the focus stop onto the icon button inside it. Wrapping `children` in the
    // button instead would be wrong twice over: call sites pass block content —
    // `<Typography component="h2">` (VpdCalculatorCard) and
    // `<Typography component="legend">` (RecognitionStatusCard) — which a
    // <button> may not contain, its content model being phrasing only; and
    // burying a heading inside a button drops it out of the heading outline a
    // screen reader navigates by. The span keeps hover over the whole label
    // working, and focus still reaches the Tooltip because React's `onFocus` is
    // `focusin`, which bubbles up from the nested button.
    <Box
      component="span"
      onClick={swallowActivation}
      sx={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: 0.5,
        minHeight: 24,
        cursor: 'help',
      }}
    >
      {children}
      {iconTrigger}
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
