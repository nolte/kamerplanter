import { render, screen } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import DataTable from '@/components/common/DataTable';

interface TestRow {
  id: string;
  name: string;
}

describe('DataTable', () => {
  const columns = [
    { id: 'name', label: 'Name', render: (r: TestRow) => r.name },
  ];

  it('renders loading skeleton when loading', () => {
    render(
      <DataTable
        columns={columns}
        rows={[]}
        loading={true}
        getRowKey={(r: TestRow) => r.id}
      />,
    );
    // LoadingSkeleton renders Skeleton components
    expect(document.querySelector('.MuiSkeleton-root')).toBeTruthy();
  });

  it('renders empty state when no rows', () => {
    render(
      <DataTable
        columns={columns}
        rows={[]}
        loading={false}
        getRowKey={(r: TestRow) => r.id}
      />,
    );
    // Default i18n fallback text
    expect(screen.getByText(/Keine Daten|No data/i)).toBeTruthy();
  });

  it('renders rows', () => {
    const rows: TestRow[] = [
      { id: '1', name: 'Alice' },
      { id: '2', name: 'Bob' },
    ];
    render(
      <DataTable
        columns={columns}
        rows={rows}
        loading={false}
        getRowKey={(r) => r.id}
      />,
    );
    expect(screen.getByText('Alice')).toBeTruthy();
    expect(screen.getByText('Bob')).toBeTruthy();
  });

  it('calls onRowClick when a row is clicked', async () => {
    const onClick = vi.fn();
    const rows: TestRow[] = [{ id: '1', name: 'Alice' }];
    render(
      <DataTable
        columns={columns}
        rows={rows}
        loading={false}
        getRowKey={(r) => r.id}
        onRowClick={onClick}
      />,
    );
    screen.getByText('Alice').closest('tr')?.click();
    expect(onClick).toHaveBeenCalledWith(rows[0]);
  });
});
