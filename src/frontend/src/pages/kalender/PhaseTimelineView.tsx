import { useMemo } from 'react';
import { useTranslation } from 'react-i18next';
import { useNavigate } from 'react-router-dom';
import Box from '@mui/material/Box';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import Typography from '@mui/material/Typography';
import Tooltip from '@mui/material/Tooltip';
import { alpha, useTheme, type Theme } from '@mui/material/styles';
import useMediaQuery from '@mui/material/useMediaQuery';
import OpenInNewIcon from '@mui/icons-material/OpenInNew';
import EmptyState from '@/components/common/EmptyState';
import type { CalendarEvent } from '@/api/types';

// ── Phase color palette ─────────────────────────────────────────────

const PHASE_COLORS: Record<string, string> = {
  germination: '#81C784',
  seedling: '#66BB6A',
  vegetative: '#43A047',
  flowering: '#AB47BC',
  harvest: '#EF5350',
  drying: '#FF7043',
  curing: '#FFA726',
  flushing: '#42A5F5',
  ripening: '#FF8A65',
  cloning: '#26A69A',
};

const FALLBACK_PALETTE = [
  '#7E57C2', '#5C6BC0', '#29B6F6', '#26C6DA', '#66BB6A',
  '#D4E157', '#FFCA28', '#FFA726', '#EC407A', '#78909C',
];

function getPhaseColor(phaseName: string): string {
  const key = phaseName.toLowerCase().replace(/[^a-z]/g, '');
  if (PHASE_COLORS[key]) return PHASE_COLORS[key];
  let hash = 0;
  for (let i = 0; i < phaseName.length; i++) {
    hash = (hash * 31 + phaseName.charCodeAt(i)) | 0;
  }
  return FALLBACK_PALETTE[Math.abs(hash) % FALLBACK_PALETTE.length];
}

// ── Types ───────────────────────────────────────────────────────────

interface RunGroup {
  runKey: string;
  runName: string;
  plants: PlantRow[];
}

interface PlantRow {
  plantKey: string;
  plantLabel: string;
  phases: PhaseBar[];
}

interface PhaseBar {
  id: string;
  phaseName: string;
  startDay: number; // 1-based day of month (clamped to month range)
  endDay: number;   // 1-based day of month (clamped to month range)
  color: string;
  isOngoing: boolean;
  status: 'completed' | 'current' | 'projected';
}

interface PhaseTimelineViewProps {
  events: CalendarEvent[];
  year: number;
  month: number; // 0-based
}

// ── Component ───────────────────────────────────────────────────────

