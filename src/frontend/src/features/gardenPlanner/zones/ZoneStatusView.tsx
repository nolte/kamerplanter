import { useCallback, useEffect, useMemo, useState, type ReactNode } from 'react';
import { useTranslation } from 'react-i18next';
import Alert from '@mui/material/Alert';
import Box from '@mui/material/Box';
import Chip from '@mui/material/Chip';
import Typography from '@mui/material/Typography';
import InfoOutlinedIcon from '@mui/icons-material/InfoOutlined';
import type { PlanModel } from '../model/planModel';
import { daysSince } from './lastWatered';
import { getZoneStatus } from './zonesApi';
import type { IrrigationZone, PlanZone, ZoneHint, ZoneStatus } from './zoneTypes';

const PREFIX = 'pages.gardenPlan.editor.zones';

function useLiters(): (value: number) => string {
  const { i18n } = useTranslation();
  const format = useMemo(() => new Intl.NumberFormat(i18n.language, { maximumFractionDigits: 1 }), [i18n.language]);
  return useCallback((value: number) => format.format(value), [format]);
}

/** The text of one hint code (GP-FR-119); a code this client does not know is named, never dropped. */
function useHintText(plan: PlanModel): (hint: ZoneHint) => string {
  const { t } = useTranslation();
  const liters = useLiters();
  return useCallback((hint: ZoneHint) => {
    const { params } = hint;
    if (hint.code === 'water_source_lasts_days') {
      return t(`${PREFIX}.hints.water_source_lasts_days`, {
        count: Number(params.days ?? 0),
        capacity: liters(Number(params.capacity_liters ?? 0)),
        daily: liters(Number(params.daily_liters ?? 0)),
      });
    }
    if (hint.code === 'irrigation_system_differs') {
      const keys = Array.isArray(params.location_keys) ? params.location_keys : [];
      return t(`${PREFIX}.hints.irrigation_system_differs`, {
        type: t(`enums.irrigationType.${String(params.zone_type)}`, { defaultValue: String(params.zone_type) }),
        beds: keys.map((key) => plan.locations[key]?.name ?? key).join(', '),
      });
    }
    return t(`${PREFIX}.hints.unknown`, { code: hint.code });
  }, [plan.locations, t, liters]);
}

interface Props {
  zone: IrrigationZone | PlanZone;
  plan: PlanModel;
  /** Bumps after a watering round so the status is read again. */
  refreshToken: number;
  /** The `technical` admin scope: provenance of the consumption and the flow-rate coupling. */
  technical: boolean;
}

type Loaded = { zoneKey: string; token: number; status: ZoneStatus } | { zoneKey: string; token: number; failed: true };

/** GP-API-052: what the zone's beds were given and what is planned. Technical fields appear for the technical scope only. */
export function ZoneStatusView({ zone, plan, refreshToken, technical }: Props) {
  const { t, i18n } = useTranslation();
  const liters = useLiters();
  const hintText = useHintText(plan);
  const [loaded, setLoaded] = useState<Loaded | null>(null);

  useEffect(() => {
    const abort = new AbortController();
    getZoneStatus(zone.key, abort.signal)
      .then((status) => {
        if (!abort.signal.aborted) setLoaded({ zoneKey: zone.key, token: refreshToken, status });
      })
      .catch(() => {
        if (!abort.signal.aborted) setLoaded({ zoneKey: zone.key, token: refreshToken, failed: true });
      });
    return () => abort.abort();
  }, [zone.key, refreshToken]);

  const current = loaded?.zoneKey === zone.key && loaded.token === refreshToken ? loaded : null;
  const bedName = (key: string | null | undefined) => (key ? (plan.locations[key]?.name ?? key) : '');
  const date = (iso: string) => new Date(iso).toLocaleDateString(i18n.language, { timeZone: 'UTC' });

  return (
    <Box component="section" aria-labelledby={`zone-status-${zone.key}`} data-testid="garden-plan-zone-status" sx={{ display: 'grid', gap: 1 }}>
      <Typography variant="subtitle2" component="h4" id={`zone-status-${zone.key}`}>
        {t(`${PREFIX}.status.title`)}
      </Typography>
      {current === null ? (
        <Typography variant="body2" color="text.secondary" role="status">
          {t(`${PREFIX}.status.loading`)}
        </Typography>
      ) : 'failed' in current ? (
        <Alert severity="warning" data-testid="garden-plan-zone-status-failed">
          {t(`${PREFIX}.status.failed`)}
        </Alert>
      ) : (
        <StatusRows
          zone={zone}
          status={current.status}
          technical={technical}
          liters={liters}
          bedName={bedName}
          date={date}
          hintText={hintText}
        />
      )}
    </Box>
  );
}

interface RowsProps {
  zone: IrrigationZone | PlanZone;
  status: ZoneStatus;
  technical: boolean;
  liters: (value: number) => string;
  bedName: (key: string | null | undefined) => string;
  date: (iso: string) => string;
  hintText: (hint: ZoneHint) => string;
}

