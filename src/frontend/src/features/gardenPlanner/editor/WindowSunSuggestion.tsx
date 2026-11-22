/**
 * "Aus Fenster vorschlagen" for the sun window of a location (REQ-053 GP-FR-181, §9.8, WP 10.7).
 *
 * The button opens a preview: the suggested sun window, the windows within the site's radius with their direction,
 * distance and contribution, and the caveats (shading and storey not considered, season, distance, glass). Nothing is
 * written until the user confirms (G-W10 c, "nie automatisch überschreiben"); cancelling or closing writes nothing.
 * A stored value other than `unknown` is only replaced through the button that says "Ersetzen" next to a warning
 * naming both values. Without a suggestion the dialog says why (not placed, no window, north only, tropics) instead
 * of a silently disabled button. The confirmation hands exactly the sun window to `onApply`; the caller commits it as
 * `site_conditions.sun_profile.sun_window` through the plan batch - hours, leaf shade, `source` and `sun_exposure`
 * stay as they are.
 */
import { useMemo, useState } from 'react';
import { useTranslation } from 'react-i18next';
import Alert from '@mui/material/Alert';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Dialog from '@mui/material/Dialog';
import DialogActions from '@mui/material/DialogActions';
import DialogContent from '@mui/material/DialogContent';
import DialogTitle from '@mui/material/DialogTitle';
import List from '@mui/material/List';
import ListItem from '@mui/material/ListItem';
import ListItemText from '@mui/material/ListItemText';
import Typography from '@mui/material/Typography';
import useMediaQuery from '@mui/material/useMediaQuery';
import { useTheme } from '@mui/material/styles';
import WbSunnyOutlinedIcon from '@mui/icons-material/WbSunnyOutlined';
import type { PlanModel } from '../model/planModel';
import type { SunWindow } from '../model/types';
import type { SuggestedSunWindow, WindowHint } from '../model/windowOrientation';
import { previewWindowSuggestion, type NearbyWindow } from './windowSuggestion';

const PREFIX = 'pages.gardenPlan.sun.fromWindow';
const TARGET_PX = 48;

export interface WindowSunSuggestionProps {
  plan: PlanModel;
  locationKey: string;
  /** The stored sun window of the location; `unknown` when none is recorded. */
  current: SunWindow;
  /** The site's radius around a window, metres (`window_thresholds.suggestion_radius_m`). */
  radiusM: number;
  /** `Site.gps_coordinates[0]`; `null` assumes the northern hemisphere. */
  latitude: number | null;
  disabled?: boolean;
  /** The confirmed suggestion; the caller writes exactly this sun window. */
  onApply: (sunWindow: SuggestedSunWindow) => void;
}

/** Why there is no suggestion, in the order the hints are checked. */
function reasonOf(placed: boolean, hints: readonly WindowHint[]): string {
  if (!placed) return 'notPlaced';
  if (hints.includes('tropics')) return 'tropics';
  if (hints.includes('no_window')) return 'noWindow';
  return 'diffuseOnly';
}