export default function PhaseTimelineView({ events, year, month }: PhaseTimelineViewProps) {
  const { t, i18n } = useTranslation();
  const navigate = useNavigate();
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));

  const daysInMonth = new Date(year, month + 1, 0).getDate();
  const labelWidth = isMobile ? 130 : 200;
  const today = new Date();
  const todayDay = today.getFullYear() === year && today.getMonth() === month ? today.getDate() : null;

  // Extract phase_transition events only
  const phaseEvents = useMemo(
    () => events.filter((e) => e.source === 'phase_transition' && e.start && e.end),
    [events],
  );

  // Group events into RunGroup → PlantRow → PhaseBar
  const runGroups = useMemo(() => {
    const groupMap = new Map<string, { runName: string; plantsMap: Map<string, { label: string; phases: PhaseBar[] }> }>();
    // Use pure date numbers (YYYYMMDD) for comparisons to avoid timezone/time-of-day issues
    const monthFirstDay = 1;
    const monthLastDay = daysInMonth;
    const monthStartNum = year * 10000 + (month + 1) * 100 + 1;
    const monthEndNum = year * 10000 + (month + 1) * 100 + daysInMonth;

    for (const ev of phaseEvents) {
      const meta = ev.metadata as Record<string, string>;
      const rk = meta?.run_key || '_standalone';
      const rn = meta?.run_name || t('pages.calendar.phaseTimeline.noRun');
      const pk = meta?.plant_instance_key || ev.plant_key || '';
      const pl = meta?.plant_name || meta?.instance_id || pk;
      const phaseName = meta?.phase_name || '';

      if (!groupMap.has(rk)) {
        groupMap.set(rk, { runName: rn, plantsMap: new Map() });
      }
      const group = groupMap.get(rk)!;
      if (!group.plantsMap.has(pk)) {
        group.plantsMap.set(pk, { label: pl, phases: [] });
      }

      // Extract date parts directly to avoid timezone shifts
      const evStart = new Date(ev.start!);
      const evEnd = new Date(ev.end!);
      const startNum = evStart.getFullYear() * 10000 + (evStart.getMonth() + 1) * 100 + evStart.getDate();
      const endNum = evEnd.getFullYear() * 10000 + (evEnd.getMonth() + 1) * 100 + evEnd.getDate();

      // Clamp to month boundaries
      const clampedStart = startNum < monthStartNum ? monthFirstDay : evStart.getDate();
      const clampedEnd = endNum > monthEndNum ? monthLastDay : evEnd.getDate();

      if (clampedStart <= monthLastDay && clampedEnd >= monthFirstDay) {
        const startDay = Math.max(monthFirstDay, clampedStart);
        const endDay = Math.min(monthLastDay, clampedEnd);
        const phaseStatus = (meta?.status as 'completed' | 'current' | 'projected') || 'completed';

        group.plantsMap.get(pk)!.phases.push({
          id: ev.id,
          phaseName,
          startDay,
          endDay,
          color: getPhaseColor(phaseName),
          isOngoing: ev.end !== null && endNum >= monthEndNum,
          status: phaseStatus,
        });
      }
    }

    const result: RunGroup[] = [];
    for (const [rk, group] of groupMap) {
      const plants: PlantRow[] = [];
      for (const [pk, pl] of group.plantsMap) {
        plants.push({
          plantKey: pk,
          plantLabel: pl.label,
          phases: pl.phases.sort((a, b) => a.startDay - b.startDay),
        });
      }
      plants.sort((a, b) => a.plantLabel.localeCompare(b.plantLabel));
      result.push({ runKey: rk, runName: group.runName, plants });
    }
    result.sort((a, b) => a.runName.localeCompare(b.runName));
    return result;
  }, [phaseEvents, year, month, daysInMonth, t]);

  // Detect used phases for legend
  const usedPhases = useMemo(() => {
    const phases = new Map<string, string>();
    for (const g of runGroups) {
      for (const p of g.plants) {
        for (const bar of p.phases) {
          phases.set(bar.phaseName, bar.color);
        }
      }
    }
    return [...phases.entries()].sort((a, b) => a[0].localeCompare(b[0]));
  }, [runGroups]);

  const formatDayHeader = (day: number) => {
    if (isMobile) return day % 2 === 1 ? String(day) : '';
    return String(day);
  };

  const locale = i18n.language === 'de' ? 'de-DE' : 'en-US';
  const monthName = new Date(year, month, 1).toLocaleDateString(locale, { month: 'long', year: 'numeric' });

  if (phaseEvents.length === 0) {
    return <EmptyState message={t('pages.calendar.phaseTimeline.noData')} />;
  }

  return (
    <Card>
      <CardContent>
        {/* Timeline grid */}
        <Box sx={{ overflowX: 'auto' }}>
          <Box
            sx={{
              display: 'grid',
              gridTemplateColumns: `${labelWidth}px repeat(${daysInMonth}, 1fr)`,
              minWidth: labelWidth + daysInMonth * (isMobile ? 18 : 28),
              gap: 0,
              position: 'relative',
            }}
          >
            {/* Day header row */}
            <Box
              sx={{
                position: 'sticky',
                left: 0,
                bgcolor: 'background.paper',
                zIndex: 3,
                borderBottom: 2,
                borderColor: 'divider',
                py: 0.5,
                px: 0.5,
              }}
            >
              <Typography variant="caption" sx={{ fontWeight: 'bold', color: 'text.secondary' }}>
                {monthName}
              </Typography>
            </Box>
            {Array.from({ length: daysInMonth }, (_, i) => i + 1).map((day) => {
              const isWeekend = new Date(year, month, day).getDay() % 6 === 0;
              const isToday = day === todayDay;
              return (
                <Box
                  key={day}
                  sx={{
                    textAlign: 'center',
                    borderBottom: 2,
                    borderColor: 'divider',
                    py: 0.5,
                    bgcolor: isToday
                      ? alpha(theme.palette.info.main, 0.15)
                      : isWeekend
                        ? alpha(theme.palette.action.hover, 0.5)
                        : 'transparent',
                  }}
                >
                  <Typography
                    variant="caption"
                    sx={{
                      fontWeight: isToday ? 'bold' : 'normal',
                      color: isToday ? 'info.main' : 'text.secondary',
                      fontSize: isMobile ? '0.6rem' : '0.7rem',
                    }}
                  >
                    {formatDayHeader(day)}
                  </Typography>
                </Box>
              );
            })}

            {/* Run groups with plant rows */}
            {runGroups.map((group) => (
              <RunGroupRows
                key={group.runKey}
                group={group}
                daysInMonth={daysInMonth}
                labelWidth={labelWidth}
                todayDay={todayDay}
                year={year}
                month={month}
                theme={theme}
                isMobile={isMobile}
                onNavigate={navigate}
                locale={locale}
              />
            ))}
          </Box>
        </Box>

        {/* Legend */}
        {usedPhases.length > 0 && (
          <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 2, mt: 2, pt: 1, borderTop: 1, borderColor: 'divider' }}>
            {usedPhases.map(([name, color]) => (
              <Box key={name} sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                <Box sx={{ width: 16, height: 12, borderRadius: 0.5, bgcolor: color }} />
                <Typography variant="caption">{name}</Typography>
              </Box>
            ))}
            {todayDay && (
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                <Box
                  sx={{
                    width: 16,
                    height: 12,
                    borderRadius: 0.5,
                    bgcolor: alpha(theme.palette.info.main, 0.25),
                    border: '1.5px solid',
                    borderColor: 'info.main',
                  }}
                />
                <Typography variant="caption">{t('pages.calendar.phaseTimeline.today')}</Typography>
              </Box>
            )}
          </Box>
        )}
      </CardContent>
    </Card>
  );
}

