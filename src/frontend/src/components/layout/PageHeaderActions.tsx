import { Fragment, type ReactNode, useState } from 'react';
import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Divider from '@mui/material/Divider';
import IconButton from '@mui/material/IconButton';
import ListItemIcon from '@mui/material/ListItemIcon';
import ListItemText from '@mui/material/ListItemText';
import Menu from '@mui/material/Menu';
import MenuItem from '@mui/material/MenuItem';
import Tooltip from '@mui/material/Tooltip';
import useMediaQuery from '@mui/material/useMediaQuery';
import { useTheme } from '@mui/material/styles';
import MoreVertIcon from '@mui/icons-material/MoreVert';

/**
 * One action in the page header.
 *
 * Declared as data rather than JSX because the same action has to render as a
 * button on `sm` and up, and as a menu entry on `xs` — a ready-made element
 * cannot be turned into a menu item.
 */
export interface HeaderAction {
  /** Menu label on `xs`; also the `aria-label` when rendered icon-only. */
  label: string;
  icon?: ReactNode;
  onClick: () => void;
  /** Render as an `IconButton` with tooltip instead of a labelled button (`sm`+). */
  iconOnly?: boolean;
  /** Toggle state: colours the control and marks the menu entry selected. */
  active?: boolean;
  variant?: 'text' | 'outlined' | 'contained';
  color?: 'inherit' | 'primary' | 'secondary' | 'success' | 'error' | 'info' | 'warning';
  disabled?: boolean;
  /**
   * Tooltip text when it differs from `label` — several pages explain *why* an
   * action is disabled ("in use", "system data"), which is not the same string
   * as the action's name. Falls back to `label` for icon-only actions, which
   * would otherwise carry no visible text at all.
   */
  tooltip?: string;
  testId?: string;
}

/**
 * Minimum hit area in px. UI-NFR-001 R-011 requires 48px and UI-NFR-021 R-022
 * repeats it for header buttons; MUI's default button height is 36px, so this
 * has to be set explicitly. Pages used to carry `sx={{ minHeight: 48 }}` by
 * hand — and most of them did not.
 */
const TOUCH_TARGET = 48;

/** Entries may be produced conditionally (`hasFavorites && {…}`). */
type MaybeAction = HeaderAction | false | null | undefined;

interface PageHeaderActionsProps {
  /**
   * The primary action (G1). Stays directly visible at every breakpoint and
   * never moves into the overflow menu — UI-NFR-021 R-017.
   */
  primary?: HeaderAction;
  /** Secondary and utility actions (G2/G3); collapse into `⋮` on `xs`. */
  secondary?: MaybeAction[];
  /** Escape hatch for controls that bring their own rendering (e.g. `PrintButton`). */
  extra?: ReactNode;
}

function renderButton(action: HeaderAction, keyPrefix: string) {
  const key = `${keyPrefix}-${action.label}`;
  const testId = action.testId ? { 'data-testid': action.testId } : {};

  if (action.iconOnly) {
    return (
      <Tooltip key={key} title={action.tooltip ?? action.label}>
        {/* A disabled button swallows pointer events, which would suppress the
            tooltip; the span keeps it reachable. */}
        <span>
          <IconButton
            onClick={action.onClick}
            color={action.active ? 'warning' : (action.color ?? 'default')}
            aria-label={action.label}
            disabled={action.disabled}
            sx={{ minWidth: TOUCH_TARGET, minHeight: TOUCH_TARGET }}
            {...testId}
          >
            {action.icon}
          </IconButton>
        </span>
      </Tooltip>
    );
  }

  const button = (
    <Button
      key={key}
      variant={action.variant ?? 'text'}
      color={action.color}
      startIcon={action.icon}
      onClick={action.onClick}
      disabled={action.disabled}
      sx={{ minHeight: TOUCH_TARGET }}
      {...testId}
    >
      {action.label}
    </Button>
  );

  // Wrapped only when there is something to say beyond the visible label — a
  // tooltip repeating the button's own text is noise. The span is required
  // because a disabled button swallows the events the tooltip listens for.
  return action.tooltip ? (
    <Tooltip key={key} title={action.tooltip}>
      <span>{button}</span>
    </Tooltip>
  ) : (
    button
  );
}

/**
 * Page-header action group implementing UI-NFR-021 R-024.
 *
 * On `xs` only the primary action stays visible; every secondary action moves
 * into a `⋮` overflow menu. From `sm` upwards all actions are shown side by
 * side, which is the behaviour the pages had before.
 *
 * Kiosk mode is deliberately out of scope here: R-027 forbids the overflow menu
 * as the only route to a frequently needed action, so a kiosk-specific layout is
 * a separate decision rather than something this component should guess.
 */
export default function PageHeaderActions({ primary, secondary, extra }: PageHeaderActionsProps) {
  const { t } = useTranslation();
  const theme = useTheme();
  const isXs = useMediaQuery(theme.breakpoints.down('sm'));
  const [anchorEl, setAnchorEl] = useState<HTMLElement | null>(null);

  const actions = (secondary ?? []).filter((a): a is HeaderAction => Boolean(a));
  const collapse = isXs && actions.length > 0;

  const renderMenuItem = (action: HeaderAction, index: number) => {
    // UI-NFR-021 R-019: a destructive entry in the overflow carries the error
    // colour *and* a separator, so it cannot be hit while aiming at the entry
    // above it. Colour alone would not satisfy R-031 either — the icon and
    // label stay, the colour is the addition.
    const destructive = action.color === 'error';
    // The tooltip explains why an action is unavailable ("system data", "in
    // use"). On `xs` there is no hover to reveal it, so it becomes the entry's
    // secondary line instead of being dropped.
    const reason = action.tooltip && action.tooltip !== action.label ? action.tooltip : undefined;

    return (
      <Fragment key={`overflow-${action.label}`}>
        {destructive && index > 0 && <Divider />}
        <MenuItem
          selected={action.active}
          disabled={action.disabled}
          onClick={() => {
            setAnchorEl(null);
            action.onClick();
          }}
          data-testid={action.testId ? `${action.testId}-menu-item` : undefined}
          sx={destructive ? { color: 'error.main' } : undefined}
        >
          {action.icon && (
            <ListItemIcon sx={destructive ? { color: 'error.main' } : undefined}>
              {action.icon}
            </ListItemIcon>
          )}
          <ListItemText primary={action.label} secondary={reason} />
        </MenuItem>
      </Fragment>
    );
  };

  return (
    <Box
      data-testid="page-header-actions"
      sx={{ display: 'flex', gap: 1, alignItems: 'center', flexWrap: 'wrap' }}
    >
      {extra}
      {!collapse && actions.map((a) => renderButton(a, 'secondary'))}
      {collapse && (
        <>
          <IconButton
            aria-label={t('common.moreActions')}
            aria-haspopup="menu"
            aria-expanded={Boolean(anchorEl)}
            onClick={(e) => setAnchorEl(e.currentTarget)}
            sx={{ minWidth: TOUCH_TARGET, minHeight: TOUCH_TARGET }}
            data-testid="page-header-overflow"
          >
            <MoreVertIcon />
          </IconButton>
          <Menu
            anchorEl={anchorEl}
            open={Boolean(anchorEl)}
            onClose={() => setAnchorEl(null)}
            // On the Menu root: MUI types both the `list` and `paper` slots
            // with component-specific prop types that reject arbitrary data
            // attributes, while the root spreads them onto the DOM node.
            data-testid="page-header-overflow-menu"
          >
            {actions.map(renderMenuItem)}
          </Menu>
        </>
      )}
      {primary && renderButton(primary, 'primary')}
    </Box>
  );
}
