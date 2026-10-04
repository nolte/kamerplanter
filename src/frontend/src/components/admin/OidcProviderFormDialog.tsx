import { useMemo, useState } from 'react';
import { useTranslation } from 'react-i18next';
import Accordion from '@mui/material/Accordion';
import AccordionDetails from '@mui/material/AccordionDetails';
import AccordionSummary from '@mui/material/AccordionSummary';
import Alert from '@mui/material/Alert';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Dialog from '@mui/material/Dialog';
import DialogActions from '@mui/material/DialogActions';
import DialogContent from '@mui/material/DialogContent';
import DialogTitle from '@mui/material/DialogTitle';
import FormControlLabel from '@mui/material/FormControlLabel';
import FormHelperText from '@mui/material/FormHelperText';
import Switch from '@mui/material/Switch';
import TextField from '@mui/material/TextField';
import Typography from '@mui/material/Typography';
import useMediaQuery from '@mui/material/useMediaQuery';
import { useTheme } from '@mui/material/styles';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import type {
  OidcProvider,
  OidcProviderCreate,
  OidcProviderType,
  OidcProviderUpdate,
} from '@/api/types';
import { githubScopesLackEmail, oidcUpdateNeedsStepUp, parseScopes } from '@/utils/oidcProviders';

/** What the form hands the page: the configuration fields, never a step-up (the page adds it). */
export type OidcCreateFields = Omit<OidcProviderCreate, 'current_password' | 'step_up_code' | 'step_up_token'>;
export type OidcUpdateFields = Omit<OidcProviderUpdate, 'current_password' | 'step_up_code' | 'step_up_token'>;

export type OidcFormSubmission =
  | { mode: 'create'; fields: OidcCreateFields }
  | { mode: 'edit'; fields: OidcUpdateFields; needsStepUp: boolean };

const PROVIDER_TYPES: readonly OidcProviderType[] = ['oidc', 'google', 'github', 'apple'];
const SLUG_PATTERN = /^[a-z0-9-]{1,50}$/;
const LOOPBACK_HOSTS = new Set(['localhost', '127.0.0.1', '[::1]']);

/**
 * Whether `value` is an address the API will accept for an endpoint: `https`, or (debug builds
 * only, decided server-side) `http` to loopback. The server stays the authority; this only
 * spares the admin a step-up for an address that is plainly not one.
 */
function isEndpointUrl(value: string): boolean {
  try {
    const url = new URL(value);
    if (url.protocol === 'https:') return true;
    return url.protocol === 'http:' && LOOPBACK_HOSTS.has(url.hostname);
  } catch {
    return false;
  }
}

interface OidcProviderFormDialogProps {
  /** `null` creates a provider, a provider edits it. */
  provider: OidcProvider | null;
  /** An error of the last submit (a direct save without step-up), shown inside the dialog. */
  error?: string;
  /** True while the page performs the submit. */
  pending?: boolean;
  onSubmit: (submission: OidcFormSubmission) => void;
  onCancel: () => void;
}

/**
 * Create / edit form for one OIDC provider configuration (#1906).
 *
 * Mounted only while open, so its state starts from the stored values each time. The client
 * secret field is **write-only**: it is never prefilled and never rendered back — the API does
 * not return it, and an empty field on edit means "keep the stored one". The form does not
 * decide the step-up on its own authority: it mirrors the backend's rule
 * (`oidcUpdateNeedsStepUp`) so the page can open the confirmation first, and says so before
 * submitting.
 */
