import { z } from 'zod';

/** Substrate-type enum values — mirrors SubstrateType in api/types.ts. */
export const substrateTypes = [
  'soil',
  'coco',
  'clay_pebbles',
  'perlite',
  'living_soil',
  'peat',
  'rockwool_slab',
  'rockwool_plug',
  'vermiculite',
  'none',
  'orchid_bark',
  'pon_mineral',
  'sphagnum',
  'hydro_solution',
] as const;

/** Application-method enum values for the watering schedule. */
export const applicationMethods = ['drench', 'foliar', 'top_dress'] as const;

export const editSchema = z.object({
  name: z.string().min(1).max(200),
  description: z.string().max(2000),
  recommended_substrate_type: z.enum(substrateTypes).nullable(),
  reference_substrate_type: z.enum(substrateTypes),
  author: z.string().max(200),
  is_template: z.boolean(),
  version: z.string().max(50),
  tags: z.array(z.string()),
  schedule_enabled: z.boolean(),
  schedule_mode: z.enum(['weekdays', 'interval']),
  weekday_schedule: z.array(z.number()),
  interval_days: z.number().min(1).max(90).nullable(),
  preferred_time: z.string().max(5),
  application_method: z.enum(applicationMethods),
  reminder_hours_before: z.number().min(0).max(24),
  times_per_day: z.number().min(1).max(6),
  water_mix_ratio_ro_percent: z.number().min(0).max(100).nullable(),
  cycle_restart_from_sequence: z.number().min(1).nullable(),
});

export type EditFormData = z.infer<typeof editSchema>;

/** Weekday order keys (Mon…Sun) for the schedule checkboxes. */
export const WEEKDAY_KEYS = ['mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun'] as const;

/** Form container max width on md+ (UI-NFR-008 R-053). */
export const FORM_MAX_WIDTH = 1280;
/** Reading-column max width for prose textareas (UI-NFR-008 R-054, ~70-80 chars). */
export const READING_COL_MAX = 760;
