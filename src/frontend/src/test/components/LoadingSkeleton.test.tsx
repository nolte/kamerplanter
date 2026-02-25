import { render } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import LoadingSkeleton from '@/components/common/LoadingSkeleton';

describe('LoadingSkeleton', () => {
  it('renders table variant by default', () => {
    const { container } = render(<LoadingSkeleton />);
    expect(container.querySelector('[aria-busy="true"]')).toBeTruthy();
    expect(container.querySelector('[aria-label="Loading table"]')).toBeTruthy();
  });

  it('renders form variant', () => {
    const { container } = render(<LoadingSkeleton variant="form" />);
    expect(container.querySelector('[aria-label="Loading form"]')).toBeTruthy();
  });

  it('renders card variant', () => {
    const { container } = render(<LoadingSkeleton variant="card" />);
    expect(container.querySelector('[aria-label="Loading cards"]')).toBeTruthy();
  });

  it('renders specified number of rows for table', () => {
    const { container } = render(<LoadingSkeleton variant="table" rows={3} />);
    // Title skeleton + header skeleton + 3 row skeletons
    const skeletons = container.querySelectorAll('.MuiSkeleton-root');
    expect(skeletons.length).toBeGreaterThanOrEqual(3);
  });
});
