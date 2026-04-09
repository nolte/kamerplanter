import { useMemo, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Link } from 'react-router-dom';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import Tooltip from '@mui/material/Tooltip';
import IconButton from '@mui/material/IconButton';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import Chip from '@mui/material/Chip';
import Collapse from '@mui/material/Collapse';
import { alpha, useTheme, type Theme } from '@mui/material/styles';
import useMediaQuery from '@mui/material/useMediaQuery';
import StarIcon from '@mui/icons-material/Star';
import StarBorderIcon from '@mui/icons-material/StarBorder';
import SearchIcon from '@mui/icons-material/Search';
import WaterDropIcon from '@mui/icons-material/WaterDrop';
import AcUnitIcon from '@mui/icons-material/AcUnit';
import CottageOutlinedIcon from '@mui/icons-material/CottageOutlined';
import LocalFloristIcon from '@mui/icons-material/LocalFlorist';
import GrassIcon from '@mui/icons-material/Grass';
import DeckIcon from '@mui/icons-material/Deck';
import WbSunnyIcon from '@mui/icons-material/WbSunny';
import ForestIcon from '@mui/icons-material/Forest';
import SpaIcon from '@mui/icons-material/Spa';
import RestaurantIcon from '@mui/icons-material/Restaurant';
import FilterVintageIcon from '@mui/icons-material/FilterVintage';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import ExpandLessIcon from '@mui/icons-material/ExpandLess';
import EmptyState from '@/components/common/EmptyState';
import type { SowingCalendarEntry, FrostConfig, SowingPhase } from '@/api/types';
import { MONTH_WEEK_SPANS, getShortMonthName } from '@/utils/weekCalculation';

type PlantCategoryKey =
  | 'indoor_houseplant' | 'outdoor_ornamental' | 'outdoor_vegetable'
  | 'balcony_plant' | 'succulent_cactus' | 'tropical_foliage'
  | 'orchid' | 'herb' | 'bulb_tuber';

const CATEGORY_ICONS: Record<PlantCategoryKey, React.ReactElement> = {
  indoor_houseplant: <CottageOutlinedIcon sx={{ fontSize: 16 }} />,
  outdoor_ornamental: <LocalFloristIcon sx={{ fontSize: 16 }} />,
  outdoor_vegetable: <GrassIcon sx={{ fontSize: 16 }} />,
  balcony_plant: <DeckIcon sx={{ fontSize: 16 }} />,
  succulent_cactus: <WbSunnyIcon sx={{ fontSize: 16 }} />,
  tropical_foliage: <ForestIcon sx={{ fontSize: 16 }} />,
  orchid: <SpaIcon sx={{ fontSize: 16 }} />,
  herb: <RestaurantIcon sx={{ fontSize: 16 }} />,
  bulb_tuber: <FilterVintageIcon sx={{ fontSize: 16 }} />,
};

const CATEGORY_DISPLAY_ORDER: PlantCategoryKey[] = [
  'outdoor_vegetable', 'herb', 'outdoor_ornamental', 'bulb_tuber',
  'balcony_plant', 'indoor_houseplant', 'tropical_foliage',
  'succulent_cactus', 'orchid',
];

const PHASE_COLORS: Record<SowingPhase, string> = {
  indoor_sowing: '#FDD835',
  outdoor_planting: '#66BB6A',
  harvest: '#FFA726',
  flowering: '#EC407A',
  growth: '#42A5F5',
  germination: '#FDD835',
  seedling: '#66BB6A',
  vegetative: '#42A5F5',
  flushing: '#AB47BC',
  ripening: '#FFA726',
};

