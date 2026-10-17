/**
 * The compass widget (REQ-053 GP-FR-015): N/E/S/W on a dial that shows where geographic north lies
 * on the plan. The angle (`north_angle_deg`, compass azimuth clockwise, 0 = north is up) is set by
 * turning the dial (pointer or arrow keys) or by typing it. A phone compass shows magnetic
 * north, so the value is never taken automatically.
 *
 * The azimuth is NOT `rotation_deg`: the named converters live in `model/compass.ts`.
 */
import { useCallback, useState, type KeyboardEvent, type PointerEvent } from 'react';
import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import Tooltip from '@mui/material/Tooltip';
import InputAdornment from '@mui/material/InputAdornment';
import TextField from '@mui/material/TextField';
import { useTheme } from '@mui/material/styles';
import { azimuthFromScreenOffset, normalizeAzimuth } from '../model/compass';

const DIAL_PX = 56;
const LETTER_RADIUS = 20;
const PREFIX = 'pages.gardenPlan.editor.compass';

interface CompassProps {
  /** `Site.plan.north_angle_deg`. */
  angleDeg: number;
  /** Absent: the angle is shown but cannot be changed (no outline to attach it to yet). */
  onChange?: (angleDeg: number) => void;
}

const LETTERS = ['n', 'e', 's', 'w'] as const;

export function Compass({ angleDeg, onChange }: CompassProps) {
  const { t } = useTranslation();
  const { palette } = useTheme();
  const editable = onChange !== undefined;
  // While the dial is dragged the draft shows; the value is committed on release.
  const [draft, setDraft] = useState<number | null>(null);
  const shown = draft ?? angleDeg;
  // What the user is typing; `null` = show the stored value (no effect needed to sync it).
  const [typed, setTyped] = useState<string | null>(null);
  const text = typed ?? String(angleDeg);
  const parsedText = Number(text);
  // Valid: a number from 0 to 360 (360 is north again and is stored as 0).
  const invalid = typed !== null && (text.trim() === '' || !Number.isFinite(parsedText) || parsedText < 0 || parsedText > 360);

  const commit = useCallback(
    (value: number) => {
      const next = normalizeAzimuth(value);
      if (onChange && next !== angleDeg) onChange(next);
    },
    [angleDeg, onChange],
  );

  const fromPointer = (event: PointerEvent<HTMLElement>): number => {
    const box = event.currentTarget.getBoundingClientRect();
    return azimuthFromScreenOffset(
      event.clientX - (box.left + box.width / 2),
      event.clientY - (box.top + box.height / 2),
    );
  };

  const onKeyDown = (event: KeyboardEvent<HTMLElement>) => {
    if (!editable) return;
    const step = event.shiftKey ? 15 : 1;
    let next: number | null = null;
    if (event.key === 'ArrowRight' || event.key === 'ArrowUp') next = angleDeg + step;
    else if (event.key === 'ArrowLeft' || event.key === 'ArrowDown') next = angleDeg - step;
    else if (event.key === 'PageUp') next = angleDeg + 15;
    else if (event.key === 'PageDown') next = angleDeg - 15;
    else if (event.key === 'Home') next = 0;
    if (next === null) return;
    event.preventDefault();
    commit(next);
  };

  const center = DIAL_PX / 2;
  const angleText = t(`${PREFIX}.value`, { angle: shown });
  return (
    <Box
      data-testid="garden-plan-compass"
      sx={{ display: 'flex', alignItems: 'center', gap: 1 }}
    >
      <Tooltip title={t(`${PREFIX}.help`)}>
      <Box
        role="slider"
        tabIndex={0}
        aria-label={t(`${PREFIX}.label`)}
        aria-valuemin={0}
        aria-valuemax={359.9}
        aria-valuenow={shown}
        aria-valuetext={angleText}
        aria-readonly={!editable}
        data-testid="garden-plan-compass-dial"
        onKeyDown={onKeyDown}
        onPointerDown={(event) => {
          if (!editable) return;
          event.currentTarget.setPointerCapture?.(event.pointerId);
          setDraft(fromPointer(event));
        }}
        onPointerMove={(event) => {
          if (draft !== null) setDraft(fromPointer(event));
        }}
        onPointerUp={(event) => {
          if (draft === null) return;
          const next = fromPointer(event);
          setDraft(null);
          commit(next);
        }}
        onPointerCancel={() => setDraft(null)}
        sx={{
          width: 44,
          height: 44,
          flexShrink: 0,
          borderRadius: '50%',
          cursor: editable ? 'grab' : 'default',
          touchAction: 'none',
          '&:focus-visible': { outline: 2, outlineStyle: 'solid', outlineColor: 'primary.main' },
        }}
      >
        <svg
          viewBox={`0 0 ${DIAL_PX} ${DIAL_PX}`}
          width={44}
          height={44}
          aria-hidden="true"
          focusable="false"
        >
          <circle cx={center} cy={center} r={center - 1} fill="none" stroke={palette.divider} strokeWidth={2} />
          <g transform={`rotate(${shown} ${center} ${center})`}>
            <path
              d={`M${center} ${center - 12}L${center + 4} ${center}L${center - 4} ${center}Z`}
              fill={palette.error.main}
            />
            <path
              d={`M${center} ${center + 12}L${center + 4} ${center}L${center - 4} ${center}Z`}
              fill={palette.text.disabled}
            />
          </g>
          {LETTERS.map((letter, index) => {
            // Letters follow their bearing around the dial but stay upright.
            const bearing = ((shown + index * 90) * Math.PI) / 180;
            return (
              <text
                key={letter}
                x={center + LETTER_RADIUS * Math.sin(bearing)}
                y={center - LETTER_RADIUS * Math.cos(bearing)}
                textAnchor="middle"
                dominantBaseline="central"
                fontSize={11}
                fontWeight={letter === 'n' ? 700 : 400}
                fill={letter === 'n' ? palette.error.main : palette.text.secondary}
              >
                {t(`${PREFIX}.${letter}`)}
              </text>
            );
          })}
        </svg>
      </Box>
      </Tooltip>
      <TextField
        size="small"
        type="number"
        label={t(`${PREFIX}.input`)}
        value={text}
        disabled={!editable}
        error={invalid}
        helperText={invalid ? t(`${PREFIX}.invalid`) : undefined}
        onChange={(event) => setTyped(event.target.value)}
        onBlur={() => {
          const wasInvalid = invalid;
          setTyped(null);
          if (!wasInvalid && typed !== null) commit(parsedText);
        }}
        onKeyDown={(event) => {
          if (event.key === 'Enter') (event.target as HTMLInputElement).blur();
        }}
        slotProps={{
          input: { endAdornment: <InputAdornment position="end">°</InputAdornment> },
          htmlInput: {
            min: 0,
            max: 360,
            step: 'any',
            inputMode: 'decimal',
            'data-testid': 'garden-plan-compass-input',
          },
        }}
        sx={{ width: 148, '& input': { minHeight: 28 } }}
      />
    </Box>
  );
}
