import { useCallback, useState } from 'react';
import type { ReactElement } from 'react';
import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import Grid from '@mui/material/Grid';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import Stack from '@mui/material/Stack';
import TextField from '@mui/material/TextField';
import Button from '@mui/material/Button';
import CircularProgress from '@mui/material/CircularProgress';
import Typography from '@mui/material/Typography';
import Chip from '@mui/material/Chip';
import type { ChipProps } from '@mui/material/Chip';
import Alert from '@mui/material/Alert';
import Divider from '@mui/material/Divider';
import AccountTreeIcon from '@mui/icons-material/AccountTree';
import CompareArrowsIcon from '@mui/icons-material/CompareArrows';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import HighlightOffIcon from '@mui/icons-material/HighlightOff';
import HelpTooltip from '@/components/common/HelpTooltip';
import { useApiError } from '@/hooks/useApiError';
import * as api from '@/api/endpoints/propagation';
import type {
  DescendantsResponse,
  GraftCompatibilityLevel,
  GraftCompatibilityResponse,
  LineageResponse,
} from '@/api/types';

const levelColor: Record<GraftCompatibilityLevel, ChipProps['color']> = {
  compatible: 'success',
  possibly_compatible: 'warning',
  incompatible: 'error',
};

const alertSeverity: Record<GraftCompatibilityLevel, 'success' | 'warning' | 'error'> = {
  compatible: 'success',
  possibly_compatible: 'warning',
  incompatible: 'error',
};

/**
 * REQ-017 lineage explorer: trace a plant's ancestor chains / descendants and
 * run the taxonomy-based graft-compatibility check between two plants.
 */
