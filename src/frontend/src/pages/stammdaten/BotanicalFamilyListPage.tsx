import { useEffect, useState } from 'react';
import { useNavigate, Link as RouterLink } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import Button from '@mui/material/Button';
import Box from '@mui/material/Box';
import Link from '@mui/material/Link';
import Tooltip from '@mui/material/Tooltip';
import Typography from '@mui/material/Typography';
import AddIcon from '@mui/icons-material/Add';
import PageTitle from '@/components/layout/PageTitle';
import DataTable, { type Column } from '@/components/common/DataTable';
import { useAppDispatch, useAppSelector } from '@/store/hooks';
import { fetchBotanicalFamilies } from '@/store/slices/botanicalFamiliesSlice';
import { useTableUrlState } from '@/hooks/useTableState';
import type { BotanicalFamily } from '@/api/types';
import Chip from '@mui/material/Chip';
import MobileCard from '@/components/common/MobileCard';
import BotanicalFamilyCreateDialog from './BotanicalFamilyCreateDialog';
import { kamiMasterdata } from '@/assets/brand/illustrations';

export default function BotanicalFamilyListPage() {
  const { t, i18n } = useTranslation();
  const dispatch = useAppDispatch();
  const navigate = useNavigate();
  const { items, loading } = useAppSelector((s) => s.botanicalFamilies);
  const [createOpen, setCreateOpen] = useState(false);
  const tableState = useTableUrlState({ defaultSort: { column: 'name', direction: 'asc' } });

  useEffect(() => {
    dispatch(fetchBotanicalFamilies({}));
  }, [dispatch]);

  /**
   * Deep-link into the species overview pre-filtered to this family
   * (`/stammdaten/species?family=<key>`). Rendered as a link only when the
   * family actually has species — a plain "0" otherwise, so the affordance
   * never promises a filtered list that would come up empty.
   *
   * - `onClick` stopPropagation keeps the surrounding row-click (→ family
   *   detail) from also firing when the link is activated with the mouse.
   * - `onKeyDown` stopPropagation does the same for the keyboard: the row
   *   itself listens for `Enter` on `keydown` (see DataTable), and that
   *   handler doesn't check `event.target` — without stopping propagation
   *   here, pressing Enter while focused on this link would fire the row's
   *   "go to family detail" navigation *and* the link's own "go to filtered
   *   species" navigation back-to-back, leaving a phantom history entry.
   * - `aria-label` is per-row (family name + count) rather than a shared
   *   generic string, so screen-reader users scanning a "links list" across
   *   many rows can tell them apart instead of hearing the same label
   *   repeated for every family.
   * - The extra `sx` padding/negative-margin enlarges the tappable area
   *   without shifting the visible number — a plain digit is too small a
   *   target on its own (UI-NFR-001 R-011, 48×48px on touch). Full literal
   *   48×48px isn't achievable for an inline value in a dense table row
   *   without breaking row density; this is a pragmatic best-effort close
   *   to it, consistent with `align: 'right'` keeping neighbouring cells
   *   clear of the enlarged hit area.
   */
  const renderSpeciesCountLink = (r: BotanicalFamily) =>
    r.species_count > 0 ? (
      <Tooltip
        title={t('pages.botanicalFamilies.showAllSpeciesFilteredFor', {
          family: r.name,
          count: r.species_count,
        })}
      >
        <Link
          component={RouterLink}
          to={`/stammdaten/species?family=${r.key}`}
          onClick={(e: React.MouseEvent) => e.stopPropagation()}
          onKeyDown={(e: React.KeyboardEvent) => e.stopPropagation()}
          aria-label={t('pages.botanicalFamilies.showAllSpeciesFilteredFor', {
            family: r.name,
            count: r.species_count,
          })}
          sx={{ display: 'inline-block', p: 1, m: -1 }}
        >
          {r.species_count}
        </Link>
      </Tooltip>
    ) : (
      r.species_count
    );

  const columns: Column<BotanicalFamily>[] = [
    {
      id: 'name',
      label: t('pages.botanicalFamilies.name'),
      // Deliberately inert. The row click already navigates here, so a link on
      // the name would duplicate that target while making the cell interactive
      // — and an interactive cell swallows the row click, because MUI's link
      // stops propagation. The suite's interaction guard rejects such a cell as
      // a row-click target outright, which is how this was caught. The species
      // count below is a link because it goes somewhere the row click does not.
      render: (r) => r.name,
      searchValue: (r) => r.name,
    },
    {
      id: 'commonName',
      label: t('pages.botanicalFamilies.commonName'),
      render: (r) =>
        i18n.language === 'en'
          ? r.common_name_en || r.common_name_de || '—'
          : r.common_name_de || r.common_name_en || '—',
      searchValue: (r) => `${r.common_name_de} ${r.common_name_en}`,
    },
    {
      id: 'nutrientDemand',
      label: t('pages.botanicalFamilies.nutrientDemand'),
      render: (r) => t(`enums.nutrientDemand.${r.typical_nutrient_demand}`),
      searchValue: (r) => t(`enums.nutrientDemand.${r.typical_nutrient_demand}`),
    },
    {
      id: 'frostTolerance',
      label: t('pages.botanicalFamilies.frostTolerance'),
      render: (r) => t(`enums.frostTolerance.${r.frost_tolerance}`),
      searchValue: (r) => t(`enums.frostTolerance.${r.frost_tolerance}`),
    },
    {
      id: 'rootDepth',
      label: t('pages.botanicalFamilies.rootDepth'),
      render: (r) => t(`enums.rootDepth.${r.typical_root_depth}`),
      searchValue: (r) => t(`enums.rootDepth.${r.typical_root_depth}`),
    },
    {
      id: 'speciesCount',
      label: t('pages.botanicalFamilies.speciesCount'),
      render: renderSpeciesCountLink,
      align: 'right',
      sortFn: (a, b) => a.species_count - b.species_count,
      searchValue: (r) => String(r.species_count),
    },
    {
      id: 'rotationCategory',
      label: t('pages.botanicalFamilies.rotationCategory'),
      render: (r) => r.rotation_category || '—',
    },
  ];

  return (
    <Box data-testid="botanical-family-list-page">
      <PageTitle
        title={t('pages.botanicalFamilies.title')}
        action={
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={() => setCreateOpen(true)}
            data-testid="create-button"
          >
            {t('pages.botanicalFamilies.create')}
          </Button>
        }
      />

      {!loading && (
        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
          {t('pages.botanicalFamilies.listIntro')}
        </Typography>
      )}

      <DataTable
        columns={columns}
        rows={items}
        loading={loading}
        onRowClick={(r) => navigate(`/stammdaten/botanical-families/${r.key}`)}
        getRowKey={(r) => r.key}
        emptyActionLabel={t('pages.botanicalFamilies.create')}
        onEmptyAction={() => setCreateOpen(true)}
        emptyIllustration={kamiMasterdata}
        tableState={tableState}
        ariaLabel={t('pages.botanicalFamilies.title')}
        mobileCardRenderer={(r) => (
          <MobileCard
            title={r.name}
            titleId="name"
            subtitle={
              i18n.language === 'en'
                ? r.common_name_en || r.common_name_de
                : r.common_name_de || r.common_name_en
            }
            subtitleId="commonName"
            chips={[
              {
                id: 'nutrientDemand',
                content: (
                  <Chip
                    label={t(`enums.nutrientDemand.${r.typical_nutrient_demand}`)}
                    size="small"
                    variant="outlined"
                  />
                ),
              },
              {
                id: 'frostTolerance',
                content: (
                  <Chip
                    label={t(`enums.frostTolerance.${r.frost_tolerance}`)}
                    size="small"
                    variant="outlined"
                  />
                ),
              },
              ...(r.rotation_category
                ? [
                    {
                      id: 'rotationCategory',
                      content: (
                        <Chip label={r.rotation_category} size="small" variant="outlined" />
                      ),
                    },
                  ]
                : []),
            ]}
            fields={[
              { id: 'rootDepth', label: t('pages.botanicalFamilies.rootDepth'), value: t(`enums.rootDepth.${r.typical_root_depth}`) },
              { id: 'speciesCount', label: t('pages.botanicalFamilies.speciesCount'), value: renderSpeciesCountLink(r) },
            ]}
          />
        )}
      />

      <BotanicalFamilyCreateDialog
        open={createOpen}
        onClose={() => setCreateOpen(false)}
        onCreated={() => {
          setCreateOpen(false);
          dispatch(fetchBotanicalFamilies({}));
        }}
      />
    </Box>
  );
}
