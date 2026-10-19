/**
 * Sun and shade of a bed as five tiles with icon and text, not a dropdown (REQ-053 GP-FR-157, WP 3.9).
 *
 * A native radio group: the arrow keys, the grouping and the screen-reader announcement come from the
 * browser. Every tile carries the definition of its class as visible help text ("more than 6 hours of
 * direct sunlight on a summer day"), tied to its radio with `aria-describedby`; the tiles are at
 * least 64 px high. `value = null` shows no selection - the bulk assignment of the plan editor has none
 * to show, and choosing a tile then sets it on every selected bed.
 *
 * The thresholds in the help texts are the RHS midsummer classes checked in
 * `spec/analysis/agrobiology-thresholds-req-053.md` (O-17); making them configurable is GP-FR-164.
 */
import { useId, type ReactNode } from 'react';
import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import CircleIcon from '@mui/icons-material/Circle';
import CloudIcon from '@mui/icons-material/Cloud';
import FilterDramaIcon from '@mui/icons-material/FilterDrama';
import HelpOutlinedIcon from '@mui/icons-material/HelpOutlined';
import WbSunnyIcon from '@mui/icons-material/WbSunny';
import type { SunExposure } from '../model/types';

/** The classes in the order of the ladder, sunniest first; `unknown` (the default) last. */
export const SUN_TILE_VALUES: readonly SunExposure[] = [
  'full_sun',
  'partial_shade',
  'shade',
  'deep_shade',
  'unknown',
];

const ICONS: Record<SunExposure, ReactNode> = {
  full_sun: <WbSunnyIcon aria-hidden fontSize="medium" />,
  partial_shade: <FilterDramaIcon aria-hidden fontSize="medium" />,
  shade: <CloudIcon aria-hidden fontSize="medium" />,
  deep_shade: <CircleIcon aria-hidden fontSize="medium" />,
  unknown: <HelpOutlinedIcon aria-hidden fontSize="medium" />,
};

export interface SunTileSelectorProps {
  /** The chosen class; `null` = none shown (bulk assignment). */
  value: SunExposure | null;
  onChange: (value: SunExposure) => void;
  disabled?: boolean;
  /** Accessible name of the group; defaults to "Sun and shade of the bed". */
  label?: string;
  testId?: string;
}

export default function SunTileSelector({
  value,
  onChange,
  disabled = false,
  label,
  testId = 'sun-tile-selector',
}: SunTileSelectorProps) {
  const { t } = useTranslation();
  const name = useId();
  const groupLabel = label ?? t('pages.gardenPlan.sun.group');

  return (
    <Box
      role="radiogroup"
      aria-label={groupLabel}
      data-testid={testId}
      sx={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(132px, 1fr))',
        gap: 1,
      }}
    >
      {SUN_TILE_VALUES.map((option) => {
        const checked = value === option;
        const helpId = `${name}-${option}-help`;
        const labelId = `${name}-${option}-label`;
        return (
          <Box
            key={option}
            component="label"
            data-testid={`${testId}-${option}`}
            sx={(theme) => ({
              position: 'relative',
              display: 'flex',
              flexDirection: 'column',
              gap: 0.5,
              minHeight: 64,
              p: 1.25,
              borderRadius: 1,
              border: '2px solid',
              borderColor: checked ? 'primary.main' : 'divider',
              bgcolor: checked ? 'action.selected' : 'background.paper',
              cursor: disabled ? 'default' : 'pointer',
              opacity: disabled ? 0.6 : 1,
              '&:hover': disabled ? undefined : { bgcolor: 'action.hover' },
              // The radio is visually hidden but stays focusable: the tile shows the focus ring.
              '&:focus-within': { outline: `3px solid ${theme.palette.primary.main}`, outlineOffset: 2 },
            })}
          >
            <input
              type="radio"
              name={name}
              value={option}
              checked={checked}
              disabled={disabled}
              onChange={() => onChange(option)}
              aria-labelledby={labelId}
              aria-describedby={helpId}
              data-testid={`${testId}-${option}-input`}
              style={{
                position: 'absolute',
                inset: 0,
                width: '100%',
                height: '100%',
                margin: 0,
                opacity: 0,
                cursor: 'inherit',
              }}
            />
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              {ICONS[option]}
              <Typography
                id={labelId}
                variant="subtitle2"
                component="span"
                sx={{ fontWeight: checked ? 700 : 500 }}
              >
                {t(`pages.gardenPlan.sun.options.${option}.label`)}
              </Typography>
            </Box>
            <Typography id={helpId} variant="caption" color="text.secondary" component="span">
              {t(`pages.gardenPlan.sun.options.${option}.help`)}
            </Typography>
          </Box>
        );
      })}
    </Box>
  );
}
