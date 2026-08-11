import { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useNavigate } from 'react-router-dom';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import Button from '@mui/material/Button';
import IconButton from '@mui/material/IconButton';
import AddIcon from '@mui/icons-material/Add';
import DeleteIcon from '@mui/icons-material/Delete';
import Chip from '@mui/material/Chip';
import MobileCard from '@/components/common/MobileCard';
import DataTable, { type Column } from '@/components/common/DataTable';
import ConfirmDialog from '@/components/common/ConfirmDialog';
import { useTableLocalState } from '@/hooks/useTableState';
import { useCanCreateCatalogEntry } from '@/hooks/useCanCreateCatalogEntry';
import CultivarCreateDialog from './CultivarCreateDialog';
import { useNotification } from '@/hooks/useNotification';
import { useApiError } from '@/hooks/useApiError';
import * as api from '@/api/endpoints/species';
import type { Cultivar } from '@/api/types';

interface Props {
  speciesKey: string;
}

export default function CultivarListSection({ speciesKey }: Props) {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const notification = useNotification();
  const { handleError } = useApiError();
  const [cultivars, setCultivars] = useState<Cultivar[]>([]);
  const [loading, setLoading] = useState(false);
  const [createOpen, setCreateOpen] = useState(false);
  const [deleteTarget, setDeleteTarget] = useState<Cultivar | null>(null);
  const [deleting, setDeleting] = useState(false);
  const tableState = useTableLocalState({ defaultSort: { column: 'name', direction: 'asc' } });
  // #1091 A-7 — UX consequence of the backend create gate (SEC-005/#1113, A-3), not
  // a security control: `POST /species/{key}/cultivars` refuses a tenant viewer with
  // 403 whatever this section renders. Same hook, and therefore the same predicate,
  // as the species list: "active tenant that cannot edit", never "cannot prove edit".
  const canCreate = useCanCreateCatalogEntry();

  const load = async () => {
    setLoading(true);
    try {
      setCultivars(await api.listCultivars(speciesKey));
    } catch (err) {
      handleError(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, [speciesKey]); // eslint-disable-line react-hooks/exhaustive-deps

  const onDelete = async () => {
    if (!deleteTarget) return;
    setDeleting(true);
    try {
      await api.deleteCultivar(speciesKey, deleteTarget.key);
      notification.success(t('common.delete'));
      load();
    } catch (err) {
      handleError(err);
    } finally {
      setDeleting(false);
      setDeleteTarget(null);
    }
  };

  const columns: Column<Cultivar>[] = [
    { id: 'name', label: t('pages.cultivars.name'), render: (r) => r.name },
    { id: 'breeder', label: t('pages.cultivars.breeder'), render: (r) => r.breeder ?? '—' },
    {
      id: 'traits',
      label: t('pages.cultivars.traits'),
      render: (r) => (
        <Box sx={{ display: 'flex', gap: 0.5, flexWrap: 'wrap' }}>
          {r.traits.map((tr) => (
            <Chip key={tr} label={t(`enums.plantTrait.${tr}`)} size="small" />
          ))}
        </Box>
      ),
    },
    {
      id: 'maturity',
      label: t('pages.cultivars.daysToMaturity'),
      render: (r) => r.days_to_maturity ?? '—',
      align: 'right',
    },
    {
      id: 'actions',
      label: t('common.actions'),
      width: 60,
      sortable: false,
      searchable: false,
      render: (r) => (
        <IconButton
          size="small"
          aria-label={t('common.delete')}
          onClick={(e) => { e.stopPropagation(); setDeleteTarget(r); }}
          data-testid={`cultivar-delete-${r.key}`}
        >
          <DeleteIcon fontSize="small" />
        </IconButton>
      ),
    },
  ];

  /** Row action for the mobile card view — the same delete the desktop actions
   *  column offers. Without it a cultivar cannot be deleted below the `sm`
   *  breakpoint at all. Touch target per UI-NFR-001 R-011 (48x48). */
  const renderRowActions = (r: Cultivar) => (
    <IconButton
      aria-label={t('common.delete')}
      onClick={(e) => { e.stopPropagation(); setDeleteTarget(r); }}
      sx={{ minWidth: 48, minHeight: 48 }}
      data-testid={`cultivar-delete-${r.key}`}
    >
      <DeleteIcon fontSize="small" />
    </IconButton>
  );

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
        <Typography variant="h6">{t('pages.cultivars.title')}</Typography>
        {canCreate && (
          <Button startIcon={<AddIcon />} onClick={() => setCreateOpen(true)} data-testid="create-button">
            {t('pages.cultivars.create')}
          </Button>
        )}
      </Box>

      <DataTable
        columns={columns}
        rows={cultivars}
        loading={loading}
        getRowKey={(r) => r.key}
        onRowClick={(r) => navigate(`/stammdaten/species/${speciesKey}/cultivars/${r.key}`)}
        tableState={tableState}
        ariaLabel={t('pages.cultivars.title')}
        // With the create button gone, the empty state is the only place left to
        // say *why* — a read-only member would otherwise face a bare "no data".
        emptyDescription={canCreate ? undefined : t('pages.cultivars.createDenied')}
        mobileCardRenderer={(r) => (
          <MobileCard
            title={r.name}
            titleId="name"
            subtitle={r.breeder || undefined}
            subtitleId="breeder"
            // Traits share one column, so they are keyed by position: a single
            // `traits` id would collide across the list.
            chips={r.traits.map((tr, i) => ({
              id: `traits-${i}`,
              content: (
                <Chip key={tr} label={t(`enums.plantTrait.${tr}`)} size="small" variant="outlined" />
              ),
            }))}
            fields={
              r.days_to_maturity != null
                ? [{ id: 'maturity', label: t('pages.cultivars.daysToMaturity'), value: r.days_to_maturity }]
                : undefined
            }
            trailing={renderRowActions(r)}
          />
        )}
      />

      <CultivarCreateDialog
        speciesKey={speciesKey}
        open={createOpen}
        onClose={() => setCreateOpen(false)}
        onCreated={() => { setCreateOpen(false); load(); }}
      />

      <ConfirmDialog
        open={!!deleteTarget}
        title={t('common.delete')}
        message={t('common.deleteConfirm', { name: deleteTarget?.name })}
        onConfirm={onDelete}
        onCancel={() => setDeleteTarget(null)}
        destructive
        loading={deleting}
      />
    </Box>
  );
}
