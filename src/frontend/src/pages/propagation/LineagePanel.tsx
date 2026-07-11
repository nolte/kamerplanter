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
import Typography from '@mui/material/Typography';
import Chip from '@mui/material/Chip';
import type { ChipProps } from '@mui/material/Chip';
import Alert from '@mui/material/Alert';
import Divider from '@mui/material/Divider';
import AccountTreeIcon from '@mui/icons-material/AccountTree';
import CompareArrowsIcon from '@mui/icons-material/CompareArrows';
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
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5, mb: 1.5 }}>
              <AccountTreeIcon fontSize="small" color="action" />
              <Typography variant="h6" component="h2">
                {t('pages.propagation.lineage.title')}
              </Typography>
            </Box>
            <Stack direction={{ xs: 'column', sm: 'row' }} spacing={1} sx={{ mb: 2 }}>
              <TextField
                fullWidth
                size="small"
                label={t('pages.propagation.lineage.plantKey')}
                value={plantKey}
                onChange={(e) => setPlantKey(e.target.value)}
                slotProps={{ htmlInput: { 'data-testid': 'lineage-plant-key' } }}
              />
              <Button
                variant="contained"
                onClick={handleTrace}
                disabled={!plantKey.trim() || lineageLoading}
                data-testid="trace-button"
              >
                {t('pages.propagation.lineage.trace')}
              </Button>
            </Stack>

            {lineage && (
              <Box data-testid="lineage-result">
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
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5, mb: 1.5 }}>
              <CompareArrowsIcon fontSize="small" color="action" />
              <Typography variant="h6" component="h2">
                {t('pages.propagation.graft.title')}
              </Typography>
            </Box>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
              {t('pages.propagation.graft.intro')}
            </Typography>
            <Stack spacing={1} sx={{ mb: 2 }}>
              <TextField
                fullWidth
                size="small"
                label={t('pages.propagation.graft.scionKey')}
                value={scionKey}
                onChange={(e) => setScionKey(e.target.value)}
                slotProps={{ htmlInput: { 'data-testid': 'graft-scion-key' } }}
              />
              <TextField
                fullWidth
                size="small"
                label={t('pages.propagation.graft.rootstockKey')}
                value={rootstockKey}
                onChange={(e) => setRootstockKey(e.target.value)}
                slotProps={{ htmlInput: { 'data-testid': 'graft-rootstock-key' } }}
              />
              <Button
                variant="contained"
                onClick={handleGraftCheck}
                disabled={!scionKey.trim() || !rootstockKey.trim() || graftLoading}
                data-testid="graft-check-button"
              >
                {t('pages.propagation.graft.check')}
              </Button>
            </Stack>

            {graft && (
              <Box data-testid="graft-result">
                <Chip
                  label={t(`enums.graftCompatibilityLevel.${graft.level}`)}
                  color={levelColor[graft.level]}
                  sx={{ mb: 1 }}
                />
                <Alert severity={graft.compatible ? 'success' : 'warning'}>
                  {graft.message}
                </Alert>
              </Box>
            )}
          </CardContent>
        </Card>
      </Grid>
    </Grid>
  );
}
