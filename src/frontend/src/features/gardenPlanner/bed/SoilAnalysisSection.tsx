/**
 * Soil analyses in the bed's soil tab (REQ-053 GP-FR-122): "Record soil analysis", the "liming likely" hint and the
 * pH/EC/humus history. The hint is the server's (method + texture + stated target pH) and only a text - never an
 * amount. The dialog and the chart are `lazy()` chunks; the chart loads only once there is a value to draw.
 */
import { lazy, Suspense, useRef, useState } from 'react';
import { useTranslation } from 'react-i18next';
import Alert from '@mui/material/Alert';
import AlertTitle from '@mui/material/AlertTitle';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Typography from '@mui/material/Typography';
import ScienceOutlinedIcon from '@mui/icons-material/ScienceOutlined';
import EmptyState from '@/components/common/EmptyState';
import LoadingSkeleton from '@/components/common/LoadingSkeleton';
import { useNotification } from '@/hooks/useNotification';
import type { LimingHint } from './soilAnalysisTypes';
import { useSoilAnalyses } from './useSoilAnalyses';

// The dialog loads when it opens; the chart (recharts) when the bed has a value to draw.
const SoilAnalysisDialog = lazy(() => import('./SoilAnalysisDialog'));
const SoilAnalysisChart = lazy(() => import('./SoilAnalysisChart'));

const PREFIX = 'pages.bed.soil';

interface SoilAnalysisSectionProps {
  bedKey: string;
  bedName: string;
  canEdit: boolean;
  /** Changes when the stored profile changed; the hint is read again. */
  profileVersion: unknown;
  /** An analysis was stored: the profile behind the summary changed, reload it. */
  onRecorded: () => void;
}

export default function SoilAnalysisSection({
  bedKey,
  bedName,
  canEdit,
  profileVersion,
  onRecorded,
}: SoilAnalysisSectionProps) {
  const { t } = useTranslation();
  const notification = useNotification();
  const [dialogOpen, setDialogOpen] = useState(false);
  const titleRef = useRef<HTMLHeadingElement>(null);
  const { data, loading, failed, reload } = useSoilAnalyses(bedKey, profileVersion);

  const record = canEdit ? (
    <Button
      variant="outlined"
      startIcon={<ScienceOutlinedIcon />}
      onClick={() => setDialogOpen(true)}
      sx={{ minHeight: 48 }}
      data-testid="soil-analysis-record"
    >
      {t(`${PREFIX}.analysis.record`)}
    </Button>
  ) : null;

  let body;
  if (loading && data === null) body = <LoadingSkeleton variant="card" />;
  else if (failed && data === null)
    body = (
      <Alert severity="warning" action={<Button onClick={reload}>{t('common.retry')}</Button>}>
        {t(`${PREFIX}.history.loadFailed`)}
      </Alert>
    );
  else if (data === null || data.analyses === 0)
    body = (
      <EmptyState
        message={t(`${PREFIX}.history.emptyTitle`)}
        description={t(canEdit ? `${PREFIX}.history.emptyDescription` : `${PREFIX}.history.emptyReadOnly`)}
        actionLabel={canEdit ? t(`${PREFIX}.analysis.record`) : undefined}
        onAction={canEdit ? () => setDialogOpen(true) : undefined}
      />
    );
  else
    body = (
      <>
        {data.truncated && (
          <Typography variant="body2" color="text.secondary">
            {t(`${PREFIX}.history.truncated`, { count: data.analyses })}
          </Typography>
        )}
        <Suspense fallback={<LoadingSkeleton variant="card" />}>
          <SoilAnalysisChart data={data} />
        </Suspense>
      </>
    );

  return (
    <Box
      component="section"
      aria-labelledby="bed-soil-analyses-title"
      data-testid="bed-soil-analyses"
      sx={{ display: 'flex', flexDirection: 'column', gap: 2, maxWidth: 960, mt: 4 }}
    >
      <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 2, alignItems: 'center', justifyContent: 'space-between' }}>
        <Box>
          <Typography id="bed-soil-analyses-title" variant="h6" component="h3" ref={titleRef} tabIndex={-1} sx={{ outline: 'none' }}>
            {t(`${PREFIX}.history.title`)}
          </Typography>
          <Typography variant="body2" color="text.secondary">
            {t(`${PREFIX}.history.intro`)}
          </Typography>
        </Box>
        {data !== null && data.analyses > 0 && record}
      </Box>
      {data !== null && <LimingHintNote hint={data.liming_hint} />}
      {body}

      {dialogOpen && (
        <Suspense fallback={null}>
          <SoilAnalysisDialog
            bedKey={bedKey}
            bedName={bedName}
            onClose={() => setDialogOpen(false)}
            onSaved={() => {
              setDialogOpen(false);
              notification.success(t(`${PREFIX}.analysis.saved`));
              reload();
              onRecorded();
              // The button that opened the dialog may vanish once the history is no longer empty.
              window.setTimeout(() => titleRef.current?.focus(), 0);
            }}
          />
        </Suspense>
      )}
    </Box>
  );
}

/** "Liming likely" as a text: the server's verdict and why - never an amount (hint-only list). */
function LimingHintNote({ hint }: { hint: LimingHint }) {
  const { t } = useTranslation();
  if (hint.status === 'likely') {
    return (
      <Alert severity="info" data-testid="soil-liming-hint" data-status={hint.status}>
        <AlertTitle>{t(`${PREFIX}.liming.likelyTitle`)}</AlertTitle>
        {t(`${PREFIX}.liming.likely`)}
      </Alert>
    );
  }
  return (
    <Typography variant="body2" color="text.secondary" data-testid="soil-liming-hint" data-status={hint.status}>
      {t(`${PREFIX}.liming.reasons.${hint.reason}`)}
    </Typography>
  );
}
