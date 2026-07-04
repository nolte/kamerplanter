import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import { TabPanel, tabA11yProps } from '@/components/common/TabPanel';

describe('TabPanel', () => {
  it('renders children and wires WAI-ARIA attributes when active (QW-1)', () => {
    render(
      <TabPanel index={2} value={2} idPrefix="demo">
        <span>active content</span>
      </TabPanel>,
    );
    const panel = screen.getByRole('tabpanel');
    expect(panel).toHaveAttribute('id', 'demo-tabpanel-2');
    expect(panel).toHaveAttribute('aria-labelledby', 'demo-tab-2');
    expect(screen.getByText('active content')).toBeInTheDocument();
  });

  it('unmounts children and hides the panel when inactive', () => {
    render(
      <TabPanel index={1} value={0} idPrefix="demo">
        <span>hidden content</span>
      </TabPanel>,
    );
    // Hidden panels are excluded from the accessibility tree.
    expect(screen.queryByRole('tabpanel')).toBeNull();
    expect(screen.queryByText('hidden content')).toBeNull();
  });

  it('derives matching tab and panel ids from tabA11yProps', () => {
    const props = tabA11yProps('species', 3);
    expect(props).toEqual({
      id: 'species-tab-3',
      'aria-controls': 'species-tabpanel-3',
    });
  });
});
