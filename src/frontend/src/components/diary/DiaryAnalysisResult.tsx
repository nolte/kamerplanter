import { useTranslation } from 'react-i18next';
import Accordion from '@mui/material/Accordion';
import AccordionDetails from '@mui/material/AccordionDetails';
import AccordionSummary from '@mui/material/AccordionSummary';
import Alert from '@mui/material/Alert';
import Box from '@mui/material/Box';
import Chip from '@mui/material/Chip';
import Divider from '@mui/material/Divider';
import List from '@mui/material/List';
import ListItem from '@mui/material/ListItem';
import ListItemIcon from '@mui/material/ListItemIcon';
import ListItemText from '@mui/material/ListItemText';
import Paper from '@mui/material/Paper';
import Typography from '@mui/material/Typography';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import CheckIcon from '@mui/icons-material/Check';
import { formatDateTime } from '@/utils/formatting';
import type { DiaryAnalysis } from '@/api/types';
import { confidenceBand, confidencePercent, confidenceSeverity } from './confidence';

interface DiaryAnalysisResultProps {
  analysis: DiaryAnalysis;
  /** All photos of the entry, to say how many of them were actually evaluated. */
  photoRefs?: string[];
}

/**
 * REQ-050 §2.5.3 — the analysis result, in the order the specification fixes:
 * summary first, then the expandable finding list, the recommended actions, the
 * provenance, and the disclaimer.
 *
 * Two of those are hard requirements rather than layout taste:
 *
 * - **The disclaimer is always visible** (AK-20, §2.4). It sits outside every
 *   collapsible element, as its own `Alert`. Folding it into the accordion
 *   would satisfy "the text exists" while defeating why it exists.
 * - **Confidence is a number *and* a wording** (AK-30). The percentage never
 *   appears on its own; {@link confidenceBand} supplies the words next to it.
 */
export default function DiaryAnalysisResult({
  analysis,
  photoRefs,
}: DiaryAnalysisResultProps) {
  const { t } = useTranslation();

  const analysedCount = analysis.analyzed_photo_ids.length;
  const totalPhotos = photoRefs?.length ?? analysedCount;

  return (
    <Paper
      variant="outlined"
      sx={{ p: { xs: 1.5, sm: 2 }, bgcolor: 'action.hover' }}
      data-testid="diary-analysis-result"
    >
      <Typography component="h3" variant="subtitle2" sx={{ fontWeight: 600, mb: 0.5 }}>
        {t('pages.plantDiary.analysis.resultTitle')}
      </Typography>

      {/* 1. Summary — first, always, unfolded. */}
      <Typography variant="body1" sx={{ mb: 2 }} data-testid="diary-analysis-summary">
        {analysis.summary}
      </Typography>

      {/* 2. Findings — collapsible, because a long rationale per finding would
             bury the summary and the recommended actions below it. */}
      {analysis.findings.length > 0 && (
        <Accordion
          disableGutters
          elevation={0}
          sx={{ bgcolor: 'transparent', '&::before': { display: 'none' } }}
          data-testid="diary-analysis-findings"
        >
          <AccordionSummary
            expandIcon={<ExpandMoreIcon />}
            aria-controls="diary-analysis-findings-content"
            id="diary-analysis-findings-header"
            sx={{ px: 0, minHeight: 44 }}
            data-testid="diary-analysis-findings-toggle"
          >
            <Typography variant="subtitle2">
              {t('pages.plantDiary.analysis.findings', { count: analysis.findings.length })}
            </Typography>
          </AccordionSummary>
          <AccordionDetails id="diary-analysis-findings-content" sx={{ px: 0, pt: 0 }}>
            {analysis.findings.map((finding, index) => {
              const band = confidenceBand(finding.confidence);
              const percent = confidencePercent(finding.confidence);
              const wording = t(`enums.diaryConfidence.${band}`);
              return (
                <Box
                  key={`${finding.label}-${index}`}
                  sx={{ mb: 2, '&:last-of-type': { mb: 0 } }}
                  data-testid="diary-analysis-finding"
                >
                  <Box
                    sx={{
                      display: 'flex',
                      flexWrap: 'wrap',
                      alignItems: 'center',
                      gap: 1,
                      mb: 0.5,
                    }}
                  >
                    <Typography variant="subtitle2" component="h4">
                      {finding.label}
                    </Typography>
                    {/* AK-30 — number and wording in one label; neither alone. */}
                    <Chip
                      size="small"
                      color={confidenceSeverity(band)}
                      variant="outlined"
                      label={t('pages.plantDiary.analysis.confidenceLabel', {
                        percent,
                        wording,
                      })}
                      data-testid="diary-analysis-confidence"
                      data-confidence-percent={percent}
                      data-confidence-band={band}
                    />
                  </Box>
                  <Typography variant="body2" color="text.secondary">
                    {finding.rationale}
                  </Typography>
                </Box>
              );
            })}
          </AccordionDetails>
        </Accordion>
      )}

      {/* 3. Recommended actions. */}
      {analysis.recommended_actions.length > 0 && (
        <Box sx={{ mt: 1 }} data-testid="diary-analysis-actions">
          <Typography variant="subtitle2" component="h4" sx={{ mb: 0.5 }}>
            {t('pages.plantDiary.analysis.recommendedActions')}
          </Typography>
          <List dense disablePadding>
            {analysis.recommended_actions.map((action, index) => (
              <ListItem key={`${action}-${index}`} disableGutters sx={{ py: 0.25 }}>
                <ListItemIcon sx={{ minWidth: 28 }}>
                  <CheckIcon fontSize="small" color="success" />
                </ListItemIcon>
                <ListItemText primary={action} />
              </ListItem>
            ))}
          </List>
        </Box>
      )}

      <Divider sx={{ my: 1.5 }} />

      {/* 4. Provenance — model, recipe version, time, evaluated photos. */}
      <Typography
        variant="caption"
        color="text.secondary"
        sx={{ display: 'block' }}
        data-testid="diary-analysis-provenance"
      >
        {t('pages.plantDiary.analysis.provenance', {
          model: analysis.model,
          recipe: analysis.recipe_version,
          time: formatDateTime(analysis.analyzed_at),
        })}
        {' · '}
        {t('pages.plantDiary.analysis.analyzedPhotos', {
          count: analysedCount,
          total: totalPhotos,
        })}
      </Typography>

      {/* 5. Disclaimer — AK-20: outside every collapsible element, no exception. */}
      <Alert
        severity="info"
        icon={false}
        sx={{ mt: 1.5 }}
        data-testid="diary-analysis-disclaimer"
      >
        {analysis.disclaimer || t('pages.plantDiary.analysis.disclaimerFallback')}
      </Alert>
    </Paper>
  );
}