const PHASE_I18N: Record<SowingPhase, string> = {
  indoor_sowing: 'pages.calendar.sowingCalendar.indoorSowing',
  outdoor_planting: 'pages.calendar.sowingCalendar.outdoorPlanting',
  harvest: 'pages.calendar.sowingCalendar.harvestPhase',
  flowering: 'pages.calendar.sowingCalendar.flowering',
  growth: 'pages.calendar.sowingCalendar.growth',
  germination: 'pages.calendar.sowingCalendar.germination',
  seedling: 'pages.calendar.sowingCalendar.seedling',
  vegetative: 'pages.calendar.sowingCalendar.vegetative',
  flushing: 'pages.calendar.sowingCalendar.flushing',
  ripening: 'pages.calendar.sowingCalendar.ripening',
};

interface SowingCalendarViewProps {
  entries: SowingCalendarEntry[];
  frostConfig: FrostConfig | null;
  year: number;
  favorites: Set<string>;
  onToggleFavorite: (speciesKey: string) => void;
  showFavoritesOnly: boolean;
}

/** Convert a date string (YYYY-MM-DD) to an approximate week number (1-52). */
function dateToWeek(dateStr: string): number {
  const d = new Date(dateStr);
  const jan1 = new Date(d.getFullYear(), 0, 1);
  const diff = d.getTime() - jan1.getTime();
  return Math.min(52, Math.max(1, Math.ceil((diff / 86400000 + jan1.getDay() + 1) / 7)));
}

