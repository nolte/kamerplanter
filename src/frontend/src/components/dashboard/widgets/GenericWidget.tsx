import { useTranslation } from 'react-i18next';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import Skeleton from '@mui/material/Skeleton';
import HelpTooltip from '@/components/common/HelpTooltip';
import { useWidgetPayload } from '@/components/dashboard/DashboardDataContext';
import type { WidgetComponentProps } from '@/components/dashboard/widgetRegistry';

/**
 * Widgets whose title is itself a domain jargon term (UI-NFR-011) get the
 * shared glossary tooltip next to the heading. Only map keys with an existing
 * `glossary.<term>` entry — see `i18n/locales/{de,en}/translation.json`.
 */
const WIDGET_GLOSSARY_TERM: Partial<Record<string, string>> = {
  vpd_gauge: 'vpd',
  ipm_alerts: 'ipm',
};

/**
 * REQ-045 — generic widget shell for widgets whose rich REQ-009 view is not yet
 * implemented. Renders the catalog label + description, any numeric slices from
 * the aggregated payload, and mandatory loading/empty states (REQ-009 DoD).
 */
export default function GenericWidget({ widgetKey }: WidgetComponentProps) {
  const { t } = useTranslation();
  const { payload, loading } = useWidgetPayload(widgetKey);
  const glossaryTerm = WIDGET_GLOSSARY_TERM[widgetKey];

  const numbers =
    payload && typeof payload === 'object'
      ? Object.entries(payload as Record<string, unknown>).filter(([, v]) => typeof v === 'number')
      : [];

  return (
    <Card sx={{ height: '100%' }} data-testid={`widget-${widgetKey}`}>
      <CardContent>
        <Typography
          variant="subtitle1"
          component="h3"
          gutterBottom
          sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}
        >
          {t(`dashboard.widgets.${widgetKey}.label`)}
          {glossaryTerm && <HelpTooltip term={glossaryTerm} iconOnly />}
        </Typography>
        {loading ? (
          <Skeleton variant="rounded" height={48} />
        ) : numbers.length > 0 ? (
          <Box sx={{ display: 'flex', gap: 3, flexWrap: 'wrap' }}>
            {numbers.map(([k, v]) => (
              <Box key={k}>
                <Typography variant="h4" component="p">
                  {String(v)}
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  {t(`dashboard.widgets.${widgetKey}.metrics.${k}`, {
                    defaultValue: k.replace(/_/g, ' '),
                  })}
                </Typography>
              </Box>
            ))}
          </Box>
        ) : (
          <Typography variant="body2" color="text.secondary">
            {t(`dashboard.widgets.${widgetKey}.description`)}
          </Typography>
        )}
      </CardContent>
    </Card>
  );
}
