import { useEffect, useMemo, useRef, useState } from 'react';
import type { ChangeEvent } from 'react';
import { useTranslation } from 'react-i18next';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { useFieldArray, useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { useSnackbar } from 'notistack';
import Alert from '@mui/material/Alert';
import AlertTitle from '@mui/material/AlertTitle';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import IconButton from '@mui/material/IconButton';
import LinearProgress from '@mui/material/LinearProgress';
import Typography from '@mui/material/Typography';
import AddIcon from '@mui/icons-material/Add';
import ArrowBackIcon from '@mui/icons-material/ArrowBack';
import DeleteIcon from '@mui/icons-material/Delete';
import UploadFileIcon from '@mui/icons-material/UploadFile';
import PageTitle from '@/components/layout/PageTitle';
import Form from '@/components/form/Form';
import FormActions from '@/components/form/FormActions';
import FormSelectField from '@/components/form/FormSelectField';
import FormSwitchField from '@/components/form/FormSwitchField';
import FormTextField from '@/components/form/FormTextField';
import UnsavedChangesGuard from '@/components/form/UnsavedChangesGuard';
import StepUpConfirmDialog from '@/components/common/StepUpConfirmDialog';
import type { StepUpConfirmation } from '@/components/common/StepUpConfirmDialog';
import TenantImportStatusCard from '@/components/admin/TenantImportStatusCard';
import { requestTenantImport } from '@/api/endpoints/adminTenantImports';
import type { AdminScope, TenantImport, TenantImportMemberGrant, TenantRole } from '@/api/types';
import { usePlanCatalogue } from '@/hooks/usePlanCatalogue';
import { useStepUpResume } from '@/hooks/useStepUpReauth';
import { toCredentialStepUpBody } from '@/utils/stepUp';
import {
  TENANT_IMPORT_DEFAULT_MAX_UPLOAD_MB,
  TENANT_IMPORT_MAX_MAPPED_MEMBERS,
  archiveStepUpTarget,
  describeImportRefusal,
  exceedsDefaultCeiling,
  formatArchiveSize,
  isStepUpRefusal,
  looksLikeZip,
} from '@/utils/tenantImport';
import type { ImportRefusal } from '@/utils/tenantImport';

/** The surface id the step-up dialog saves before a fresh sign-in at the identity provider. */
export const TENANT_IMPORT_STEP_UP_SURFACE = 'tenant-import';

/** Query parameter carrying the key of the import the page follows — a reload keeps watching it. */
export const TENANT_IMPORT_SEARCH_PARAM = 'import';

/** Select value standing for "no `plan_key`: the installation's default plan". */
const DEFAULT_PLAN = '__default__';

const ROLES: readonly TenantRole[] = ['viewer', 'grower', 'lead'];

/** 48 px touch target on phones (UI-NFR-001 R-011), compact on desktop. */
const TOUCH_SX = { width: { xs: 48, md: 40 }, height: { xs: 48, md: 40 } } as const;

/** The hash the step-up is bound to — computed once per selected file. */
type ArchiveTarget =
  { status: 'idle' } | { status: 'hashing' } | { status: 'ready'; target: string | undefined };

interface MemberRow {
  archive_user_key: string;
  email: string;
  role: TenantRole;
  management: boolean;
  technical: boolean;
}

interface ImportFormData {
  plan_key: string;
  members: MemberRow[];
}

const EMPTY_MEMBER: MemberRow = {
  archive_user_key: '',
  email: '',
  role: 'grower',
  management: false,
  technical: false,
};

const DEFAULT_VALUES: ImportFormData = { plan_key: DEFAULT_PLAN, members: [] };

/** The form's member rows as the `member_mapping` object the backend reads. */
function toMemberMapping(rows: readonly MemberRow[]): Record<string, TenantImportMemberGrant> {
  const mapping: Record<string, TenantImportMemberGrant> = {};
  for (const row of rows) {
    const scopes: AdminScope[] = [];
    if (row.management) scopes.push('management');
    if (row.technical) scopes.push('technical');
    mapping[row.archive_user_key.trim()] = {
      email: row.email.trim(),
      role: row.role,
      admin_scopes: scopes,
    };
  }
  return mapping;
}

/**
 * Admin › Imports — bring a tenant archive back as a **new** garden (REQ-056 §8.4, §15, #2138).
 *
 * Guarded by `<RequirePlatformAdmin>` and mounted in full mode only: both routes are
 * `require_platform_admin` and refuse an API key. The admin picks the archive an export produced,
 * optionally the plan of the new garden, and maps the archive's members to existing accounts —
 * with the role and scopes the admin confirms (never the archive's; unmapped members are dropped
 * and their references become the pseudonym `_anonymized`). The member keys come from the
 * archive's `members.jsonl`; the backend offers no route that reads them out of an upload.
 *
 * Starting the import asks for the admin's own step-up (`tenant_import`), bound to the first 32 hex
 * digits of the file's SHA-256 — computed here, before the dialog opens, so an e-mailed code or a
 * fresh sign-in is bound to exactly this file. The server checks the step-up first, then verifies
 * the whole archive and the target plan's quotas before writing; a refusal closes the dialog and is
 * explained on the page with the offending entries. An accepted import (`202`) is followed by
 * {@link TenantImportStatusCard}, whose key sits in the URL so a reload keeps watching it.
 *
 * The upload ceiling is the server's (`TENANT_IMPORT_MAX_UPLOAD_MB`, default
 * {@link TENANT_IMPORT_DEFAULT_MAX_UPLOAD_MB} MB, behind the general upload limit): the page only
 * warns about a file above the default and shows the server's `413` with the limit it named.
 */
export default function AdminTenantImportsPage() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const { enqueueSnackbar } = useSnackbar();
  const [searchParams, setSearchParams] = useSearchParams();
  const { plans, status: plansStatus } = usePlanCatalogue();
  // #1815 — back from the fresh sign-in: the file (and the form) did not survive the redirect.
  const resumed = useStepUpResume(TENANT_IMPORT_STEP_UP_SURFACE);

  const fileInputRef = useRef<HTMLInputElement>(null);
  const [file, setFile] = useState<File | null>(null);
  const [fileMissing, setFileMissing] = useState(false);
  const [archiveTarget, setArchiveTarget] = useState<ArchiveTarget>({ status: 'idle' });
  const [dialogOpen, setDialogOpen] = useState(false);
  const [uploadPercent, setUploadPercent] = useState<number | null>(null);
  const [refusal, setRefusal] = useState<ImportRefusal | null>(null);
  const [accepted, setAccepted] = useState<TenantImport | null>(null);
  // Mirrored into the URL after the render that cleared the form, so the unsaved-changes guard
  // never sees a navigation while the form still reads as dirty.
  const [importKey, setImportKey] = useState<string | null>(() =>
    searchParams.get(TENANT_IMPORT_SEARCH_PARAM),
  );
  // The validated form the dialog confirms — held apart so a later edit cannot change what is sent.
  const [submitted, setSubmitted] = useState<ImportFormData | null>(null);

  const schema = useMemo(
    () =>
      z.object({
        plan_key: z.string(),
        members: z
          .array(
            z.object({
              archive_user_key: z
                .string()
                .trim()
                .min(1, t('validation.required'))
                .max(256, t('pages.tenantImports.form.archiveKeyTooLong')),
              email: z
                .string()
                .trim()
                .pipe(z.email(t('pages.tenantImports.form.emailInvalid'))),
              role: z.enum(['viewer', 'grower', 'lead']),
              management: z.boolean(),
              technical: z.boolean(),
            }),
          )
          .max(
            TENANT_IMPORT_MAX_MAPPED_MEMBERS,
            t('pages.tenantImports.form.tooManyMembers', {
              max: TENANT_IMPORT_MAX_MAPPED_MEMBERS,
            }),
          )
          // One entry per archive key: a JSON object cannot carry a key twice — the second
          // row would silently replace the first.
          .superRefine((rows, ctx) => {
            const seen = new Set<string>();
            rows.forEach((row, index) => {
              const key = row.archive_user_key.trim();
              if (key && seen.has(key)) {
                ctx.addIssue({
                  code: 'custom',
                  path: [index, 'archive_user_key'],
                  message: t('pages.tenantImports.form.archiveKeyDuplicate'),
                });
              }
              seen.add(key);
            });
          }),
      }),
    [t],
  );

  const {
    control,
    handleSubmit,
    reset,
    setError,
    formState: { isDirty },
  } = useForm<ImportFormData>({ resolver: zodResolver(schema), defaultValues: DEFAULT_VALUES });
  const { fields, append, remove } = useFieldArray({ control, name: 'members' });

  useEffect(() => {
    const current = searchParams.get(TENANT_IMPORT_SEARCH_PARAM);
    if (current === importKey) return;
    const next = new URLSearchParams(searchParams);
    if (importKey) next.set(TENANT_IMPORT_SEARCH_PARAM, importKey);
    else next.delete(TENANT_IMPORT_SEARCH_PARAM);
    setSearchParams(next, { replace: true });
  }, [importKey, searchParams, setSearchParams]);

  // The step-up target of the chosen file; a newer choice wins over a slower hash of an older one.
  useEffect(() => {
    if (!file) return undefined;
    let cancelled = false;
    archiveStepUpTarget(file)
      .then((target) => {
        if (!cancelled) setArchiveTarget({ status: 'ready', target });
      })
      .catch(() => {
        // No digest (e.g. the file became unreadable): the password still confirms unbound acts.
        if (!cancelled) setArchiveTarget({ status: 'ready', target: undefined });
      });
    return () => {
      cancelled = true;
    };
  }, [file]);

  const planOptions = useMemo(
    () => [
      { value: DEFAULT_PLAN, label: t('pages.tenantImports.form.planDefault') },
      ...plans.map((plan) => ({
        value: plan.key,
        label: plan.is_default
          ? t('pages.tenantImports.form.planIsDefault', { name: plan.name })
          : plan.name,
      })),
    ],
    [plans, t],
  );

  const roleOptions = useMemo(
    () => ROLES.map((role) => ({ value: role, label: t(`enums.tenantRole.${role}`) })),
    [t],
  );

  const handleFileChange = (event: ChangeEvent<HTMLInputElement>) => {
    const chosen = event.target.files?.[0] ?? null;
    // Reset the input so choosing the same file again (after a refusal) fires a change again.
    event.target.value = '';
    setFile(chosen);
    setFileMissing(false);
    setRefusal(null);
    setArchiveTarget(chosen ? { status: 'hashing' } : { status: 'idle' });
  };

  const onSubmit = (data: ImportFormData) => {
    if (!file) {
      setFileMissing(true);
      return;
    }
    setSubmitted(data);
    setRefusal(null);
    setDialogOpen(true);
  };

  const showMemberRefusals = (entries: readonly string[], rows: readonly MemberRow[]) => {
    const refused = new Set(entries);
    rows.forEach((row, index) => {
      if (refused.has(row.archive_user_key.trim())) {
        setError(`members.${index}.archive_user_key`, {
          type: 'server',
          message: t('pages.tenantImports.form.memberRefused'),
        });
      }
    });
  };

  // The admin's OWN step-up; a refused step-up propagates to the dialog, which shows it.
  const handleConfirm = async (credentials: StepUpConfirmation) => {
    const data = submitted;
    if (!file || !data) return;
    setUploadPercent(0);
    try {
      const record = await requestTenantImport({
        archive: file,
        memberMapping: toMemberMapping(data.members),
        planKey: data.plan_key === DEFAULT_PLAN ? undefined : data.plan_key,
        stepUp: toCredentialStepUpBody(credentials),
        onUploadProgress: setUploadPercent,
      });
      setDialogOpen(false);
      setFile(null);
      setArchiveTarget({ status: 'idle' });
      reset(DEFAULT_VALUES);
      setAccepted(record);
      setImportKey(record.key);
      enqueueSnackbar(t('pages.tenantImports.accepted'), { variant: 'success' });
    } catch (error) {
      if (isStepUpRefusal(error)) throw error;
      // The step-up was accepted (or never reached); the archive or the request was not.
      setDialogOpen(false);
      const described = describeImportRefusal(error);
      setRefusal(described);
      if (described.code === 'IMPORT_MEMBER_NOT_FOUND')
        showMemberRefusals(described.entries, data.members);
    } finally {
      setUploadPercent(null);
    }
  };

  const fileTooLargeForDefault = file !== null && exceedsDefaultCeiling(file.size);
  const fileNotZip = file !== null && !looksLikeZip(file);
  const hashing = archiveTarget.status === 'hashing';
  const stepUpTarget = archiveTarget.status === 'ready' ? archiveTarget.target : undefined;

  const refusalText = (r: ImportRefusal): string => {
    if (r.code === 'PAYLOAD_TOO_LARGE' || r.code === 'REQUEST_BODY_TOO_LARGE') {
      return r.limitMb !== null
        ? t(`pages.tenantImports.refusal.${r.code}`, { limit: r.limitMb })
        : t('pages.tenantImports.refusal.tooLargeNoLimit');
    }
    return t(`pages.tenantImports.refusal.${r.code}`, { code: r.rawCode, message: r.message });
  };

  const dialogDescription = (
    <>
      {t('pages.tenantImports.dialogDescription', {
        file: file?.name ?? '',
        size: file ? formatArchiveSize(file.size) : '',
        count: submitted?.members.length ?? 0,
      })}
      {uploadPercent !== null && (
        <>
          <br />
          <br />
          {t('pages.tenantImports.uploadProgress', { percent: uploadPercent })}
          <LinearProgress
            variant={uploadPercent >= 100 ? 'indeterminate' : 'determinate'}
            value={uploadPercent}
            aria-label={t('pages.tenantImports.uploadProgressLabel')}
            sx={{ display: 'block', mt: 1 }}
            data-testid="tenant-import-upload-progress"
          />
          {uploadPercent >= 100 && (
            <>
              <br />
              {t('pages.tenantImports.verifying')}
            </>
          )}
        </>
      )}
    </>
  );

  return (
    <Box sx={{ mt: 2 }} data-testid="tenant-import-admin-page">
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
        <IconButton
          onClick={() => navigate('/settings#platform')}
          sx={TOUCH_SX}
          aria-label={t('pages.tenantImports.back')}
          data-testid="tenant-imports-back"
        >
          <ArrowBackIcon />
        </IconButton>
        <Box sx={{ flex: 1 }}>
          <PageTitle title={t('pages.tenantImports.title')} sx={{ mb: 0 }} />
        </Box>
      </Box>
      <Typography variant="body1" color="text.secondary" sx={{ mb: 2 }}>
        {t('pages.tenantImports.intro')}
      </Typography>
      <Alert severity="info" sx={{ mb: 3 }} data-testid="tenant-imports-rules">
        {t('pages.tenantImports.rules')}
      </Alert>

      {resumed && (
        <Alert severity="info" sx={{ mb: 3 }} data-testid="tenant-import-resumed">
          {t('pages.tenantImports.resumed')}
        </Alert>
      )}

      {importKey && (
        <TenantImportStatusCard
          key={importKey}
          importKey={importKey}
          initial={accepted}
          onDismiss={() => {
            setAccepted(null);
            setImportKey(null);
          }}
        />
      )}

      {refusal && (
        <Alert
          severity="error"
          sx={{ mb: 3 }}
          onClose={() => setRefusal(null)}
          data-testid="tenant-import-refusal"
        >
          <AlertTitle>{t('pages.tenantImports.refusalTitle')}</AlertTitle>
          {refusalText(refusal)}
          {refusal.entries.length > 0 && (
            <Box
              component="ul"
              sx={{ m: 0, mt: 1, pl: 2.5, fontFamily: 'monospace', wordBreak: 'break-all' }}
              data-testid="tenant-import-refusal-entries"
            >
              {refusal.entries.map((entry) => (
                <li key={entry}>{entry}</li>
              ))}
            </Box>
          )}
        </Alert>
      )}

      <Form onSubmit={handleSubmit(onSubmit)}>
        <Card sx={{ mb: 3 }}>
          <CardContent>
            <Typography variant="h6" component="h2" sx={{ mb: 1 }}>
              {t('pages.tenantImports.archive.title')}
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
              {t('pages.tenantImports.archive.description')}
            </Typography>
            <Box
              sx={{
                display: 'flex',
                flexDirection: { xs: 'column', sm: 'row' },
                alignItems: { xs: 'stretch', sm: 'center' },
                gap: 1.5,
                mb: 1,
              }}
            >
              <Button
                variant="outlined"
                startIcon={<UploadFileIcon />}
                onClick={() => fileInputRef.current?.click()}
                aria-describedby="tenant-import-file-hint"
                sx={{ minHeight: 44, flexShrink: 0 }}
                data-testid="tenant-import-file-select"
              >
                {file
                  ? t('pages.tenantImports.archive.change')
                  : t('pages.tenantImports.archive.select')}
              </Button>
              <input
                ref={fileInputRef}
                type="file"
                accept=".zip,application/zip"
                hidden
                onChange={handleFileChange}
                data-testid="tenant-import-file-input"
              />
              <Typography
                variant="body2"
                sx={{ wordBreak: 'break-all' }}
                aria-live="polite"
                data-testid="tenant-import-file-info"
              >
                {file
                  ? t('pages.tenantImports.archive.selected', {
                      name: file.name,
                      size: formatArchiveSize(file.size),
                    })
                  : t('pages.tenantImports.archive.none')}
              </Typography>
            </Box>
            <Typography id="tenant-import-file-hint" variant="body2" color="text.secondary">
              {t('pages.tenantImports.archive.sizeHint', {
                limit: TENANT_IMPORT_DEFAULT_MAX_UPLOAD_MB,
              })}
            </Typography>
            {hashing && (
              <Typography
                variant="body2"
                color="text.secondary"
                sx={{ mt: 1 }}
                data-testid="tenant-import-hashing"
              >
                {t('pages.tenantImports.archive.hashing')}
              </Typography>
            )}
            {fileMissing && (
              <Alert severity="error" sx={{ mt: 2 }} data-testid="tenant-import-file-missing">
                {t('pages.tenantImports.archive.missing')}
              </Alert>
            )}
            {fileNotZip && (
              <Alert severity="warning" sx={{ mt: 2 }} data-testid="tenant-import-file-not-zip">
                {t('pages.tenantImports.archive.notZip')}
              </Alert>
            )}
            {fileTooLargeForDefault && (
              <Alert severity="warning" sx={{ mt: 2 }} data-testid="tenant-import-file-too-large">
                {t('pages.tenantImports.archive.tooLarge', {
                  limit: TENANT_IMPORT_DEFAULT_MAX_UPLOAD_MB,
                })}
              </Alert>
            )}
          </CardContent>
        </Card>

        <Card sx={{ mb: 3 }}>
          <CardContent>
            <Typography variant="h6" component="h2" sx={{ mb: 1 }}>
              {t('pages.tenantImports.plan.title')}
            </Typography>
            <FormSelectField
              name="plan_key"
              control={control}
              label={t('pages.tenantImports.form.plan')}
              options={planOptions}
              helperText={
                plansStatus === 'error'
                  ? t('pages.tenantImports.form.planLoadFailed')
                  : t('pages.tenantImports.form.planHelper')
              }
            />
          </CardContent>
        </Card>

        <Card sx={{ mb: 3 }}>
          <CardContent>
            <Typography variant="h6" component="h2" sx={{ mb: 1 }}>
              {t('pages.tenantImports.members.title')}
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
              {t('pages.tenantImports.members.description')}
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
              {t('pages.tenantImports.members.ownerHint')}
            </Typography>

            {fields.length === 0 && (
              <Typography variant="body2" sx={{ mb: 2 }} data-testid="member-mapping-empty">
                {t('pages.tenantImports.members.empty')}
              </Typography>
            )}

            <Box
              component="ol"
              sx={{ listStyle: 'none', m: 0, p: 0 }}
              data-testid="member-mapping-list"
            >
              {fields.map((field, index) => (
                <Box
                  component="li"
                  key={field.id}
                  sx={{ border: 1, borderColor: 'divider', borderRadius: 1, p: 2, mb: 2 }}
                >
                  <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                    <Typography variant="subtitle2" component="h3" sx={{ flex: 1 }}>
                      {t('pages.tenantImports.members.rowTitle', { number: index + 1 })}
                    </Typography>
                    <IconButton
                      onClick={() => remove(index)}
                      sx={TOUCH_SX}
                      aria-label={t('pages.tenantImports.members.remove', { number: index + 1 })}
                      data-testid={`member-mapping-remove-${index}`}
                    >
                      <DeleteIcon />
                    </IconButton>
                  </Box>
                  <Box
                    sx={{
                      display: 'grid',
                      gridTemplateColumns: { xs: '1fr', md: '1fr 1fr 12rem' },
                      columnGap: 2,
                    }}
                  >
                    <FormTextField
                      name={`members.${index}.archive_user_key`}
                      control={control}
                      label={t('pages.tenantImports.form.archiveKey')}
                      helperText={t('pages.tenantImports.form.archiveKeyHelper')}
                      required
                    />
                    <FormTextField
                      name={`members.${index}.email`}
                      control={control}
                      type="email"
                      label={t('pages.tenantImports.form.email')}
                      helperText={t('pages.tenantImports.form.emailHelper')}
                      required
                    />
                    <FormSelectField
                      name={`members.${index}.role`}
                      control={control}
                      label={t('pages.tenantImports.form.role')}
                      options={roleOptions}
                      required
                    />
                  </Box>
                  <Box sx={{ display: 'flex', flexWrap: 'wrap', columnGap: 3 }}>
                    <FormSwitchField
                      name={`members.${index}.management`}
                      control={control}
                      label={t('enums.adminScope.management')}
                      helperText={t('pages.tenantImports.form.managementHelper')}
                    />
                    <FormSwitchField
                      name={`members.${index}.technical`}
                      control={control}
                      label={t('enums.adminScope.technical')}
                      helperText={t('pages.tenantImports.form.technicalHelper')}
                    />
                  </Box>
                </Box>
              ))}
            </Box>

            <Button
              variant="outlined"
              startIcon={<AddIcon />}
              onClick={() => append({ ...EMPTY_MEMBER })}
              disabled={fields.length >= TENANT_IMPORT_MAX_MAPPED_MEMBERS}
              sx={{ minHeight: 44 }}
              data-testid="member-mapping-add"
            >
              {t('pages.tenantImports.members.add')}
            </Button>
          </CardContent>
        </Card>

        <Typography variant="body2" color="text.secondary">
          {t('pages.tenantImports.startHint')}
        </Typography>
        <FormActions
          onCancel={() => navigate('/settings#platform')}
          saveLabel={t('pages.tenantImports.start')}
          disabled={hashing}
        />
      </Form>

      <UnsavedChangesGuard dirty={(isDirty || file !== null) && !dialogOpen} />

      <StepUpConfirmDialog
        open={dialogOpen}
        title={t('pages.tenantImports.dialogTitle')}
        description={dialogDescription}
        confirmLabel={t('pages.tenantImports.dialogConfirm')}
        confirmColor="primary"
        testIdPrefix={TENANT_IMPORT_STEP_UP_SURFACE}
        stepUpAction="tenant_import"
        stepUpTarget={stepUpTarget}
        onConfirm={handleConfirm}
        onCancel={() => setDialogOpen(false)}
      />
    </Box>
  );
}
