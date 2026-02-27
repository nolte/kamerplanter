import client from '../client';
import type {
  WateringConfirmRequest,
  WateringConfirmResponse,
  WateringQuickConfirmRequest,
} from '../types';

export async function confirmWatering(
  data: WateringConfirmRequest,
): Promise<WateringConfirmResponse> {
  const { data: result } = await client.post<WateringConfirmResponse>(
    '/watering-events/confirm',
    data,
  );
  return result;
}

export async function quickConfirmWatering(
  data: WateringQuickConfirmRequest,
): Promise<WateringConfirmResponse> {
  const { data: result } = await client.post<WateringConfirmResponse>(
    '/watering-events/quick-confirm',
    data,
  );
  return result;
}
