import { useEffect, useMemo, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useForm, useWatch } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import Alert from '@mui/material/Alert';
import Box from '@mui/material/Box';
import Dialog from '@mui/material/Dialog';
import DialogContent from '@mui/material/DialogContent';
import DialogTitle from '@mui/material/DialogTitle';
import Divider from '@mui/material/Divider';
import Typography from '@mui/material/Typography';
import useMediaQuery from '@mui/material/useMediaQuery';
import { useTheme } from '@mui/material/styles';
import ClearIcon from '@mui/icons-material/Clear';
import IconButton from '@mui/material/IconButton';
import InputAdornment from '@mui/material/InputAdornment';
import Form from '@/components/form/Form';
import FormActions from '@/components/form/FormActions';
import FormNumberField from '@/components/form/FormNumberField';
import FormRow from '@/components/form/FormRow';
import FormSwitchField from '@/components/form/FormSwitchField';
import FormTextField from '@/components/form/FormTextField';
import UnsavedChangesGuard from '@/components/form/UnsavedChangesGuard';
import { createPlan, updatePlan } from '@/api/endpoints/adminPlans';
import type { EntitlementDimension, Plan, PlanCreate, PlanLimits, PlanUpdate } from '@/api/types';
import { useApiError } from '@/hooks/useApiError';
import { useFieldViolations } from '@/hooks/useFieldViolations';
import {
  ENTITLEMENT_DIMENSIONS,
  LIMIT_MAXIMA,
  formatPlanLimit,
  minimumLimit,
} from '@/utils/entitlements';

/** The plan key rule of the backend (`PLAN_KEY_PATTERN`, REQ-056 §7.6). */
const PLAN_KEY_PATTERN = /^[a-z][a-z0-9_-]{1,39}$/;

/**
 * Backend violation `code` → i18n key (#1015: translated on the stable code, never the English reason).
 * `DUPLICATE_ENTRY` lands on `key`, `members_above_ceiling` on `limits.members`.
 */
const VIOLATION_MESSAGE_KEYS: Record<string, string> = {
  DUPLICATE_ENTRY: 'pages.plans.form.keyTaken',
  members_above_ceiling: 'pages.plans.form.membersAboveCeiling',
};

type LimitValues = Record<EntitlementDimension, number | null>;

interface FormData {
  key: string;
  name: string;
  description: string;
  limits: LimitValues;
  make_default: boolean;
}

function emptyLimits(): LimitValues {
  return Object.fromEntries(ENTITLEMENT_DIMENSIONS.map((d) => [d, null])) as LimitValues;
}

function planToForm(plan: Plan | null): FormData {
  const limits = emptyLimits();
  if (plan) {
    for (const d of ENTITLEMENT_DIMENSIONS) limits[d] = plan.limits[d] ?? null;
  }
  return {
    key: plan?.key ?? '',
    name: plan?.name ?? '',
    description: plan?.description ?? '',
    limits,
    make_default: plan?.is_default ?? false,
  };
}

/** The dimensions grouped as the form shows them: people, storage, AI. */
const DIMENSION_GROUPS: readonly { id: string; dimensions: readonly EntitlementDimension[] }[] = [
  { id: 'people', dimensions: ['members', 'service_accounts'] },
  { id: 'storage', dimensions: ['storage_mb', 'photos_per_instance'] },
  { id: 'ai', dimensions: ['ai_calls_per_user_day', 'ai_calls_per_tenant_day', 'ai_tokens_per_tenant_day'] },
];

interface PlanFormDialogProps {
  open: boolean;
  /** `null` creates a plan, a plan edits it. */
  plan: Plan | null;
  onClose: () => void;
  /** Called with the stored plan after a successful save. */
  onSaved: (plan: Plan) => void;
}

/**
 * Create / edit form of one plan (REQ-056 §7.6, §15, AK-45) — react-hook-form + Zod, `FormActions`
 * and `UnsavedChangesGuard` like every form of the app.
 *
 * The form makes the two easy-to-misread values of a limit explicit: an **empty** field follows the
 * instance setting (the operator's environment variable), and `0` lifts the limit — unlimited for
 * storage and photos, budget off for the AI budgets — it never means "nothing allowed". Under each
 * field the current value is spelled out as the backend will apply it.
 *
 * Edit sends only what changed (a partial update; inside `limits` only the changed dimensions), so
 * the audit row names exactly the fields the admin touched. The default mark can be set here but not
 * taken away: a default is replaced by marking another plan.
 */