// ── Run group sub-component ─────────────────────────────────────────

function RunGroupRows({
  group,
  daysInMonth,
  labelWidth,
  todayDay,
  year,
  month,
  theme,
  isMobile,
  onNavigate,
  locale,
}: {
  group: RunGroup;
  daysInMonth: number;
  labelWidth: number;
  todayDay: number | null;
  year: number;
  month: number;
  theme: Theme;
  isMobile: boolean;
  onNavigate: (path: string) => void;
  locale: string;
}) {
  const isStandalone = group.runKey === '_standalone';

  return (
    <>
      {/* Run header row */}
      {!isStandalone && (
        <>
          <Box
            sx={{
              position: 'sticky',
              left: 0,
              bgcolor: alpha(theme.palette.primary.main, 0.06),
              zIndex: 2,
              display: 'flex',
              alignItems: 'center',
              py: 0.5,
              px: 1,
              borderBottom: 1,
              borderColor: 'divider',
              cursor: 'pointer',
              '&:hover': { bgcolor: alpha(theme.palette.primary.main, 0.12) },
            }}
            onClick={() => onNavigate(`/durchlaeufe/planting-runs/${group.runKey}`)}
          >
            <Typography variant="body2" sx={{ fontWeight: 700, color: 'primary.main' }} noWrap>
              {group.runName}
            </Typography>
            <OpenInNewIcon sx={{ fontSize: '0.75rem', ml: 0.5, color: 'primary.main' }} />
          </Box>
          {/* Empty cells for run header */}
          {Array.from({ length: daysInMonth }, (_, i) => (
            <Box
              key={i}
              sx={{
                bgcolor: alpha(theme.palette.primary.main, 0.06),
                borderBottom: 1,
                borderColor: 'divider',
              }}
            />
          ))}
        </>
      )}

      {/* Plant rows */}
      {group.plants.map((plant) => (
        <PlantPhaseRow
          key={plant.plantKey}
          plant={plant}
          daysInMonth={daysInMonth}
          labelWidth={labelWidth}
          todayDay={todayDay}
          year={year}
          month={month}
          theme={theme}
          isMobile={isMobile}
          indented={!isStandalone}
          onNavigate={onNavigate}
          locale={locale}
        />
      ))}
    </>
  );
}

// ── Plant row sub-component ─────────────────────────────────────────

