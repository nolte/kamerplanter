import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Link as RouterLink } from 'react-router-dom';
import Box from '@mui/material/Box';
import CircularProgress from '@mui/material/CircularProgress';
import MuiLink from '@mui/material/Link';
import Tabs from '@mui/material/Tabs';
import Tab from '@mui/material/Tab';
import Table from '@mui/material/Table';
import TableBody from '@mui/material/TableBody';
import TableCell from '@mui/material/TableCell';
import TableContainer from '@mui/material/TableContainer';
import TableHead from '@mui/material/TableHead';
import TableRow from '@mui/material/TableRow';
import Paper from '@mui/material/Paper';
import Switch from '@mui/material/Switch';
import Checkbox from '@mui/material/Checkbox';
import Button from '@mui/material/Button';
import Typography from '@mui/material/Typography';
import Alert from '@mui/material/Alert';
import TextField from '@mui/material/TextField';
import InputAdornment from '@mui/material/InputAdornment';
import SearchIcon from '@mui/icons-material/Search';
import EmptyState from '@/components/common/EmptyState';
import LoadingSkeleton from '@/components/common/LoadingSkeleton';
import { useNotification } from '@/hooks/useNotification';
import { listPlantInstances } from '@/api/endpoints/plantInstances';
import { listTanks } from '@/api/endpoints/tanks';
import { listSites, listLocations } from '@/api/endpoints/sites';
import {
  bulkSetHaPublishStatus,
  listHaPublishSettings,
  setHaPublishStatus,
  type HaPublishEntityType,
} from '@/api/endpoints/haPublish';

interface EntityRow {
  key: string;
  label: string;
}

const PAGE_LIMIT = 200;

async function loadPlants(): Promise<EntityRow[]> {
  const plants = await listPlantInstances(0, PAGE_LIMIT);
  return plants.map((p) => ({ key: p.key, label: p.plant_name || p.instance_id }));
}

async function loadTanks(): Promise<EntityRow[]> {
  const tanks = await listTanks(0, PAGE_LIMIT);
  return tanks.map((t) => ({ key: t.key, label: t.name }));
}

async function loadLocations(): Promise<EntityRow[]> {
  const sites = await listSites(0, PAGE_LIMIT);
  const perSite = await Promise.all(sites.map((s) => listLocations(s.key)));
  return perSite.flat().map((l) => ({ key: l.key, label: l.name }));
}

const LOADERS: Record<HaPublishEntityType, () => Promise<EntityRow[]>> = {
  plant: loadPlants,
  tank: loadTanks,
  location: loadLocations,
};

/** Detail-page route per entity type, so a row links to its element. */
const DETAIL_PATH: Record<HaPublishEntityType, (key: string) => string> = {
  plant: (key) => `/pflanzen/plant-instances/${key}`,
  tank: (key) => `/standorte/tanks/${key}`,
  location: (key) => `/standorte/locations/${key}`,
};

interface EntityPublishTableProps {
  entityType: HaPublishEntityType;
  /** id suffix used to link tab panel to tab via aria-labelledby */
  panelId: string;
}

/**
 * One tabular view per entity type, listing every entity of that type with a
 * switch to publish it to Home Assistant or not (opt-in default).
 */
