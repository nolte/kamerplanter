import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import Button from '@mui/material/Button';
import AddIcon from '@mui/icons-material/Add';
import DataTable, { type Column } from '@/components/common/DataTable';
import LocationCreateDialog from './LocationCreateDialog';
import { useApiError } from '@/hooks/useApiError';
import { useTableLocalState } from '@/hooks/useTableState';
import * as api from '@/api/endpoints/sites';
import type { Location } from '@/api/types';

interface Props {
  siteKey: string;
}

export default function LocationListSection({ siteKey }: Props) {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const { handleError } = useApiError();
  const [locations, setLocations] = useState<Location[]>([]);
  const [loading, setLoading] = useState(false);
  const [createOpen, setCreateOpen] = useState(false);
  const tableState = useTableLocalState({ defaultSort: { column: 'name', direction: 'asc' } });

  const load = async () => {
    setLoading(true);
    try {
      setLocations(await api.listLocations(siteKey));
    } catch (err) {
      handleError(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, [siteKey]); // eslint-disable-line react-hooks/exhaustive-deps

  const columns: Column<Location>[] = [
    { id: 'name', label: t('pages.locations.name'), render: (r) => r.name },
    { id: 'area', label: t('pages.locations.area'), render: (r) => `${r.area_m2} m²`, align: 'right', searchValue: (r) => String(r.area_m2) },
    { id: 'light', label: t('pages.locations.lightType'), render: (r) => t(`enums.lightType.${r.light_type}`), searchValue: (r) => t(`enums.lightType.${r.light_type}`) },
    { id: 'irrigation', label: t('pages.locations.irrigationSystem'), render: (r) => t(`enums.irrigationSystem.${r.irrigation_system}`), searchValue: (r) => t(`enums.irrigationSystem.${r.irrigation_system}`) },
  ];

  return (
    <Box sx={{ mt: 4 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
        <Typography variant="h6">{t('pages.locations.title')}</Typography>
        <Button startIcon={<AddIcon />} onClick={() => setCreateOpen(true)}>
          {t('pages.locations.create')}
        </Button>
      </Box>
      <DataTable
        columns={columns}
        rows={locations}
        loading={loading}
        onRowClick={(r) => navigate(`/standorte/locations/${r.key}`)}
        getRowKey={(r) => r.key}
        tableState={tableState}
        ariaLabel={t('pages.locations.title')}
      />
      <LocationCreateDialog
        siteKey={siteKey}
        open={createOpen}
        onClose={() => setCreateOpen(false)}
        onCreated={() => { setCreateOpen(false); load(); }}
      />
    </Box>
  );
}
