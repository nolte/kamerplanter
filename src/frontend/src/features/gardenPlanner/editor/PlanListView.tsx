/**
 * "As list" (REQ-053 GP-NFR-023, GP-ACC-032): the same plan as a hierarchy - garden, area, bed,
 * object - that a screen reader or keyboard can walk without the canvas. Every row gives name,
 * type, position and size; the selected row adds its properties and every action the canvas
 * offers apart from freehand drawing: move (arrow buttons or X/Y in metres), delete (through the
 * editor's confirmation). The list is also the phone fallback for objects too small to hit.
 *
 * It owns no plan state: it reads the model, reports a selection, and asks the editor to move or
 * delete - so every change is a `PlanOperation` batch like on the canvas. It is one tab stop
 * (roving tabindex); Up/Down/Home/End walk the rows.
 */
import {
  useCallback,
  useMemo,
  useState,
  type FormEvent,
  type KeyboardEvent as ReactKeyboardEvent,
} from 'react';
import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Form from '@/components/form/Form';
import ButtonBase from '@mui/material/ButtonBase';
import IconButton from '@mui/material/IconButton';
import TextField from '@mui/material/TextField';
import Typography from '@mui/material/Typography';
import ArrowBackIcon from '@mui/icons-material/ArrowBack';
import ArrowDownwardIcon from '@mui/icons-material/ArrowDownward';
import ArrowForwardIcon from '@mui/icons-material/ArrowForward';
import ArrowUpwardIcon from '@mui/icons-material/ArrowUpward';
import DeleteOutlinedIcon from '@mui/icons-material/DeleteOutlined';
import LockOutlinedIcon from '@mui/icons-material/LockOutlined';
import { areaM2 } from '../model/geometry';
import { plantsInLocations, type PlanModel } from '../model/planModel';
import type { Point } from '../model/types';
import type { RendererLabels } from '../renderer';
import type { SelectionRef } from '../state/gardenPlanSlice';
import { EDITOR_ANCHORS } from './anchors';
import { buildTree, type TreeRow } from './planTree';
import { positionOf } from './tools/keyboardMove';
import { sameRef } from './tools/selection';

const PREFIX = 'pages.gardenPlan.editor.list';
const TARGET_PX = 44;

interface PlanListViewProps {
  plan: PlanModel;
  labels: RendererLabels;
  selection: readonly SelectionRef[];
  /** Metres one arrow button moves by (the grid step). */
  stepM: number;
  onSelect: (ref: SelectionRef) => void;
  onMove: (delta: Point) => void;
  /** Delete was asked for; the editor shows its confirmation. */
  onRequestDelete: () => void;
}

function rowSource(plan: PlanModel, row: TreeRow) {
  return row.ref.entity === 'location' ? plan.locations[row.key] : plan.gardenObjects[row.key];
}

function useFormatNumber(): (value: number) => string {
  const { i18n } = useTranslation();
  return useMemo(() => {
    const format = new Intl.NumberFormat(i18n.language, { maximumFractionDigits: 2 });
    return (value: number) => format.format(value);
  }, [i18n.language]);
}

interface MoveToProps {
  position: Point;
  disabled: boolean;
  name: string;
  onMove: (delta: Point) => void;
}

/** X and Y in metres; the form is re-keyed by the caller when the position changes. */
function MoveToForm({ position, disabled, name, onMove }: MoveToProps) {
  const { t } = useTranslation();
  const [x, setX] = useState(String(position[0]));
  const [y, setY] = useState(String(position[1]));
  // A move changes the position: the fields follow (state adjusted while rendering, no effect).
  const [shown, setShown] = useState(position);
  if (shown[0] !== position[0] || shown[1] !== position[1]) {
    setShown(position);
    setX(String(position[0]));
    setY(String(position[1]));
  }
  const nx = Number(x);
  const ny = Number(y);
  const valid = x.trim() !== '' && y.trim() !== '' && Number.isFinite(nx) && Number.isFinite(ny);
  const changed = valid && (nx !== position[0] || ny !== position[1]);
  const submit = (event: FormEvent) => {
    event.preventDefault();
    if (changed) onMove([nx - position[0], ny - position[1]]);
  };
  return (
    <Form
      onSubmit={submit}
      aria-label={t(`${PREFIX}.moveTo.group`, { name })}
      sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, alignItems: 'flex-start' }}
    >
      {(
        [
          ['x', x, setX],
          ['y', y, setY],
        ] as const
      ).map(([axis, value, set]) => (
        <TextField
          key={axis}
          size="small"
          type="number"
          label={t(`${PREFIX}.moveTo.${axis}`)}
          value={value}
          onChange={(event) => set(event.target.value)}
          disabled={disabled}
          slotProps={{
            htmlInput: {
              step: 0.1,
              inputMode: 'decimal',
              'data-testid': `garden-plan-list-${axis}`,
            },
          }}
          sx={{ width: 120, '& .MuiInputBase-root': { minHeight: TARGET_PX } }}
        />
      ))}
      <Button
        type="submit"
        variant="outlined"
        disabled={disabled || !changed}
        sx={{ minHeight: TARGET_PX }}
        data-testid="garden-plan-list-move-to"
      >
        {t(`${PREFIX}.moveTo.apply`)}
      </Button>
    </Form>
  );
}

