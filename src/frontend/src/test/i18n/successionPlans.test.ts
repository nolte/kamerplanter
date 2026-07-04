import { describe, it, expect } from 'vitest';
import de from '@/i18n/locales/de/translation.json';
import en from '@/i18n/locales/en/translation.json';

/**
 * Guards DE/EN parity for the REQ-013 §2 succession-plan UI strings. Every key
 * consumed by SuccessionPlanListPage / SuccessionPlanDialog must exist and be
 * non-empty in both locales, and the status enum must cover every
 * SuccessionPlanStatus value.
 */

const PAGE_KEYS = [
  'title',
  'listIntro',
  'intro',
  'create',
  'createTitle',
  'editTitle',
  'name',
  'status',
  'intervalDays',
  'intervalDaysHelper',
  'everyNDays',
  'daysSuffix',
  'startDate',
  'endDate',
  'plantsPerBatch',
  'plantsPerBatchHelper',
  'reminderDaysBefore',
  'reminderDaysBeforeHelper',
  'location',
  'notes',
  'batches',
  'window',
  'empty',
  'speciesLockedHelper',
  'previewTitle',
  'previewBatches',
  'endBeforeStart',
  'planCreated',
  'planUpdated',
  'planDeleted',
  'deleteTitle',
  'deleteConfirm',
  'generateRuns',
  'runsGenerated',
  'generatedRunsTitle',
  'runSequenceLabel',
  'plannedStartLabel',
  'noRunsGenerated',
] as const;

const STATUS_KEYS = ['planned', 'active', 'completed', 'cancelled'] as const;

function page(locale: unknown): Record<string, string> {
  return (locale as { pages: { successionPlans: Record<string, string> } }).pages
    .successionPlans;
}

function statusEnum(locale: unknown): Record<string, string> {
  return (locale as { enums: { successionPlanStatus: Record<string, string> } })
    .enums.successionPlanStatus;
}

describe('succession-plan i18n consistency', () => {
  it.each(PAGE_KEYS)('has a non-empty DE + EN string for pages.successionPlans.%s', (key) => {
    expect(page(de)[key]?.length).toBeGreaterThan(0);
    expect(page(en)[key]?.length).toBeGreaterThan(0);
  });

  it.each(STATUS_KEYS)('has a DE + EN label for enums.successionPlanStatus.%s', (key) => {
    expect(statusEnum(de)[key]?.length).toBeGreaterThan(0);
    expect(statusEnum(en)[key]?.length).toBeGreaterThan(0);
  });

  it('provides the nav label in both locales', () => {
    expect((de as { nav: Record<string, string> }).nav.successionPlans?.length).toBeGreaterThan(0);
    expect((en as { nav: Record<string, string> }).nav.successionPlans?.length).toBeGreaterThan(0);
  });
});
