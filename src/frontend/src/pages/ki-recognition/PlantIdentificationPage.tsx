import { useCallback, useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Alert from '@mui/material/Alert';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import Typography from '@mui/material/Typography';
import List from '@mui/material/List';
import ListItem from '@mui/material/ListItem';
import ListItemText from '@mui/material/ListItemText';
import Divider from '@mui/material/Divider';
import Chip from '@mui/material/Chip';
import PhotoCameraIcon from '@mui/icons-material/PhotoCamera';
import LocalFloristIcon from '@mui/icons-material/LocalFlorist';
import PageTitle from '@/components/layout/PageTitle';
import EmptyState from '@/components/common/EmptyState';
import LoadingSkeleton from '@/components/common/LoadingSkeleton';
import PlantIdentificationDialog, {
  type IdentifiedSpecies,
} from '@/components/identification/PlantIdentificationDialog';
import PlantInstanceCreateDialog from '@/pages/pflanzen/PlantInstanceCreateDialog';
import { LOCAL_EMBEDDING_ADAPTER_KEY, linkPlantInstance } from '@/api/endpoints/identification';
import { useNotification } from '@/hooks/useNotification';
import { useAppDispatch, useAppSelector } from '@/store/hooks';
import {
  fetchIdentificationHistory,
  fetchIdentificationStatus,
} from '@/store/slices/identificationSlice';

/** REQ-029 / REQ-029-A — AI plant identification page (Phase 1, Pl@ntNet-first).
 *
 * Usability improvements over v1:
 * - Page intro text moved above the feature-gate card (UI-NFR-008 R-038)
 * - History section has intro text explaining what the list shows (UI-NFR-008 R-038)
 * - History items show date + top-result name + "selected" chip — previously the
 *   chip only appeared for selected items; now a "no result" caption is shown for
 *   failed identifications so the row is never empty
 * - History list items use Divider between entries for visual separation on dense lists
 * - Start button has sufficient touch target height (UI-NFR-001 R-011)
 */
export default function PlantIdentificationPage() {
  const { t } = useTranslation();
  const dispatch = useAppDispatch();
  const navigate = useNavigate();
  const notification = useNotification();

  const status = useAppSelector((s) => s.identification.status);
  const statusLoading = useAppSelector((s) => s.identification.statusLoading);
  const history = useAppSelector((s) => s.identification.history);
  const historyLoading = useAppSelector((s) => s.identification.historyLoading);

  const [dialogOpen, setDialogOpen] = useState(false);
  const [resolvedSpecies, setResolvedSpecies] = useState<IdentifiedSpecies | null>(null);

  useEffect(() => {
    dispatch(fetchIdentificationStatus());
    dispatch(fetchIdentificationHistory(20));
  }, [dispatch]);

  const available = status?.available ?? false;
  // DINOv2 self-hosted mode is active when the resolved primary/active adapter
  // is the local-embedding path — only then can a photo be reused as a
  // few-shot recognition reference (issue #447).
  const referenceModeAvailable = status?.active_adapter === LOCAL_EMBEDDING_ADAPTER_KEY;

  const handleSpeciesResolved = useCallback((result: IdentifiedSpecies) => {
    // Hand the identified/created species to the plant-creation flow.
    setResolvedSpecies(result);
  }, []);

  const handlePlantCreated = useCallback(
    async (key: string) => {
      const requestKey = resolvedSpecies?.requestKey;
      setResolvedSpecies(null);
      // Persist the link from the identification record to the created instance
      // (#630). Best-effort: the plant is already created, so a failed link must
      // not block the flow — we warn and still refresh history + navigate. When
      // it succeeds the history surfaces a link to the instance that survives a
      // reload.
      if (requestKey) {
        try {
          await linkPlantInstance(requestKey, key);
        } catch {
          notification.warning(t('pages.plantIdentification.historyLinkFailed'));
        }
      }
      dispatch(fetchIdentificationHistory(20));
      navigate(`/pflanzen/plant-instances/${key}`);
    },
    [dispatch, navigate, notification, t, resolvedSpecies],
  );

  return (
    <Box sx={{ p: { xs: 2, sm: 3 } }} data-testid="plant-identification-page">
      <PageTitle
        title={t('pages.plantIdentification.title')}
        action={
          available ? (
            <Button
              variant="contained"
              startIcon={<PhotoCameraIcon />}
              onClick={() => setDialogOpen(true)}
              data-testid="open-identification-dialog"
              sx={{ minHeight: { xs: 48, sm: 40 } }}
            >
              {t('pages.plantIdentification.startButton')}
            </Button>
          ) : undefined
        }
      />

      {/* Page intro — explains what this feature does before any gating (UI-NFR-008 R-038) */}
      <Typography variant="body1" color="text.secondary" sx={{ mb: 3, maxWidth: '72ch' }}>
        {t('pages.plantIdentification.pageIntro')}
      </Typography>

      {statusLoading ? (
        <LoadingSkeleton variant="card" />
      ) : !available ? (
        <Alert severity="info" data-testid="page-feature-unavailable">
          {t('pages.plantIdentification.notConfigured')}
        </Alert>
      ) : (
        <Card variant="outlined">
          <CardContent>
            <Typography variant="h6" gutterBottom>
              {t('pages.plantIdentification.historyTitle')}
            </Typography>

            {/* History section intro — explains what the list represents (UI-NFR-008 R-038) */}
            <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
              {t('pages.plantIdentification.historyIntro')}
            </Typography>

            {historyLoading ? (
              <LoadingSkeleton variant="card" />
            ) : history.length === 0 ? (
              <EmptyState message={t('pages.plantIdentification.historyEmpty')} />
            ) : (
              <List disablePadding data-testid="identification-history-list">
                {history.map((entry, index) => {
                  const selected =
                    entry.selected_result_rank != null
                      ? entry.results.find((r) => r.rank === entry.selected_result_rank)
                      : undefined;
                  const top = entry.results[0];
                  const shown = selected ?? top;
                  const isLast = index === history.length - 1;
                  const instanceKey = entry.plant_instance_key;
                  // Once a plant instance was created from this result (#630), the
                  // link to it is the most relevant status — show a clickable chip
                  // navigating to the instance detail page. Otherwise keep the
                  // existing "selected" indicator.
                  const secondaryAction = instanceKey ? (
                    <Chip
                      icon={<LocalFloristIcon />}
                      label={t('pages.plantIdentification.historyOpenInstance')}
                      size="small"
                      color="primary"
                      variant="filled"
                      clickable
                      onClick={() => navigate(`/pflanzen/plant-instances/${instanceKey}`)}
                      aria-label={t('pages.plantIdentification.historyOpenInstance')}
                      data-testid="identification-history-instance-link"
                      sx={{ height: { xs: 40, sm: 32 } }}
                    />
                  ) : selected ? (
                    <Chip
                      label={t('pages.plantIdentification.historySelected')}
                      size="small"
                      color="success"
                      variant="outlined"
                    />
                  ) : undefined;
                  return (
                    <Box key={entry.key ?? `${entry.adapter_key}-${entry.created_at}`}>
                      <ListItem
                        disableGutters
                        data-testid="identification-history-item"
                        secondaryAction={secondaryAction}
                        sx={{ pr: secondaryAction ? 16 : 0 }}
                      >
                        <ListItemText
                          primary={
                            shown ? (
                              <Typography sx={{ fontStyle: 'italic' }}>
                                {shown.scientific_name}
                              </Typography>
                            ) : (
                              <Typography color="text.secondary">
                                {t('pages.plantIdentification.historyNoResult')}
                              </Typography>
                            )
                          }
                          secondary={
                            <>
                              {entry.created_at
                                ? new Date(entry.created_at).toLocaleString()
                                : null}
                              {instanceKey && (
                                <Typography
                                  component="span"
                                  variant="caption"
                                  color="success.main"
                                  sx={{ display: 'block' }}
                                  data-testid="identification-history-instance-created"
                                >
                                  {t('pages.plantIdentification.historyInstanceCreated')}
                                </Typography>
                              )}
                            </>
                          }
                        />
                      </ListItem>
                      {!isLast && <Divider />}
                    </Box>
                  );
                })}
              </List>
            )}
          </CardContent>
        </Card>
      )}

      <PlantIdentificationDialog
        open={dialogOpen}
        onClose={() => setDialogOpen(false)}
        onSpeciesResolved={handleSpeciesResolved}
        onManualSearch={() => {
          setDialogOpen(false);
          navigate('/stammdaten/species');
        }}
      />

      {/* Create-plant step after a candidate was selected/created */}
      <PlantInstanceCreateDialog
        open={resolvedSpecies != null}
        onClose={() => setResolvedSpecies(null)}
        onCreated={handlePlantCreated}
        initialSpeciesKey={resolvedSpecies?.speciesKey}
        identificationPhoto={resolvedSpecies?.photo}
        allowReferenceContribution={referenceModeAvailable}
      />
    </Box>
  );
}
