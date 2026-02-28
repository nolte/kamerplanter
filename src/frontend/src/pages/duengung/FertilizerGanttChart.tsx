import { useState, useMemo, useCallback } from 'react';
import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import Tooltip from '@mui/material/Tooltip';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import { alpha, useTheme, type Theme } from '@mui/material/styles';
import useMediaQuery from '@mui/material/useMediaQuery';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import ExpandLessIcon from '@mui/icons-material/ExpandLess';
import type { NutrientPlanPhaseEntry, Fertilizer } from '@/api/types';

// ── Data transformation ─────────────────────────────────────────────

interface MethodSpan {
  method: string;
  weekStart: number;
  weekEnd: number;
  phaseName: string;
  channelLabel: string;
  mlPerLiter: number;
}

interface FertilizerRow {
  fertKey: string;
  fertName: string;
  brand: string;
  methods: Map<string, MethodSpan[]>;
}

function buildFertilizerRows(
  entries: NutrientPlanPhaseEntry[],
  fertilizers: Fertilizer[],
): FertilizerRow[] {
  const fertMap = new Map<string, FertilizerRow>();
  const fertLookup = new Map(fertilizers.map((f) => [f.key, f]));

  for (const entry of entries) {
    for (const ch of entry.delivery_channels) {
      for (const dosage of ch.fertilizer_dosages) {
        let row = fertMap.get(dosage.fertilizer_key);
        if (!row) {
          const f = fertLookup.get(dosage.fertilizer_key);
          row = {
            fertKey: dosage.fertilizer_key,
            fertName: f ? f.product_name : dosage.fertilizer_key,
            brand: f?.brand ?? '',
            methods: new Map(),
          };
          fertMap.set(dosage.fertilizer_key, row);
        }
        const methodKey = ch.application_method;
        const spans = row.methods.get(methodKey) ?? [];
        spans.push({
          method: methodKey,
          weekStart: entry.week_start,
          weekEnd: entry.week_end,
          phaseName: entry.phase_name,
          channelLabel: ch.label || ch.channel_id,
          mlPerLiter: dosage.ml_per_liter,
        });
        row.methods.set(methodKey, spans);
      }
    }
  }

  return [...fertMap.values()].sort((a, b) => a.fertName.localeCompare(b.fertName));
}

// ── Color palette ───────────────────────────────────────────────────

const METHOD_COLORS: Record<string, string> = {
  fertigation: '#1976d2',
  drench: '#2e7d32',
  foliar: '#ed6c02',
  top_dress: '#9c27b0',
};

function getMethodColor(method: string): string {
  return METHOD_COLORS[method] ?? '#757575';
}

// ── Component ───────────────────────────────────────────────────────

interface FertilizerGanttChartProps {
  entries: NutrientPlanPhaseEntry[];
  fertilizers: Fertilizer[];
}

export default function FertilizerGanttChart({ entries, fertilizers }: FertilizerGanttChartProps) {
  const { t } = useTranslation();
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));
  const [expanded, setExpanded] = useState<Set<string>>(new Set());

  const rows = useMemo(() => buildFertilizerRows(entries, fertilizers), [entries, fertilizers]);

  const totalWeeks = useMemo(() => {
    const sorted = [...entries].sort((a, b) => b.week_end - a.week_end);
    return sorted.length > 0 ? sorted[0].week_end : 0;
  }, [entries]);

  const toggleExpand = useCallback((key: string) => {
    setExpanded((prev) => {
      const next = new Set(prev);
      if (next.has(key)) next.delete(key);
      else next.add(key);
      return next;
    });
  }, []);

  if (rows.length === 0 || totalWeeks === 0) return null;

  const labelWidth = isMobile ? 120 : 160;
  const weeks = Array.from({ length: totalWeeks }, (_, i) => i + 1);

  return (
    <Card>
      <CardContent>
        <Typography variant="h6" gutterBottom>
          {t('pages.fertilizerGantt.title')}
        </Typography>

        <Box sx={{ overflowX: 'auto' }}>
          <Box
            sx={{
              display: 'grid',
              gridTemplateColumns: `${labelWidth}px repeat(${totalWeeks}, 1fr)`,
              minWidth: labelWidth + totalWeeks * 32,
              gap: 0,
            }}
          >
            {/* Header row */}
            <Box
              sx={{
                position: 'sticky',
                left: 0,
                bgcolor: 'background.paper',
                zIndex: 1,
                borderBottom: 1,
                borderColor: 'divider',
                py: 0.5,
              }}
            />
            {weeks.map((w) => (
              <Box
                key={w}
                role="columnheader"
                sx={{
                  textAlign: 'center',
                  borderBottom: 1,
                  borderColor: 'divider',
                  py: 0.5,
                }}
              >
                <Typography variant="caption" color="text.secondary">
                  {t('pages.gantt.week')}{w}
                </Typography>
              </Box>
            ))}

            {/* Fertilizer rows */}
            {rows.map((row) => {
              const methodKeys = [...row.methods.keys()].sort();
              const isExpanded = expanded.has(row.fertKey);
              const hasMultipleMethods = methodKeys.length > 1;

              // Merged week spans across all methods
              const allSpans = [...row.methods.values()].flat();

              return (
                <FertilizerGroupRow
                  key={row.fertKey}
                  row={row}
                  methodKeys={methodKeys}
                  allSpans={allSpans}
                  isExpanded={isExpanded}
                  hasMultipleMethods={hasMultipleMethods}
                  totalWeeks={totalWeeks}
                  labelWidth={labelWidth}
                  onToggle={toggleExpand}
                  t={t}
                  theme={theme}
                />
              );
            })}
          </Box>
        </Box>
      </CardContent>
    </Card>
  );
}

