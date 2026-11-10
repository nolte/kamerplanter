/**
 * The history chart's view of `GET /locations/{key}/soil-analyses` (GP-FR-122): per parameter one line per method
 * series and the instants the method changed. Pure - the server already split the series per method; this only
 * reshapes, it never merges two methods or converts a value (U-002/U-003).
 */
import type { ChartParameter, SoilAnalysesResponse, SoilAnalysisPoint } from './soilAnalysisTypes';

export interface ChartPoint {
  time: number;
  value: number;
}

export interface ChartLine {
  /** Stable identity of the line: one per method and unit. */
  id: string;
  method: string;
  unit: string;
  points: ChartPoint[];
}

export interface TableRow {
  key: string;
  time: number;
  method: string;
  value: number;
  unit: string;
  source: string;
  depthCm: number | null;
  contentClass: string | null;
  /** The method differs from the analysis before: values on both sides are not comparable. */
  methodChanged: boolean;
}

export interface ParameterHistory {
  parameter: ChartParameter;
  lines: ChartLine[];
  /** Instants (ms) at which the method of this parameter changed. */
  changes: number[];
  /** Every value, oldest first - the table alternative of the chart. */
  rows: TableRow[];
}

const toTime = (iso: string) => new Date(iso).getTime();

/** The history of one parameter, or `null` when it has no value. */
export function parameterHistory(response: SoilAnalysesResponse, parameter: ChartParameter): ParameterHistory | null {
  const series = response.series.filter((item) => item.parameter === parameter && item.points.length > 0);
  if (series.length === 0) return null;
  const changes = response.method_changes
    .filter((change) => change.parameter === parameter)
    .map((change) => toTime(change.at));
  const changeSet = new Set(changes);
  const lines = series.map((item) => ({
    id: `${item.method}|${item.unit}`,
    method: item.method,
    unit: item.unit,
    points: item.points.map((point) => ({ time: toTime(point.performed_at), value: point.value })),
  }));
  const rows = series
    .flatMap((item) =>
      item.points.map((point: SoilAnalysisPoint, index) => ({
        key: `${item.method}-${item.unit}-${point.event_key}-${index}`,
        time: toTime(point.performed_at),
        method: item.method,
        value: point.value,
        unit: point.unit,
        source: point.source,
        depthCm: point.sample_depth_cm,
        contentClass: point.content_class,
        methodChanged: changeSet.has(toTime(point.performed_at)),
      })),
    )
    .sort((a, b) => a.time - b.time || a.method.localeCompare(b.method));
  return { parameter, lines, changes, rows };
}

/** Share of the time span kept free left and right of the outermost values, so no dot sits on the chart edge. */
const EDGE_SHARE = 0.05;
/** The padding of a history whose values share one day (a span of 0 has no share). */
const ONE_DAY_MS = 24 * 60 * 60 * 1000;

/**
 * The time axis of a history: its values plus a margin on both sides (#2764). Without it the newest value - often
 * the first of a new method - sits on the right edge, half a dot, with the method-change mark on top of it.
 */
export function timeDomain(history: ParameterHistory): [number, number] {
  const times = history.rows.map((row) => row.time);
  const first = Math.min(...times);
  const last = Math.max(...times);
  const pad = last > first ? (last - first) * EDGE_SHARE : ONE_DAY_MS;
  return [first - pad, last + pad];
}

/**
 * Which side of a method-change line its label goes (#2764): to the right of the line in the left half of the axis,
 * to the left of it in the right half - a change near the right edge would otherwise cut "Methodenwechsel" to "M".
 */
export function changeLabelPosition(time: number, domain: readonly [number, number]): 'insideTopLeft' | 'insideTopRight' {
  return time > (domain[0] + domain[1]) / 2 ? 'insideTopRight' : 'insideTopLeft';
}