function EntityPublishTable({ entityType, panelId }: EntityPublishTableProps) {
  const { t } = useTranslation();
  const notify = useNotification();

  const [rows, setRows] = useState<EntityRow[]>([]);
  const [enabled, setEnabled] = useState<Record<string, boolean>>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);
  const [savingKey, setSavingKey] = useState<string | null>(null);
  const [search, setSearch] = useState('');
  const [selected, setSelected] = useState<Set<string>>(() => new Set());
  const [bulkSaving, setBulkSaving] = useState(false);

  /*
   * Ref to the header checkbox — used to restore focus when the bulk action bar
   * is dismissed (either after a successful bulk action or via "Clear selection").
   * This prevents focus loss when the bulk bar unmounts (UI-NFR-002 R-003/R-006).
   */
  const selectAllRef = useRef<HTMLButtonElement>(null);

  useEffect(() => {
    let active = true;
    setLoading(true);
    setError(false);
    setSearch('');
    setSelected(new Set());
    Promise.all([LOADERS[entityType](), listHaPublishSettings(entityType)])
      .then(([entities, settings]) => {
        if (!active) return;
        const enabledMap: Record<string, boolean> = {};
        for (const s of settings) enabledMap[s.entity_key] = s.enabled;
        setRows(entities);
        setEnabled(enabledMap);
      })
      .catch(() => {
        if (active) setError(true);
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
    };
  }, [entityType]);

  const handleToggle = useCallback(
    async (entityKey: string, checked: boolean) => {
      const previous = enabled[entityKey] ?? false;
      setEnabled((prev) => ({ ...prev, [entityKey]: checked }));
      setSavingKey(entityKey);
      try {
        await setHaPublishStatus(entityType, entityKey, checked);
      } catch {
        setEnabled((prev) => ({ ...prev, [entityKey]: previous }));
        notify.error(t('haPublish.saveError'));
      } finally {
        setSavingKey(null);
      }
    },
    [enabled, entityType, notify, t],
  );

  const filteredRows = useMemo(() => {
    if (!search.trim()) return rows;
    const q = search.trim().toLowerCase();
    return rows.filter((r) => r.label.toLowerCase().includes(q));
  }, [rows, search]);

  const enabledCount = useMemo(
    () => rows.filter((r) => enabled[r.key]).length,
    [rows, enabled],
  );

  const toggleSelected = useCallback((entityKey: string) => {
    setSelected((prev) => {
      const next = new Set(prev);
      if (next.has(entityKey)) next.delete(entityKey);
      else next.add(entityKey);
      return next;
    });
  }, []);

  // Header checkbox state derives from the currently visible (filtered) rows.
  const selectedVisibleCount = useMemo(
    () => filteredRows.filter((r) => selected.has(r.key)).length,
    [filteredRows, selected],
  );
  const allVisibleSelected = filteredRows.length > 0 && selectedVisibleCount === filteredRows.length;
  const someVisibleSelected = selectedVisibleCount > 0 && !allVisibleSelected;

  const toggleSelectAllVisible = useCallback(() => {
    setSelected((prev) => {
      const next = new Set(prev);
      const allSelected = filteredRows.every((r) => next.has(r.key));
      if (allSelected) {
        for (const r of filteredRows) next.delete(r.key);
      } else {
        for (const r of filteredRows) next.add(r.key);
      }
      return next;
    });
  }, [filteredRows]);

  const handleBulkSet = useCallback(
    async (value: boolean) => {
      const keys = [...selected];
      if (keys.length === 0) return;
      const previous = { ...enabled };
      setEnabled((prev) => {
        const next = { ...prev };
        for (const k of keys) next[k] = value;
        return next;
      });
      setBulkSaving(true);
      try {
        await bulkSetHaPublishStatus(
          entityType,
          keys.map((entity_key) => ({ entity_key, enabled: value })),
        );
        setSelected(new Set());
        /*
         * Restore focus to the header checkbox after the bulk bar unmounts so
         * keyboard/AT users are not stranded (UI-NFR-002 R-003/R-006).
         * setTimeout defers until after the state-driven unmount of the bar.
         */
        setTimeout(() => selectAllRef.current?.focus(), 0);
        notify.success(
          value ? t('haPublish.manage.bulkEnabled') : t('haPublish.manage.bulkDisabled'),
        );
      } catch {
        setEnabled(previous);
        notify.error(t('haPublish.saveError'));
      } finally {
        setBulkSaving(false);
      }
    },
    [selected, enabled, entityType, notify, t],
  );

  const handleBulkClear = useCallback(() => {
    setSelected(new Set());
    setTimeout(() => selectAllRef.current?.focus(), 0);
  }, []);

  if (loading) {
    return <LoadingSkeleton variant="table" rows={5} />;
  }

  if (error) {
    return <Alert severity="error">{t('haPublish.loadError')}</Alert>;
  }

  if (rows.length === 0) {
    return <EmptyState message={t('haPublish.manage.noEntities')} />;
  }

  return (
    <Box
      role="tabpanel"
      id={panelId}
      aria-labelledby={`ha-publish-tab-${entityType}`}
    >
      {/* Summary + Search row */}
      <Box
        sx={{
          display: 'flex',
          flexWrap: 'wrap',
          alignItems: 'center',
          justifyContent: 'space-between',
          gap: 1,
          mb: 1.5,
        }}
      >
        <Typography variant="body2" color="text.secondary">
          {t('haPublish.manage.publishedCount', { count: enabledCount, total: rows.length })}
        </Typography>
        <TextField
          size="small"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder={t('haPublish.manage.searchPlaceholder')}
          aria-label={t('haPublish.manage.searchAriaLabel')}
          data-testid="ha-publish-search"
          slotProps={{
            input: {
              startAdornment: (
                <InputAdornment position="start">
                  <SearchIcon fontSize="small" aria-hidden="true" />
                </InputAdornment>
              ),
            },
          }}
          sx={{ width: { xs: '100%', sm: 260 } }}
        />
      </Box>

      {/*
       * Polite live region announces bulk-bar appearance and count changes to
       * screen readers without interrupting ongoing speech (UI-NFR-002 R-011).
       * It is always rendered (never conditionally mounted) so AT can track it.
       */}
      <Box
        aria-live="polite"
        aria-atomic="true"
        sx={{ position: 'absolute', width: 1, height: 1, overflow: 'hidden', clip: 'rect(0,0,0,0)', whiteSpace: 'nowrap' }}
      >
        {selected.size > 0
          ? t('haPublish.manage.bulkSelected', { count: selected.size })
          : ''}
      </Box>

      {/* Bulk action bar — visible once at least one entity is selected */}
      {selected.size > 0 && (
        <Box
          sx={{
            display: 'flex',
            flexWrap: 'wrap',
            alignItems: 'center',
            gap: 1,
            mb: 1.5,
            p: 1,
            borderRadius: 1,
            bgcolor: 'action.selected',
          }}
          role="region"
          aria-label={t('haPublish.manage.bulkBarAria')}
        >
          <Typography variant="body2" sx={{ flexGrow: 1, minWidth: 0 }}>
            {t('haPublish.manage.bulkSelected', { count: selected.size })}
          </Typography>
          <Button
            size="small"
            variant="contained"
            disabled={bulkSaving}
            aria-busy={bulkSaving}
            data-testid="ha-publish-bulk-enable"
            onClick={() => handleBulkSet(true)}
            startIcon={bulkSaving ? <CircularProgress size={14} color="inherit" /> : undefined}
          >
            {t('haPublish.manage.bulkEnable')}
          </Button>
          <Button
            size="small"
            variant="outlined"
            disabled={bulkSaving}
            aria-busy={bulkSaving}
            data-testid="ha-publish-bulk-disable"
            onClick={() => handleBulkSet(false)}
            startIcon={bulkSaving ? <CircularProgress size={14} color="inherit" /> : undefined}
          >
            {t('haPublish.manage.bulkDisable')}
          </Button>
          <Button
            size="small"
            color="inherit"
            disabled={bulkSaving}
            data-testid="ha-publish-bulk-clear"
            onClick={handleBulkClear}
          >
            {t('haPublish.manage.bulkClear')}
          </Button>
        </Box>
      )}

      {/* No-results state after filtering */}
      {filteredRows.length === 0 ? (
        <EmptyState
          message={t('haPublish.manage.noSearchResults')}
          actionLabel={t('haPublish.manage.clearSearch')}
          onAction={() => setSearch('')}
        />
      ) : (
        <TableContainer
          component={Paper}
          variant="outlined"
          aria-busy={bulkSaving}
          sx={{
            /* Horizontal scroll on very narrow viewports (UI-NFR-001 R-006) */
            overflowX: 'auto',
            /* Sticky header needs a bounded height on desktop (UI-NFR-010 R-023) */
            maxHeight: { xs: 'none', md: 520 },
          }}
        >
          <Table
            size="small"
            stickyHeader
            aria-label={t('haPublish.manage.tableAriaLabel')}
          >
            <TableHead>
              <TableRow>
                <TableCell padding="checkbox">
                  <Checkbox
                    ref={selectAllRef}
                    checked={allVisibleSelected}
                    indeterminate={someVisibleSelected}
                    onChange={toggleSelectAllVisible}
                    data-testid="ha-publish-select-all"
                    slotProps={{ input: { 'aria-label': t('haPublish.manage.selectAllAria') } }}
                  />
                </TableCell>
                <TableCell>{t('haPublish.manage.colName')}</TableCell>
                <TableCell
                  align="right"
                  sx={{ whiteSpace: 'nowrap' }}
                >
                  {t('haPublish.manage.colPublished')}
                </TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {filteredRows.map((row) => (
                <TableRow key={row.key} hover selected={selected.has(row.key)}>
                  <TableCell padding="checkbox">
                    <Checkbox
                      checked={selected.has(row.key)}
                      onChange={() => toggleSelected(row.key)}
                      slotProps={{
                        input: {
                          'aria-label': t('haPublish.manage.selectRowAria', { name: row.label }),
                        },
                      }}
                    />
                  </TableCell>
                  <TableCell
                    sx={{
                      /* Prevent very long names from pushing the switch off-screen */
                      wordBreak: 'break-word',
                      overflowWrap: 'anywhere',
                      /*
                       * Touch-target: size="small" table has ~8px vertical padding which
                       * yields ~28px row height — too small for 48px touch-target (UI-NFR-001 R-011).
                       * Increase cell padding on xs so the link tap area meets the requirement.
                       */
                      py: { xs: 1.5, sm: 0.75 },
                    }}
                  >
                    <MuiLink
                      component={RouterLink}
                      to={DETAIL_PATH[entityType](row.key)}
                      /*
                       * `underline="always"` provides a permanent visual cue that the name
                       * is a navigation link — more discoverable than "hover" only, especially
                       * on touch devices where hover state never fires (UI-NFR-001 R-011,
                       * UI-NFR-002 R-003/R-009).
                       */
                      underline="always"
                      color="primary"
                      /*
                       * `title` adds a browser tooltip on hover (desktop) and supplies an
                       * additional Screen Reader hint without overriding the accessible name
                       * (which must stay equal to the visible label for the existing test).
                       */
                      title={t('haPublish.manage.linkTitle')}
                      data-testid={`ha-publish-link-${row.key}`}
                    >
                      {row.label}
                    </MuiLink>
                  </TableCell>
                  <TableCell align="right" sx={{ whiteSpace: 'nowrap', py: { xs: 1.5, sm: 0.75 } }}>
                    <Switch
                      checked={enabled[row.key] ?? false}
                      onChange={(_e, checked) => handleToggle(row.key, checked)}
                      disabled={savingKey === row.key}
                      data-testid={`ha-publish-toggle-${row.key}`}
                      slotProps={{
                        input: {
                          'aria-label': t('haPublish.manage.toggleAria', { name: row.label }),
                        },
                      }}
                    />
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      )}
    </Box>
  );
}

const ENTITY_TYPES: HaPublishEntityType[] = ['plant', 'tank', 'location'];

/**
 * Settings tab to centrally manage which plants, tanks and locations are
 * published to Home Assistant. Each entity type has its own table.
 */
export default function HaPublishSettingsTab() {
  const { t } = useTranslation();
  const [typeIndex, setTypeIndex] = useState(0);
  const activeType = ENTITY_TYPES[typeIndex];

  return (
    <Box>
      <Typography variant="h6" gutterBottom>
        {t('haPublish.manage.title')}
      </Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
        {t('haPublish.manage.intro')}
      </Typography>
      <Tabs
        value={typeIndex}
        onChange={(_e, v) => setTypeIndex(v)}
        sx={{ mb: 2 }}
        variant="scrollable"
        scrollButtons="auto"
        aria-label={t('haPublish.manage.subTabsAriaLabel')}
      >
        <Tab
          id="ha-publish-tab-plant"
          aria-controls="ha-publish-panel-plant"
          label={t('haPublish.manage.tabPlants')}
        />
        <Tab
          id="ha-publish-tab-tank"
          aria-controls="ha-publish-panel-tank"
          label={t('haPublish.manage.tabTanks')}
        />
        <Tab
          id="ha-publish-tab-location"
          aria-controls="ha-publish-panel-location"
          label={t('haPublish.manage.tabLocations')}
        />
      </Tabs>
      {/* Remount per type so each table loads its own data fresh */}
      <EntityPublishTable
        key={activeType}
        entityType={activeType}
        panelId={`ha-publish-panel-${activeType}`}
      />
    </Box>
  );
}
