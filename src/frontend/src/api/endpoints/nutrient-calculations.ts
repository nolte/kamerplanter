import { tenantClient as client } from '../client';
import type {
  EcBudgetRequest,
  EcBudgetResponse,
  FlushingRequest,
  FlushingResponse,
  MixingProtocolRequest,
  MixingProtocolResponse,
  MixingSafetyRequest,
  MixingSafetyResponse,
  RunoffRequest,
  RunoffResponse,
  WaterMixReverseRequest,
  WaterMixReverseResponse,
} from '../types';

const BASE = '/nutrient-calculations';

// ── Mixing Protocol ───────────────────────────────────────────────────

export async function calculateMixingProtocol(
  payload: MixingProtocolRequest,
): Promise<MixingProtocolResponse> {
  const { data } = await client.post<MixingProtocolResponse>(
    `${BASE}/mixing-protocol`,
    payload,
  );
  return data;
}

// ── Flushing ──────────────────────────────────────────────────────────

export async function calculateFlushing(
  payload: FlushingRequest,
): Promise<FlushingResponse> {
  const { data } = await client.post<FlushingResponse>(
    `${BASE}/flushing`,
    payload,
  );
  return data;
}

// ── Runoff ────────────────────────────────────────────────────────────

export async function calculateRunoff(
  payload: RunoffRequest,
): Promise<RunoffResponse> {
  const { data } = await client.post<RunoffResponse>(
    `${BASE}/runoff`,
    payload,
  );
  return data;
}

// ── Mixing Safety Validation ──────────────────────────────────────────

export async function validateMixingSafety(
  payload: MixingSafetyRequest,
): Promise<MixingSafetyResponse> {
  const { data } = await client.post<MixingSafetyResponse>(
    `${BASE}/mixing-safety`,
    payload,
  );
  return data;
}

// ── Water Mix Reverse ────────────────────────────────────────────────

export async function calculateWaterMixReverse(
  payload: WaterMixReverseRequest,
): Promise<WaterMixReverseResponse> {
  const { data } = await client.post<WaterMixReverseResponse>(
    `${BASE}/water-mix/reverse`,
    payload,
  );
  return data;
}

// ── EC Budget ────────────────────────────────────────────────────────

export async function calculateEcBudget(
  payload: EcBudgetRequest,
): Promise<EcBudgetResponse> {
  const { data } = await client.post<EcBudgetResponse>(
    `${BASE}/ec-budget`,
    payload,
  );
  return data;
}