export default function SowingCalendarView({ entries, frostConfig, year, favorites, onToggleFavorite, showFavoritesOnly }: SowingCalendarViewProps) {
  const { t, i18n } = useTranslation();
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));
  const [selectedCategories, setSelectedCategories] = useState<Set<PlantCategoryKey>>(() => new Set());
  const [legendOpen, setLegendOpen] = useState(false);

  const labelWidth = isMobile ? 120 : 210;
  const totalWeeks = 52;

  // Detect which plant categories are present in the data
  const usedCategories = useMemo(() => {
    const cats = new Set<PlantCategoryKey>();
    for (const entry of entries) {
      if (entry.plant_category) cats.add(entry.plant_category as PlantCategoryKey);
    }
    return CATEGORY_DISPLAY_ORDER.filter((c) => cats.has(c));
  }, [entries]);

  const toggleCategory = (cat: PlantCategoryKey) => {
    setSelectedCategories((prev) => {
      const next = new Set(prev);
      if (next.has(cat)) next.delete(cat);
      else next.add(cat);
      return next;
    });
  };

  // Eisheilige week for the vertical line
  const eisheiligenWeek = useMemo(() => {
    if (!frostConfig?.eisheilige_date) return null;
    return dateToWeek(frostConfig.eisheilige_date);
  }, [frostConfig]);

  // Current week indicator — only show if viewing the current year
  const todayWeek = useMemo(() => {
    const now = new Date();
    if (now.getFullYear() !== year) return null;
    const iso = now.toISOString().slice(0, 10);
    return dateToWeek(iso);
  }, [year]);

  // Detect which phases are actually present in the data for the legend
  const usedPhases = useMemo(() => {
    const phases = new Set<SowingPhase>();
    for (const entry of entries) {
      for (const bar of entry.bars) {
        phases.add(bar.phase as SowingPhase);
      }
    }
    // Return in a stable display order
    const order: SowingPhase[] = [
      'indoor_sowing', 'outdoor_planting', 'germination', 'seedling',
      'vegetative', 'flowering', 'flushing', 'ripening', 'harvest', 'growth',
    ];
    return order.filter((p) => phases.has(p));
  }, [entries]);

  // Filter by favorites, category, then sort
  const sortedEntries = useMemo(() => {
    let filtered = showFavoritesOnly
      ? entries.filter((e) => favorites.has(e.species_key))
      : entries;
    if (selectedCategories.size > 0) {
      filtered = filtered.filter((e) =>
        e.plant_category ? selectedCategories.has(e.plant_category as PlantCategoryKey) : false,
      );
    }
    return [...filtered].sort((a, b) => {
      const aFav = favorites.has(a.species_key);
      const bFav = favorites.has(b.species_key);
      if (aFav !== bFav) return aFav ? -1 : 1;
      const aName = a.common_name || a.species_name;
      const bName = b.common_name || b.species_name;
      return aName.localeCompare(bName);
    });
  }, [entries, favorites, showFavoritesOnly, selectedCategories]);

  const formatDate = (dateStr: string) => {
    const d = new Date(dateStr);
    return d.toLocaleDateString(i18n.language === 'de' ? 'de-DE' : 'en-US', {
      day: 'numeric',
      month: 'short',
    });
  };

  if (entries.length === 0) {
    return <EmptyState message={t('pages.calendar.sowingCalendar.noData')} />;
  }

  return (
    <Card>
      <CardContent>
        {/* Frost info */}
        {frostConfig && (
          <Box sx={{ display: 'flex', gap: 1.5, mb: 1.5, flexWrap: 'wrap' }}>
            <Chip
              icon={<AcUnitIcon />}
              label={`${t('pages.calendar.sowingCalendar.lastFrost')}: ${formatDate(frostConfig.last_frost_date)}`}
              size="small"
              variant="outlined"
              color="info"
            />
            <Chip
              icon={<WaterDropIcon />}
              label={`${t('pages.calendar.sowingCalendar.eisheilige')}: ${formatDate(frostConfig.eisheilige_date)}`}
              size="small"
              variant="outlined"
              color="error"
            />
          </Box>
        )}

        {/* Plant category filter chips */}
        {usedCategories.length > 1 && (
          <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.75, mb: 1.5 }} role="group" aria-label={t('pages.calendar.sowingCalendar.filterByCategory')}>
            {usedCategories.map((cat) => (
              <Chip
                key={cat}
                icon={CATEGORY_ICONS[cat]}
                label={t(`enums.plantCategory.${cat}`)}
                size="small"
                variant={selectedCategories.has(cat) ? 'filled' : 'outlined'}
                color={selectedCategories.has(cat) ? 'primary' : 'default'}
                onClick={() => toggleCategory(cat)}
                data-testid={`sowing-category-filter-${cat}`}
              />
            ))}
            {selectedCategories.size > 0 && (
              <Chip
                label={t('common.all')}
                size="small"
                variant="outlined"
                onClick={() => setSelectedCategories(new Set())}
                onDelete={() => setSelectedCategories(new Set())}
                data-testid="sowing-category-filter-clear"
              />
            )}
          </Box>
        )}

        <Box sx={{ overflowX: 'auto', WebkitOverflowScrolling: 'touch', mx: isMobile ? -1 : 0 }}>
          <Box
            sx={{
              display: 'grid',
              gridTemplateColumns: `${labelWidth}px repeat(${totalWeeks}, 1fr)`,
              minWidth: labelWidth + totalWeeks * (isMobile ? 14 : 20),
              gap: 0,
              position: 'relative',
            }}
          >
            {/* Header row: month names */}
            <Box
              sx={{
                position: 'sticky',
                left: 0,
                bgcolor: 'background.paper',
                zIndex: 2,
                borderBottom: 1,
                borderColor: 'divider',
                py: 0.5,
              }}
            />
            {MONTH_WEEK_SPANS.map((ms) => (
              <Box
                key={ms.month}
                role="columnheader"
                sx={{
                  gridColumn: `span ${ms.span}`,
                  textAlign: 'center',
                  borderBottom: 1,
                  borderColor: 'divider',
                  borderLeft: ms.month > 0 ? 1 : 0,
                  py: 0.5,
                }}
              >
                <Typography variant="caption" color="text.secondary">
                  {getShortMonthName(ms.month, i18n.language)}
                </Typography>
              </Box>
            ))}

            {/* Species rows */}
            {sortedEntries.map((entry) => (
              <SowingRow
                key={entry.species_key}
                entry={entry}
                totalWeeks={totalWeeks}
                labelWidth={labelWidth}
                eisheiligenWeek={eisheiligenWeek}
                todayWeek={todayWeek}
                formatDate={formatDate}
                t={t}
                theme={theme}
                isFavorite={favorites.has(entry.species_key)}
                onToggleFavorite={onToggleFavorite}
                isMobile={isMobile}
              />
            ))}

          </Box>
        </Box>

        {/* Legend — collapsible, auto-detect which phases are actually used */}
        <Box sx={{ mt: 2, pt: 1, borderTop: 1, borderColor: 'divider' }}>
          <Box
            sx={{ display: 'flex', alignItems: 'center', cursor: 'pointer', userSelect: 'none' }}
            onClick={() => setLegendOpen((p) => !p)}
            role="button"
            aria-expanded={legendOpen}
          >
            <Typography variant="caption" color="text.secondary" sx={{ fontWeight: 600 }}>
              {t('pages.calendar.sowingCalendar.legend')}
            </Typography>
            {legendOpen
              ? <ExpandLessIcon sx={{ fontSize: 18, color: 'text.secondary', ml: 0.5 }} />
              : <ExpandMoreIcon sx={{ fontSize: 18, color: 'text.secondary', ml: 0.5 }} />
            }
          </Box>
          <Collapse in={legendOpen}>
            <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 2, mt: 1 }}>
              {usedPhases.map((phase) => (
                <Box key={phase} sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                  <Box
                    sx={{
                      width: 16,
                      height: 12,
                      borderRadius: 0.5,
                      bgcolor: PHASE_COLORS[phase],
                    }}
                  />
                  <Typography variant="caption">{t(PHASE_I18N[phase])}</Typography>
                </Box>
              ))}
              {eisheiligenWeek && (
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                  <Box
                    sx={{
                      width: 16,
                      height: 0,
                      borderTop: '2px dashed',
                      borderColor: 'error.main',
                    }}
                  />
                  <Typography variant="caption">{t('pages.calendar.sowingCalendar.eisheilige')}</Typography>
                </Box>
              )}
              {todayWeek && (
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
                  <Typography variant="caption">{t('pages.calendar.sowingCalendar.today')}</Typography>
                </Box>
              )}
            </Box>
          </Collapse>
        </Box>
      </CardContent>
    </Card>
  );
}

