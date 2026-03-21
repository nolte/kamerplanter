import { useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import Tooltip from '@mui/material/Tooltip';
import IconButton from '@mui/material/IconButton';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import { alpha, useTheme, type Theme } from '@mui/material/styles';
import useMediaQuery from '@mui/material/useMediaQuery';
import OpenInNewIcon from '@mui/icons-material/OpenInNew';
import type { NutrientPlanUsage, PhaseName } from '@/api/types';

const PHASE_COLORS: Record<string, string> = {
  germination: '#8D6E63',
  seedling: '#66BB6A',
  vegetative: '#2E7D32',
  flowering: '#AB47BC',
  flushing: '#26C6DA',
  harvest: '#FF8F00',
};

interface GanttRow {
  planKey: string;
  planName: string;
  applicationMethod: string;
  segments: Array<{
    weekStart: number;
    weekEnd: number;
    phaseName: string;
    mlPerLiter: number;
  }>;
}

interface FertilizerUsageGanttProps {
  planUsage: NutrientPlanUsage[];
}

export default function FertilizerUsageGantt({ planUsage }: FertilizerUsageGanttProps) {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));

  const rows = useMemo<GanttRow[]>(() => {
    const result: GanttRow[] = [];
    for (const plan of planUsage) {
      const grouped = new Map<string, GanttRow>();
      for (const phase of plan.phase_entries) {
        for (const ch of phase.channels) {
          const groupKey = ch.application_method;
          let row = grouped.get(groupKey);
          if (!row) {
            row = {
              planKey: plan.key,
              planName: plan.name,
              applicationMethod: ch.application_method,
              segments: [],
            };
            grouped.set(groupKey, row);
          }
          row.segments.push({
            weekStart: phase.week_start,
            weekEnd: phase.week_end,
            phaseName: phase.phase_name,
            mlPerLiter: ch.ml_per_liter,
          });
        }
      }
      result.push(...grouped.values());
    }
    return result;
  }, [planUsage]);

  const totalWeeks = useMemo(() => {
    let max = 0;
    for (const row of rows) {
      for (const seg of row.segments) {
        if (seg.weekEnd > max) max = seg.weekEnd;
      }
    }
    return max;
  }, [rows]);

  if (rows.length === 0 || totalWeeks === 0) {
    return (
      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            {t('pages.fertilizers.usedInPlans')}
          </Typography>
          <Typography variant="body2" color="text.secondary">
            {t('pages.fertilizers.notUsedInAnyPlan')}
          </Typography>
        </CardContent>
      </Card>
    );
  }

  const labelWidth = isMobile ? 100 : 160;
  const weeks = Array.from({ length: totalWeeks }, (_, i) => i + 1);

  return (
    <Card>
      <CardContent>
        <Typography variant="h6" gutterBottom>
          {t('pages.fertilizers.usedInPlans')}
        </Typography>

        <Box sx={{ overflowX: 'auto', WebkitOverflowScrolling: 'touch', mx: isMobile ? -1 : 0 }}>
          <Box
            sx={{
              display: 'grid',
              gridTemplateColumns: `${labelWidth}px repeat(${totalWeeks}, 1fr)`,
              minWidth: labelWidth + totalWeeks * (isMobile ? 22 : 32),
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

            {/* Data rows */}
            {rows.map((row, idx) => {
              const methodLabel = t(`enums.applicationMethod.${row.applicationMethod}`);
              const rowLabel = `${row.planName} · ${methodLabel}`;

              return (
                <UsageRow
                  key={`${row.planKey}-${row.applicationMethod}-${idx}`}
                  row={row}
                  rowLabel={rowLabel}
                  totalWeeks={totalWeeks}
                  labelWidth={labelWidth}
                  theme={theme}
                  t={t}
                  onNavigate={() => navigate(`/duengung/plans/${row.planKey}`)}
                />
              );
            })}
          </Box>
        </Box>
      </CardContent>
    </Card>
  );
}

function UsageRow({
  row,
  rowLabel,
  totalWeeks,
  labelWidth,
  theme,
  t,
  onNavigate,
}: {
  row: GanttRow;
  rowLabel: string;
  totalWeeks: number;
  labelWidth: number;
  theme: Theme;
  t: (key: string, opts?: Record<string, unknown>) => string;
  onNavigate: () => void;
}) {
  const segmentMap = useMemo(() => {
    const map = new Map<number, (typeof row.segments)[number]>();
    for (const seg of row.segments) {
      for (let w = seg.weekStart; w <= seg.weekEnd; w++) {
        map.set(w, seg);
      }
    }
    return map;
  }, [row]);

  return (
    <>
      {/* Label cell */}
      <Box
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
          borderBottom: 1,
          borderColor: 'divider',
        }}
      >
        <Box sx={{ minWidth: 0, flex: 1 }}>
          <Typography
            variant="body2"
            noWrap
            sx={{ fontWeight: 600, maxWidth: labelWidth - 40 }}
          >
            {rowLabel}
          </Typography>
        </Box>
        <Tooltip title={t('pages.fertilizers.usedInPlans')} arrow>
          <IconButton size="small" onClick={onNavigate} aria-label={row.planName}>
            <OpenInNewIcon sx={{ fontSize: 16 }} />
          </IconButton>
        </Tooltip>
      </Box>

      {/* Week cells */}
      {Array.from({ length: totalWeeks }, (_, i) => i + 1).map((w) => {
        const seg = segmentMap.get(w);
        if (!seg) {
          return (
            <Box
              key={w}
              sx={{
                py: 0.75,
                px: '2px',
                borderBottom: 1,
                borderColor: 'divider',
              }}
            />
          );
        }

        const prevSeg = segmentMap.get(w - 1);
        const isChange = !prevSeg || prevSeg.mlPerLiter !== seg.mlPerLiter;
        const color = PHASE_COLORS[seg.phaseName] ?? theme.palette.grey[600];
        const isStart = w === seg.weekStart;
        const isEnd = w === seg.weekEnd;
        const phaseLabel = t(`enums.phaseName.${seg.phaseName as PhaseName}`);
        const tooltipText = [
          phaseLabel,
          `${t('pages.gantt.week')}${seg.weekStart}–${seg.weekEnd}`,
          `${seg.mlPerLiter} ml/L`,
        ].join('\n');

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
            <Tooltip
              title={<Box sx={{ whiteSpace: 'pre-line' }}>{tooltipText}</Box>}
              arrow
            >
              <Box
                sx={{
                  width: '100%',
                  height: 24,
                  bgcolor: alpha(color, isChange ? 0.85 : 0.45),
                  borderRadius: `${isStart ? 4 : 0}px ${isEnd ? 4 : 0}px ${isEnd ? 4 : 0}px ${isStart ? 4 : 0}px`,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  overflow: 'hidden',
                }}
              >
                <Typography
                  variant="caption"
                  sx={{
                    color: '#fff',
                    fontSize: '0.65rem',
                    lineHeight: 1,
                    fontWeight: isChange ? 700 : 500,
                    textShadow: '0 1px 2px rgba(0,0,0,0.4)',
                    whiteSpace: 'nowrap',
                    opacity: isChange ? 1 : 0.7,
                  }}
                >
                  {seg.mlPerLiter}
                </Typography>
              </Box>
            </Tooltip>
          </Box>
        );
      })}
    </>
  );
}
