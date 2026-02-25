import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import Button from '@mui/material/Button';
import AddIcon from '@mui/icons-material/Add';
import PageTitle from '@/components/layout/PageTitle';
import LoadingSkeleton from '@/components/common/LoadingSkeleton';
import ErrorDisplay from '@/components/common/ErrorDisplay';
import DataTable, { type Column } from '@/components/common/DataTable';
import BatchCreateDialog from './BatchCreateDialog';
import { useNotification } from '@/hooks/useNotification';
import { useApiError } from '@/hooks/useApiError';
import * as api from '@/api/endpoints/substrates';
import type { Substrate, Batch, ReusabilityResponse } from '@/api/types';
import Chip from '@mui/material/Chip';
import Alert from '@mui/material/Alert';

export default function SubstrateDetailPage() {
  const { key } = useParams<{ key: string }>();
  const { t } = useTranslation();
  const navigate = useNavigate();
  const notification = useNotification();
  const { handleError } = useApiError();
  const [substrate, setSubstrate] = useState<Substrate | null>(null);
  const [batches, setBatches] = useState<Batch[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [batchCreateOpen, setBatchCreateOpen] = useState(false);
  const [reusability, setReusability] = useState<Record<string, ReusabilityResponse>>({});

  const load = async () => {
    if (!key) return;
    setLoading(true);
    try {
      setSubstrate(await api.getSubstrate(key));
      // Batches are not directly listed per substrate in the API,
      // but we display substrate info
    } catch (err) {
      setError(String(err));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, [key]); // eslint-disable-line react-hooks/exhaustive-deps

  const checkReusability = async (batchKey: string) => {
    try {
      const result = await api.checkReusability(batchKey);
      setReusability((prev) => ({ ...prev, [batchKey]: result }));
      if (result.can_reuse) {
        notification.success(t('pages.substrates.checkReusability') + ': OK');
      } else {
        notification.warning(t('pages.substrates.checkReusability') + ': ' + result.treatments.join(', '));
      }
    } catch (err) {
      handleError(err);
    }
  };

  const batchColumns: Column<Batch>[] = [
    { id: 'batchId', label: t('pages.batches.batchId'), render: (r) => r.batch_id },
    { id: 'volume', label: t('pages.batches.volume'), render: (r) => `${r.volume_liters} L` },
    { id: 'mixedOn', label: t('pages.batches.mixedOn'), render: (r) => r.mixed_on },
    { id: 'cycles', label: t('pages.batches.cyclesUsed'), render: (r) => r.cycles_used },
    {
      id: 'actions',
      label: t('common.actions'),
      render: (r) => (
        <Button size="small" onClick={(e) => { e.stopPropagation(); checkReusability(r.key); }}>
          {t('pages.substrates.checkReusability')}
        </Button>
      ),
    },
  ];

  if (loading) return <LoadingSkeleton variant="form" />;
  if (error) return <ErrorDisplay error={error} onRetry={() => navigate(-1)} />;

  return (
    <>
      <PageTitle title={substrate ? `${t(`enums.substrateType.${substrate.type}`)} ${substrate.brand ?? ''}` : t('entities.substrate')} />

      {substrate && (
        <Box sx={{ mb: 3 }}>
          <Typography variant="body1">pH: {substrate.ph_base} | EC: {substrate.ec_base_ms} mS/cm</Typography>
          <Typography variant="body2">
            {t('pages.substrates.waterRetention')}: {t(`enums.waterRetention.${substrate.water_retention}`)} |
            {t('pages.substrates.bufferCapacity')}: {t(`enums.bufferCapacity.${substrate.buffer_capacity}`)}
          </Typography>
          <Chip
            label={substrate.reusable ? t('common.yes') : t('common.no')}
            size="small"
            color={substrate.reusable ? 'success' : 'default'}
            sx={{ mt: 1 }}
          />
        </Box>
      )}

      {Object.entries(reusability).map(([batchKey, result]) => (
        <Alert key={batchKey} severity={result.can_reuse ? 'success' : 'warning'} sx={{ mb: 1 }}>
          Batch {batchKey}: {result.can_reuse ? 'Reusable' : result.treatments.join(', ')}
        </Alert>
      ))}

      <Box sx={{ mt: 3 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
          <Typography variant="h6">{t('pages.batches.title')}</Typography>
          <Button startIcon={<AddIcon />} onClick={() => setBatchCreateOpen(true)}>
            {t('pages.batches.create')}
          </Button>
        </Box>
        <DataTable columns={batchColumns} rows={batches} getRowKey={(r) => r.key} />
      </Box>

      {key && (
        <BatchCreateDialog
          substrateKey={key}
          open={batchCreateOpen}
          onClose={() => setBatchCreateOpen(false)}
          onCreated={(batch) => {
            setBatchCreateOpen(false);
            setBatches((prev) => [...prev, batch]);
          }}
        />
      )}
    </>
  );
}
