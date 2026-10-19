/**
 * The care history of the whole tenant (REQ-053 GP-FR-107, GP-API-034): every bed, newest first, the
 * last 90 days by default, with the same filters as a bed's history (category, period, bed, plant,
 * person, corrections). Reads are open to every member; a viewer or grower may name only themselves
 * in the person filter (E-16, SR-020).
 */
import { useCallback, useEffect, useMemo, useState } from 'react';
import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import PageTitle from '@/components/layout/PageTitle';
import { getCareEvents, listAllBedOptions, listBedPlantOptions } from './historyApi';
import HistoryFilterBar from './HistoryFilterBar';
import HistoryList from './HistoryList';
import { careLineToItem, isCorrectionLine } from './historyFormat';
import { activeFilterCount, emptyFilters, isRangeInverted, toQuery, type HistoryFilters } from './historyFilters';
import type { FilterOption } from './historyTypes';
import { useHistoryPages } from './useHistoryPages';
import { usePersonOptions } from './usePersonOptions';

/** GP-FR-107: the tenant-wide history shows 90 days unless the caller says otherwise. */
const DEFAULTS: HistoryFilters = emptyFilters('90d');
const NO_OPTIONS: FilterOption[] = [];

export default function CareHistoryPage() {
  const { t } = useTranslation();
  const people = usePersonOptions();
  const [filters, setFilters] = useState<HistoryFilters>(DEFAULTS);
  const [beds, setBeds] = useState<FilterOption[]>([]);
  const [plantsOf, setPlantsOf] = useState<{ bed: string; options: FilterOption[] } | null>(null);

  useEffect(() => {
    let cancelled = false;
    listAllBedOptions()
      .then((options) => {
        if (!cancelled) setBeds(options);
      })
      .catch(() => undefined);
    return () => {
      cancelled = true;
    };
  }, []);

  // The plant filter belongs to one bed: it appears once a bed is chosen and its plants have arrived.
  const { locationKey } = filters;
  useEffect(() => {
    if (!locationKey) return undefined;
    let cancelled = false;
    listBedPlantOptions(locationKey)
      .then((options) => {
        if (!cancelled) setPlantsOf({ bed: locationKey, options });
      })
      .catch(() => {
        if (!cancelled) setPlantsOf({ bed: locationKey, options: [] });
      });
    return () => {
      cancelled = true;
    };
  }, [locationKey]);
  const plants = plantsOf !== null && plantsOf.bed === locationKey ? plantsOf.options : NO_OPTIONS;

  const inverted = isRangeInverted(filters);
  const query = useMemo(() => toQuery(filters, new Date(), 'tenant'), [filters]);
  const fetchPage = useCallback(
    async (offset: number) => {
      if (inverted) return [];
      const lines = await getCareEvents(query, offset);
      return lines.map(careLineToItem);
    },
    [query, inverted],
  );
  const raw = useHistoryPages(fetchPage, JSON.stringify(query));
  // The server lists `position_corrected` lines like any other; they are corrections of the plan and stay
  // hidden unless asked for. The page size is the server's, so the "more" test above keeps using the raw page.
  const pages = useMemo(() => {
    if (raw.state.status !== 'ready' || filters.includeCorrections) return raw;
    return { ...raw, state: { ...raw.state, items: raw.state.items.filter((item) => !isCorrectionLine(item)) } };
  }, [raw, filters.includeCorrections]);

  const bedNames = useMemo(() => new Map(beds.map((bed) => [bed.key, bed.label])), [beds]);
  const bedName = useCallback((key: string) => bedNames.get(key), [bedNames]);

  return (
    <Box data-testid="care-history-page" sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
      <PageTitle title={t('pages.bed.history.page.title')} />
      <Typography variant="body2" color="text.secondary">
        {t('pages.bed.history.page.description')}
      </Typography>
      <HistoryFilterBar
        filters={filters}
        defaults={DEFAULTS}
        onChange={(patch) => setFilters((current) => ({ ...current, ...patch }))}
        onReset={() => setFilters(DEFAULTS)}
        beds={beds}
        plants={plants}
        people={people}
        testIdPrefix="care-history"
      />
      <HistoryList
        pages={pages}
        bedName={bedName}
        filtered={activeFilterCount(filters, DEFAULTS) > 0}
        testIdPrefix="care-history"
      />
    </Box>
  );
}