// ── Fertilizer group row ────────────────────────────────────────────

function FertilizerGroupRow({
  row,
  methodKeys,
  allSpans,
  isExpanded,
  hasMultipleMethods,
  totalWeeks,
  labelWidth,
  onToggle,
  t,
  theme,
}: {
  row: FertilizerRow;
  methodKeys: string[];
  allSpans: MethodSpan[];
  isExpanded: boolean;
  hasMultipleMethods: boolean;
  totalWeeks: number;
  labelWidth: number;
  onToggle: (key: string) => void;
  t: (key: string, opts?: Record<string, unknown>) => string;
  theme: Theme;
}) {
  const weeks = Array.from({ length: totalWeeks }, (_, i) => i + 1);

  // Build tooltip
  const tooltip = [
    row.fertName,
    row.brand ? `(${row.brand})` : null,
    ...methodKeys.map((m) => t(`enums.applicationMethod.${m}`)),
  ]
    .filter(Boolean)
    .join('\n');

  return (
    <>
      {/* Fertilizer label cell */}
      <Box
        role={hasMultipleMethods ? 'button' : undefined}
        tabIndex={hasMultipleMethods ? 0 : undefined}
        aria-expanded={hasMultipleMethods ? isExpanded : undefined}
        onClick={hasMultipleMethods ? () => onToggle(row.fertKey) : undefined}
        onKeyDown={hasMultipleMethods ? (e: React.KeyboardEvent) => {
          if (e.key === 'Enter' || e.key === ' ') {
            e.preventDefault();
            onToggle(row.fertKey);
          }
        } : undefined}
        sx={{
          position: 'sticky',
          left: 0,
          bgcolor: 'background.paper',
          zIndex: 1,
          display: 'flex',
          alignItems: 'center',
          gap: 0.5,
          py: 0.5,
          px: 0.5,
          cursor: hasMultipleMethods ? 'pointer' : 'default',
          borderBottom: 1,
          borderColor: 'divider',
          '&:hover': hasMultipleMethods ? { bgcolor: 'action.hover' } : undefined,
          '&:focus-visible': {
            outline: `2px solid ${theme.palette.primary.main}`,
            outlineOffset: -2,
          },
        }}
      >
        {hasMultipleMethods && (
          isExpanded
            ? <ExpandLessIcon sx={{ fontSize: 16, color: 'text.secondary', flexShrink: 0 }} />
            : <ExpandMoreIcon sx={{ fontSize: 16, color: 'text.secondary', flexShrink: 0 }} />
        )}
        <Box sx={{ minWidth: 0 }}>
          <Typography
            variant="body2"
            noWrap
            sx={{ fontWeight: 600, maxWidth: labelWidth - 30 }}
          >
            {row.fertName}
          </Typography>
          {row.brand && (
            <Typography
              variant="caption"
              noWrap
              color="text.secondary"
              sx={{ lineHeight: 1.2 }}
            >
              {row.brand}
            </Typography>
          )}
          {!hasMultipleMethods && methodKeys.length === 1 && (
            <Typography
              variant="caption"
              noWrap
              color="text.secondary"
              sx={{ lineHeight: 1.2 }}
            >
              {t(`enums.applicationMethod.${methodKeys[0]}`)}
            </Typography>
          )}
        </Box>
      </Box>

      {/* Merged bar cells (all methods combined) */}
      {weeks.map((w) => {
        // Find all spans covering this week
        const activeSpans = allSpans.filter((s) => w >= s.weekStart && w <= s.weekEnd);
        const inRange = activeSpans.length > 0;

        // Use the method color of the first span (or blend for parent row)
        const barColor = activeSpans.length === 1
          ? getMethodColor(activeSpans[0].method)
          : theme.palette.primary.main;

        const isStart = inRange && activeSpans.some((s) => w === s.weekStart);
        const isEnd = inRange && activeSpans.some((s) => w === s.weekEnd);

        const cellTooltip = activeSpans
          .map((s) => `${t(`enums.applicationMethod.${s.method}`)}: ${t('pages.fertilizerGantt.dosage', { ml: s.mlPerLiter })}`)
          .join('\n');

        return (
          <Box
            key={w}
            sx={{
              py: 0.75,
              px: '2px',
              borderBottom: 1,
              borderColor: 'divider',
              display: 'flex',
              alignItems: 'center',
            }}
          >
            {inRange && (
              <Tooltip
                title={<Box sx={{ whiteSpace: 'pre-line' }}>{tooltip + '\n' + cellTooltip}</Box>}
                arrow
              >
                <Box
                  sx={{
                    width: '100%',
                    height: 24,
                    bgcolor: alpha(barColor, 0.7),
                    borderRadius: `${isStart ? 4 : 0}px ${isEnd ? 4 : 0}px ${isEnd ? 4 : 0}px ${isStart ? 4 : 0}px`,
                  }}
                />
              </Tooltip>
            )}
          </Box>
        );
      })}

      {/* Expanded method sub-rows */}
      {isExpanded &&
        methodKeys.map((methodKey) => {
          const spans = row.methods.get(methodKey) ?? [];
          return (
            <MethodSubRow
              key={methodKey}
              methodKey={methodKey}
              spans={spans}
              totalWeeks={totalWeeks}
              labelWidth={labelWidth}
              t={t}
              theme={theme}
            />
          );
        })}
    </>
  );
}