function SowingRow({
  entry,
  totalWeeks,
  labelWidth,
  eisheiligenWeek,
  todayWeek,
  formatDate,
  t,
  theme,
  isFavorite,
  onToggleFavorite,
  isMobile,
}: {
  entry: SowingCalendarEntry;
  totalWeeks: number;
  labelWidth: number;
  eisheiligenWeek: number | null;
  todayWeek: number | null;
  formatDate: (d: string) => string;
  t: (key: string) => string;
  theme: Theme;
  isFavorite: boolean;
  onToggleFavorite: (speciesKey: string) => void;
  isMobile: boolean;
}) {
  const displayName = entry.common_name || entry.species_name;
  const isIndoor = entry.plant_category
    ? entry.plant_category === 'indoor_houseplant'
      || entry.plant_category === 'tropical_foliage'
      || entry.plant_category === 'orchid'
      || entry.plant_category === 'succulent_cactus'
    : !entry.bars.some((b) => b.phase === 'indoor_sowing' || b.phase === 'outdoor_planting');

  // Build tooltip
  const tooltipLines = entry.bars.map((bar) => {
    const phaseLabel = t(PHASE_I18N[bar.phase as SowingPhase] ?? bar.phase);
    return `${phaseLabel}: ${formatDate(bar.start_date)} – ${formatDate(bar.end_date)}`;
  });

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
          px: 0.5,
          borderBottom: 1,
          borderColor: 'divider',
          gap: 0.25,
        }}
      >
        <IconButton
          size="small"
          onClick={() => onToggleFavorite(entry.species_key)}
          aria-label={t('pages.calendar.sowingCalendar.toggleFavorite')}
          sx={{ p: isMobile ? 0.25 : 0.5 }}
        >
          {isFavorite ? (
            <StarIcon sx={{ fontSize: isMobile ? 16 : 20, color: 'warning.main' }} />
          ) : (
            <StarBorderIcon sx={{ fontSize: isMobile ? 16 : 20, color: 'action.disabled' }} />
          )}
        </IconButton>
        <IconButton
          size="small"
          component={Link}
          to={`/stammdaten/species/${entry.link_species_key || entry.species_key}`}
          aria-label={t('pages.calendar.sowingCalendar.viewDetails')}
          sx={{ p: isMobile ? 0.25 : 0.5 }}
        >
          <SearchIcon sx={{ fontSize: isMobile ? 16 : 20 }} />
        </IconButton>
        {isIndoor && (
          <Tooltip title={t('pages.calendar.sowingCalendar.indoorPlant')} arrow>
            <CottageOutlinedIcon sx={{ fontSize: isMobile ? 14 : 16, color: 'text.secondary', flexShrink: 0 }} />
          </Tooltip>
        )}
        <Tooltip title={entry.species_name} arrow>
          <Typography
            variant="body2"
            noWrap
            sx={{ fontWeight: 500, maxWidth: labelWidth - (isMobile ? (isIndoor ? 86 : 70) : (isIndoor ? 110 : 90)) }}
          >
            {displayName}
          </Typography>
        </Tooltip>
      </Box>

      {/* Week cells */}
      {Array.from({ length: totalWeeks }, (_, i) => i + 1).map((weekNum) => {
        // Find which bar(s) cover this week
        const matchingBar = entry.bars.find((bar) => {
          const startWeek = dateToWeek(bar.start_date);
          const endWeek = dateToWeek(bar.end_date);
          return weekNum >= startWeek && weekNum <= endWeek;
        });

        const isEisheiligen = eisheiligenWeek === weekNum;
        const isToday = todayWeek === weekNum;
        const barColor = matchingBar ? (matchingBar.color || PHASE_COLORS[matchingBar.phase as SowingPhase] || theme.palette.grey[400]) : undefined;

        // Determine rounded corners
        let borderRadius = '0';
        if (matchingBar) {
          const startWeek = dateToWeek(matchingBar.start_date);
          const endWeek = dateToWeek(matchingBar.end_date);
          const isStart = weekNum === startWeek;
          const isEnd = weekNum === endWeek;
          borderRadius = `${isStart ? 4 : 0}px ${isEnd ? 4 : 0}px ${isEnd ? 4 : 0}px ${isStart ? 4 : 0}px`;
        }

        return (
          <Box
            key={weekNum}
            sx={{
              py: 0.5,
              px: '1px',
              borderBottom: 1,
              borderColor: 'divider',
              display: 'flex',
              alignItems: 'center',
              position: 'relative',
              ...(isToday && {
                bgcolor: alpha(theme.palette.info.main, 0.10),
                borderLeft: `2px solid ${alpha(theme.palette.info.main, 0.5)}`,
                borderRight: `2px solid ${alpha(theme.palette.info.main, 0.5)}`,
              }),
              ...(isEisheiligen && {
                '&::after': {
                  content: '""',
                  position: 'absolute',
                  top: 0,
                  bottom: 0,
                  right: 0,
                  width: '2px',
                  borderRight: '2px dashed',
                  borderColor: 'error.main',
                  opacity: 0.6,
                  zIndex: 1,
                },
              }),
            }}
          >
            {matchingBar && (
              <Tooltip
                title={
                  <Box sx={{ whiteSpace: 'pre-line' }}>
                    <strong>{entry.common_name || entry.species_name}</strong>
                    {'\n'}
                    {tooltipLines.join('\n')}
                  </Box>
                }
                arrow
              >
                <Box
                  sx={{
                    width: '100%',
                    height: 20,
                    bgcolor: alpha(barColor!, 0.85),
                    borderRadius,
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
