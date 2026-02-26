import client from '../client';
import type {
  FlushingRequest,
  FlushingResponse,
  MixingProtocolRequest,
  MixingProtocolResponse,
  MixingSafetyRequest,
  MixingSafetyResponse,
  RunoffRequest,
  RunoffResponse,
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