export default function LineagePanel(): ReactElement {
  const { t } = useTranslation();
  const { handleError } = useApiError();

  const [plantKey, setPlantKey] = useState('');
  const [lineage, setLineage] = useState<LineageResponse | null>(null);
  const [descendants, setDescendants] = useState<DescendantsResponse | null>(null);
  const [lineageLoading, setLineageLoading] = useState(false);

  const [scionKey, setScionKey] = useState('');
  const [rootstockKey, setRootstockKey] = useState('');
  const [graft, setGraft] = useState<GraftCompatibilityResponse | null>(null);
  const [graftLoading, setGraftLoading] = useState(false);

  const handleTrace = useCallback(async () => {
    const key = plantKey.trim();
    if (!key) return;
    setLineageLoading(true);
    try {
      const [lin, desc] = await Promise.all([
        api.getLineage(key),
        api.getDescendants(key),
      ]);
      setLineage(lin);
      setDescendants(desc);
    } catch (error) {
      handleError(error);
    } finally {
      setLineageLoading(false);
    }
  }, [plantKey, handleError]);

  const handleGraftCheck = useCallback(async () => {
    const scion = scionKey.trim();
    const rootstock = rootstockKey.trim();
    if (!scion || !rootstock) return;
    setGraftLoading(true);
    try {
      setGraft(await api.checkGraftCompatibility(scion, rootstock));
    } catch (error) {
      handleError(error);
    } finally {
      setGraftLoading(false);
    }
  }, [scionKey, rootstockKey, handleError]);

  return (
    <Grid container spacing={3}>
      {/* Ancestry / descendants */}
      <Grid size={{ xs: 12, md: 6 }}>
        <Card variant="outlined">
          <CardContent>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5, mb: 0.5 }}>
              <AccountTreeIcon fontSize="small" color="action" />
              <Typography variant="h6" component="h2">
                {t('pages.propagation.lineage.title')}
              </Typography>
              <HelpTooltip term="abstammung" iconOnly />
            </Box>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
              {t('pages.propagation.lineage.intro')}
            </Typography>
            <Stack
              direction={{ xs: 'column', sm: 'row' }}
              spacing={1}
              sx={{ mb: 0.5, alignItems: { xs: 'stretch', sm: 'flex-start' } }}
            >
              <TextField
                fullWidth
                size="small"
                label={t('pages.propagation.lineage.plantKey')}
                helperText={t('pages.propagation.lineage.plantKeyHelper')}
                value={plantKey}
                onChange={(e) => setPlantKey(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && plantKey.trim() && !lineageLoading) {
                    e.preventDefault();
                    void handleTrace();
                  }
                }}
                slotProps={{ htmlInput: { 'data-testid': 'lineage-plant-key' } }}
              />
              <Button
                variant="contained"
                onClick={handleTrace}
                disabled={!plantKey.trim() || lineageLoading}
                startIcon={lineageLoading ? <CircularProgress size={16} color="inherit" /> : undefined}
                data-testid="trace-button"
                sx={{ minHeight: 48, flexShrink: 0 }}
              >
                {t('pages.propagation.lineage.trace')}
              </Button>
            </Stack>

            {!lineage && (
              <Typography variant="body2" color="text.secondary" sx={{ mt: 2 }}>
                {t('pages.propagation.lineage.hint')}
              </Typography>
            )}

            {lineage && (
              <Box data-testid="lineage-result" sx={{ mt: 2 }}>
                <Typography variant="subtitle2">
                  {t('pages.propagation.lineage.ancestors')}
                </Typography>
                {lineage.ancestors.length === 0 ? (
                  <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                    {t('pages.propagation.lineage.noAncestors')}
                  </Typography>
                ) : (
                  <Stack direction="row" sx={{ flexWrap: 'wrap', gap: 1, mb: 1 }}>
                    {lineage.ancestors.map((a) => (
                      <Chip
                        key={a.key}
                        size="small"
                        label={a.plant_name || a.instance_id || a.key}
                      />
                    ))}
                  </Stack>
                )}
                <Divider sx={{ my: 1.5 }} />
                <Typography variant="subtitle2">
                  {t('pages.propagation.lineage.descendants')}
                </Typography>
                {descendants && descendants.descendants.length === 0 ? (
                  <Typography variant="body2" color="text.secondary">
                    {t('pages.propagation.lineage.noDescendants')}
                  </Typography>
                ) : (
                  <Stack direction="row" sx={{ flexWrap: 'wrap', gap: 1 }}>
                    {descendants?.descendants.map((d) => (
                      <Chip
                        key={d.key}
                        size="small"
                        variant="outlined"
                        label={d.plant_name || d.instance_id || d.key}
                      />
                    ))}
                  </Stack>
                )}
              </Box>
            )}
          </CardContent>
        </Card>
      </Grid>

      {/* Graft compatibility */}
      <Grid size={{ xs: 12, md: 6 }}>
        <Card variant="outlined">
          <CardContent>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5, mb: 0.5 }}>
              <CompareArrowsIcon fontSize="small" color="action" />
              <Typography variant="h6" component="h2">
                {t('pages.propagation.graft.title')}
              </Typography>
              <HelpTooltip term="veredelung" iconOnly />
            </Box>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
              {t('pages.propagation.graft.intro')}
            </Typography>
            <Stack spacing={1.5} sx={{ mb: 0.5 }}>
              <TextField
                fullWidth
                size="small"
                label={t('pages.propagation.graft.scionKey')}
                value={scionKey}
                onChange={(e) => setScionKey(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && scionKey.trim() && rootstockKey.trim() && !graftLoading) {
                    e.preventDefault();
                    void handleGraftCheck();
                  }
                }}
                slotProps={{ htmlInput: { 'data-testid': 'graft-scion-key' } }}
              />
              <TextField
                fullWidth
                size="small"
                label={t('pages.propagation.graft.rootstockKey')}
                value={rootstockKey}
                onChange={(e) => setRootstockKey(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && scionKey.trim() && rootstockKey.trim() && !graftLoading) {
                    e.preventDefault();
                    void handleGraftCheck();
                  }
                }}
                slotProps={{ htmlInput: { 'data-testid': 'graft-rootstock-key' } }}
              />
              <Button
                variant="contained"
                onClick={handleGraftCheck}
                disabled={!scionKey.trim() || !rootstockKey.trim() || graftLoading}
                startIcon={graftLoading ? <CircularProgress size={16} color="inherit" /> : undefined}
                data-testid="graft-check-button"
                sx={{ minHeight: 48, alignSelf: 'flex-start' }}
              >
                {t('pages.propagation.graft.check')}
              </Button>
            </Stack>

            {!graft && (
              <Typography variant="body2" color="text.secondary" sx={{ mt: 2 }}>
                {t('pages.propagation.graft.hint')}
              </Typography>
            )}

            {graft && (
              <Box data-testid="graft-result" sx={{ mt: 2 }}>
                <Chip
                  label={t(`enums.graftCompatibilityLevel.${graft.level}`)}
                  color={levelColor[graft.level]}
                  sx={{ mb: 1 }}
                />
                <Alert severity={alertSeverity[graft.level]} sx={{ mb: 1.5 }}>
                  {graft.message}
                </Alert>
                <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                  {t('pages.propagation.graft.speciesLine', {
                    scion: graft.scion_species_key,
                    rootstock: graft.rootstock_species_key,
                  })}
                </Typography>
                <Stack direction="row" sx={{ flexWrap: 'wrap', gap: 1 }}>
                  <Chip
                    size="small"
                    variant="outlined"
                    icon={
                      graft.same_genus ? (
                        <CheckCircleIcon />
                      ) : (
                        <HighlightOffIcon />
                      )
                    }
                    color={graft.same_genus ? 'success' : 'default'}
                    label={
                      graft.same_genus
                        ? t('pages.propagation.graft.sameGenus')
                        : t('pages.propagation.graft.differentGenus')
                    }
                  />
                  <Chip
                    size="small"
                    variant="outlined"
                    icon={
                      graft.same_family ? (
                        <CheckCircleIcon />
                      ) : (
                        <HighlightOffIcon />
                      )
                    }
                    color={graft.same_family ? 'success' : 'default'}
                    label={
                      graft.same_family
                        ? t('pages.propagation.graft.sameFamily')
                        : t('pages.propagation.graft.differentFamily')
                    }
                  />
                  <HelpTooltip term="gattung_familie" iconOnly />
                </Stack>
              </Box>
            )}
          </CardContent>
        </Card>
      </Grid>
    </Grid>
  );
}
