import i18n from '@/i18n/i18n';
import { tenantClient as client } from '../client';

const BASE = '/print';

/**
 * Returns the current i18next language as a locale string for the backend PDF renderer.
 * Falls back to 'de' (the application default) when i18n is not yet initialised.
 */
function getLocale(): string {
  return i18n.language ?? 'de';
}

/**
 * Downloads a nutrient plan as a formatted PDF.
 *
 * @param planKey - The ArangoDB key of the nutrient plan.
 * @param locale  - BCP-47 locale for the PDF content (defaults to the active UI language).
 */
export async function downloadNutrientPlanPdf(
  planKey: string,
  locale?: string,
): Promise<Blob> {
  const { data } = await client.get<Blob>(`${BASE}/nutrient-plan/${planKey}`, {
    params: { locale: locale ?? getLocale() },
    responseType: 'blob',
  });
  return data;
}

/**
 * Downloads the daily care checklist as a formatted PDF.
 *
 * @param date   - ISO date string to filter reminders (defaults to today on the backend).
 * @param locale - BCP-47 locale for the PDF content (defaults to the active UI language).
 */
export async function downloadCareChecklistPdf(
  date?: string,
  locale?: string,
): Promise<Blob> {
  const params: Record<string, string> = { locale: locale ?? getLocale() };
  if (date) params.date = date;
  const { data } = await client.get<Blob>(`${BASE}/care-checklist`, {
    params,
    responseType: 'blob',
  });
  return data;
}

/**
 * Downloads plant info cards (labels with QR codes) as a formatted PDF.
 *
 * @param plantKeys - Array of PlantInstance ArangoDB keys to include.
 * @param fields    - Which fields to display on the cards (e.g. 'name', 'scientific_name').
 * @param layout    - Card layout: 'single' (A6), 'grid_2x4' (8/page), or 'grid_3x3' (9/page).
 * @param qrSizeMm  - QR code size in mm (default 25, min 20, max 60).
 * @param locale    - BCP-47 locale for the PDF content (defaults to the active UI language).
 */
export async function downloadPlantLabelsPdf(
  plantKeys: string[],
  fields?: string[],
  layout?: 'single' | 'grid_2x4' | 'grid_3x3',
  qrSizeMm?: number,
  locale?: string,
): Promise<Blob> {
  const params: Record<string, string> = {
    plant_keys: plantKeys.join(','),
    locale: locale ?? getLocale(),
  };
  if (fields && fields.length > 0) {
    params.fields = fields.join(',');
  }
  if (layout) {
    params.layout = layout;
  }
  if (qrSizeMm !== undefined) {
    params.qr_size_mm = String(qrSizeMm);
  }
  const { data } = await client.get<Blob>(`${BASE}/plant-labels`, {
    params,
    responseType: 'blob',
  });
  return data;
}
