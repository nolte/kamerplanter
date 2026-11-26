import { useCallback, useEffect, useMemo, useState } from 'react';
import { useCatalogue } from '@/hooks/useCatalogue';
import CatalogueLoadError from '@/components/common/CatalogueLoadError';
import { Link as RouterLink } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import Chip from '@mui/material/Chip';
import FormControlLabel from '@mui/material/FormControlLabel';
import Switch from '@mui/material/Switch';
import Skeleton from '@mui/material/Skeleton';
import LinearProgress from '@mui/material/LinearProgress';
import Tooltip from '@mui/material/Tooltip';
import Typography from '@mui/material/Typography';
import IconButton from '@mui/material/IconButton';
import AddIcon from '@mui/icons-material/Add';
import ContentCopyIcon from '@mui/icons-material/ContentCopy';
import QrCode2Icon from '@mui/icons-material/QrCode2';
import PageTitle from '@/components/layout/PageTitle';
import PageHeaderActions from '@/components/layout/PageHeaderActions';
import { PlantLabelDialog } from '@/components/print/PlantLabelDialog';
import DataTable, { type Column } from '@/components/common/DataTable';
import { useAppDispatch, useAppSelector } from '@/store/hooks';
import { fetchAllPlantInstances } from '@/store/slices/plantInstancesSlice';
import { useTableUrlState } from '@/hooks/useTableState';
import type { PlantInstance, Species, Cultivar, Site, LocationOption, Slot } from '@/api/types';
import { listCultivars } from '@/api/endpoints/species';
import { listAllSites, listAllLocationOptions, getSlot } from '@/api/endpoints/sites';
import MobileCard from '@/components/common/MobileCard';
import PlantInstanceCreateDialog, { type PlantInstanceDuplicateData } from './PlantInstanceCreateDialog';
import SurvivalStatsPanel from './SurvivalStatsPanel';
import { useSurvivalStats } from '@/hooks/useSurvivalStats';
import { kamiPlants } from '@/assets/brand/illustrations';
import { getLocalizedCommonName, getPlantDisplayName } from '@/utils/plantDisplay';
import PlantCoverPreview from './photos/PlantCoverPreview';
import { captureHandledError } from '@/observability/errorTracking';
import { createRequestLimiter, ENRICHMENT_CONCURRENCY, RequestDroppedError } from '@/api/requestLimiter';
import { formatDate } from '@/utils/formatting';

/**
 * A read the limiter dropped because the page moved on is not a failure; every other
 * rejection of an enrichment read is logged, so a row without its label has a trace.
 */
function logEnrichmentFailure(err: unknown, source: string): void {
  if (err instanceof RequestDroppedError) return;
  captureHandledError(err, { source });
}

