import client from '../client';
import type { ModeResponse } from '../types';

/** `GET /mode` — public in both modes; carries the registration mode the auth pages adapt to (#2132). */
export async function getMode(): Promise<ModeResponse> {
  const res = await client.get<ModeResponse>('/mode');
  return res.data;
}
