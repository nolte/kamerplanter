/**
 * The rotation matrix of a site (REQ-053 GP-FR-135, GP-API `GET /sites/{key}/rotation-matrix`): one row per bed,
 * one column per year, a cell lists what stood in the bed that year. The family is marked by colour **and** by a
 * short code plus a fill pattern (greyscale and colour-blind safe), the feeder class stands as text. A grower taps
 * a past cell to fill the year in ("What stood here in {year}?", GP-API-042); every member can read. The header row
 * and the bed column stay put while the table scrolls, on a 390 px screen too.
 */
import { useCallback, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Link as RouterLink, useParams } from 'react-router-dom';
import Alert from '@mui/material/Alert';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import ButtonBase from '@mui/material/ButtonBase';
import Link from '@mui/material/Link';
import Table from '@mui/material/Table';
import TableBody from '@mui/material/TableBody';
import TableCell from '@mui/material/TableCell';
import TableContainer from '@mui/material/TableContainer';
import TableHead from '@mui/material/TableHead';
import TableRow from '@mui/material/TableRow';
import Typography from '@mui/material/Typography';
import { visuallyHidden } from '@mui/utils';
import ErrorDisplay from '@/components/common/ErrorDisplay';
import LoadingSkeleton from '@/components/common/LoadingSkeleton';
import PageTitle from '@/components/layout/PageTitle';
import { useTenantPermissions } from '@/hooks/useTenantPermissions';
import { useUndoSnackbar } from '../care/useUndoSnackbar';
import BackfillDialog from './BackfillDialog';
import { cancelBackfill } from './historyApi';
import type { BackfillResult, RotationPlanting, RotationYear } from './historyTypes';
import { FAMILY_PATTERNS, type FamilyMark, hasMoreBeds } from './rotationMatrix';
import { useRotationMatrix } from './useRotationMatrix';

const MIN_CELL_WIDTH = 104;
const BED_COLUMN_WIDTH = 132;

function Swatch({ mark }: { mark: FamilyMark | undefined }) {
  return (
    <Box
      component="span"
      aria-hidden="true"
      data-testid={mark ? `matrix-swatch-${mark.familyKey}` : undefined}
      sx={{
        display: 'inline-block',
        width: 14,
        height: 14,
        flex: 'none',
        borderRadius: '3px',
        bgcolor: mark?.color ?? 'action.disabledBackground',
        backgroundImage: mark ? FAMILY_PATTERNS[mark.pattern] : 'none',
        backgroundSize: '6px 6px',
        border: 1,
        borderColor: 'text.primary',
      }}
    />
  );
}

function demandText(planting: RotationPlanting, t: (key: string, options?: Record<string, unknown>) => string): string | null {
  return planting.nutrient_demand
    ? t(`enums.nutrientDemandLevel.${planting.nutrient_demand}`, { defaultValue: planting.nutrient_demand })
    : null;
}

function PlantingEntry({
  planting,
  mark,
  t,
}: {
  planting: RotationPlanting;
  mark: FamilyMark | undefined;
  t: (key: string, options?: Record<string, unknown>) => string;
}) {
  const fallow = planting.plan_role === 'fallow';
  const greenManure = planting.plan_role === 'green_manure';
  const season = planting.season ? t(`pages.bed.history.timeline.seasons.${planting.season}`) : null;
  const demand = demandText(planting, t);
  return (
    <Box component="li" sx={{ listStyle: 'none', display: 'flex', alignItems: 'flex-start', gap: 0.75, textAlign: 'left' }}>
      <Swatch mark={fallow ? undefined : mark} />
      <Box sx={{ minWidth: 0 }}>
        <Typography component="span" variant="body2" sx={{ fontWeight: 700, display: 'block' }}>
          {fallow ? t('pages.bed.history.timeline.fallow') : (mark?.code ?? planting.family_name ?? '?')}
          {greenManure && ` · ${t('pages.bed.history.timeline.greenManure')}`}
        </Typography>
        {(demand || season) && (
          <Typography component="span" variant="caption" color="text.secondary" sx={{ display: 'block', lineHeight: 1.3 }}>
            {[demand, season].filter(Boolean).join(' · ')}
          </Typography>
        )}
      </Box>
    </Box>
  );
}

/** The cell in words, for the accessible name of its button: full family names, never the codes. */
function summarize(
  year: RotationYear,
  marks: ReadonlyMap<string, FamilyMark>,
  t: (key: string, options?: Record<string, unknown>) => string,
): string {
  if (year.plantings.length === 0) return t('pages.rotationMatrix.cellEmpty');
  return year.plantings
    .map((planting) => {
      if (planting.plan_role === 'fallow') return t('pages.bed.history.timeline.fallow');
      const name = (planting.family_key ? marks.get(planting.family_key)?.name : null) ?? planting.family_name ?? '?';
      return planting.plan_role === 'green_manure' ? `${name} (${t('pages.bed.history.timeline.greenManure')})` : name;
    })
    .join(', ');
}

