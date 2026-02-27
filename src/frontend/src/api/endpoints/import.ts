import client from '../client';
import type { DuplicateStrategy, EntityType, ImportJob } from '../types';

const BASE = '/import';

export async function uploadImportFile(
  file: File,
  entityType: EntityType,
  duplicateStrategy: DuplicateStrategy,
): Promise<ImportJob> {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('entity_type', entityType);
  formData.append('duplicate_strategy', duplicateStrategy);
  const { data } = await client.post<ImportJob>(`${BASE}/upload`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return data;
}

export async function getImportJob(key: string): Promise<ImportJob> {
  const { data } = await client.get<ImportJob>(`${BASE}/jobs/${key}`);
  return data;
}

export async function listImportJobs(
  offset = 0,
  limit = 50,
): Promise<{ items: ImportJob[]; total: number }> {
  const { data } = await client.get<{ items: ImportJob[]; total: number }>(
    `${BASE}/jobs`,
    { params: { offset, limit } },
  );
  return data;
}

export async function confirmImportJob(key: string): Promise<ImportJob> {
  const { data } = await client.post<ImportJob>(`${BASE}/jobs/${key}/confirm`);
  return data;
}

export async function deleteImportJob(key: string): Promise<void> {
  await client.delete(`${BASE}/jobs/${key}`);
}

export async function getImportTemplate(entityType: EntityType): Promise<string> {
  const { data } = await client.get<string>(`${BASE}/templates/${entityType}`);
  return data;
}
