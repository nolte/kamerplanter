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