export default function OidcProviderFormDialog({
  provider,
  error,
  pending = false,
  onSubmit,
  onCancel,
}: OidcProviderFormDialogProps) {
  const { t } = useTranslation();
  const theme = useTheme();
  const fullScreen = useMediaQuery(theme.breakpoints.down('sm'));
  const isEdit = provider !== null;

  const [slug, setSlug] = useState('');
  const [displayName, setDisplayName] = useState(provider?.display_name ?? '');
  const [providerType, setProviderType] = useState<string>(provider?.provider_type ?? 'oidc');
  const [issuerUrl, setIssuerUrl] = useState(provider?.issuer_url ?? '');
  const [clientId, setClientId] = useState(provider?.client_id ?? '');
  const [clientSecret, setClientSecret] = useState('');
  const [scopesText, setScopesText] = useState((provider?.scopes ?? ['openid', 'email', 'profile']).join(' '));
  const [autoDiscover, setAutoDiscover] = useState(provider?.auto_discover ?? true);
  const [enabled, setEnabled] = useState(provider?.enabled ?? false);
  const [iconUrl, setIconUrl] = useState(provider?.icon_url ?? '');
  const [authorizationUrl, setAuthorizationUrl] = useState('');
  const [tokenUrl, setTokenUrl] = useState('');
  const [userinfoUrl, setUserinfoUrl] = useState('');
  const [jwksUrl, setJwksUrl] = useState('');
  const [defaultTenantKey, setDefaultTenantKey] = useState('');
  const [submitted, setSubmitted] = useState(false);

  const scopes = useMemo(() => parseScopes(scopesText), [scopesText]);

  // The vocabulary the form can *write*; a stored record outside it stays visible and
  // repairable, so its current spelling is offered as an extra option.
  const typeOptions = useMemo(
    () =>
      provider && !PROVIDER_TYPES.includes(provider.provider_type as OidcProviderType)
        ? [provider.provider_type, ...PROVIDER_TYPES]
        : [...PROVIDER_TYPES],
    [provider],
  );

  const errors = useMemo(() => {
    const e: Record<string, string> = {};
    if (!isEdit && !SLUG_PATTERN.test(slug)) e.slug = t('pages.admin.oidc.form.slugInvalid');
    if (displayName.trim().length === 0) e.displayName = t('pages.admin.oidc.form.required');
    if (issuerUrl.trim().length === 0) e.issuerUrl = t('pages.admin.oidc.form.required');
    else if (!isEndpointUrl(issuerUrl.trim())) e.issuerUrl = t('pages.admin.oidc.form.urlInvalid');
    if (clientId.trim().length === 0) e.clientId = t('pages.admin.oidc.form.required');
    if (!isEdit && clientSecret.length === 0) e.clientSecret = t('pages.admin.oidc.form.required');
    if (scopes.length === 0) e.scopes = t('pages.admin.oidc.form.scopesRequired');
    else if (providerType === 'github' && githubScopesLackEmail(scopes)) {
      e.scopes = t('pages.admin.oidc.form.githubScopes');
    }
    const endpoints = { authorizationUrl, tokenUrl, userinfoUrl, jwksUrl };
    for (const [name, value] of Object.entries(endpoints)) {
      if (!isEdit && value.trim().length > 0 && !isEndpointUrl(value.trim())) {
        e[name] = t('pages.admin.oidc.form.urlInvalid');
      }
    }
    return e;
  }, [
    isEdit, slug, displayName, issuerUrl, clientId, clientSecret, scopes, providerType,
    authorizationUrl, tokenUrl, userinfoUrl, jwksUrl, t,
  ]);

  /** Edit: only what differs from the stored configuration — a partial update. */
  const changes = useMemo<OidcUpdateFields>(() => {
    if (!provider) return {};
    const c: OidcUpdateFields = {};
    if (displayName.trim() !== provider.display_name) c.display_name = displayName.trim();
    if (providerType !== provider.provider_type) c.provider_type = providerType as OidcProviderType;
    if (issuerUrl.trim() !== provider.issuer_url) c.issuer_url = issuerUrl.trim();
    if (clientId.trim() !== provider.client_id) c.client_id = clientId.trim();
    if (clientSecret.length > 0) c.client_secret = clientSecret;
    if (scopes.join(' ') !== provider.scopes.join(' ')) c.scopes = scopes;
    if (autoDiscover !== provider.auto_discover) c.auto_discover = autoDiscover;
    if (enabled !== provider.enabled) c.enabled = enabled;
    if (iconUrl.trim() !== (provider.icon_url ?? '')) c.icon_url = iconUrl.trim();
    return c;
  }, [provider, displayName, providerType, issuerUrl, clientId, clientSecret, scopes, autoDiscover, enabled, iconUrl]);

  const hasChanges = Object.keys(changes).length > 0;
  const needsStepUp = !provider || oidcUpdateNeedsStepUp(provider, changes);
  const valid = Object.keys(errors).length === 0;

  // The callback URL the provider must allow. Derived from where the UI is served; the real
  // base is APP_BASE_URL on the server, which the hint names.
  const callbackUrl = `${window.location.origin}/api/v1/auth/oauth/${isEdit ? provider.slug : slug || '<slug>'}/callback`;

  const handleSubmit = () => {
    setSubmitted(true);
    if (!valid || pending) return;
    if (provider) {
      if (!hasChanges) return;
      onSubmit({ mode: 'edit', fields: changes, needsStepUp });
      return;
    }
    const fields: OidcCreateFields = {
      slug,
      display_name: displayName.trim(),
      provider_type: providerType as OidcProviderType,
      issuer_url: issuerUrl.trim(),
      client_id: clientId.trim(),
      client_secret: clientSecret,
      scopes,
      auto_discover: autoDiscover,
      enabled,
    };
    if (iconUrl.trim()) fields.icon_url = iconUrl.trim();
    if (authorizationUrl.trim()) fields.authorization_url = authorizationUrl.trim();
    if (tokenUrl.trim()) fields.token_url = tokenUrl.trim();
    if (userinfoUrl.trim()) fields.userinfo_url = userinfoUrl.trim();
    if (jwksUrl.trim()) fields.jwks_url = jwksUrl.trim();
    if (defaultTenantKey.trim()) fields.default_tenant_key = defaultTenantKey.trim();
    onSubmit({ mode: 'create', fields });
  };

  /** Format errors show while typing; "required" waits for the first submit. */
  const shown = (name: string, requiredText: string): string | undefined => {
    const message = errors[name];
    if (!message) return undefined;
    if (message === requiredText && !submitted) return undefined;
    return message;
  };
  const requiredText = t('pages.admin.oidc.form.required');
  const hint = (name: string, text: string) => shown(name, requiredText) ?? text;

  const submitLabel = !isEdit
    ? t('pages.admin.oidc.form.submitCreate')
    : needsStepUp && hasChanges
      ? t('pages.admin.oidc.form.submitSaveConfirm')
      : t('pages.admin.oidc.form.submitSave');

  return (
    <Dialog
      open
      onClose={pending ? undefined : onCancel}
      fullScreen={fullScreen}
      maxWidth="sm"
      fullWidth
      aria-labelledby="oidc-form-title"
      data-testid="oidc-form-dialog"
    >
      <DialogTitle id="oidc-form-title">
        {isEdit
          ? t('pages.admin.oidc.form.editTitle', { name: provider.display_name })
          : t('pages.admin.oidc.form.createTitle')}
      </DialogTitle>
      <DialogContent>
        <Box
          component="form"
          noValidate
          onSubmit={(e) => {
            e.preventDefault();
            handleSubmit();
          }}
          sx={{ display: 'flex', flexDirection: 'column', gap: 2.5, pt: 1 }}
        >
          <TextField
            label={t('pages.admin.oidc.form.slug')}
            value={isEdit ? provider.slug : slug}
            onChange={(e) => setSlug(e.target.value.toLowerCase())}
            disabled={isEdit || pending}
            required={!isEdit}
            autoFocus={!isEdit}
            autoComplete="off"
            fullWidth
            error={!isEdit && (slug.length > 0 || submitted) && Boolean(errors.slug)}
            helperText={
              isEdit
                ? t('pages.admin.oidc.form.slugLocked')
                : (slug.length > 0 || submitted) && errors.slug
                  ? errors.slug
                  : t('pages.admin.oidc.form.slugHelper')
            }
            slotProps={{ htmlInput: { maxLength: 50, spellCheck: false, autoCapitalize: 'none' } }}
            data-testid="oidc-form-slug"
          />
          <TextField
            label={t('pages.admin.oidc.form.displayName')}
            value={displayName}
            onChange={(e) => setDisplayName(e.target.value)}
            disabled={pending}
            required
            autoFocus={isEdit}
            fullWidth
            error={Boolean(shown('displayName', requiredText))}
            helperText={hint('displayName', t('pages.admin.oidc.form.displayNameHelper'))}
            slotProps={{ htmlInput: { maxLength: 200 } }}
            data-testid="oidc-form-display-name"
          />
          <TextField
            select
            label={t('pages.admin.oidc.form.providerType')}
            value={providerType}
            onChange={(e) => setProviderType(e.target.value)}
            disabled={pending}
            fullWidth
            helperText={t('pages.admin.oidc.form.providerTypeHelper')}
            slotProps={{ select: { native: true } }}
            data-testid="oidc-form-type"
          >
            {typeOptions.map((type) => (
              <option key={type} value={type}>
                {t(`pages.admin.oidc.types.${type}`, { defaultValue: type })}
              </option>
            ))}
          </TextField>
          <TextField
            label={t('pages.admin.oidc.form.issuerUrl')}
            value={issuerUrl}
            onChange={(e) => setIssuerUrl(e.target.value)}
            disabled={pending}
            required
            fullWidth
            type="url"
            autoComplete="off"
            error={Boolean(shown('issuerUrl', requiredText))}
            helperText={hint('issuerUrl', t('pages.admin.oidc.form.issuerUrlHelper'))}
            slotProps={{ htmlInput: { spellCheck: false, autoCapitalize: 'none' } }}
            data-testid="oidc-form-issuer"
          />
          <TextField
            label={t('pages.admin.oidc.form.clientId')}
            value={clientId}
            onChange={(e) => setClientId(e.target.value)}
            disabled={pending}
            required
            fullWidth
            autoComplete="off"
            error={Boolean(shown('clientId', requiredText))}
            helperText={shown('clientId', requiredText)}
            slotProps={{ htmlInput: { spellCheck: false, autoCapitalize: 'none' } }}
            data-testid="oidc-form-client-id"
          />
          <TextField
            label={isEdit ? t('pages.admin.oidc.form.clientSecretNew') : t('pages.admin.oidc.form.clientSecret')}
            value={clientSecret}
            onChange={(e) => setClientSecret(e.target.value)}
            disabled={pending}
            required={!isEdit}
            fullWidth
            type="password"
            // A password manager must not offer the admin's own login here.
            autoComplete="new-password"
            error={Boolean(shown('clientSecret', requiredText))}
            helperText={hint(
              'clientSecret',
              isEdit
                ? t('pages.admin.oidc.form.clientSecretHelperEdit')
                : t('pages.admin.oidc.form.clientSecretHelper'),
            )}
            data-testid="oidc-form-client-secret"
          />
          <TextField
            label={t('pages.admin.oidc.form.scopes')}
            value={scopesText}
            onChange={(e) => setScopesText(e.target.value)}
            disabled={pending}
            required
            fullWidth
            autoComplete="off"
            error={Boolean(errors.scopes) && (submitted || scopesText.length > 0)}
            helperText={errors.scopes && (submitted || scopesText.length > 0) ? errors.scopes : t('pages.admin.oidc.form.scopesHelper')}
            slotProps={{ htmlInput: { spellCheck: false, autoCapitalize: 'none' } }}
            data-testid="oidc-form-scopes"
          />
          <Box>
            <FormControlLabel
              control={
                <Switch
                  checked={autoDiscover}
                  onChange={(e) => setAutoDiscover(e.target.checked)}
                  disabled={pending}
                  slotProps={{ input: { 'aria-describedby': 'oidc-form-auto-discover-help' } }}
                />
              }
              label={t('pages.admin.oidc.form.autoDiscover')}
              data-testid="oidc-form-auto-discover"
            />
            <FormHelperText id="oidc-form-auto-discover-help" sx={{ mt: -0.5, ml: 0 }}>
              {t('pages.admin.oidc.form.autoDiscoverHelper')}
            </FormHelperText>
          </Box>
          <Box>
            <FormControlLabel
              control={
                <Switch
                  checked={enabled}
                  onChange={(e) => setEnabled(e.target.checked)}
                  disabled={pending}
                  slotProps={{ input: { 'aria-describedby': 'oidc-form-enabled-help' } }}
                />
              }
              label={t('pages.admin.oidc.form.enabled')}
              data-testid="oidc-form-enabled"
            />
            <FormHelperText id="oidc-form-enabled-help" sx={{ mt: -0.5, ml: 0 }}>
              {t('pages.admin.oidc.form.enabledHelper')}
            </FormHelperText>
          </Box>
          <TextField
            label={t('pages.admin.oidc.form.iconUrl')}
            value={iconUrl}
            onChange={(e) => setIconUrl(e.target.value)}
            disabled={pending}
            fullWidth
            type="url"
            autoComplete="off"
            helperText={t('pages.admin.oidc.form.iconUrlHelper')}
            slotProps={{ htmlInput: { spellCheck: false, autoCapitalize: 'none' } }}
            data-testid="oidc-form-icon-url"
          />

          {!isEdit && (
            <Accordion variant="outlined" disableGutters data-testid="oidc-form-advanced">
              <AccordionSummary
                expandIcon={<ExpandMoreIcon />}
                aria-controls="oidc-form-advanced-content"
                id="oidc-form-advanced-header"
              >
                <Typography>{t('pages.admin.oidc.form.advanced')}</Typography>
              </AccordionSummary>
              <AccordionDetails
                id="oidc-form-advanced-content"
                sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}
              >
                <Typography variant="body2" color="text.secondary">
                  {t('pages.admin.oidc.form.advancedHint')}
                </Typography>
                {(
                  [
                    ['authorizationUrl', authorizationUrl, setAuthorizationUrl, 'authorization-url'],
                    ['tokenUrl', tokenUrl, setTokenUrl, 'token-url'],
                    ['userinfoUrl', userinfoUrl, setUserinfoUrl, 'userinfo-url'],
                    ['jwksUrl', jwksUrl, setJwksUrl, 'jwks-url'],
                  ] as const
                ).map(([name, value, set, testId]) => (
                  <TextField
                    key={name}
                    label={t(`pages.admin.oidc.form.${name}`)}
                    value={value}
                    onChange={(e) => set(e.target.value)}
                    disabled={pending}
                    fullWidth
                    type="url"
                    autoComplete="off"
                    error={value.length > 0 && Boolean(errors[name])}
                    helperText={value.length > 0 ? errors[name] : undefined}
                    slotProps={{ htmlInput: { spellCheck: false, autoCapitalize: 'none' } }}
                    data-testid={`oidc-form-${testId}`}
                  />
                ))}
                <TextField
                  label={t('pages.admin.oidc.form.defaultTenantKey')}
                  value={defaultTenantKey}
                  onChange={(e) => setDefaultTenantKey(e.target.value)}
                  disabled={pending}
                  fullWidth
                  autoComplete="off"
                  slotProps={{ htmlInput: { spellCheck: false, autoCapitalize: 'none' } }}
                  data-testid="oidc-form-default-tenant"
                />
              </AccordionDetails>
            </Accordion>
          )}

          <Alert severity="info" data-testid="oidc-form-callback-hint">
            {t('pages.admin.oidc.form.callbackHint', { url: callbackUrl })}
          </Alert>

          {isEdit && !hasChanges && (
            <Typography variant="body2" color="text.secondary" data-testid="oidc-form-no-changes">
              {t('pages.admin.oidc.form.noChanges')}
            </Typography>
          )}
          {isEdit && hasChanges && (
            <Alert severity={needsStepUp ? 'warning' : 'success'} data-testid="oidc-form-step-up-hint">
              {needsStepUp
                ? t('pages.admin.oidc.form.willAskStepUp')
                : t('pages.admin.oidc.form.presentationOnly')}
            </Alert>
          )}
          {error && (
            <Alert severity="error" data-testid="oidc-form-error">
              {error}
            </Alert>
          )}
        </Box>
      </DialogContent>
      <DialogActions>
        <Button onClick={onCancel} disabled={pending} data-testid="oidc-form-cancel">
          {t('common.cancel')}
        </Button>
        <Button
          variant="contained"
          onClick={handleSubmit}
          disabled={pending || (isEdit && !hasChanges)}
          loading={pending}
          data-testid="oidc-form-submit"
        >
          {submitLabel}
        </Button>
      </DialogActions>
    </Dialog>
  );
}
