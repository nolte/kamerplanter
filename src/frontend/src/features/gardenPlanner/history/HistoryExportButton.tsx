/**
 * "Export CSV" of the care history (REQ-053 GP-FR-104, GP-API-034 `format=csv`): downloads the stored care
 * entries the current filters list (same role rules, at most 50 000 rows). A bed's list also shows planting
 * events derived from plants and runs; those are not care entries and are not in the file. The Excel variant uses
 * a semicolon and a decimal comma. The file is built by the server; this button only asks and saves.
 */
import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import DownloadIcon from '@mui/icons-material/Download';
import Button from '@mui/material/Button';
import CircularProgress from '@mui/material/CircularProgress';
import Menu from '@mui/material/Menu';
import MenuItem from '@mui/material/MenuItem';
import axios from 'axios';
import { isApiError } from '@/api/errors';
import { useApiError } from '@/hooks/useApiError';
import { useNotification } from '@/hooks/useNotification';
import { saveBlob } from '@/utils/saveBlob';
import { downloadCareEventsCsv, type CsvDelimiter } from './historyApi';
import type { HistoryQuery } from './historyFilters';

const TOO_MANY_ROWS = 'export.too_many_rows';
const RATE_LIMITED = 429;

interface HistoryExportButtonProps {
  /** The filters of the list on screen (a bed adds its `location_key`). */
  query: HistoryQuery;
  disabled?: boolean;
  testIdPrefix: string;
}

function fileName(now: Date): string {
  const pad = (value: number) => String(value).padStart(2, '0');
  return `care-events-${now.getFullYear()}${pad(now.getMonth() + 1)}${pad(now.getDate())}.csv`;
}

/** The rate limiter answers its own 429 body (no error envelope), so the status is read from the raw response. */
function isRateLimited(error: unknown): boolean {
  if (axios.isAxiosError(error)) return error.response?.status === RATE_LIMITED;
  return isApiError(error) && error.statusCode === RATE_LIMITED;
}

function isTooManyRows(error: unknown): boolean {
  return isApiError(error) && (error.errorCode === TOO_MANY_ROWS || error.details.some((detail) => detail.code === TOO_MANY_ROWS));
}

export default function HistoryExportButton({ query, disabled = false, testIdPrefix }: HistoryExportButtonProps) {
  const { t } = useTranslation();
  const { handleError } = useApiError();
  const notification = useNotification();
  const [anchor, setAnchor] = useState<HTMLElement | null>(null);
  const [busy, setBusy] = useState(false);

  const download = async (delimiter: CsvDelimiter) => {
    setAnchor(null);
    setBusy(true);
    try {
      saveBlob(await downloadCareEventsCsv(query, delimiter), fileName(new Date()));
      notification.success(t('pages.bed.history.export.done'));
    } catch (error) {
      if (isTooManyRows(error)) {
        notification.error(t('pages.bed.history.export.tooManyRows'));
      } else if (isRateLimited(error)) {
        notification.warning(t('pages.bed.history.export.rateLimited'));
      } else {
        handleError(error);
      }
    } finally {
      setBusy(false);
    }
  };

  return (
    <>
      <Button
        variant="outlined"
        size="small"
        startIcon={busy ? <CircularProgress size={16} color="inherit" /> : <DownloadIcon />}
        onClick={(event) => setAnchor(event.currentTarget)}
        disabled={disabled || busy}
        aria-haspopup="menu"
        aria-expanded={anchor !== null}
        sx={{ minHeight: 44 }}
        data-testid={`${testIdPrefix}-export`}
      >
        {t('pages.bed.history.export.button')}
      </Button>
      <Menu anchorEl={anchor} open={anchor !== null} onClose={() => setAnchor(null)}>
        <MenuItem onClick={() => void download('comma')} data-testid={`${testIdPrefix}-export-comma`}>
          {t('pages.bed.history.export.comma')}
        </MenuItem>
        <MenuItem onClick={() => void download('semicolon')} data-testid={`${testIdPrefix}-export-semicolon`}>
          {t('pages.bed.history.export.semicolon')}
        </MenuItem>
      </Menu>
    </>
  );
}
