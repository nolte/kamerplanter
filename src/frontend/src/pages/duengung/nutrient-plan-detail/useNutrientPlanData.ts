import { useEffect, useState, useCallback, useMemo } from 'react';
import { useTabUrl } from '@/hooks/useTabUrl';
import { useParams, useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { useOriginProtection, resolveOrigin } from '@/hooks/useOriginProtection';
import { useNotification } from '@/hooks/useNotification';
import { useApiError } from '@/hooks/useApiError';
import { useLocalFavorites } from '@/hooks/useLocalFavorites';
import { useAppDispatch } from '@/store/hooks';
import { setBreadcrumbs } from '@/store/slices/uiSlice';
import * as planApi from '@/api/endpoints/nutrient-plans';
import * as fertApi from '@/api/endpoints/fertilizers';
import {
  editSchema,
  substrateTypes,
  applicationMethods,
  type EditFormData,
} from './nutrientPlanSchema';
import type {
  NutrientPlan,
  NutrientPlanPhaseEntry,
  PlanValidationResult,
  Fertilizer,
} from '@/api/types';

/**
 * Read/entity-side controller for the nutrient-plan detail page (AP-20). Owns the
 * loaded plan/entries/fertilizers, the validation result, the active tab, the edit
 * form (react-hook-form host — its state survives tab switches because this hook
 * stays mounted in the orchestrator) and the plan-level delete. The timeline
 * mutation handlers live in {@link useNutrientPlanActions}. Behaviour is a verbatim
 * extraction of the former inline controller — no logic changes.
 */
export function useNutrientPlanData() {
  const { key } = useParams<{ key: string }>();
  const { t } = useTranslation();
  const navigate = useNavigate();
  const dispatch = useAppDispatch();
  const notification = useNotification();
  const { handleError } = useApiError();

  const { isFavorite, toggleFavorite } = useLocalFavorites('kamerplanter-nutrient-plan-favorites');

  const [plan, setPlan] = useState<NutrientPlan | null>(null);
  const [entries, setEntries] = useState<NutrientPlanPhaseEntry[]>([]);
  const [fertilizers, setFertilizers] = useState<Fertilizer[]>([]);
  const [validation, setValidation] = useState<PlanValidationResult | null>(null);
  const [validating, setValidating] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [tab, setTab] = useTabUrl(['phases', 'validation', 'dosage', 'edit']);
  const [saving, setSaving] = useState(false);
  const [deleteOpen, setDeleteOpen] = useState(false);

  // TODO: REQ-001 v5.0 origin field — backend pending; nutrient plans currently have no origin field.
  const planOrigin = resolveOrigin(plan);
  const { isReadOnly, isDeletionProtected, canCopyAsTemplate } = useOriginProtection({ origin: planOrigin });

  const {
    control,
    handleSubmit,
    reset,
    watch,
    setValue,
    formState: { isDirty },
  } = useForm<EditFormData>({
    resolver: zodResolver(editSchema),
    defaultValues: {
      name: '',
      description: '',
      recommended_substrate_type: null,
      reference_substrate_type: 'soil',
      author: '',
      is_template: false,
      version: '',
      tags: [],
      schedule_enabled: false,
      schedule_mode: 'weekdays',
      weekday_schedule: [],
      interval_days: null,
      preferred_time: '',
      application_method: 'drench',
      reminder_hours_before: 2,
      times_per_day: 1,
      water_mix_ratio_ro_percent: null,
      cycle_restart_from_sequence: null,
    },
  });

  const editScheduleMode = watch('schedule_mode');
  const editWeekdaySchedule = watch('weekday_schedule');
  const editScheduleEnabled = watch('schedule_enabled');

  const handleEditWeekdayToggle = useCallback((dayIndex: number) => {
    const current = editWeekdaySchedule;
    if (current.includes(dayIndex)) {
      setValue('weekday_schedule', current.filter((d) => d !== dayIndex), { shouldDirty: true });
    } else {
      setValue('weekday_schedule', [...current, dayIndex].sort(), { shouldDirty: true });
    }
  }, [editWeekdaySchedule, setValue]);

  const load = useCallback(async (silent = false) => {
    if (!key) return;
    if (!silent) setLoading(true);
    try {
      const [p, e, f] = await Promise.all([
        planApi.fetchNutrientPlan(key),
        planApi.fetchPhaseEntries(key),
        fertApi.fetchFertilizers(0, 200),
      ]);
      setPlan(p);
      setEntries(e);
      setFertilizers(f);
      const ws = p.watering_schedule;
      reset({
        name: p.name,
        description: p.description,
        recommended_substrate_type: p.recommended_substrate_type as typeof substrateTypes[number] | null,
        reference_substrate_type: (p.reference_substrate_type ?? 'soil') as typeof substrateTypes[number],
        author: p.author,
        is_template: p.is_template,
        version: p.version,
        tags: p.tags,
        schedule_enabled: ws != null,
        schedule_mode: ws?.schedule_mode ?? 'weekdays',
        weekday_schedule: ws?.weekday_schedule ?? [],
        interval_days: ws?.interval_days ?? null,
        preferred_time: ws?.preferred_time ?? '',
        application_method: (ws?.application_method ?? 'drench') as typeof applicationMethods[number],
        reminder_hours_before: ws?.reminder_hours_before ?? 2,
        times_per_day: ws?.times_per_day ?? 1,
        water_mix_ratio_ro_percent: p.water_mix_ratio_ro_percent ?? null,
        cycle_restart_from_sequence: p.cycle_restart_from_sequence ?? null,
      });
      setError(null);
    } catch (err) {
      setError(String(err));
    } finally {
      if (!silent) setLoading(false);
    }
  }, [key, reset]);

  useEffect(() => {
    load();
  }, [load]);

  const loadValidation = useCallback(async () => {
    if (!key) return;
    setValidating(true);
    try {
      const result = await planApi.validateNutrientPlan(key);
      setValidation(result);
    } catch (err) {
      handleError(err);
    } finally {
      setValidating(false);
    }
  }, [key, handleError]);

  useEffect(() => {
    if (tab === 1) {
      loadValidation();
    }
  }, [tab, loadValidation]);

  // Dynamic breadcrumbs
  useEffect(() => {
    if (!plan) return;
    dispatch(setBreadcrumbs([
      { label: 'nav.dashboard', path: '/dashboard' },
      { label: 'nav.nutrientPlans', path: '/duengung/plans' },
      { label: plan.name },
    ]));
  }, [plan, dispatch]);

  // Clear dynamic breadcrumbs on unmount
  useEffect(() => () => { dispatch(setBreadcrumbs([])); }, [dispatch]);

  const onSave = useCallback(async (data: EditFormData) => {
    if (!key) return;
    try {
      setSaving(true);
      const hasSchedule = data.schedule_enabled && (
        (data.schedule_mode === 'weekdays' && data.weekday_schedule.length > 0) ||
        (data.schedule_mode === 'interval' && data.interval_days != null && data.interval_days > 0)
      );
      await planApi.updateNutrientPlan(key, {
        name: data.name,
        description: data.description,
        recommended_substrate_type: data.recommended_substrate_type,
        reference_substrate_type: data.reference_substrate_type,
        author: data.author,
        is_template: data.is_template,
        version: data.version,
        tags: data.tags,
        watering_schedule: hasSchedule ? {
          schedule_mode: data.schedule_mode,
          weekday_schedule: data.weekday_schedule,
          interval_days: data.interval_days,
          preferred_time: data.preferred_time || null,
          application_method: data.application_method,
          reminder_hours_before: data.reminder_hours_before,
          times_per_day: data.times_per_day,
        } : null,
        water_mix_ratio_ro_percent: data.water_mix_ratio_ro_percent,
        cycle_restart_from_sequence: data.cycle_restart_from_sequence,
      });
      notification.success(t('common.save'));
      load(true);
    } catch (err) {
      handleError(err);
    } finally {
      setSaving(false);
    }
  }, [key, notification, t, load, handleError]);

  const onDelete = useCallback(async () => {
    if (!key) return;
    try {
      await planApi.deleteNutrientPlan(key);
      notification.success(t('common.delete'));
      navigate('/duengung/plans');
    } catch (err) {
      handleError(err);
    }
  }, [key, notification, t, navigate, handleError]);

  const resetForm = useCallback(() => reset(), [reset]);

  return useMemo(
    () => ({
      key, plan, entries, fertilizers, validation, validating, loading, error, tab, setTab,
      saving, isDirty, planOrigin, isReadOnly, isDeletionProtected, canCopyAsTemplate,
      isFavorite, toggleFavorite, control, handleSubmit, onSave, resetForm,
      editScheduleMode, editScheduleEnabled, editWeekdaySchedule, handleEditWeekdayToggle,
      deleteOpen, setDeleteOpen, onDelete, load,
    }),
    [
      key, plan, entries, fertilizers, validation, validating, loading, error, tab, setTab,
      saving, isDirty, planOrigin, isReadOnly, isDeletionProtected, canCopyAsTemplate,
      isFavorite, toggleFavorite, control, handleSubmit, onSave, resetForm,
      editScheduleMode, editScheduleEnabled, editWeekdaySchedule, handleEditWeekdayToggle,
      deleteOpen, onDelete, load,
    ],
  );
}
