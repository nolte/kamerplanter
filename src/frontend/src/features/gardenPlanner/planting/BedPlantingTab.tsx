/**
 * The "Planting" tab of the bed view (REQ-053 §11.1, §11.3, GP-FR-066/068/069): what is planned and what
 * stands in the bed, the "Plant" button that opens the planting dialog, and the two actions on a
 * standing plant - "Correct position" and "Transplant to …". The dialog is a separate chunk.
 */
import { lazy, Suspense, useCallback, useEffect, useMemo, useState } from 'react';
import { useTranslation } from 'react-i18next';
import Alert from '@mui/material/Alert';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import Typography from '@mui/material/Typography';
import AddIcon from '@mui/icons-material/Add';
import EmptyState from '@/components/common/EmptyState';
import ErrorDisplay from '@/components/common/ErrorDisplay';
import LoadingSkeleton from '@/components/common/LoadingSkeleton';
import { parseApiError } from '@/api/errors';
import { getSpecies } from '@/api/endpoints/species';
import { useNotification } from '@/hooks/useNotification';
import { useTenantPermissions } from '@/hooks/useTenantPermissions';
import type { BedSummary } from '../bed/types';
import PlantActionHost, { type PlantActionTarget } from './PlantActionHost';
import { listPlantings } from './plantingApi';
import type { PlantingItem } from './plantingTypes';
import type { PlantedResult } from './PlantingDialog';

const PlantingDialog = lazy(() => import('./PlantingDialog'));

interface BedPlantingTabProps {
  bed: BedSummary;
  /** The bed's own data changed (plant counters, runs); the page reloads its summary. */
  onChanged: () => void;
}

type ListState =
  | { status: 'loading' }
  | { status: 'error'; message: string }
  | { status: 'ready'; items: PlantingItem[] };