// ── Method sub-row ──────────────────────────────────────────────────

function MethodSubRow({
  methodKey,
  spans,
  totalWeeks,
  labelWidth,
  t,
  theme,
}: {
  methodKey: string;
  spans: MethodSpan[];
  totalWeeks: number;
  labelWidth: number;
  t: (key: string, opts?: Record<string, unknown>) => string;
  theme: Theme;
}) {
  const color = getMethodColor(methodKey);
  const weeks = Array.from({ length: totalWeeks }, (_, i) => i + 1);
  const methodLabel = t(`enums.applicationMethod.${methodKey}`);

  return (
    <>
      {/* Method label */}
      <Box
        sx={{
          position: 'sticky',
          left: 0,
          bgcolor: 'background.paper',
          zIndex: 1,
          display: 'flex',
          alignItems: 'center',
          py: 0.5,
          pl: 3,
          pr: 0.5,
          borderBottom: 1,
          borderColor: 'divider',
        }}
      >
        <Typography
          variant="caption"
          noWrap
          color="text.secondary"
          sx={{ maxWidth: labelWidth - 30, fontStyle: 'italic' }}
        >
          {methodLabel}
        </Typography>
      </Box>

      {/* Method bar cells */}
      {weeks.map((w) => {
        const activeSpans = spans.filter((s) => w >= s.weekStart && w <= s.weekEnd);
        const inRange = activeSpans.length > 0;
        const isStart = inRange && activeSpans.some((s) => w === s.weekStart);
        const isEnd = inRange && activeSpans.some((s) => w === s.weekEnd);

        const cellTooltip = activeSpans
          .map((s) => `${s.phaseName}: ${t('pages.fertilizerGantt.dosage', { ml: s.mlPerLiter })}`)
          .join('\n');

        return (
          <Box
            key={w}
            sx={{
              py: 0.5,
              px: '2px',
              borderBottom: 1,
              borderColor: theme.palette.divider,
              display: 'flex',
              alignItems: 'center',
            }}
          >
            {inRange && (
              <Tooltip
                title={<Box sx={{ whiteSpace: 'pre-line' }}>{methodLabel + '\n' + cellTooltip}</Box>}
                arrow
              >
                <Box
                  sx={{
                    width: '100%',
                    height: 16,
                    bgcolor: alpha(color, 0.4),
                    borderRadius: `${isStart ? 3 : 0}px ${isEnd ? 3 : 0}px ${isEnd ? 3 : 0}px ${isStart ? 3 : 0}px`,
                  }}
                />
              </Tooltip>
            )}
          </Box>
        );
      })}
    </>
  );
}
