/**
 * The soil history (REQ-053 GP-FR-122): pH, EC and humus over time, one chart per parameter and in it one line per
 * measuring method; where the method changes a dashed mark says the values before and after are not comparable.
 * The server splits the series per method - nothing here merges or converts them (U-002/U-003). Every chart has its
 * table: always present for screen readers, shown on request for everybody else.
 *
 * Loaded as a `lazy()` chunk (it brings recharts), only once the bed has a value to show.
 */
import { useMemo, useState } from 'react';
import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import Chip from '@mui/material/Chip';
import FormControlLabel from '@mui/material/FormControlLabel';
import Paper from '@mui/material/Paper';
import Switch from '@mui/material/Switch';
import Table from '@mui/material/Table';
import TableBody from '@mui/material/TableBody';
import TableCell from '@mui/material/TableCell';
import TableContainer from '@mui/material/TableContainer';
import TableHead from '@mui/material/TableHead';
import TableRow from '@mui/material/TableRow';
import Typography from '@mui/material/Typography';
import { useTheme } from '@mui/material/styles';
import { visuallyHidden } from '@mui/utils';
import { CartesianGrid, Legend, Line, LineChart, ReferenceLine, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';
import { changeLabelPosition, parameterHistory, timeDomain, type ParameterHistory } from './soilAnalysisChartData';
import { CHART_PARAMETERS, type SoilAnalysesResponse } from './soilAnalysisTypes';

const PREFIX = 'pages.bed.soil.history';
/** Lines differ by dash as well as by colour, so a method stays recognisable without colour (WCAG 1.4.1). */
const DASHES = ['', '6 3', '2 3', '10 4 2 4', '1 5'];

interface SoilAnalysisChartProps {
  data: SoilAnalysesResponse;
}

export default function SoilAnalysisChart({ data }: SoilAnalysisChartProps) {
  const { t } = useTranslation();
  const [asTable, setAsTable] = useState(false);
  const histories = useMemo(
    () =>
      CHART_PARAMETERS.map((parameter) => parameterHistory(data, parameter)).filter(
        (history): history is ParameterHistory => history !== null,
      ),
    [data],
  );

  if (histories.length === 0) {
    return (
      <Typography variant="body2" color="text.secondary" data-testid="soil-history-no-chart-values">
        {t(`${PREFIX}.noChartValues`)}
      </Typography>
    );
  }

  return (
    <Box data-testid="soil-history-chart" sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
      <FormControlLabel
        control={
          <Switch
            checked={asTable}
            onChange={(event) => setAsTable(event.target.checked)}
            slotProps={{ input: { 'aria-describedby': 'soil-history-table-hint' } }}
            data-testid="soil-history-as-table"
          />
        }
        label={t(`${PREFIX}.asTable`)}
        sx={{ minHeight: 48 }}
      />
      <Typography id="soil-history-table-hint" variant="body2" color="text.secondary">
        {t(`${PREFIX}.methodsNotComparable`)}
      </Typography>
      {histories.map((history) => (
        <ParameterPanel key={history.parameter} history={history} asTable={asTable} />
      ))}
    </Box>
  );
}

function ParameterPanel({ history, asTable }: { history: ParameterHistory; asTable: boolean }) {
  const { t, i18n } = useTranslation();
  const theme = useTheme();
  const colors = [
    theme.palette.primary.main,
    theme.palette.secondary.main,
    theme.palette.info.main,
    theme.palette.warning.main,
    theme.palette.error.main,
  ];
  const headingId = `soil-history-${history.parameter}`;
  const parameterName = t(`enums.soilParameter.${history.parameter}`);
  const methodLabel = (method: string) => methodName(t, history.parameter, method);
  const unitLabel = (unit: string) => t(`enums.soilUnit.${unit}`, { defaultValue: unit });
  const date = (time: number) => new Date(time).toLocaleDateString(i18n.language);
  const number = (value: number) => value.toLocaleString(i18n.language, { maximumFractionDigits: 3 });
  const domain = timeDomain(history);

  const table = (
    <TableContainer component={Paper} variant="outlined">
      <Table size="small" aria-labelledby={headingId} data-testid={`soil-history-table-${history.parameter}`}>
        <TableHead>
          <TableRow>
            <TableCell>{t(`${PREFIX}.columns.date`)}</TableCell>
            <TableCell>{t(`${PREFIX}.columns.method`)}</TableCell>
            <TableCell align="right">{t(`${PREFIX}.columns.value`)}</TableCell>
            <TableCell>{t(`${PREFIX}.columns.source`)}</TableCell>
            <TableCell align="right">{t(`${PREFIX}.columns.depth`)}</TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {history.rows.map((row) => (
            <TableRow key={row.key}>
              <TableCell>{date(row.time)}</TableCell>
              <TableCell>
                {methodLabel(row.method)}
                {row.methodChanged && (
                  <Chip size="small" variant="outlined" label={t(`${PREFIX}.methodChange`)} sx={{ ml: 1 }} />
                )}
              </TableCell>
              <TableCell align="right">
                {number(row.value)} {unitLabel(row.unit)}
                {row.contentClass ? ` (${t(`${PREFIX}.contentClass`, { value: row.contentClass })})` : ''}
              </TableCell>
              <TableCell>{t(`enums.soilAnalysisSource.${row.source}`, { defaultValue: row.source })}</TableCell>
              <TableCell align="right">{row.depthCm === null ? '–' : `${number(row.depthCm)} cm`}</TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </TableContainer>
  );

  return (
    <Box component="section" aria-labelledby={headingId} data-testid={`soil-history-${history.parameter}`}>
      <Typography id={headingId} variant="subtitle2" component="h4" sx={{ mb: 1 }}>
        {t(`${PREFIX}.parameterTitle`, { parameter: parameterName })}
      </Typography>
      {asTable ? (
        table
      ) : (
        <>
          {/* The chart is a picture of the table below it; screen readers read the table. */}
          <Box aria-hidden sx={{ width: '100%', height: { xs: 280, sm: 300 } }}>
            <ResponsiveContainer width="100%" height="100%">
              <LineChart margin={{ top: 16, right: 16, bottom: 8, left: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke={theme.palette.divider} />
                <XAxis
                  type="number"
                  dataKey="time"
                  domain={domain}
                  scale="time"
                  tickFormatter={date}
                  stroke={theme.palette.text.secondary}
                  allowDuplicatedCategory={false}
                  minTickGap={32}
                  tick={{ fontSize: 12 }}
                />
                <YAxis stroke={theme.palette.text.secondary} tickFormatter={number} width={48} tick={{ fontSize: 12 }} />
                <Tooltip
                  labelFormatter={(label) => date(Number(label))}
                  formatter={(value, name) => [number(Number(value)), name]}
                />
                <Legend wrapperStyle={{ fontSize: 13, paddingTop: 8 }} />
                {history.changes.map((time) => (
                  <ReferenceLine
                    key={time}
                    x={time}
                    stroke={theme.palette.warning.main}
                    strokeDasharray="4 4"
                    label={{
                      value: t(`${PREFIX}.methodChange`),
                      position: changeLabelPosition(time, domain),
                      fill: theme.palette.text.secondary,
                      fontSize: 12,
                    }}
                  />
                ))}
                {history.lines.map((line, index) => (
                  <Line
                    key={line.id}
                    data={line.points}
                    dataKey="value"
                    name={`${methodLabel(line.method)} (${unitLabel(line.unit)})`}
                    stroke={colors[index % colors.length]}
                    strokeDasharray={DASHES[index % DASHES.length]}
                    strokeWidth={2}
                    dot={{ r: 5 }}
                    isAnimationActive={false}
                  />
                ))}
              </LineChart>
            </ResponsiveContainer>
          </Box>
          <Box sx={visuallyHidden}>{table}</Box>
        </>
      )}
    </Box>
  );
}

type Translate = ReturnType<typeof useTranslation>['t'];

/** The label of a series method: pH and EC their own enums, the rest the extraction. */
function methodName(t: Translate, parameter: string, method: string): string {
  if (method === 'unknown') return t(`${PREFIX}.methodUnknown`);
  const group = parameter === 'ph' ? 'phMethod' : parameter === 'ec' ? 'ecMethod' : 'soilExtractionMethod';
  return t(`enums.${group}.${method}`, { defaultValue: method });
}