export default function PlantInstanceListPage() {
  const { t, i18n } = useTranslation();
  const dispatch = useAppDispatch();
  // `loading` covers only the wait for the first page; later pages append while
  // `loadingMore` is set, so a large tenant renders at once (#3032).
  const { items, loading, loadingMore = false, loadedGeneration = 0 } = useAppSelector((s) => s.plantInstances);
  const [createOpen, setCreateOpen] = useState(false);
  const [duplicateData, setDuplicateData] = useState<PlantInstanceDuplicateData | undefined>();
  const [labelDialogOpen, setLabelDialogOpen] = useState(false);
  const [hideRemoved, setHideRemoved] = useState(true);
  // The complete species catalogue through the shared reader (#1560). The
  // explicit `listSpecies(0, 500)` was legal only because the species route caps
  // at `le=1000` rather than the shared `le=200`, and it is still a bound on a
  // tenant-extensible catalogue — one whose rows this page resolves client-side,
  // so a missing row renders as an unnamed plant rather than as an error.
  const speciesCatalogue = useCatalogue('species');
  const speciesMap = useMemo(() => {
    const map = new Map<string, Species>();
    for (const s of speciesCatalogue.items) map.set(s.key, s);
    return map;
  }, [speciesCatalogue.items]);
  const [cultivarMap, setCultivarMap] = useState<Map<string, Cultivar>>(new Map());
  const [siteMap, setSiteMap] = useState<Map<string, Site>>(new Map());
  const [locationMap, setLocationMap] = useState<Map<string, LocationOption>>(new Map());
  const [slotMap, setSlotMap] = useState<Map<string, Slot>>(new Map());
  // Each row's run comes with the row (#3015): the list route resolves `planting_runs` for a whole page in one
  // read. The page used to read the plants of every run of the tenant — one request per run — to build this map.
  // The newest attached run labels the row, as the run detail is where the full membership is shown.
  const plantRunMap = useMemo(() => {
    const map = new Map<string, { runKey: string; runName: string }>();
    for (const p of items) {
      const run = p.planting_runs?.[0];
      if (run) map.set(p.key, { runKey: run.key, runName: run.name });
    }
    return map;
  }, [items]);
  const tableState = useTableUrlState({ defaultSort: { column: 'plantedOn', direction: 'desc' } });
  // REQ-003 G1 — survival / failure-cause analytics. Re-fetched whenever a
  // complete load of the instance list landed (mount, create) so the panel stays
  // in sync — keyed on the load, not on `items.length`, which now grows page by
  // page and would refetch the stats once per page.
  const { stats: survivalStats, loading: survivalStatsLoading } = useSurvivalStats(loadedGeneration);

  // Every enrichment read below goes through one limiter per page (#3032): the
  // per-key fan-out (a slot per plant, a cultivar list per species; until #3015 also
  // the plants of every run and the locations of every site) used to fire all at
  // once — hundreds of requests on a large tenant — and the browser queued the route chunk of a row click behind them, so the
  // detail page could not render for as long as the queue took. Each effect aborts
  // its queued reads when it re-runs or the page unmounts.
  const [enrichmentLimiter] = useState(() => createRequestLimiter(ENRICHMENT_CONCURRENCY));

  useEffect(() => {
    dispatch(fetchAllPlantInstances());
    const controller = new AbortController();
    const { signal } = controller;
    // Sites and every location of the tenant: two paged reads, independent of the number of sites (#3015). The
    // locations used to be read once per site. Both only label rows: a failure leaves the columns on their keys.
    listAllSites().then((sites) => {
      if (signal.aborted) return;
      const sm = new Map<string, Site>();
      for (const s of sites) sm.set(s.key, s);
      setSiteMap(sm);
    }).catch((err: unknown) => {
      // Display enrichment only: the site part of the location column stays empty; the plants come from the store.
      captureHandledError(err, { source: 'PlantInstanceListPage.siteNames' });
    });
    enrichmentLimiter.run(() => listAllLocationOptions(), signal).then((locations) => {
      if (signal.aborted) return;
      const lm = new Map<string, LocationOption>();
      for (const l of locations) lm.set(l.key, l);
      setLocationMap(lm);
    }).catch((err: unknown) => {
      // Display enrichment only: the location column shows no name; a read dropped on unmount is no failure.
      logEnrichmentFailure(err, 'PlantInstanceListPage.locationNames');
    });
    return () => controller.abort();
  }, [dispatch, enrichmentLimiter]);

  // Load cultivars for species that have instances with cultivar_key. Both
  // enrichments wait for the complete list: while pages still arrive, `items`
  // changes once per page, and re-resolving every slot on each of them would
  // multiply the requests by the page count (#3032).
  useEffect(() => {
    if (loadingMore || items.length === 0 || speciesMap.size === 0) return;
    const speciesKeysWithCultivars = new Set(
      items.filter((p) => p.cultivar_key).map((p) => p.species_key),
    );
    if (speciesKeysWithCultivars.size === 0) return;
    const controller = new AbortController();
    const { signal } = controller;
    const promises = [...speciesKeysWithCultivars].map((sk) =>
      enrichmentLimiter
        .run(() => listCultivars(sk), signal)
        .catch((err: unknown): Cultivar[] => {
          // Cultivar names only label rows; the list is complete without them.
          logEnrichmentFailure(err, 'PlantInstanceListPage.cultivars');
          return [];
        }),
    );
    Promise.all(promises).then((results) => {
      if (signal.aborted) return;
      const map = new Map<string, Cultivar>();
      for (const cultivars of results) {
        for (const c of cultivars) map.set(c.key, c);
      }
      setCultivarMap(map);
    });
    return () => controller.abort();
  }, [items, speciesMap, loadingMore, enrichmentLimiter]);

  // Load slots for instances that have slot_key
  useEffect(() => {
    if (loadingMore || items.length === 0) return;
    const slotKeys = new Set(items.map((p) => p.slot_key).filter(Boolean) as string[]);
    if (slotKeys.size === 0) return;
    const controller = new AbortController();
    const { signal } = controller;
    Promise.all(
      [...slotKeys].map((sk) =>
        enrichmentLimiter
          .run(() => getSlot(sk), signal)
          .catch((err: unknown) => {
            // Slot names only label rows; the list is complete without them.
            logEnrichmentFailure(err, 'PlantInstanceListPage.slots');
            return null;
          }),
      ),
    ).then((results) => {
      if (signal.aborted) return;
      const map = new Map<string, Slot>();
      for (const s of results) {
        if (s) map.set(s.key, s);
      }
      setSlotMap(map);
    });
    return () => controller.abort();
  }, [items, loadingMore, enrichmentLimiter]);

  const filteredItems = useMemo(
    () => (hideRemoved ? items.filter((p) => !p.removed_on) : items),
    [items, hideRemoved],
  );

  const labelPlantKeys = useMemo(
    () => filteredItems.map((p) => p.key),
    [filteredItems],
  );

  const labelPlantNames = useMemo(
    () =>
      Object.fromEntries(
        filteredItems.map((p) => [p.key, getPlantDisplayName(p, i18n.language, speciesMap.get(p.species_key), p.cultivar_key ? cultivarMap.get(p.cultivar_key) : null)]),
      ),
    [filteredItems, speciesMap, cultivarMap, i18n.language],
  );

  const columns: Column<PlantInstance>[] = [
    {
      id: 'cover',
      label: '',
      width: 64,
      sortable: false,
      render: (r) => <PlantCoverPreview plantInstanceKey={r.key} size={44} />,
    },
    { id: 'instanceId', label: t('pages.plantInstances.instanceId'), render: (r) => r.instance_id },
    {
      id: 'plantName',
      label: t('pages.plantInstances.plantName'),
      render: (r) => {
        const species = speciesMap.get(r.species_key);
        const cultivar = r.cultivar_key ? cultivarMap.get(r.cultivar_key) : null;
        const displayName = getPlantDisplayName(r, i18n.language, species, cultivar);
        // The instance_id already has its own column — avoid showing it twice.
        const shown = displayName === r.instance_id ? '—' : displayName;
        if (!species) return shown;
        return (
          <Tooltip
            arrow
            title={
              <Box>
                <Typography variant="caption" sx={{ display: 'block' }}>
                  <strong>{t('entities.species')}:</strong> {getLocalizedCommonName(species, i18n.language) ?? species.scientific_name}
                </Typography>
                <Typography variant="caption" sx={{ display: 'block', fontStyle: 'italic' }}>
                  {species.scientific_name}
                </Typography>
                {cultivar && (
                  <Typography variant="caption" sx={{ display: 'block' }}>
                    <strong>{t('entities.cultivar')}:</strong> {cultivar.name}
                  </Typography>
                )}
              </Box>
            }
          >
            <span>{shown}</span>
          </Tooltip>
        );
      },
      searchValue: (r) => getPlantDisplayName(r, i18n.language, speciesMap.get(r.species_key), r.cultivar_key ? cultivarMap.get(r.cultivar_key) : null),
    },
    {
      id: 'location',
      label: t('entities.location'),
      render: (r) => {
        if (r.slot_key) {
          const slot = slotMap.get(r.slot_key);
          if (slot) {
            const location = locationMap.get(slot.location_key);
            if (!location) return slot.slot_id;
            const site = siteMap.get(location.site_key);
            const parts = [site?.name, location.name, slot.slot_id].filter(Boolean);
            return (
              <Tooltip arrow title={parts.join(' › ')}>
                <span>{location.name}</span>
              </Tooltip>
            );
          }
        }
        // Fallback: resolve from location_key directly
        if (r.location_key) {
          const location = locationMap.get(r.location_key);
          if (location) {
            const site = siteMap.get(location.site_key);
            const parts = [site?.name, location.name].filter(Boolean);
            return (
              <Tooltip arrow title={parts.join(' › ')}>
                <span>{location.name}</span>
              </Tooltip>
            );
          }
        }
        if (r.site_key) {
          const site = siteMap.get(r.site_key);
          if (site) return site.name;
        }
        return '—';
      },
      searchValue: (r) => {
        if (r.slot_key) {
          const slot = slotMap.get(r.slot_key);
          if (slot) {
            const location = locationMap.get(slot.location_key);
            if (!location) return '';
            const site = siteMap.get(location.site_key);
            return [site?.name, location.name, slot.slot_id].filter(Boolean).join(' ');
          }
        }
        if (r.location_key) {
          const location = locationMap.get(r.location_key);
          if (location) {
            const site = siteMap.get(location.site_key);
            return [site?.name, location.name].filter(Boolean).join(' ');
          }
        }
        if (r.site_key) {
          const site = siteMap.get(r.site_key);
          if (site) return site.name;
        }
        return '';
      },
    },
    {
      id: 'plantedOn',
      label: t('pages.plantInstances.plantedOn'),
      render: (r) => r.planted_on ? formatDate(r.planted_on) : '—',
    },
    {
      id: 'currentPhase',
      label: t('pages.plantInstances.currentPhase'),
      render: (r) => {
        if (!r.current_phase) return <Typography variant="body2" color="text.secondary">{'—'}</Typography>;
        const phaseColorMap: Record<string, 'default' | 'primary' | 'secondary' | 'success' | 'warning' | 'info' | 'error'> = {
          germination: 'info',
          seedling: 'success',
          vegetative: 'primary',
          flowering: 'warning',
          harvest: 'secondary',
        };
        return (
          <Chip
            label={t(`enums.phaseName.${r.current_phase}`, { defaultValue: r.current_phase })}
            size="small"
            color={phaseColorMap[r.current_phase] ?? 'default'}
          />
        );
      },
      searchValue: (r) => r.current_phase ? t(`enums.phaseName.${r.current_phase}`, { defaultValue: r.current_phase }) : '',
    },
    {
      id: 'plantingRun',
      label: t('entities.plantingRun'),
      render: (r) => {
        const runInfo = plantRunMap.get(r.key);
        if (!runInfo) return '—';
        return (
          <Chip
            label={runInfo.runName}
            size="small"
            color="secondary"
            variant="outlined"
            // A real link (#3047). The old `/durchlaeufe/<key>` target matched no route.
            component={RouterLink}
            to={`/durchlaeufe/planting-runs/${runInfo.runKey}`}
            // The row's own handler would follow the row's link instead.
            onClick={(e) => e.stopPropagation()}
            clickable
          />
        );
      },
      searchValue: (r) => plantRunMap.get(r.key)?.runName ?? '',
    },
    {
      id: 'removedOn',
      label: t('pages.plantInstances.removedOn'),
      render: (r) =>
        r.removed_on ? formatDate(r.removed_on) : '—',
    },
    {
      id: 'actions',
      label: '',
      width: 48,
      sortable: false,
      render: (r) => (
        <Tooltip title={t('pages.plantInstances.duplicate')} arrow>
          <IconButton
            size="small"
            onClick={(e) => {
              e.stopPropagation();
              setDuplicateData({
                species_key: r.species_key,
                cultivar_key: r.cultivar_key,
                plant_name: r.plant_name,
                substrate_key: r.substrate_key,
                substrate_type_override: r.substrate_type_override,
                current_phase_key: r.current_phase_key,
                slot_key: r.slot_key,
              });
              setCreateOpen(true);
            }}
            aria-label={t('pages.plantInstances.duplicate')}
          >
            <ContentCopyIcon fontSize="small" />
          </IconButton>
        </Tooltip>
      ),
    },
  ];

  const renderMobileCard = useCallback((r: PlantInstance) => {
    const species = speciesMap.get(r.species_key);
    const cultivar = r.cultivar_key ? cultivarMap.get(r.cultivar_key) : null;
    const slot = r.slot_key ? slotMap.get(r.slot_key) : null;
    const location = slot ? locationMap.get(slot.location_key) : (r.location_key ? locationMap.get(r.location_key) : null);
    const runInfo = plantRunMap.get(r.key);
    const phaseColorMap: Record<string, 'default' | 'primary' | 'secondary' | 'success' | 'warning' | 'info' | 'error'> = {
      germination: 'info', seedling: 'success', vegetative: 'primary', flowering: 'warning', harvest: 'secondary',
    };
    const displayName = getPlantDisplayName(r, i18n.language, species, cultivar);
    return (
      <MobileCard
        leading={<PlantCoverPreview plantInstanceKey={r.key} size={48} />}
        title={displayName}
        titleId="plantName"
        subtitle={displayName !== r.instance_id ? r.instance_id : undefined}
        subtitleId="instanceId"
        chips={[
          ...(r.current_phase
            ? [{
                id: 'currentPhase',
                content: (
                  <Chip
                    label={t(`enums.phaseName.${r.current_phase}`, { defaultValue: r.current_phase })}
                    size="small"
                    color={phaseColorMap[r.current_phase] ?? 'default'}
                  />
                ),
              }]
            : []),
          ...(runInfo
            ? [{
                id: 'plantingRun',
                content: (
                  <Chip
                    label={runInfo.runName}
                    size="small"
                    color="secondary"
                    variant="outlined"
                  />
                ),
              }]
            : []),
        ]}
        fields={[
          ...(location ? [{ id: 'location', label: t('entities.location'), value: location.name }] : []),
          ...(r.planted_on ? [{ id: 'plantedOn', label: t('pages.plantInstances.plantedOn'), value: formatDate(r.planted_on) }] : []),
        ]}
      />
    );
  }, [speciesMap, cultivarMap, slotMap, locationMap, plantRunMap, t, i18n.language]);

  return (
    <Box data-testid="plant-instance-list-page">
      <PageTitle
        title={t('pages.plantInstances.title')}
        action={
          <PageHeaderActions
            // The "hide removed" switch is a filter, not an action: it has a
            // state to display rather than a command to invoke, and a menu
            // entry cannot show a toggle position. It therefore stays outside
            // the overflow via `extra` instead of being flattened into an
            // action — R-024 governs actions (G1/G2/G3), not filter controls.
            extra={
              <FormControlLabel
                control={
                  <Switch
                    checked={hideRemoved}
                    onChange={(_, v) => setHideRemoved(v)}
                    size="small"
                  />
                }
                label={t('pages.plantInstances.hideRemoved')}
                sx={{ mr: 0 }}
              />
            }
            primary={{
              label: t('pages.plantInstances.create'),
              icon: <AddIcon />,
              variant: 'contained',
              testId: 'create-button',
              onClick: () => {
                setDuplicateData(undefined);
                setCreateOpen(true);
              },
            }}
            secondary={[
              {
                label: t('print.printLabels'),
                icon: <QrCode2Icon />,
                iconOnly: true,
                disabled: filteredItems.length === 0,
                testId: 'label-button',
                onClick: () => setLabelDialogOpen(true),
              },
            ]}
          />
        }
      />

      {!loading && filteredItems.length > 0 && (
        <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
          {t('pages.plantInstances.intro')}
        </Typography>
      )}

      {survivalStatsLoading && !survivalStats && (
        <Skeleton
          variant="rectangular"
          height={160}
          sx={{ mb: 3, borderRadius: 1 }}
          data-testid="survival-stats-loading"
        />
      )}
      {survivalStats && survivalStats.total > 0 && (
        <SurvivalStatsPanel stats={survivalStats} />
      )}

      {loadingMore && (
        <Box role="status" sx={{ mb: 1 }} data-testid="plant-list-loading-more">
          <LinearProgress sx={{ height: 2, mb: 0.5 }} aria-hidden="true" />
          <Typography variant="caption" color="text.secondary">
            {t('pages.plantInstances.loadingMore', { count: items.length })}
          </Typography>
        </Box>
      )}

      {/* Lookup only: a failed load leaves plants without their species name (#1628). */}
      <CatalogueLoadError reader={speciesCatalogue} impact="lookup" />
      <DataTable
        columns={columns}
        rows={filteredItems}
        loading={loading}
        getRowHref={(r) => `/pflanzen/plant-instances/${r.key}`}
        getRowKey={(r) => r.key}
        emptyActionLabel={t('pages.plantInstances.create')}
        onEmptyAction={() => setCreateOpen(true)}
        emptyIllustration={kamiPlants}
        tableState={tableState}
        ariaLabel={t('pages.plantInstances.title')}
        mobileCardRenderer={renderMobileCard}
      />
      <PlantInstanceCreateDialog
        open={createOpen}
        onClose={() => { setCreateOpen(false); setDuplicateData(undefined); }}
        onCreated={() => { setCreateOpen(false); setDuplicateData(undefined); dispatch(fetchAllPlantInstances()); }}
        duplicateFrom={duplicateData}
      />
      <PlantLabelDialog
        open={labelDialogOpen}
        onClose={() => setLabelDialogOpen(false)}
        plantKeys={labelPlantKeys}
        plantNames={labelPlantNames}
      />
    </Box>
  );
}