export default function WindowSunSuggestion({
  plan,
  locationKey,
  current,
  radiusM,
  latitude,
  disabled = false,
  onApply,
}: WindowSunSuggestionProps) {
  const { t, i18n } = useTranslation();
  const theme = useTheme();
  const fullScreen = useMediaQuery(theme.breakpoints.down('sm'));
  const [open, setOpen] = useState(false);
  const preview = useMemo(
    () => (open ? previewWindowSuggestion(plan, locationKey, radiusM, latitude) : null),
    [open, plan, locationKey, radiusM, latitude],
  );
  const number = useMemo(
    () => new Intl.NumberFormat(i18n.language, { maximumFractionDigits: 1, useGrouping: false }),
    [i18n.language],
  );
  const radius = number.format(radiusM);
  const suggested = preview?.suggestion.sunWindow ?? null;
  const replaces = suggested !== null && current !== 'unknown' && current !== suggested;
  const canApply = suggested !== null && current !== suggested;
  const close = () => setOpen(false);
  const confirm = () => {
    if (suggested === null || !canApply) return;
    onApply(suggested);
    setOpen(false);
  };

  const windowText = (window: NearbyWindow): string => {
    const contributionText =
      window.contribution === null
        ? t(`${PREFIX}.noDirectSun`)
        : t(`enums.sunWindow.${window.contribution}`);
    return t(`${PREFIX}.windowLine`, {
      direction: t(`enums.orientation.${window.facing.orientation}`),
      azimuth: number.format(window.facing.azimuthDeg),
      distance: number.format(window.distanceM),
      contribution: contributionText,
    });
  };

  return (
    <Box data-testid="garden-plan-panel-window-suggest-section" sx={{ mt: 2 }}>
      <Button
        variant="outlined"
        startIcon={<WbSunnyOutlinedIcon />}
        disabled={disabled}
        onClick={() => setOpen(true)}
        data-testid="garden-plan-panel-window-suggest"
        sx={{ minHeight: TARGET_PX }}
      >
        {t(`${PREFIX}.action`)}
      </Button>
      <Typography variant="caption" color="text.secondary" component="p" sx={{ mt: 0.5 }}>
        {t(`${PREFIX}.actionHint`, { radius })}
      </Typography>

      {preview !== null && (
        <Dialog
          open
          onClose={close}
          fullScreen={fullScreen}
          maxWidth="sm"
          fullWidth
          aria-labelledby="garden-plan-window-suggestion-title"
          data-testid="garden-plan-window-suggestion-dialog"
        >
          <DialogTitle id="garden-plan-window-suggestion-title">{t(`${PREFIX}.title`)}</DialogTitle>
          <DialogContent sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
            {suggested !== null ? (
              <Box data-testid="garden-plan-window-suggestion-value" data-sun-window={suggested}>
                <Typography variant="subtitle1" component="p">
                  {t(`${PREFIX}.suggested`, { value: t(`enums.sunWindow.${suggested}`) })}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  {t(`${PREFIX}.current`, { value: t(`enums.sunWindow.${current}`) })}
                </Typography>
              </Box>
            ) : (
              <Alert severity="info" data-testid="garden-plan-window-suggestion-none">
                <Typography variant="subtitle2" component="p">
                  {t(`${PREFIX}.noneTitle`)}
                </Typography>
                {t(`${PREFIX}.reason.${reasonOf(preview.placed, preview.suggestion.hints)}`, { radius })}
              </Alert>
            )}

            {replaces && (
              <Alert severity="warning" data-testid="garden-plan-window-suggestion-replace">
                {t(`${PREFIX}.replaceWarning`, {
                  current: t(`enums.sunWindow.${current}`),
                  value: t(`enums.sunWindow.${suggested}`),
                })}
              </Alert>
            )}
            {suggested !== null && !canApply && (
              <Alert severity="success" data-testid="garden-plan-window-suggestion-unchanged">
                {t(`${PREFIX}.unchanged`)}
              </Alert>
            )}

            {preview.windows.length > 0 && (
              <Box component="section" aria-labelledby="garden-plan-window-suggestion-windows-title">
                <Typography variant="subtitle2" component="h3" id="garden-plan-window-suggestion-windows-title">
                  {t(`${PREFIX}.windowsTitle`, { count: preview.windows.length, radius })}
                </Typography>
                <List dense disablePadding data-testid="garden-plan-window-suggestion-windows">
                  {preview.windows.map((window) => (
                    <ListItem
                      key={window.key}
                      disableGutters
                      data-testid={`garden-plan-window-suggestion-window-${window.key}`}
                      data-orientation={window.facing.orientation}
                    >
                      <ListItemText
                        primary={window.label || t(`${PREFIX}.windowUnnamed`)}
                        secondary={
                          window.facing.basis === 'drawing_direction'
                            ? `${windowText(window)} ${t(`${PREFIX}.byConvention`)}`
                            : windowText(window)
                        }
                      />
                    </ListItem>
                  ))}
                </List>
              </Box>
            )}

            {preview.suggestion.hints.length > 0 && (
              <Box component="section" aria-labelledby="garden-plan-window-suggestion-hints-title">
                <Typography variant="subtitle2" component="h3" id="garden-plan-window-suggestion-hints-title">
                  {t(`${PREFIX}.hintsTitle`)}
                </Typography>
                <Box component="ul" data-testid="garden-plan-window-suggestion-hints" sx={{ pl: 2.5, my: 0.5 }}>
                  {preview.suggestion.hints.map((hint) => (
                    <Typography key={hint} component="li" variant="body2" data-hint={hint}>
                      {t(`${PREFIX}.hints.${hint}`, { radius })}
                    </Typography>
                  ))}
                </Box>
              </Box>
            )}
          </DialogContent>
          <DialogActions>
            <Button onClick={close} sx={{ minHeight: TARGET_PX }} data-testid="garden-plan-window-suggestion-cancel">
              {canApply ? t(`${PREFIX}.cancel`) : t(`${PREFIX}.close`)}
            </Button>
            {canApply && (
              <Button
                variant="contained"
                color={replaces ? 'warning' : 'primary'}
                onClick={confirm}
                sx={{ minHeight: TARGET_PX }}
                data-testid="garden-plan-window-suggestion-apply"
              >
                {replaces ? t(`${PREFIX}.replace`) : t(`${PREFIX}.apply`)}
              </Button>
            )}
          </DialogActions>
        </Dialog>
      )}
    </Box>
  );
}
