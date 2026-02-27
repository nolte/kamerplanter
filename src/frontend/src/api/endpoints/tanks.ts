import client from '../client';
import type {
  DueMaintenance,
  MaintenanceLog,
  MaintenanceLogCreate,
  MaintenanceSchedule,
  MaintenanceScheduleCreate,
  MaintenanceScheduleUpdate,
  Tank,
  TankAlert,
  TankCreate,
  TankState,
  TankStateCreate,
  TankUpdate,
} from '../types';

const BASE = '/tanks';

// ── Tank CRUD ──────────────────────────────────────────────────────────

export async function listTanks(
  offset = 0,
  limit = 50,
  tankType?: string,
): Promise<Tank[]> {
  const params: Record<string, string | number> = { offset, limit };
  if (tankType) params.tank_type = tankType;
  const { data } = await client.get<Tank[]>(BASE, { params });
  return data;
}

export async function getTank(key: string): Promise<Tank> {
  const { data } = await client.get<Tank>(`${BASE}/${key}`);
  return data;
}

export async function createTank(payload: TankCreate): Promise<Tank> {
  const { data } = await client.post<Tank>(BASE, payload);
  return data;
}

export async function updateTank(
  key: string,
  payload: TankUpdate,
): Promise<Tank> {
  const { data } = await client.put<Tank>(`${BASE}/${key}`, payload);
  return data;
}

export async function deleteTank(key: string): Promise<void> {
  await client.delete(`${BASE}/${key}`);
}

// ── States ─────────────────────────────────────────────────────────────

export async function recordState(
  tankKey: string,
  payload: TankStateCreate,
): Promise<TankState> {
  const { data } = await client.post<TankState>(
    `${BASE}/${tankKey}/states`,
    payload,
  );
  return data;
}

export async function getStates(
  tankKey: string,
  offset = 0,
  limit = 50,
): Promise<TankState[]> {
  const { data } = await client.get<TankState[]>(
    `${BASE}/${tankKey}/states`,
    { params: { offset, limit } },
  );
  return data;
}

export async function getLatestState(
  tankKey: string,
): Promise<TankState | null> {
  const { data } = await client.get<TankState | null>(
    `${BASE}/${tankKey}/states/latest`,
  );
  return data;
}

// ── Alerts ─────────────────────────────────────────────────────────────

export async function getAlerts(tankKey: string): Promise<TankAlert[]> {
  const { data } = await client.get<TankAlert[]>(
    `${BASE}/${tankKey}/alerts`,
  );
  return data;
}

// ── Maintenance logs ───────────────────────────────────────────────────

export async function logMaintenance(
  tankKey: string,
  payload: MaintenanceLogCreate,
): Promise<MaintenanceLog> {
  const { data } = await client.post<MaintenanceLog>(
    `${BASE}/${tankKey}/maintenance`,
    payload,
  );
  return data;
}

export async function getMaintenanceHistory(
  tankKey: string,
  offset = 0,
  limit = 50,
): Promise<MaintenanceLog[]> {
  const { data } = await client.get<MaintenanceLog[]>(
    `${BASE}/${tankKey}/maintenance`,
    { params: { offset, limit } },
  );
  return data;
}

export async function getDueMaintenances(
  tankKey: string,
): Promise<DueMaintenance[]> {
  const { data } = await client.get<DueMaintenance[]>(
    `${BASE}/${tankKey}/maintenance/due`,
  );
  return data;
}

// ── Schedules ──────────────────────────────────────────────────────────

export async function createSchedule(
  tankKey: string,
  payload: MaintenanceScheduleCreate,
): Promise<MaintenanceSchedule> {
  const { data } = await client.post<MaintenanceSchedule>(
    `${BASE}/${tankKey}/schedules`,
    payload,
  );
  return data;
}

export async function getSchedules(
  tankKey: string,
): Promise<MaintenanceSchedule[]> {
  const { data } = await client.get<MaintenanceSchedule[]>(
    `${BASE}/${tankKey}/schedules`,
  );
  return data;
}

export async function updateSchedule(
  tankKey: string,
  scheduleKey: string,
  payload: MaintenanceScheduleUpdate,
): Promise<MaintenanceSchedule> {
  const { data } = await client.put<MaintenanceSchedule>(
    `${BASE}/${tankKey}/schedules/${scheduleKey}`,
    payload,
  );
  return data;
}

export async function deleteSchedule(
  tankKey: string,
  scheduleKey: string,
): Promise<void> {
  await client.delete(`${BASE}/${tankKey}/schedules/${scheduleKey}`);
}

// ── Global maintenance overview ────────────────────────────────────────

export async function getAllDueMaintenances(): Promise<DueMaintenance[]> {
  const { data } = await client.get<DueMaintenance[]>(
    `${BASE}/maintenance/due`,
  );
  return data;
}

// ── Relationships ──────────────────────────────────────────────────────

export async function linkFeedsFrom(
  tankKey: string,
  sourceTankKey: string,
): Promise<void> {
  await client.post(`${BASE}/${tankKey}/feeds-from`, {
    source_tank_key: sourceTankKey,
  });
}