export function PlanListView({
  plan,
  labels,
  selection,
  stepM,
  onSelect,
  onMove,
  onRequestDelete,
}: PlanListViewProps) {
  const { t } = useTranslation();
  const format = useFormatNumber();
  const rows = useMemo(() => buildTree(plan, labels.objectType), [plan, labels]);
  const [focused, setFocused] = useState<string | null>(null);
  // The one tab stop: the row last focused, else the selected one, else the first.
  const primary = selection.length > 0 ? selection[0] : null;
  const tabKey =
    [focused, primary?.key].find((key) => key != null && rows.some((row) => row.key === key)) ??
    rows[0]?.key ??
    null;

  const onKeyDown = useCallback((event: ReactKeyboardEvent<HTMLElement>) => {
    const target = event.target;
    if (!(target instanceof HTMLElement) || !target.dataset.listKey) return;
    const buttons = Array.from(
      event.currentTarget.querySelectorAll<HTMLElement>('button[data-list-key]'),
    );
    const at = buttons.indexOf(target);
    let next = -1;
    if (event.key === 'ArrowDown') next = Math.min(buttons.length - 1, at + 1);
    else if (event.key === 'ArrowUp') next = Math.max(0, at - 1);
    else if (event.key === 'Home') next = 0;
    else if (event.key === 'End') next = buttons.length - 1;
    if (next < 0) return;
    event.preventDefault();
    buttons[next]?.focus();
  }, []);

  const describe = (row: TreeRow) => {
    const source = rowSource(plan, row);
    const geometry = source?.geometry ?? null;
    const type =
      row.objectType !== null
        ? labels.objectType(row.objectType)
        : t(`${PREFIX}.level.${row.level}`);
    const position = positionOf(plan, row.ref);
    const size = geometry
      ? labels.size(geometry, source && 'area_m2' in source ? source.area_m2 : areaM2(geometry))
      : null;
    return {
      type,
      position,
      positionText: position
        ? t(`${PREFIX}.position`, { x: format(position[0]), y: format(position[1]) })
        : t(`${PREFIX}.notPlaced`),
      size,
    };
  };

  const renderDetails = (row: TreeRow) => {
    const info = describe(row);
    const location = row.ref.entity === 'location' ? plan.locations[row.key] : null;
    const object = row.ref.entity === 'garden_object' ? plan.gardenObjects[row.key] : null;
    const facts: [string, string][] = [
      [t(`${PREFIX}.fact.type`), info.type],
      [t(`${PREFIX}.fact.position`), info.positionText],
    ];
    if (info.size) facts.push([t(`${PREFIX}.fact.size`), info.size]);
    if (location) {
      facts.push([t(`${PREFIX}.fact.status`), t(`${PREFIX}.status.${location.bed_status}`)]);
      facts.push([
        t(`${PREFIX}.fact.plants`),
        String(plantsInLocations(plan, new Set([row.key])).length),
      ]);
      facts.push([t(`${PREFIX}.fact.openTasks`), String(location.open_task_count)]);
    }
    if (object?.notes) facts.push([t(`${PREFIX}.fact.notes`), object.notes]);
    facts.push([t(`${PREFIX}.fact.locked`), t(row.locked ? 'common.yes' : 'common.no')]);
    const blocked = row.locked || info.position === null;
    const step = format(stepM);
    const buttons = [
      { id: 'left', delta: [-stepM, 0] as Point, icon: <ArrowBackIcon /> },
      { id: 'right', delta: [stepM, 0] as Point, icon: <ArrowForwardIcon /> },
      { id: 'up', delta: [0, stepM] as Point, icon: <ArrowUpwardIcon /> },
      { id: 'down', delta: [0, -stepM] as Point, icon: <ArrowDownwardIcon /> },
    ];
    return (
      <Box
        role="group"
        aria-label={t(`${PREFIX}.actions.group`, { name: row.name })}
        data-testid="garden-plan-list-details"
        sx={{ display: 'flex', flexDirection: 'column', gap: 1.5, py: 1.5, pl: 2, minWidth: 0 }}
      >
        <Box
          component="dl"
          sx={{
            m: 0,
            display: 'grid',
            gridTemplateColumns: 'minmax(0, auto) minmax(0, 1fr)',
            columnGap: 2,
            rowGap: 0.25,
          }}
        >
          {facts.map(([term, value]) => (
            <Box key={term} sx={{ display: 'contents' }}>
              <Box component="dt" sx={{ color: 'text.secondary' }}>
                {term}
              </Box>
              <Box component="dd" sx={{ m: 0, overflowWrap: 'anywhere' }}>
                {value}
              </Box>
            </Box>
          ))}
        </Box>
        {info.position && (
          <>
            <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
              {buttons.map(({ id, delta, icon }) => (
                <IconButton
                  key={id}
                  disabled={blocked}
                  onClick={() => onMove(delta)}
                  aria-label={t(`${PREFIX}.move.${id}`, { step })}
                  data-testid={`garden-plan-list-move-${id}`}
                  sx={{ width: TARGET_PX, height: TARGET_PX, border: 1, borderColor: 'divider' }}
                >
                  {icon}
                </IconButton>
              ))}
            </Box>
            <MoveToForm
              key={row.key}
              position={info.position}
              disabled={blocked}
              name={row.name}
              onMove={onMove}
            />
          </>
        )}
        {row.locked && (
          <Typography variant="body2" color="text.secondary">
            {t(`${PREFIX}.lockedHint`)}
          </Typography>
        )}
        <Box>
          <Button
            color="error"
            variant="outlined"
            startIcon={<DeleteOutlinedIcon />}
            onClick={onRequestDelete}
            sx={{ minHeight: TARGET_PX }}
            data-testid="garden-plan-list-delete"
          >
            {t(`${PREFIX}.delete`)}
          </Button>
        </Box>
      </Box>
    );
  };

  return (
    <Box
      component="section"
      id={EDITOR_ANCHORS.list}
      tabIndex={-1}
      aria-labelledby="garden-plan-list-heading"
      data-testid="garden-plan-list"
      sx={{
        outline: 'none',
        '&:focus-visible': { outline: 2, outlineStyle: 'solid', outlineColor: 'primary.main' },
      }}
    >
      <Typography id="garden-plan-list-heading" variant="h2" sx={{ fontSize: '1.125rem', mb: 0.5 }}>
        {t(`${PREFIX}.heading`)}
      </Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
        {t(`${PREFIX}.intro`, { name: plan.siteName })}
      </Typography>
      {rows.length === 0 ? (
        <Typography data-testid="garden-plan-list-empty">{t(`${PREFIX}.empty`)}</Typography>
      ) : (
        <Box component="ul" onKeyDown={onKeyDown} sx={{ listStyle: 'none', m: 0, p: 0 }}>
          {rows.map((row) => {
            const selected = selection.some((ref) => sameRef(ref, row.ref));
            const info = describe(row);
            return (
              <Box
                component="li"
                key={row.key}
                data-testid={`garden-plan-list-row-${row.key}`}
                sx={{
                  ml: (row.depth - 1) * 2,
                  borderLeft: row.depth > 1 ? 1 : 0,
                  borderColor: 'divider',
                  pl: row.depth > 1 ? 1 : 0,
                }}
              >
                <ButtonBase
                  component="button"
                  data-list-key={row.key}
                  tabIndex={row.key === tabKey ? 0 : -1}
                  aria-pressed={selected}
                  onFocus={() => setFocused(row.key)}
                  onClick={() => onSelect(row.ref)}
                  sx={{
                    display: 'block',
                    width: '100%',
                    textAlign: 'left',
                    minHeight: TARGET_PX,
                    px: 1.5,
                    py: 0.75,
                    borderRadius: 1,
                    border: 1,
                    borderColor: selected ? 'primary.main' : 'transparent',
                    bgcolor: selected ? 'action.selected' : 'transparent',
                    '&:focus-visible': {
                      outline: 2,
                      outlineStyle: 'solid',
                      outlineColor: 'primary.main',
                      outlineOffset: 1,
                    },
                  }}
                >
                  <Typography
                    component="span"
                    sx={{ display: 'flex', alignItems: 'center', gap: 0.5, fontWeight: 600 }}
                  >
                    {row.name}
                    {row.locked && (
                      <LockOutlinedIcon
                        fontSize="inherit"
                        titleAccess={t(`${PREFIX}.lockedIcon`)}
                      />
                    )}
                  </Typography>
                  <Typography
                    component="span"
                    variant="body2"
                    color="text.secondary"
                    sx={{ display: 'block', overflowWrap: 'anywhere' }}
                  >
                    {[info.type, info.positionText, info.size].filter(Boolean).join(' · ')}
                  </Typography>
                </ButtonBase>
                {selected && primary && sameRef(primary, row.ref) && renderDetails(row)}
              </Box>
            );
          })}
        </Box>
      )}
    </Box>
  );
}
