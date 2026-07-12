import { tenantClient } from '../client';
import type {
  DiagnoseRequest,
  DiagnosisResult,
  DiagnosisSymptom,
  DiagnosisSymptomListResponse,
} from '../types';

/**
 * REQ-036 KI-Diagnose-Assistent API layer.
 *
 * All calls are tenant-scoped (`/t/{slug}/diagnosis/...`) and pass through the
 * shared three-stage KI toggle enforced by the backend. The diagnosis flow is
 * stateless — no session resources are created client-side.
 */

/** The curated symptom catalogue for the wizard's first step. */
export async function listSymptoms(
  language: 'de' | 'en' = 'de',
  phase?: string,
  category?: string,
): Promise<DiagnosisSymptom[]> {
  const { data } = await tenantClient.get<DiagnosisSymptomListResponse>('/diagnosis/symptoms', {
    params: { language, phase, category },
  });
  return data.symptoms;
}

/** Run the structured diagnosis; returns the top-3 candidates. */
export async function analyzeDiagnosis(body: DiagnoseRequest): Promise<DiagnosisResult> {
  const { data } = await tenantClient.post<DiagnosisResult>('/diagnosis/analyze', body);
  return data;
}
