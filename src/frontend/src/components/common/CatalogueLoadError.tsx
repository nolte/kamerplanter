import Alert from '@mui/material/Alert';
import AlertTitle from '@mui/material/AlertTitle';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import { useTranslation } from 'react-i18next';
import type { CatalogueName, CatalogueReader } from '@/hooks/useCatalogue';

/**
 * What a failed catalogue load costs the user at this site, which decides the
 * second sentence of the message.
 *
 * - `picker` — the catalogue backs a selection field. The field is unusable
 *   until the catalogue arrives, and an empty field must not read as "there are
 *   no entries".
 * - `lookup` — the catalogue only resolves stored keys to display names. The
 *   page still works; names may show as their raw identifier instead.
 */
export type CatalogueFailureImpact = 'picker' | 'lookup';

interface CatalogueLoadErrorProps {
  /** The reader returned by `useCatalogue`; renders nothing unless it `failed`. */
  reader: Pick<CatalogueReader<unknown>, 'name' | 'status' | 'reload'>;
  /** Defaults to `picker`, the case where an empty list actively misleads. */
  impact?: CatalogueFailureImpact;
  /** Called before `reader.reload()`, e.g. to arm a focus restore. */
  onRetry?: () => void;
  /** Defaults to `catalogue-load-error-<name>`. */
  'data-testid'?: string;
}

/**
 * The ready-made failure element for {@link useCatalogue} (#1628).
 *
 * Every call site of the hook either renders this next to what the catalogue
 * feeds, or states in a comment why it does not. It exists so that decision is
 * "render it or justify it" rather than rebuilding a failure state per site —
 * fourteen of sixteen sites had rebuilt none and showed a failed load as an
 * empty picker.
 *
 * Renders `null` while the catalogue is loading or ready, so a caller can mount
 * it unconditionally and keep its own loading and empty states distinct.
 *
 * Accessibility: MUI's `Alert` carries `role="alert"`, so the failure is
 * announced when it appears; severity is conveyed by the title text and icon,
 * not colour alone; the retry is a real `<button>` (keyboard-reachable) with a
 * 48 px minimum hit area (UI-NFR-001 R-011). The action wraps below the message
 * on narrow screens instead of squeezing it.
 */
export default function CatalogueLoadError({
  reader,
  impact = 'picker',
  onRetry,
  'data-testid': testId,
}: CatalogueLoadErrorProps) {
  const { t } = useTranslation();
  if (reader.status !== 'failed') return null;

  const id = testId ?? `catalogue-load-error-${reader.name}`;
  const catalogueLabel = t(`common.catalogue.names.${reader.name satisfies CatalogueName}`);

  return (
    <Box sx={{ my: 1.5 }} data-testid={id}>
      <Alert
        severity="error"
        sx={{
          flexWrap: { xs: 'wrap', sm: 'nowrap' },
          '& .MuiAlert-action': { pl: { xs: 0, sm: 2 }, ml: { xs: 0, sm: 'auto' } },
        }}
        action={
          <Button
            color="inherit"
            size="small"
            onClick={() => {
              onRetry?.();
              reader.reload();
            }}
            data-testid={`${id}-retry`}
            sx={{ minHeight: 48, minWidth: 48 }}
          >
            {t('common.retry')}
          </Button>
        }
      >
        <AlertTitle>{t('common.catalogue.loadFailedTitle', { catalogue: catalogueLabel })}</AlertTitle>
        {impact === 'picker'
          ? t('common.catalogue.loadFailedPicker')
          : t('common.catalogue.loadFailedLookup')}
      </Alert>
    </Box>
  );
}
