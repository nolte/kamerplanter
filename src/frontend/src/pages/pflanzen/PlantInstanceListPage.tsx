import { useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import Button from '@mui/material/Button';
import Box from '@mui/material/Box';
import Chip from '@mui/material/Chip';
import FormControlLabel from '@mui/material/FormControlLabel';
import Switch from '@mui/material/Switch';
import Tooltip from '@mui/material/Tooltip';
import Typography from '@mui/material/Typography';
import IconButton from '@mui/material/IconButton';
import AddIcon from '@mui/icons-material/Add';
import ContentCopyIcon from '@mui/icons-material/ContentCopy';
import PageTitle from '@/components/layout/PageTitle';
import DataTable, { type Column } from '@/components/common/DataTable';
import { useAppDispatch, useAppSelector } from '@/store/hooks';
import { fetchPlantInstances } from '@/store/slices/plantInstancesSlice';
import { useTableUrlState } from '@/hooks/useTableState';
import type { PlantInstance, Species, Cultivar, Site, Location, Slot } from '@/api/types';
import { listSpecies, listCultivars } from '@/api/endpoints/species';
import { listSites, listLocations, getSlot } from '@/api/endpoints/sites';
import PlantInstanceCreateDialog, { type PlantInstanceDuplicateData } from './PlantInstanceCreateDialog';
import { kamiPlants } from '@/assets/brand/illustrations';

export default function PlantInstanceListPage() {
  const { t } = useTranslation();
  const dispatch = useAppDispatch();
  const navigate = useNavigate();
  const { items, loading } = useAppSelector((s) => s.plantInstances);
  const [createOpen, setCreateOpen] = useState(false);
  const [duplicateData, setDuplicateData] = useState<PlantInstanceDuplicateData | undefined>();
  const [hideRemoved, setHideRemoved] = useState(true);
  const [speciesMap, setSpeciesMap] = useState<Map<string, Species>>(new Map());
  const [cultivarMap, setCultivarMap] = useState<Map<string, Cultivar>>(new Map());
  const [siteMap, setSiteMap] = useState<Map<string, Site>>(new Map());
  const [locationMap, setLocationMap] = useState<Map<string, Location>>(new Map());
  const [slotMap, setSlotMap] = useState<Map<string, Slot>>(new Map());
  const tableState = useTableUrlState({ defaultSort: { column: 'plantedOn', direction: 'desc' } });

  useEffect(() => {
    dispatch(fetchPlantInstances({}));
    listSpecies(0, 500).then((res) => {
      const map = new Map<string, Species>();
      for (const s of res.items) map.set(s.key, s);
      setSpeciesMap(map);
    }).catch(() => {});
    // Load sites + all locations
    listSites(0, 200).then((sites) => {
      const sm = new Map<string, Site>();
      for (const s of sites) sm.set(s.key, s);
      setSiteMap(sm);
      return Promise.all(sites.map((s) => listLocations(s.key).catch(() => [] as Location[])));
    }).then((results) => {
      const lm = new Map<string, Location>();
      for (const locs of results) {
        for (const l of locs) lm.set(l.key, l);
      }
      setLocationMap(lm);
    }).catch(() => {});
  }, [dispatch]);

  // Load cultivars for species that have instances with cultivar_key
  useEffect(() => {
    if (items.length === 0 || speciesMap.size === 0) return;
    const speciesKeysWithCultivars = new Set(
      items.filter((p) => p.cultivar_key).map((p) => p.species_key),
    );
    if (speciesKeysWithCultivars.size === 0) return;
    const promises = [...speciesKeysWithCultivars].map((sk) =>
      listCultivars(sk).catch(() => [] as Cultivar[]),
    );
    Promise.all(promises).then((results) => {
      const map = new Map<string, Cultivar>();
      for (const cultivars of results) {
        for (const c of cultivars) map.set(c.key, c);
      }
      setCultivarMap(map);
    });
  }, [items, speciesMap]);

  // Load slots for instances that have slot_key
  useEffect(() => {
    if (items.length === 0) return;
    const slotKeys = new Set(items.map((p) => p.slot_key).filter(Boolean) as string[]);
    if (slotKeys.size === 0) return;
    Promise.all([...slotKeys].map((sk) => getSlot(sk).catch(() => null))).then((results) => {
      const map = new Map<string, Slot>();
      for (const s of results) {
        if (s) map.set(s.key, s);
      }
      setSlotMap(map);
    });
  }, [items]);

  const filteredItems = useMemo(
    () => (hideRemoved ? items.filter((p) => !p.removed_on) : items),
    [items, hideRemoved],
  );

  const columns: Column<PlantInstance>[] = [
    { id: 'instanceId', label: t('pages.plantInstances.instanceId'), render: (r) => r.instance_id },
    {
      id: 'plantName',
      label: t('pages.plantInstances.plantName'),
      render: (r) => {
        const species = speciesMap.get(r.species_key);
        const cultivar = r.cultivar_key ? cultivarMap.get(r.cultivar_key) : null;
        const displayName = r.plant_name ?? '\u2014';
        if (!species) return displayName;
        return (
          <Tooltip
            arrow
            title={
              <Box>
                <Typography variant="caption" display="block">
                  <strong>{t('entities.species')}:</strong> {species.common_names[0] ?? species.scientific_name}
                </Typography>
                <Typography variant="caption" display="block" sx={{ fontStyle: 'italic' }}>
                  {species.scientific_name}
                </Typography>
                {cultivar && (
                  <Typography variant="caption" display="block">
                    <strong>{t('entities.cultivar')}:</strong> {cultivar.name}
                  </Typography>
                )}
              </Box>
            }
          >
            <span>{displayName}</span>
          </Tooltip>
        );
      },
      searchValue: (r) => r.plant_name ?? '',
    },
    {
      id: 'location',
      label: t('entities.location'),
      render: (r) => {
        if (!r.slot_key) return '\u2014';
        const slot = slotMap.get(r.slot_key);
        if (!slot) return '\u2014';
        const location = locationMap.get(slot.location_key);
        if (!location) return slot.slot_id;
        const site = siteMap.get(location.site_key);
        const parts = [site?.name, location.name, slot.slot_id].filter(Boolean);
        return (
          <Tooltip arrow title={parts.join(' \u203A ')}>
            <span>{location.name}</span>
          </Tooltip>
        );
      },
      searchValue: (r) => {
        if (!r.slot_key) return '';
        const slot = slotMap.get(r.slot_key);
        if (!slot) return '';
        const location = locationMap.get(slot.location_key);
        if (!location) return '';
        const site = siteMap.get(location.site_key);
        return [site?.name, location.name, slot.slot_id].filter(Boolean).join(' ');
      },
    },
    {
      id: 'plantedOn',
      label: t('pages.plantInstances.plantedOn'),
      render: (r) => r.planted_on ? new Date(r.planted_on).toLocaleDateString() : '\u2014',
    },
    {
      id: 'currentPhase',
      label: t('pages.plantInstances.currentPhase'),
      render: (r) => {
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
      searchValue: (r) => t(`enums.phaseName.${r.current_phase}`, { defaultValue: r.current_phase }),
    },
    {
      id: 'removedOn',
      label: t('pages.plantInstances.removedOn'),
      render: (r) => r.removed_on ?? '\u2014',
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

  return (
    <Box data-testid="plant-instance-list-page">
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <PageTitle title={t('pages.plantInstances.title')} />
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          <FormControlLabel
            control={<Switch checked={hideRemoved} onChange={(_, v) => setHideRemoved(v)} size="small" />}
            label={t('pages.plantInstances.hideRemoved')}
          />
          <Button variant="contained" startIcon={<AddIcon />} onClick={() => { setDuplicateData(undefined); setCreateOpen(true); }} data-testid="create-button">
            {t('pages.plantInstances.create')}
          </Button>
        </Box>
      </Box>
      <DataTable
        columns={columns}
        rows={filteredItems}
        loading={loading}
        onRowClick={(r) => navigate(`/pflanzen/plant-instances/${r.key}`)}
        getRowKey={(r) => r.key}
        emptyActionLabel={t('pages.plantInstances.create')}
        onEmptyAction={() => setCreateOpen(true)}
        emptyIllustration={kamiPlants}
        tableState={tableState}
        ariaLabel={t('pages.plantInstances.title')}
      />
      <PlantInstanceCreateDialog
        open={createOpen}
        onClose={() => { setCreateOpen(false); setDuplicateData(undefined); }}
        onCreated={() => { setCreateOpen(false); setDuplicateData(undefined); dispatch(fetchPlantInstances({})); }}
        duplicateFrom={duplicateData}
      />
    </Box>
  );
}
