import { type ReactNode } from 'react';
import { useTranslation } from 'react-i18next';
import Table from '@mui/material/Table';
import TableBody from '@mui/material/TableBody';
import TableCell from '@mui/material/TableCell';
import TableContainer from '@mui/material/TableContainer';
import TableHead from '@mui/material/TableHead';
import TableRow from '@mui/material/TableRow';
import TablePagination from '@mui/material/TablePagination';
import Paper from '@mui/material/Paper';
import LoadingSkeleton from './LoadingSkeleton';
import EmptyState from './EmptyState';

export interface Column<T> {
  id: string;
  label: string;
  render: (row: T) => ReactNode;
  width?: number | string;
}

interface DataTableProps<T> {
  columns: Column<T>[];
  rows: T[];
  loading?: boolean;
  total?: number;
  page?: number;
  rowsPerPage?: number;
  onPageChange?: (page: number) => void;
  onRowsPerPageChange?: (rowsPerPage: number) => void;
  onRowClick?: (row: T) => void;
  emptyMessage?: string;
  emptyActionLabel?: string;
  onEmptyAction?: () => void;
  getRowKey: (row: T) => string;
}

export default function DataTable<T>({
  columns,
  rows,
  loading,
  total,
  page = 0,
  rowsPerPage = 50,
  onPageChange,
  onRowsPerPageChange,
  onRowClick,
  emptyMessage,
  emptyActionLabel,
  onEmptyAction,
  getRowKey,
}: DataTableProps<T>) {
  const { t } = useTranslation();

  if (loading) {
    return <LoadingSkeleton variant="table" />;
  }

  if (rows.length === 0) {
    return (
      <EmptyState
        message={emptyMessage}
        actionLabel={emptyActionLabel}
        onAction={onEmptyAction}
      />
    );
  }

  return (
    <Paper variant="outlined" data-testid="data-table">
      <TableContainer>
        <Table size="small">
          <TableHead>
            <TableRow>
              {columns.map((col) => (
                <TableCell key={col.id} width={col.width}>
                  {col.label}
                </TableCell>
              ))}
            </TableRow>
          </TableHead>
          <TableBody>
            {rows.map((row) => (
              <TableRow
                key={getRowKey(row)}
                hover
                onClick={() => onRowClick?.(row)}
                sx={onRowClick ? { cursor: 'pointer' } : undefined}
                data-testid="data-table-row"
              >
                {columns.map((col) => (
                  <TableCell key={col.id}>{col.render(row)}</TableCell>
                ))}
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
      {total !== undefined && onPageChange && onRowsPerPageChange && (
        <TablePagination
          component="div"
          count={total}
          page={page}
          onPageChange={(_, newPage) => onPageChange(newPage)}
          rowsPerPage={rowsPerPage}
          onRowsPerPageChange={(e) => onRowsPerPageChange(parseInt(e.target.value, 10))}
          labelRowsPerPage={t('common.rowsPerPage')}
          rowsPerPageOptions={[10, 25, 50, 100]}
        />
      )}
    </Paper>
  );
}
