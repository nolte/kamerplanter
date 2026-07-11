import { tenantClient } from '../client';
import type {
  Actuator,
  ActuatorCreate,
  ActuatorState,
  ControlEvent,
  EmergencyStopScenario,
  EmergencyStopResult,
} from '../types';

// ── Actuators ─────────────────────────────────────────────────────────────

export async function listActuators(): Promise<Actuator[]> {
  const { data } = await tenantClient.get<Actuator[]>('/actuators');
  return data;
}

export async function listLocationActuators(locationKey: string): Promise<Actuator[]> {
  const { data } = await tenantClient.get<Actuator[]>(
    `/locations/${locationKey}/actuators`,
  );
  return data;
}

export async function createActuator(
  locationKey: string,
  payload: ActuatorCreate,
): Promise<Actuator> {
  const { data } = await tenantClient.post<Actuator>(
    `/locations/${locationKey}/actuators`,
    payload,
  );
  return data;
}

export async function deleteActuator(actuatorKey: string): Promise<void> {
  await tenantClient.delete(`/actuators/${actuatorKey}`);
}

// ── Command & override ─────────────────────────────────────────────────────

export async function sendCommand(
  actuatorKey: string,
  command: 'turn_on' | 'turn_off' | 'set_value',
  value?: number,
): Promise<ControlEvent> {
  const { data } = await tenantClient.post<ControlEvent>(
    `/actuators/${actuatorKey}/command`,
    { command, value: value ?? null },
  );
  return data;
}

export async function setOverride(
  actuatorKey: string,
  payload: { expires_at: string; override_state?: 'on' | 'off'; override_value?: number; reason?: string },
): Promise<{ key: string; expires_at: string; is_active: boolean }> {
  const { data } = await tenantClient.post(`/actuators/${actuatorKey}/override`, payload);
  return data;
}

export async function clearOverride(actuatorKey: string): Promise<void> {
  await tenantClient.delete(`/actuators/${actuatorKey}/override`);
}

export async function getActuatorState(actuatorKey: string): Promise<ActuatorState> {
  const { data } = await tenantClient.get<ActuatorState>(`/actuators/${actuatorKey}/state`);
  return data;
}

// ── Events ─────────────────────────────────────────────────────────────────

export async function listActuatorEvents(actuatorKey: string): Promise<ControlEvent[]> {
  const { data } = await tenantClient.get<ControlEvent[]>(`/actuators/${actuatorKey}/events`);
  return data;
}

// ── Emergency stop ─────────────────────────────────────────────────────────

export async function emergencyStop(
  scenario: EmergencyStopScenario,
): Promise<EmergencyStopResult> {
  const { data } = await tenantClient.post<EmergencyStopResult>('/emergency-stop', {
    scenario,
  });
  return data;
}
