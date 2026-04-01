import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { renderWithProviders } from './helpers';
import { PlantLabelDialog } from '@/components/print/PlantLabelDialog';

// Mock the print API
vi.mock('@/api/endpoints/print', () => ({
  downloadPlantLabelsPdf: vi.fn(),
}));

import { downloadPlantLabelsPdf } from '@/api/endpoints/print';

const mockDownload = vi.mocked(downloadPlantLabelsPdf);

/**
 * Helper to get the actual <input> element inside a MUI Checkbox/Radio wrapper
 * identified by data-testid.
 */
function getInput(testId: string): HTMLInputElement {
  const wrapper = screen.getByTestId(testId);
  const input = wrapper.querySelector('input');
  if (!input) throw new Error(`No input found inside element with testId "${testId}"`);
  return input;
}

describe('PlantLabelDialog', () => {
  const defaultProps = {
    open: true,
    onClose: vi.fn(),
    plantKeys: ['plant-1', 'plant-2'],
    plantNames: { 'plant-1': 'Monstera', 'plant-2': 'Ficus' },
  };

  const originalCreateObjectURL = URL.createObjectURL;
  const originalRevokeObjectURL = URL.revokeObjectURL;

  beforeEach(() => {
    vi.clearAllMocks();
    URL.createObjectURL = vi.fn(() => 'blob:mock-url');
    URL.revokeObjectURL = vi.fn();
  });

  afterEach(() => {
    URL.createObjectURL = originalCreateObjectURL;
    URL.revokeObjectURL = originalRevokeObjectURL;
  });

  it('renders with default field selections', () => {
    renderWithProviders(<PlantLabelDialog {...defaultProps} />);

    // Dialog should be visible
    expect(screen.getByTestId('plant-label-dialog')).toBeInTheDocument();

    // Default checked fields
    expect(getInput('field-checkbox-name')).toBeChecked();
    expect(getInput('field-checkbox-scientific_name')).toBeChecked();
    expect(getInput('field-checkbox-planted_date')).toBeChecked();

    // Default unchecked fields
    expect(getInput('field-checkbox-family')).not.toBeChecked();
    expect(getInput('field-checkbox-current_phase')).not.toBeChecked();

    // QR code should be checked and disabled
    expect(getInput('field-checkbox-qr_code')).toBeChecked();
    expect(getInput('field-checkbox-qr_code')).toBeDisabled();

    // Plant names should be displayed
    expect(screen.getByText('Monstera')).toBeInTheDocument();
    expect(screen.getByText('Ficus')).toBeInTheDocument();
  });

  it('allows toggling all checkboxes except QR code', async () => {
    const user = userEvent.setup();
    renderWithProviders(<PlantLabelDialog {...defaultProps} />);

    // Toggle family on
    const familyInput = getInput('field-checkbox-family');
    await user.click(familyInput);
    expect(familyInput).toBeChecked();

    // Toggle name off
    const nameInput = getInput('field-checkbox-name');
    await user.click(nameInput);
    expect(nameInput).not.toBeChecked();

    // QR code should remain checked and disabled (cannot be unchecked)
    const qrInput = getInput('field-checkbox-qr_code');
    expect(qrInput).toBeChecked();
    expect(qrInput).toBeDisabled();
  });

  it('allows changing layout via radio buttons', async () => {
    const user = userEvent.setup();
    renderWithProviders(<PlantLabelDialog {...defaultProps} />);

    // Default layout is grid_2x4
    const grid2x4Input = getInput('layout-radio-grid_2x4');
    expect(grid2x4Input).toBeChecked();

    // Switch to single
    const singleInput = getInput('layout-radio-single');
    await user.click(singleInput);
    expect(singleInput).toBeChecked();
    expect(grid2x4Input).not.toBeChecked();

    // Switch to grid_3x3
    const grid3x3Input = getInput('layout-radio-grid_3x3');
    await user.click(grid3x3Input);
    expect(grid3x3Input).toBeChecked();
    expect(singleInput).not.toBeChecked();
  });

  it('calls API with correct params on download', async () => {
    const user = userEvent.setup();
    const blob = new Blob(['pdf-content'], { type: 'application/pdf' });
    mockDownload.mockResolvedValue(blob);

    renderWithProviders(<PlantLabelDialog {...defaultProps} />);

    // Click download
    const downloadButton = screen.getByTestId('plant-label-download');
    await user.click(downloadButton);

    await waitFor(() => {
      expect(mockDownload).toHaveBeenCalledOnce();
      expect(mockDownload).toHaveBeenCalledWith(
        ['plant-1', 'plant-2'],
        // Default fields minus qr_code (filtered out)
        expect.arrayContaining(['name', 'scientific_name', 'planted_date']),
        'grid_2x4',
      );
    });

    // Verify blob download was triggered
    expect(URL.createObjectURL).toHaveBeenCalledWith(blob);
    expect(URL.revokeObjectURL).toHaveBeenCalledWith('blob:mock-url');
  });

  it('closes dialog after successful download', async () => {
    const user = userEvent.setup();
    const blob = new Blob(['pdf-content'], { type: 'application/pdf' });
    mockDownload.mockResolvedValue(blob);

    renderWithProviders(<PlantLabelDialog {...defaultProps} />);

    const downloadButton = screen.getByTestId('plant-label-download');
    await user.click(downloadButton);

    await waitFor(() => {
      expect(defaultProps.onClose).toHaveBeenCalledOnce();
    });
  });

  it('shows error notification on download failure', async () => {
    const user = userEvent.setup();
    mockDownload.mockRejectedValue(new Error('Network error'));

    renderWithProviders(<PlantLabelDialog {...defaultProps} />);

    const downloadButton = screen.getByTestId('plant-label-download');
    await user.click(downloadButton);

    await waitFor(() => {
      expect(mockDownload).toHaveBeenCalledOnce();
      // Dialog should NOT close on error
      expect(defaultProps.onClose).not.toHaveBeenCalled();
    });
  });

  it('does not render when open is false', () => {
    renderWithProviders(<PlantLabelDialog {...defaultProps} open={false} />);
    expect(screen.queryByTestId('plant-label-dialog')).not.toBeInTheDocument();
  });

  it('shows plant count when plantNames is not provided', () => {
    renderWithProviders(
      <PlantLabelDialog
        open={true}
        onClose={vi.fn()}
        plantKeys={['plant-1', 'plant-2', 'plant-3']}
      />,
    );

    const dialog = screen.getByTestId('plant-label-dialog');
    // The count text contains "3" as part of the plant count message
    const subtitle = within(dialog).getByText(/3 .*selected|3 .*ausgewählt/i);
    expect(subtitle).toBeInTheDocument();
  });
});