export default function PlanFormDialog({ open, plan, onClose, onSaved }: PlanFormDialogProps) {
  const { t } = useTranslation();
  const theme = useTheme();
  const fullScreen = useMediaQuery(theme.breakpoints.down('sm'));
  const { handleError } = useApiError();
  const [saving, setSaving] = useState(false);
  const isEdit = plan !== null;

  const schema = useMemo(() => {
    const limitShape = Object.fromEntries(
      ENTITLEMENT_DIMENSIONS.map((d) => [
        d,
        z
          .number({ message: t('pages.plans.form.wholeNumber') })
          .int(t('pages.plans.form.wholeNumber'))
          .min(minimumLimit(d), t('pages.plans.form.min', { min: minimumLimit(d) }))
          .max(LIMIT_MAXIMA[d], t('pages.plans.form.max', { max: LIMIT_MAXIMA[d].toLocaleString() }))
          .nullable(),
      ]),
    ) as Record<EntitlementDimension, z.ZodNullable<z.ZodNumber>>;
    return z.object({
      key: isEdit
        ? z.string()
        : z.string().regex(PLAN_KEY_PATTERN, t('pages.plans.form.keyInvalid')),
      name: z.string().trim().min(1, t('validation.required')).max(100, t('pages.plans.form.nameTooLong')),
      description: z.string().max(500, t('pages.plans.form.descriptionTooLong')),
      limits: z.object(limitShape),
      make_default: z.boolean(),
    });
  }, [isEdit, t]);

  const {
    control,
    handleSubmit,
    reset,
    setError,
    setValue,
    formState: { isDirty },
  } = useForm<FormData>({
    resolver: zodResolver(schema),
    defaultValues: planToForm(plan),
  });

  useEffect(() => {
    if (open) reset(planToForm(plan));
  }, [open, plan, reset]);

  const applyFieldViolation = useFieldViolations(setError, { messageKeys: VIOLATION_MESSAGE_KEYS });
  const limits = useWatch({ control, name: 'limits' });

  const onSubmit = async (data: FormData) => {
    setSaving(true);
    try {
      let saved: Plan;
      if (!plan) {
        const createLimits: PlanLimits = {};
        for (const d of ENTITLEMENT_DIMENSIONS) {
          if (data.limits[d] !== null) createLimits[d] = data.limits[d];
        }
        const payload: PlanCreate = {
          key: data.key,
          name: data.name.trim(),
          description: data.description.trim() || null,
          limits: createLimits,
        };
        saved = await createPlan(payload);
      } else {
        const payload: PlanUpdate = {};
        if (data.name.trim() !== plan.name) payload.name = data.name.trim();
        const description = data.description.trim() || null;
        if (description !== (plan.description ?? null)) payload.description = description;
        const changedLimits: PlanLimits = {};
        for (const d of ENTITLEMENT_DIMENSIONS) {
          if (data.limits[d] !== (plan.limits[d] ?? null)) changedLimits[d] = data.limits[d];
        }
        if (Object.keys(changedLimits).length > 0) payload.limits = changedLimits;
        if (data.make_default && !plan.is_default) payload.is_default = true;
        saved = Object.keys(payload).length > 0 ? await updatePlan(plan.key, payload) : plan;
      }
      reset(planToForm(saved));
      onSaved(saved);
    } catch (err) {
      handleError(err, applyFieldViolation);
    } finally {
      setSaving(false);
    }
  };

  return (
    <Dialog
      open={open}
      onClose={saving ? undefined : onClose}
      fullScreen={fullScreen}
      maxWidth="md"
      fullWidth
      aria-labelledby="plan-form-title"
      data-testid="plan-form-dialog"
    >
      <UnsavedChangesGuard dirty={isDirty && open} />
      <DialogTitle id="plan-form-title">
        {isEdit ? t('pages.plans.form.editTitle', { name: plan.name }) : t('pages.plans.form.createTitle')}
      </DialogTitle>
      <DialogContent>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
          {t('pages.plans.form.intro')}
        </Typography>
        <Form onSubmit={handleSubmit(onSubmit)}>
          <FormRow>
            <FormTextField
              name="key"
              control={control}
              label={t('pages.plans.form.key')}
              required={!isEdit}
              disabled={isEdit || saving}
              autoFocus={!isEdit}
              helperText={isEdit ? t('pages.plans.form.keyLocked') : t('pages.plans.form.keyHelper')}
            />
            <FormTextField
              name="name"
              control={control}
              label={t('pages.plans.form.name')}
              required
              disabled={saving}
              autoFocus={isEdit}
              helperText={t('pages.plans.form.nameHelper')}
            />
          </FormRow>
          <FormTextField
            name="description"
            control={control}
            label={t('pages.plans.form.description')}
            multiline
            minRows={2}
            maxRows={5}
            disabled={saving}
            helperText={t('pages.plans.form.descriptionHelper')}
          />

          {isEdit && plan.tenant_count > 0 && (
            <Alert severity="warning" sx={{ mt: 2 }} data-testid="plan-form-in-use-warning">
              {t('pages.plans.form.inUseWarning', { count: plan.tenant_count })}
            </Alert>
          )}

          <Alert severity="info" sx={{ my: 2 }} data-testid="plan-form-limit-rules">
            {t('pages.plans.form.limitRules')}
          </Alert>

          {DIMENSION_GROUPS.map((group) => (
            <Box key={group.id} sx={{ mb: 1 }}>
              <Divider sx={{ my: 1.5 }} />
              <Typography variant="subtitle2" component="h3" sx={{ mb: 0.25 }}>
                {t(`pages.plans.form.groups.${group.id}.title`)}
              </Typography>
              <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 1 }}>
                {t(`pages.plans.form.groups.${group.id}.description`)}
              </Typography>
              <Box
                sx={{
                  display: 'grid',
                  gridTemplateColumns: { xs: '1fr', sm: group.dimensions.length > 2 ? '1fr 1fr 1fr' : '1fr 1fr' },
                  columnGap: 2,
                }}
              >
                {group.dimensions.map((d) => (
                  <FormNumberField
                    key={d}
                    name={`limits.${d}`}
                    control={control}
                    label={t(`enums.entitlementDimension.${d}`)}
                    min={minimumLimit(d)}
                    max={LIMIT_MAXIMA[d]}
                    step={1}
                    inputMode="numeric"
                    placeholder={t('pages.plans.form.emptyPlaceholder')}
                    endAdornment={
                      <InputAdornment position="end">
                        {limits?.[d] != null && (
                          <IconButton
                            size="small"
                            edge="end"
                            onClick={() => setValue(`limits.${d}`, null, { shouldDirty: true, shouldValidate: true })}
                            disabled={saving}
                            aria-label={t('pages.plans.form.resetToInstance', { field: t(`enums.entitlementDimension.${d}`) })}
                            sx={{ width: { xs: 40, md: 32 }, height: { xs: 40, md: 32 } }}
                            data-testid={`plan-form-reset-${d}`}
                          >
                            <ClearIcon fontSize="small" />
                          </IconButton>
                        )}
                        {t(`pages.plans.unit.${d}`)}
                      </InputAdornment>
                    }
                    disabled={saving}
                    helperText={`${t(`pages.plans.form.fieldHelp.${d}`)} ${t('pages.plans.form.appliesAs', {
                      value: formatPlanLimit(d, limits?.[d] ?? null, t),
                    })}`}
                  />
                ))}
              </Box>
            </Box>
          ))}

          <Divider sx={{ my: 1.5 }} />
          {isEdit && plan.is_default ? (
            <Alert severity="success" data-testid="plan-form-is-default">
              {t('pages.plans.form.isDefaultInfo')}
            </Alert>
          ) : isEdit ? (
            <FormSwitchField
              name="make_default"
              control={control}
              label={t('pages.plans.form.makeDefault')}
              disabled={saving}
              helperText={t('pages.plans.form.makeDefaultHelper')}
            />
          ) : (
            <Typography variant="body2" color="text.secondary" data-testid="plan-form-default-hint">
              {t('pages.plans.form.createDefaultHint')}
            </Typography>
          )}

          <FormActions
            onCancel={onClose}
            loading={saving}
            saveLabel={isEdit ? t('common.save') : t('pages.plans.form.submitCreate')}
          />
        </Form>
      </DialogContent>
    </Dialog>
  );
}