/** Display names of the species in `keys` (common name, else scientific); the key until they arrive. */
function useSpeciesNames(keys: readonly string[]): ReadonlyMap<string, string> {
  const [names, setNames] = useState<ReadonlyMap<string, string>>(new Map());
  const wanted = useMemo(() => [...new Set(keys)].sort(), [keys]);
  const signature = wanted.join('|');
  useEffect(() => {
    if (wanted.length === 0) return undefined;
    let cancelled = false;
    Promise.all(
      wanted.map((key) =>
        getSpecies(key)
          .then((species): [string, string] => [key, species.common_names?.[0] || species.scientific_name])
          .catch((): [string, string] => [key, key]),
      ),
    ).then((entries) => {
      if (!cancelled) setNames(new Map(entries));
    });
    return () => {
      cancelled = true;
    };
    // `signature` is the content of `wanted`.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [signature]);
  return names;
}

export default function BedPlantingTab({ bed, onChanged }: BedPlantingTabProps) {
  const { t, i18n } = useTranslation();
  const { canEdit } = useTenantPermissions();
  const notification = useNotification();
  const [state, setState] = useState<ListState>({ status: 'loading' });
  const [attempt, setAttempt] = useState(0);
  const [planting, setPlanting] = useState(false);
  const [target, setTarget] = useState<PlantActionTarget | null>(null);

  useEffect(() => {
    let cancelled = false;
    listPlantings(bed.key)
      .then((items) => {
        if (!cancelled) setState({ status: 'ready', items });
      })
      .catch((error: unknown) => {
        if (!cancelled) setState({ status: 'error', message: parseApiError(error) });
      });
    return () => {
      cancelled = true;
    };
  }, [bed.key, attempt]);

  const reload = useCallback(() => {
    setState({ status: 'loading' });
    setAttempt((value) => value + 1);
    onChanged();
  }, [onChanged]);

  const items = useMemo(() => (state.status === 'ready' ? state.items : []), [state]);
  const planned = items.filter((item) => item.state === 'planned');
  const active = items.filter((item) => item.state === 'active');
  const finished = items.filter((item) => item.state === 'harvested' || item.state === 'historical');
  const names = useSpeciesNames(useMemo(() => items.map((item) => item.species_key), [items]));
  const nameOf = (key: string) => names.get(key) ?? key;
  const dateFormat = useMemo(() => new Intl.DateTimeFormat(i18n.language, { dateStyle: 'medium' }), [i18n.language]);
  const dateText = (value: string | null | undefined) => (value ? dateFormat.format(new Date(value)) : null);

  const placed = Boolean(bed.geometry);
  const retired = bed.bed_status === 'retired';
  const canPlant = canEdit && placed && !retired;

  const onPlanted = (result: PlantedResult) => {
    setPlanting(false);
    notification.success(
      t(result.quick ? 'pages.bed.planting.recorded' : 'pages.bed.planting.planned', { count: result.plantCount }),
    );
    reload();
  };

  return (
    <Box data-testid="bed-planting-tab" sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
      <Box sx={{ display: 'flex', flexWrap: 'wrap', alignItems: 'center', justifyContent: 'space-between', gap: 1 }}>
        <Typography variant="h6" component="h2">
          {t('pages.bed.planting.tab.title')}
        </Typography>
        {canEdit ? (
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={() => setPlanting(true)}
            disabled={!canPlant}
            sx={{ minHeight: 48 }}
            data-testid="bed-plant-button"
          >
            {t('pages.bed.planting.tab.plant')}
          </Button>
        ) : null}
      </Box>
      {canEdit && !placed ? <Alert severity="info">{t('pages.bed.planting.tab.notPlaced')}</Alert> : null}
      {canEdit && retired ? <Alert severity="info">{t('pages.bed.planting.tab.retired')}</Alert> : null}

      {state.status === 'loading' ? <LoadingSkeleton variant="card" /> : null}
      {state.status === 'error' ? <ErrorDisplay error={state.message} onRetry={reload} /> : null}
      {state.status === 'ready' && items.length === 0 ? (
        <EmptyState
          message={t('pages.bed.planting.tab.empty.title')}
          description={t('pages.bed.planting.tab.empty.description')}
        />
      ) : null}

      {planned.length > 0 ? (
        <Card variant="outlined" component="section" aria-label={t('pages.bed.planting.tab.planned', { count: planned.length })} data-testid="bed-planting-planned">
          <CardContent>
            <Typography variant="subtitle1" component="h3" gutterBottom>
              {t('pages.bed.planting.tab.planned', { count: planned.length })}
            </Typography>
            <Box component="ul" sx={{ m: 0, p: 0, listStyle: 'none', display: 'flex', flexDirection: 'column', gap: 0.5 }}>
              {planned.map((item) => (
                <li key={`${item.slot_key}-${item.run_key}`} data-testid={`planting-planned-${item.slot_key}`}>
                  {nameOf(item.species_key)} · {item.slot_id}
                  {item.planned_from ? ` · ${t('pages.bed.planting.tab.from', { date: dateText(item.planned_from) })}` : ''}
                </li>
              ))}
            </Box>
          </CardContent>
        </Card>
      ) : null}

      {active.length > 0 ? (
        <Card variant="outlined" component="section" aria-label={t('pages.bed.planting.tab.active', { count: active.length })} data-testid="bed-planting-active">
          <CardContent>
            <Typography variant="subtitle1" component="h3" gutterBottom>
              {t('pages.bed.planting.tab.active', { count: active.length })}
            </Typography>
            <Box component="ul" sx={{ m: 0, p: 0, listStyle: 'none', display: 'flex', flexDirection: 'column', gap: 1 }}>
              {active.map((item) => {
                const label = item.instance_id ?? item.plant_key ?? '';
                return (
                  <Box
                    component="li"
                    key={item.plant_key}
                    data-testid={`planting-active-${item.plant_key}`}
                    sx={{ display: 'flex', flexWrap: 'wrap', alignItems: 'center', justifyContent: 'space-between', gap: 1 }}
                  >
                    <span>
                      {label} · {nameOf(item.species_key)}
                      {item.planted_on ? ` · ${dateText(item.planted_on)}` : ''}
                    </span>
                    {canEdit && item.plant_key ? (
                      <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                        {item.slot_key && placed ? (
                          <Button
                            size="small"
                            onClick={() =>
                              setTarget({ action: 'correct', plantKey: item.plant_key!, slotKey: item.slot_key!, plantLabel: label })
                            }
                            sx={{ minHeight: 44 }}
                            data-testid={`planting-correct-${item.plant_key}`}
                          >
                            {t('pages.bed.planting.tab.correct')}
                          </Button>
                        ) : null}
                        <Button
                          size="small"
                          onClick={() =>
                            setTarget({ action: 'transplant', plantKey: item.plant_key!, slotKey: item.slot_key ?? null, plantLabel: label })
                          }
                          sx={{ minHeight: 44 }}
                          data-testid={`planting-transplant-${item.plant_key}`}
                        >
                          {t('pages.bed.planting.tab.transplant')}
                        </Button>
                      </Box>
                    ) : null}
                  </Box>
                );
              })}
            </Box>
          </CardContent>
        </Card>
      ) : null}

      {finished.length > 0 ? (
        <Typography variant="body2" color="text.secondary" data-testid="bed-planting-finished">
          {t('pages.bed.planting.tab.finished', { count: finished.length })}
        </Typography>
      ) : null}

      {planting && bed.geometry ? (
        <Suspense fallback={null}>
          <PlantingDialog
            bedKey={bed.key}
            bedName={bed.name}
            geometry={bed.geometry}
            sunExposure={bed.sun_exposure}
            onClose={() => setPlanting(false)}
            onPlanted={onPlanted}
          />
        </Suspense>
      ) : null}
      <PlantActionHost bed={bed} target={target} onClose={() => setTarget(null)} onChanged={reload} />
    </Box>
  );
}
