/**
 * Central ID name generator for CreateDialogs.
 * Produces prefilled suggestions for slot_id, batch_id, and instance_id.
 */

function shortTimeSuffix(): string {
  return (Date.now() % 46656).toString(36).toUpperCase().padStart(3, '0');
}

function sanitize(input: string, maxLen: number): string {
  return input
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .replace(/[^A-Za-z0-9]/g, '')
    .toUpperCase()
    .slice(0, maxLen);
}

export function generateSlotId(locationKey: string): string {
  const prefix = sanitize(locationKey, 8) || 'SLOT';
  return `${prefix}_${shortTimeSuffix()}`;
}

export function generateBatchId(substrateKey: string): string {
  const prefix = sanitize(substrateKey, 6) || 'SUB';
  const year = new Date().getFullYear();
  return `${prefix}-${year}-${shortTimeSuffix()}`;
}

export function generateInstanceId(speciesName: string): string {
  const prefix = sanitize(speciesName, 5) || 'PLANT';
  const now = new Date();
  const mm = String(now.getMonth() + 1).padStart(2, '0');
  const dd = String(now.getDate()).padStart(2, '0');
  return `${prefix}-${mm}${dd}-${shortTimeSuffix()}`;
}
