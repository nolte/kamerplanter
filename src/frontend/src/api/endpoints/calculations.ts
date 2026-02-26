import client from '../client';
import type {
  VPDRequest,
  VPDResponse,
  GDDRequest,
  GDDResponse,
  PhotoperiodTransitionRequest,
  PhotoperiodScheduleEntry,
  SlotCapacityRequest,
  SlotCapacityResponse,
  SunTimesRequest,
  SunTimesResponse,
} from '../types';

const BASE = '/calculations';

export async function calculateVPD(payload: VPDRequest): Promise<VPDResponse> {
  const { data } = await client.post<VPDResponse>(`${BASE}/vpd`, payload);
  return data;
}

export async function calculateGDD(payload: GDDRequest): Promise<GDDResponse> {
  const { data } = await client.post<GDDResponse>(`${BASE}/gdd`, payload);
  return data;
}

export async function calculatePhotoperiodTransition(
  payload: PhotoperiodTransitionRequest,
): Promise<PhotoperiodScheduleEntry[]> {
  const { data } = await client.post<PhotoperiodScheduleEntry[]>(
    `${BASE}/photoperiod-transition`,
    payload,
  );
  return data;
}

export async function calculateSunTimes(payload: SunTimesRequest): Promise<SunTimesResponse> {
  const { data } = await client.post<SunTimesResponse>(`${BASE}/sun-times`, payload);
  return data;
}

export async function calculateSlotCapacity(
  payload: SlotCapacityRequest,
): Promise<SlotCapacityResponse> {
  const { data } = await client.post<SlotCapacityResponse>(`${BASE}/slot-capacity`, payload);
  return data;
}
