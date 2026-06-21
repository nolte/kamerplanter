import { describe, it, expect, beforeEach, vi } from 'vitest';
import { screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { http, HttpResponse } from 'msw';
import { server } from '@/test/mocks/server';
import { renderWithProviders, createTestStore } from '@/test/helpers';
import { setActiveTenantSlug } from '@/api/client';
import PestDetectionDialog from '@/components/pests/PestDetectionDialog';

// Mode is mocked so we can switch full/light without rebuilding the graph.
const modeMock = vi.hoisted(() => ({ isLightMode: false, isFullMode: true }));
vi.mock('@/config/mode', () => ({
  get isLightMode() {
    return modeMock.isLightMode;
  },
  get isFullMode() {
    return modeMock.isFullMode;
  },
  KAMERPLANTER_MODE: 'full',
}));

// Spy on the gallery-contribution endpoint while keeping the rest of the
// ipm endpoints (detect/feedback flow uses the slice, not this module) intact.
const contributePestImageMock = vi.hoisted(() => vi.fn());
vi.mock('@/api/endpoints/ipm', async (importActual) => {
  const actual = await importActual<typeof import('@/api/endpoints/ipm')>();
  return { ...actual, contributePestImage: contributePestImageMock };
});

// Mock the capture panel: one click fires onImageReady with a fake JPEG + preview.
vi.mock('@/components/identification/ImageCapturePanel', () => ({
  default: ({ onImageReady }: { onImageReady: (f: File, url: string) => void }) => (
    <button
      data-testid="mock-capture"
      onClick={() => onImageReady(new File([new Uint8Array([1])], 'p.jpg', { type: 'image/jpeg' }), 'blob:preview')}
    >
      capture
    </button>
  ),
}));

const STATUS_AVAILABLE = {
  pestDetection: {
    status: {
      available: true,
      feature_enabled: true,
      primary_adapter: 'local_pest_symptom',
      active_adapter: 'local_pest_symptom',
      adapters: {},
    },
    statusLoading: false,
    result: null,
    detecting: false,
    history: [],
    historyLoading: false,
    error: null,
    errorCode: null,
  },
};

const DETECT_URL = '/api/v1/t/t1/pests/plants/p1/detect';

function detection(overrides: Record<string, unknown> = {}) {
  return {
    key: 'pestdet_1',
    plant_instance_key: 'p1',
    source: 'local_symptom',
    adapter_key: 'local_pest_symptom',
    is_confident: true,
    trigger: 'user_photo',
    findings: [],
    tiles_processed: 4,
    suggested_next_step: 'none',
    image_hash: 'sha256:abc',
    disclaimer: 'Nur eine Einschätzung der Bilderkennung.',
    created_at: null,
    ...overrides,
  };
}

beforeEach(() => {
  modeMock.isLightMode = false;
  setActiveTenantSlug('t1');
  contributePestImageMock.mockReset();
});

const PEST_FINDING = {
  label: 'spider_mite',
  category: 'pest',
  common_name: 'Spinnmilbe',
  confidence: 0.72,
  mode: 'direct',
  bounding_box: { x: 0.1, y: 0.2, width: 0.3, height: 0.2 },
  matched_pest_key: 'pest_spider_mite',
  matched_beneficial_key: null,
};

function render() {
  return renderWithProviders(<PestDetectionDialog open onClose={() => {}} plantKey="p1" />, {
    store: createTestStore(STATUS_AVAILABLE),
  });
}

describe('PestDetectionDialog', () => {
  it('always shows the disclaimer', () => {
    render();
    expect(screen.getByTestId('pest-disclaimer')).toBeInTheDocument();
  });

  it('renders a bounding box and feedback buttons for a direct pest finding', async () => {
    server.use(
      http.post(DETECT_URL, () =>
        HttpResponse.json(
          detection({
            is_confident: true,
            suggested_next_step: 'ipm_inspection',
            findings: [
              {
                label: 'spider_mite',
                category: 'pest',
                common_name: 'Spinnmilbe',
                confidence: 0.72,
                mode: 'direct',
                bounding_box: { x: 0.1, y: 0.2, width: 0.3, height: 0.2 },
                matched_pest_key: 'pest_spider_mite',
                matched_beneficial_key: null,
              },
            ],
          }),
        ),
      ),
    );
    render();
    await userEvent.click(screen.getByTestId('mock-capture'));

    expect(await screen.findByTestId('pest-bounding-box')).toBeInTheDocument();
    expect(screen.getByTestId('pest-finding')).toHaveTextContent('Spinnmilbe');
    expect(screen.getByTestId('pest-feedback-confirm')).toBeInTheDocument();
    expect(screen.getByTestId('pest-create-inspection')).toBeInTheDocument();
  });

  it('shows the abstention hint when not confident', async () => {
    server.use(http.post(DETECT_URL, () => HttpResponse.json(detection({ is_confident: false }))));
    render();
    await userEvent.click(screen.getByTestId('mock-capture'));
    expect(await screen.findByTestId('pest-abstain')).toBeInTheDocument();
  });

  it('shows the beneficial hint and no inspection CTA for a beneficial', async () => {
    server.use(
      http.post(DETECT_URL, () =>
        HttpResponse.json(
          detection({
            suggested_next_step: 'none',
            findings: [
              {
                label: 'ladybird',
                category: 'beneficial',
                common_name: 'Marienkäfer',
                confidence: 0.9,
                mode: 'direct',
                bounding_box: null,
                matched_pest_key: null,
                matched_beneficial_key: 'beneficial_ladybird',
              },
            ],
          }),
        ),
      ),
    );
    render();
    await userEvent.click(screen.getByTestId('mock-capture'));
    expect(await screen.findByTestId('pest-beneficial')).toBeInTheDocument();
    expect(screen.queryByTestId('pest-create-inspection')).not.toBeInTheDocument();
  });

  it('allows the self-hosted path in light mode', () => {
    modeMock.isLightMode = true;
    render();
    expect(screen.queryByTestId('pest-light-mode')).not.toBeInTheDocument();
    expect(screen.getByTestId('mock-capture')).toBeInTheDocument();
  });

  it('contributes the captured photo to the gallery with the matched pest key', async () => {
    contributePestImageMock.mockResolvedValue({});
    server.use(
      http.post(DETECT_URL, () =>
        HttpResponse.json(
          detection({ is_confident: true, suggested_next_step: 'none', findings: [PEST_FINDING] }),
        ),
      ),
    );
    render();
    await userEvent.click(screen.getByTestId('mock-capture'));

    const addBtn = await screen.findByTestId('pest-detection-add-to-gallery');
    await userEvent.click(addBtn);

    expect(contributePestImageMock).toHaveBeenCalledTimes(1);
    const [pestKey, file] = contributePestImageMock.mock.calls[0];
    expect(pestKey).toBe('pest_spider_mite');
    // The already-captured File (from onImageReady) is uploaded as-is.
    expect(file).toBeInstanceOf(File);
    expect((file as File).name).toBe('p.jpg');
    // After success the CTA is disabled (no repeated uploads).
    await vi.waitFor(() => expect(screen.getByTestId('pest-detection-add-to-gallery')).toBeDisabled());
  });

  it('does not offer the gallery CTA for a finding without a matched pest', async () => {
    server.use(
      http.post(DETECT_URL, () =>
        HttpResponse.json(
          detection({
            findings: [{ ...PEST_FINDING, matched_pest_key: null, bounding_box: null }],
          }),
        ),
      ),
    );
    render();
    await userEvent.click(screen.getByTestId('mock-capture'));
    await screen.findByTestId('pest-finding');
    expect(screen.queryByTestId('pest-detection-add-to-gallery')).not.toBeInTheDocument();
  });

  it('blocks only the cloud path in light mode', () => {
    modeMock.isLightMode = true;
    const cloudState = {
      pestDetection: {
        ...STATUS_AVAILABLE.pestDetection,
        status: {
          ...STATUS_AVAILABLE.pestDetection.status,
          active_adapter: 'kindwise_pest',
          adapters: {
            kindwise_pest: {
              configured: true,
              is_external: true,
              requires_consent: 'pest_detection_cloud',
              supports_modes: ['symptom'],
            },
          },
        },
      },
    };
    renderWithProviders(<PestDetectionDialog open onClose={() => {}} plantKey="p1" />, {
      store: createTestStore(cloudState),
    });
    expect(screen.getByTestId('pest-light-mode')).toBeInTheDocument();
  });
});
