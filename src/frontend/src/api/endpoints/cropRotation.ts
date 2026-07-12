import client from '../client';
import type { RotationCountsMap, RotationSuccessor, RotationSuccessorSet } from '../types';

const BASE = '/crop-rotation';

export async function getRotationCounts(): Promise<RotationCountsMap> {
  const { data } = await client.get<RotationCountsMap>(`${BASE}/counts`);
  return data;
}

export async function getSuccessors(familyKey: string): Promise<RotationSuccessor[]> {
  const { data } = await client.get<RotationSuccessor[]>(
    `${BASE}/families/${familyKey}/successors`,
  );
  return data;
}

export async function setSuccessor(payload: RotationSuccessorSet): Promise<void> {
  await client.post(`${BASE}/successors`, payload);
}
