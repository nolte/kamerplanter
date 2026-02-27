import client from '../client';
import type {
  HarvestBatch,
  HarvestBatchCreate,
  HarvestBatchUpdate,
  HarvestIndicator,
  HarvestIndicatorCreate,
  HarvestObservation,
  HarvestObservationCreate,
  QualityAssessment,
  QualityAssessmentCreate,
  ReadinessAssessment,
  YieldMetric,
  YieldMetricCreate,
  YieldStats,
} from '../types';

const BASE = '/harvest';

// -- Indicators ----------------------------------------------------------

export async function getIndicators(
  offset = 0,
  limit = 50,
): Promise<HarvestIndicator[]> {
  const { data } = await client.get<HarvestIndicator[]>(
    `${BASE}/indicators`,
    { params: { offset, limit } },
  );
  return data;
}

export async function createIndicator(
  payload: HarvestIndicatorCreate,
): Promise<HarvestIndicator> {
  const { data } = await client.post<HarvestIndicator>(
    `${BASE}/indicators`,
    payload,
  );
  return data;
}

export async function getIndicatorsForSpecies(
  speciesKey: string,
): Promise<HarvestIndicator[]> {
  const { data } = await client.get<HarvestIndicator[]>(
    `${BASE}/species/${speciesKey}/indicators`,
  );
  return data;
}

// -- Observations --------------------------------------------------------

export async function createObservation(
  plantKey: string,
  payload: HarvestObservationCreate,
): Promise<HarvestObservation> {
  const { data } = await client.post<HarvestObservation>(
    `${BASE}/plants/${plantKey}/observations`,
    payload,
  );
  return data;
}

export async function getObservations(
  plantKey: string,
  offset = 0,
  limit = 50,
): Promise<HarvestObservation[]> {
  const { data } = await client.get<HarvestObservation[]>(
    `${BASE}/plants/${plantKey}/observations`,
    { params: { offset, limit } },
  );
  return data;
}

// -- Readiness -----------------------------------------------------------

export async function assessReadiness(
  plantKey: string,
): Promise<ReadinessAssessment> {
  const { data } = await client.get<ReadinessAssessment>(
    `${BASE}/plants/${plantKey}/readiness`,
  );
  return data;
}

// -- Harvest Batches -----------------------------------------------------

export async function getBatches(
  offset = 0,
  limit = 50,
): Promise<HarvestBatch[]> {
  const { data } = await client.get<HarvestBatch[]>(`${BASE}/batches`, {
    params: { offset, limit },
  });
  return data;
}

export async function createBatch(
  plantKey: string,
  payload: HarvestBatchCreate,
): Promise<HarvestBatch> {
  const { data } = await client.post<HarvestBatch>(
    `${BASE}/plants/${plantKey}/batches`,
    payload,
  );
  return data;
}

export async function getBatch(key: string): Promise<HarvestBatch> {
  const { data } = await client.get<HarvestBatch>(`${BASE}/batches/${key}`);
  return data;
}

export async function updateBatch(
  key: string,
  payload: HarvestBatchUpdate,
): Promise<HarvestBatch> {
  const { data } = await client.put<HarvestBatch>(
    `${BASE}/batches/${key}`,
    payload,
  );
  return data;
}

// -- Quality Assessment --------------------------------------------------

export async function createQualityAssessment(
  batchKey: string,
  payload: QualityAssessmentCreate,
): Promise<QualityAssessment> {
  const { data } = await client.post<QualityAssessment>(
    `${BASE}/batches/${batchKey}/quality`,
    payload,
  );
  return data;
}

export async function getQuality(
  batchKey: string,
): Promise<QualityAssessment | null> {
  const { data } = await client.get<QualityAssessment | null>(
    `${BASE}/batches/${batchKey}/quality`,
  );
  return data;
}

// -- Yield Metrics -------------------------------------------------------

export async function createYieldMetric(
  batchKey: string,
  payload: YieldMetricCreate,
): Promise<YieldMetric> {
  const { data } = await client.post<YieldMetric>(
    `${BASE}/batches/${batchKey}/yield`,
    payload,
  );
  return data;
}

export async function getYield(
  batchKey: string,
): Promise<YieldMetric | null> {
  const { data } = await client.get<YieldMetric | null>(
    `${BASE}/batches/${batchKey}/yield`,
  );
  return data;
}

// -- Yield Stats ---------------------------------------------------------

export async function getYieldStats(
  speciesKey: string,
  daysBack = 365,
): Promise<YieldStats> {
  const { data } = await client.get<YieldStats>(
    `${BASE}/species/${speciesKey}/yield-stats`,
    { params: { days_back: daysBack } },
  );
  return data;
}
