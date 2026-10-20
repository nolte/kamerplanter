/**
 * The quick choice of standard sizes in "add with dimensions" (REQ-053 GP-FR-045, WP 7.10): one button per
 * system template; a press fills shape, size, bed type and height. Its own lazy chunk, and it loads the
 * catalogue itself - the dialog makes no request when the choice never renders.
 */
import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Typography from '@mui/material/Typography';
import type { BedTemplate } from '../model/types';
import { standardSizeOf, standardSizeTemplates, type StandardSize } from './standardSizes';
import { templateName } from './templateName';
import { useBedTemplates } from './useBedTemplates';

const PREFIX = 'pages.gardenPlan.editor.templates.standard';

interface StandardSizesProps {
  onPick: (size: StandardSize, template: BedTemplate) => void;
}

export default function StandardSizes({ onPick }: StandardSizesProps) {
  const { t } = useTranslation();
  const catalogue = useBedTemplates(true);
  const standards = standardSizeTemplates(catalogue.templates);
  if (standards.length === 0) return null;
  return (
    <Box role="group" aria-label={t(`${PREFIX}.label`)} data-testid="garden-plan-add-standard-sizes">
      <Typography variant="caption" color="text.secondary" component="p" sx={{ mb: 0.5 }}>
        {t(`${PREFIX}.hint`)}
      </Typography>
      <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
        {standards.map((template) => {
          const size = standardSizeOf(template);
          if (!size) return null;
          return (
            <Button
              key={template.key}
              size="small"
              variant="outlined"
              onClick={() => onPick(size, template)}
              data-testid={`garden-plan-add-standard-${template.key}`}
              sx={{ minHeight: 44 }}
            >
              {templateName(t, template)}
            </Button>
          );
        })}
      </Box>
    </Box>
  );
}