function Row({ label, testId, children }: { label: string; testId: string; children: ReactNode }) {
  return (
    <Box data-testid={testId}>
      <Typography variant="caption" color="text.secondary" component="p">
        {label}
      </Typography>
      <Typography variant="body2" component="div">
        {children}
      </Typography>
    </Box>
  );
}

function StatusRows({ zone, status, technical, liters, bedName, date, hintText }: RowsProps) {
  const { t } = useTranslation();
  const [nowMs] = useState(() => Date.now());
  const last = status.last_watering ?? null;
  const next = status.next_planned ?? null;
  const days = last ? daysSince(last.at, nowMs) : null;
  const percent = status.application_efficiency != null ? Math.round(status.application_efficiency * 100) : null;
  const record = zone as Partial<IrrigationZone>;
  return (
    <>
      <Row label={t(`${PREFIX}.status.lastWatering`)} testId="garden-plan-zone-last-watering">
        {last === null ? (
          t(`${PREFIX}.status.lastWateringNone`)
        ) : (
          <>
            {t(`${PREFIX}.status.lastWateringValue`, {
              date: date(last.at),
              days: days === null ? '' : t(`${PREFIX}.wateredDays`, { count: days }),
            })}
            {last.location_key ? ` · ${t(`${PREFIX}.status.lastWateringBed`, { bed: bedName(last.location_key) })}` : ''}
            {last.allocation !== 'measured' && (
              <Chip
                size="small"
                variant="outlined"
                icon={<InfoOutlinedIcon />}
                label={t(`enums.careEventAllocation.${last.allocation}`)}
                data-testid="garden-plan-zone-allocation-marker"
                sx={{ ml: 1 }}
              />
            )}
          </>
        )}
      </Row>
      <Row label={t(`${PREFIX}.status.nextPlanned`)} testId="garden-plan-zone-next-planned">
        {next === null
          ? t(`${PREFIX}.status.nextPlannedNone`)
          : t(`${PREFIX}.status.${next.overdue ? 'nextPlannedOverdue' : 'nextPlannedValue'}`, {
              bed: bedName(next.location_key),
              date: next.due_date ? date(next.due_date) : '–',
            })}
      </Row>
      {status.demand_liters_today != null && (
        <Row label={t(`${PREFIX}.status.demand`)} testId="garden-plan-zone-demand">
          {t(`${PREFIX}.status.demandNet`, { liters: liters(status.demand_liters_today) })}
          {status.demand_gross_liters_today != null && (
            <>
              {' · '}
              {t(`${PREFIX}.status.demandGross`, { liters: liters(status.demand_gross_liters_today) })}
            </>
          )}
          {percent !== null && (
            <>
              {' · '}
              {t(`${PREFIX}.status.efficiency`, { percent })}
              {status.efficiency_source ? ` (${t(`${PREFIX}.status.efficiencySource.${status.efficiency_source}`)})` : ''}
            </>
          )}
        </Row>
      )}
      <Row label={t(`${PREFIX}.status.consumption`)} testId="garden-plan-zone-consumption">
        {t(`${PREFIX}.status.consumptionValue`, { liters: liters(status.consumption_liters_30d) })}
      </Row>
      {technical && (
        <Box data-testid="garden-plan-zone-technical" sx={{ display: 'grid', gap: 1 }}>
          <Typography variant="subtitle2" component="h5">
            {t(`${PREFIX}.status.technical`)}
          </Typography>
          {status.consumption_sources.length > 0 && (
            <Row label={t(`${PREFIX}.status.consumptionSources`)} testId="garden-plan-zone-consumption-sources">
              <Box component="ul" sx={{ m: 0, pl: 2 }}>
                {status.consumption_sources.map((part) => (
                  <li key={part.source}>
                    {t(`${PREFIX}.status.consumptionSource.${part.source}`)}: {t(`${PREFIX}.status.consumptionValue`, { liters: liters(part.liters) })}
                  </li>
                ))}
              </Box>
            </Row>
          )}
          <Row label={t(`${PREFIX}.status.flowRate`)} testId="garden-plan-zone-flow-rate">
            {record.flow_rate_l_per_min != null
              ? t(`${PREFIX}.status.flowRateValue`, { value: liters(record.flow_rate_l_per_min) })
              : t(`${PREFIX}.status.flowRateNone`)}
            {record.flow_rate_source ? ` · ${t(`${PREFIX}.status.flowSourceValue.${record.flow_rate_source}`)}` : ''}
            {record.flow_rate_ha_entity_bound !== undefined &&
              ` · ${t(`${PREFIX}.status.${record.flow_rate_ha_entity_bound ? 'haBound' : 'haNotBound'}`)}`}
          </Row>
        </Box>
      )}
      {status.hints.length > 0 && (
        <Box data-testid="garden-plan-zone-hints">
          <Typography variant="caption" color="text.secondary" component="p">
            {t(`${PREFIX}.status.hints`)}
          </Typography>
          <Box component="ul" sx={{ m: 0, pl: 2 }}>
            {status.hints.map((hint, index) => (
              <Typography key={`${hint.code}-${index}`} component="li" variant="body2">
                {hintText(hint)}
              </Typography>
            ))}
          </Box>
        </Box>
      )}
    </>
  );
}
