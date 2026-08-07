import type { LiveStateResponse } from '@/api/types';

/**
 * A live state as the backend produces it for **two** sensors of one metric —
 * two thermometers at opposite ends of one tent.
 *
 * Freshly built per call, so a test may mutate it. Typed against
 * `LiveStateResponse` on purpose: if the response type ever loses `readings` or
 * the derived view's collapse fields again, this fixture stops compiling instead
 * of quietly describing a shape the API no longer sends.
 */
export function twoThermometersLiveState(): LiveStateResponse {
  const front = {
    sensor_key: 's-front',
    sensor_name: 'Zelt vorne',
    metric_type: 'temperature_celsius',
    value: 21.4,
    last_changed: '2026-08-06T05:50:00Z',
    last_updated: '2026-08-06T05:50:00Z',
    last_reported: '2026-08-06T05:50:00Z',
    entity_id: 'sensor.zelt_vorne',
    unit: '°C',
  };
  const back = {
    sensor_key: 's-back',
    sensor_name: 'Zelt hinten',
    metric_type: 'temperature_celsius',
    value: 23.9,
    last_changed: '2026-08-06T05:59:00Z',
    last_updated: '2026-08-06T05:59:00Z',
    last_reported: '2026-08-06T05:59:00Z',
    entity_id: 'sensor.zelt_hinten',
    unit: '°C',
  };
  return {
    readings: { 's-front': front, 's-back': back },
    values: {
      temperature_celsius: {
        ...back,
        sensor_count: 2,
        superseded_sensor_keys: ['s-front'],
      },
    },
    errors: [],
    source: 'ha_live',
  };
}