/** Keyed by site: a change of the address starts a fresh view, nothing of the old site stays on screen. */
export default function RotationMatrixPage() {
  const { key = '' } = useParams<{ key: string }>();
  return <RotationMatrixView key={key} siteKey={key} />;
}

function RotationMatrixView({ siteKey: key }: { siteKey: string }) {
  const { t } = useTranslation();
  const { canEdit } = useTenantPermissions();
  const { offerUndo } = useUndoSnackbar();
  const { state, reload, loadMore } = useRotationMatrix(key);
  const [backfill, setBackfill] = useState<{ bedKey: string; year: number } | null>(null);
  const thisYear = new Date().getFullYear();

  const onSaved = useCallback(
    (result: BackfillResult) => {
      const bedKey = backfill?.bedKey;
      setBackfill(null);
      reload();
      if (bedKey) {
        offerUndo({
          message: t('pages.bed.history.backfill.saved', { year: result.year }),
          undo: () => cancelBackfill(bedKey, result.care_event_key),
          onUndone: reload,
        });
      }
    },
    [backfill, offerUndo, reload, t],
  );

  const title = t('pages.rotationMatrix.title');
  const back = (
    <Button component={RouterLink} to={`/standorte/sites/${key}`} variant="text" sx={{ minHeight: 44 }} data-testid="matrix-back-link">
      {t('pages.rotationMatrix.backToSite')}
    </Button>
  );

  if (state.status === 'loading') return <LoadingSkeleton variant="table" />;
  if (state.status === 'error') return <ErrorDisplay error={state.message} onRetry={reload} />;

  const { matrix, marks } = state;
  const legend = [...marks.values()];

  return (
    <Box data-testid="rotation-matrix-page" sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
      <PageTitle title={title} action={back} />
      <Typography variant="body2" color="text.secondary">
        {t('pages.rotationMatrix.description')}
      </Typography>
      {canEdit && (
        <Typography variant="body2" color="text.secondary" data-testid="matrix-edit-hint">
          {t('pages.rotationMatrix.editHint')}
        </Typography>
      )}

      {matrix.beds.length === 0 ? (
        <Alert severity="info" data-testid="matrix-empty">
          {t('pages.rotationMatrix.empty')}
        </Alert>
      ) : (
        <TableContainer
          tabIndex={0}
          role="region"
          aria-label={t('pages.rotationMatrix.regionLabel')}
          data-testid="matrix-scroll"
          sx={{
            // The table scrolls inside its container, never the page (#2764): the container is the containing block of
            // the visually hidden texts in the cells, so none of them can reach past it into the page.
            position: 'relative',
            maxWidth: '100%',
            maxHeight: '70vh',
            border: 1,
            borderColor: 'divider',
            borderRadius: 1,
            '&:focus-visible': { outline: 2, outlineStyle: 'solid', outlineColor: 'primary.main' },
          }}
        >
          <Table stickyHeader size="small" data-testid="rotation-matrix-table" sx={{ minWidth: BED_COLUMN_WIDTH + matrix.columns.length * MIN_CELL_WIDTH }}>
            <caption style={visuallyHidden}>
              {t('pages.rotationMatrix.caption')}
            </caption>
            <TableHead>
              <TableRow>
                <TableCell
                  component="th"
                  scope="col"
                  sx={{ position: 'sticky', left: 0, zIndex: 4, minWidth: BED_COLUMN_WIDTH, bgcolor: 'background.paper' }}
                >
                  {t('pages.rotationMatrix.bedColumn')}
                </TableCell>
                {matrix.columns.map((year) => (
                  <TableCell key={year} component="th" scope="col" align="center" sx={{ minWidth: MIN_CELL_WIDTH }}>
                    {year}
                  </TableCell>
                ))}
              </TableRow>
            </TableHead>
            <TableBody>
              {matrix.beds.map((bed) => (
                <TableRow key={bed.location_key} data-testid={`matrix-row-${bed.location_key}`}>
                  <TableCell
                    component="th"
                    scope="row"
                    sx={{ position: 'sticky', left: 0, zIndex: 1, bgcolor: 'background.paper', verticalAlign: 'top' }}
                  >
                    <Link
                      component={RouterLink}
                      to={`/standorte/locations/${bed.location_key}`}
                      sx={{ minHeight: 44, display: 'inline-flex', alignItems: 'center', fontWeight: 600 }}
                      data-testid={`matrix-bed-link-${bed.location_key}`}
                    >
                      {bed.name}
                    </Link>
                    {!bed.rotation_applicable && (
                      <Typography
                        variant="caption"
                        color="text.secondary"
                        sx={{ display: 'block' }}
                        data-testid={`matrix-off-${bed.location_key}`}
                      >
                        {t(`pages.rotationMatrix.off.${bed.not_applicable_reason?.split('.').pop() ?? 'unknown'}`, {
                          defaultValue: t('pages.rotationMatrix.off.unknown'),
                        })}
                      </Typography>
                    )}
                  </TableCell>
                  {bed.cells.map((cell) => {
                    const interactive = canEdit && cell.year < thisYear;
                    const content =
                      cell.plantings.length === 0 ? (
                        <Typography variant="caption" color="text.secondary">
                          <span aria-hidden="true">{'–'}</span>
                          <Box component="span" sx={visuallyHidden}>
                            {t('pages.rotationMatrix.cellEmpty')}
                          </Box>
                        </Typography>
                      ) : (
                        <Box component="ul" sx={{ m: 0, p: 0, display: 'flex', flexDirection: 'column', gap: 0.5 }}>
                          {cell.plantings.map((planting, index) => (
                            <PlantingEntry
                              key={`${planting.source}-${planting.care_event_key ?? planting.species_key ?? planting.family_key ?? index}-${index}`}
                              planting={planting}
                              mark={planting.family_key ? marks.get(planting.family_key) : undefined}
                              t={t}
                            />
                          ))}
                        </Box>
                      );
                    return (
                      <TableCell
                        key={cell.year}
                        sx={{ p: 0, verticalAlign: 'top', opacity: bed.rotation_applicable ? 1 : 0.75 }}
                        data-testid={`matrix-cell-${bed.location_key}-${cell.year}`}
                      >
                        {interactive ? (
                          <ButtonBase
                            onClick={() => setBackfill({ bedKey: bed.location_key, year: cell.year })}
                            aria-label={t('pages.rotationMatrix.cellAction', {
                              bed: bed.name,
                              year: cell.year,
                              content: summarize(cell, marks, t),
                            })}
                            sx={{
                              width: '100%',
                              minHeight: 48,
                              p: 1,
                              display: 'flex',
                              justifyContent: 'flex-start',
                              alignItems: 'flex-start',
                              '&:focus-visible': { outline: 2, outlineStyle: 'solid', outlineColor: 'primary.main', outlineOffset: -2 },
                              '&:hover': { bgcolor: 'action.hover' },
                            }}
                            data-testid={`matrix-cell-button-${bed.location_key}-${cell.year}`}
                          >
                            {content}
                          </ButtonBase>
                        ) : (
                          <Box sx={{ p: 1, minHeight: 48 }}>{content}</Box>
                        )}
                      </TableCell>
                    );
                  })}
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      )}

      {legend.length > 0 && (
        <Box component="section" aria-labelledby="matrix-legend-title" data-testid="matrix-legend">
          <Typography id="matrix-legend-title" variant="subtitle2" component="h2" sx={{ mb: 0.5 }}>
            {t('pages.rotationMatrix.legend')}
          </Typography>
          <Box component="ul" sx={{ m: 0, p: 0, display: 'flex', flexWrap: 'wrap', gap: 1.5 }}>
            {legend.map((mark) => (
              <Box component="li" key={mark.familyKey} sx={{ listStyle: 'none', display: 'inline-flex', alignItems: 'center', gap: 0.75 }}>
                <Swatch mark={mark} />
                <Typography variant="body2">
                  <strong>{mark.code}</strong> {mark.name}
                </Typography>
              </Box>
            ))}
          </Box>
        </Box>
      )}

      <Typography variant="caption" color="text.secondary" data-testid="matrix-count">
        {t('pages.rotationMatrix.count', { shown: matrix.beds.length, total: matrix.total })}
      </Typography>
      {matrix.truncated && (
        <Alert severity="info" data-testid="matrix-truncated">
          {t('pages.rotationMatrix.truncated', { count: matrix.total })}
        </Alert>
      )}
      {state.failure !== null && (
        <Alert severity="error" data-testid="matrix-more-failed">
          {t(state.failure === 'refresh' ? 'pages.rotationMatrix.refreshFailed' : 'pages.rotationMatrix.moreFailed')}
        </Alert>
      )}
      {hasMoreBeds(matrix) && (
        <Box>
          <Button
            variant="outlined"
            onClick={loadMore}
            disabled={state.busy}
            sx={{ minHeight: 44 }}
            data-testid="matrix-more"
          >
            {t('pages.rotationMatrix.more')}
          </Button>
        </Box>
      )}

      {backfill !== null && (
        <BackfillDialog
          bedKey={backfill.bedKey}
          initialYear={backfill.year}
          onClose={() => setBackfill(null)}
          onSaved={onSaved}
        />
      )}
    </Box>
  );
}