function PlantPhaseRow({
  plant,
  daysInMonth,
  labelWidth,
  todayDay,
  year,
  month,
  theme,
  isMobile,
  indented,
  onNavigate,
  locale,
}: {
  plant: PlantRow;
  daysInMonth: number;
  labelWidth: number;
  todayDay: number | null;
  year: number;
  month: number;
  theme: Theme;
  isMobile: boolean;
  indented: boolean;
  onNavigate: (path: string) => void;
  locale: string;
}) {
  const { t } = useTranslation();

  // Build a map: day → phase bar
  const dayPhaseMap = useMemo(() => {
    const map = new Map<number, PhaseBar>();
    for (const bar of plant.phases) {
      for (let d = bar.startDay; d <= bar.endDay; d++) {
        map.set(d, bar);
      }
    }
    return map;
  }, [plant.phases]);

  const formatDate = (day: number) =>
    new Date(year, month, day).toLocaleDateString(locale, { day: 'numeric', month: 'short' });

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
          py: 0.5,
          pl: indented ? 2.5 : 0.5,
          pr: 0.5,
          borderBottom: 1,
          borderColor: 'divider',
          cursor: 'pointer',
          '&:hover': { bgcolor: 'action.hover' },
        }}
        onClick={() => onNavigate(`/pflanzen/plant-instances/${plant.plantKey}`)}
      >
        <Tooltip title={plant.plantLabel} arrow>
          <Typography
            variant="body2"
            noWrap
            sx={{
              fontWeight: 500,
              maxWidth: labelWidth - (indented ? 30 : 10),
              color: 'primary.main',
              fontSize: isMobile ? '0.75rem' : undefined,
            }}
          >
            {plant.plantLabel}
          </Typography>
        </Tooltip>
      </Box>

      {/* Day cells with phase bars */}
      {Array.from({ length: daysInMonth }, (_, i) => i + 1).map((day) => {
        const bar = dayPhaseMap.get(day);
        const isWeekend = new Date(year, month, day).getDay() % 6 === 0;
        const isToday = day === todayDay;

        // Determine rounded corners for bar edges
        let borderRadius = '0';
        if (bar) {
          const isStart = day === bar.startDay;
          const isEnd = day === bar.endDay;
          borderRadius = `${isStart ? 4 : 0}px ${isEnd ? 4 : 0}px ${isEnd ? 4 : 0}px ${isStart ? 4 : 0}px`;
        }

        return (
          <Box
            key={day}
            sx={{
              py: 0.5,
              px: '1px',
              borderBottom: 1,
              borderColor: 'divider',
              display: 'flex',
              alignItems: 'center',
              bgcolor: isToday
                ? alpha(theme.palette.info.main, 0.10)
                : isWeekend
                  ? alpha(theme.palette.action.hover, 0.3)
                  : 'transparent',
            }}
          >
            {bar && (
              <Tooltip
                title={
                  <Box sx={{ whiteSpace: 'pre-line' }}>
                    <strong>{plant.plantLabel}</strong>
                    {'\n'}
                    {bar.phaseName}: {formatDate(bar.startDay)} – {formatDate(bar.endDay)}
                    {bar.status === 'projected' ? ` (${t('pages.calendar.phaseTimeline.projected')})` : ''}
                    {bar.isOngoing && bar.status !== 'projected' ? ` (\u2026)` : ''}
                  </Box>
                }
                arrow
              >
                <Box
                  sx={{
                    width: '100%',
                    height: 20,
                    borderRadius,
                    ...(bar.status === 'projected'
                      ? {
                          background: `repeating-linear-gradient(
                            45deg,
                            ${alpha(bar.color, 0.35)},
                            ${alpha(bar.color, 0.35)} 3px,
                            ${alpha(bar.color, 0.15)} 3px,
                            ${alpha(bar.color, 0.15)} 6px
                          )`,
                          border: `1px dashed ${alpha(bar.color, 0.6)}`,
                        }
                      : bar.isOngoing && day === bar.endDay
                        ? {
                            background: `linear-gradient(90deg, ${alpha(bar.color, 0.85)} 60%, ${alpha(bar.color, 0.3)} 100%)`,
                          }
                        : {
                            bgcolor: alpha(bar.color, 0.85),
                          }),
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
