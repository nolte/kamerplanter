import { describe, it, expect, beforeEach, vi } from 'vitest';
import { screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { http, HttpResponse } from 'msw';
import { server } from '@/test/mocks/server';
import { renderWithProviders, createTestStore } from '@/test/helpers';
import { setActiveTenantSlug } from '@/api/client';
import PestIdentificationPage from '@/pages/ki-recognition/PestIdentificationPage';

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

const navigateSpy = vi.fn();
vi.mock('react-router-dom', async (importOriginal) => {
  const actual = await importOriginal<typeof import('react-router-dom')>();
  return { ...actual, useNavigate: () => navigateSpy };
});

// Spy on the gallery-contribution endpoint; keep the rest of ipm intact.
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

const STATUS_UNAVAILABLE = {
  pestDetection: {
    ...STATUS_AVAILABLE.pestDetection,
    status: {
      available: false,
      feature_enabled: false,
      primary_adapter: '',
      active_adapter: null,
      adapters: {},
    },
  },
};

// The page does a plant-agnostic detect against /pests/detect (no plant_key).
const DETECT_URL = '/api/v1/t/t1/pests/detect';
const STATUS_URL = '/api/v1/t/t1/pests/status';

function detection(overrides: Record<string, unknown> = {}) {
  return {
    key: 'pestdet_1',
    plant_instance_key: null,
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

beforeEach(() => {
  modeMock.isLightMode = false;
  setActiveTenantSlug('t1');
  contributePestImageMock.mockReset();
  navigateSpy.mockReset();
  // Default: status endpoint reports the available self-hosted adapter.
  server.use(http.get(STATUS_URL, () => HttpResponse.json(STATUS_AVAILABLE.pestDetection.status)));
});

// #1333 — the page's capture panel is gated on `canEdit`, which reads the active
// tenant's domain role. Every test below describes a user who may actually act,
// so the default is `grower`; the viewer case is asserted explicitly instead of
// arriving by accident through an absent tenant.
function tenantState(role: 'lead' | 'grower' | 'viewer') {
  return {
    tenants: {
      activeTenant: { key: 't1', slug: 't1', name: 'Garten', role, admin_scopes: [] },
      myTenants: [],
      isLoading: false,
      error: null,
    },
  };
}

function render(
  state: Record<string, unknown> = STATUS_AVAILABLE,
  role: 'lead' | 'grower' | 'viewer' = 'grower',
) {
  return renderWithProviders(<PestIdentificationPage />, {
    store: createTestStore({ ...state, ...tenantState(role) }),
  });
}

describe('PestIdentificationPage', () => {
  // #1333 — the server refuses `POST /pests/detect` below grower, so the capture
  // panel must not be reachable by a viewer. Asserted on the panel rather than on
  // a banner: this page has no read body (§7 omits history), so a route wrapper's
  // restrict-only mode would leave the panel standing and let a viewer walk into
  // the 403 — the guard being visible and inert.
  it('offers a viewer an explanation instead of the capture panel', () => {
    render(STATUS_AVAILABLE, 'viewer');

    expect(screen.getByTestId('pest-identification-role-restricted')).toBeInTheDocument();
    expect(screen.queryByTestId('mock-capture')).not.toBeInTheDocument();
  });

  it.each(['grower', 'lead'] as const)('lets a %s reach the capture panel', (role) => {
    render(STATUS_AVAILABLE, role);

    expect(screen.getByTestId('mock-capture')).toBeInTheDocument();
    expect(screen.queryByTestId('pest-identification-role-restricted')).not.toBeInTheDocument();
  });

  // An unconfigured feature reads the same for everyone: the role message must
  // not turn a disabled-feature answer into a role answer.
  it('shows the unavailable notice, not the role notice, when the feature is off', () => {
    render(STATUS_UNAVAILABLE, 'viewer');

    expect(screen.getByTestId('page-feature-unavailable')).toBeInTheDocument();
    expect(screen.queryByTestId('pest-identification-role-restricted')).not.toBeInTheDocument();
  });

  it('always shows the disclaimer and the page intro', () => {
    render();
    expect(screen.getByTestId('pest-disclaimer')).toBeInTheDocument();
    expect(screen.getByTestId('pest-identification-page')).toBeInTheDocument();
  });

  it('shows the capture panel when the feature is available', () => {
    render();
    expect(screen.getByTestId('mock-capture')).toBeInTheDocument();
    expect(screen.queryByTestId('page-feature-unavailable')).not.toBeInTheDocument();
  });

  it('shows the unavailable hint and no capture panel when not configured', () => {
    render(STATUS_UNAVAILABLE);
    expect(screen.getByTestId('page-feature-unavailable')).toBeInTheDocument();
    expect(screen.queryByTestId('mock-capture')).not.toBeInTheDocument();
  });

  it('runs a global detect and renders findings with feedback (no inspection CTA)', async () => {
    server.use(
      http.post(DETECT_URL, () =>
        HttpResponse.json(
          detection({
            is_confident: true,
            suggested_next_step: 'ipm_inspection',
            findings: [PEST_FINDING],
          }),
        ),
      ),
    );
    render();
    await userEvent.click(screen.getByTestId('mock-capture'));

    expect(await screen.findByTestId('pest-finding')).toHaveTextContent('Spinnmilbe');
    expect(screen.getByTestId('pest-bounding-box')).toBeInTheDocument();
    expect(screen.getByTestId('pest-feedback-confirm')).toBeInTheDocument();
    // The plant-bound CTA must NOT appear on the standalone page.
    expect(screen.queryByTestId('pest-create-inspection')).not.toBeInTheDocument();
    // Instead a hint points to the per-plant entry point.
    expect(screen.getByTestId('pest-identification-plant-hint')).toBeInTheDocument();
  });

  it('shows the abstention hint when not confident', async () => {
    server.use(http.post(DETECT_URL, () => HttpResponse.json(detection({ is_confident: false }))));
    render();
    await userEvent.click(screen.getByTestId('mock-capture'));
    expect(await screen.findByTestId('pest-abstain')).toBeInTheDocument();
  });

  it('navigates to the pest detail page from a matched finding', async () => {
    server.use(
      http.post(DETECT_URL, () =>
        HttpResponse.json(detection({ findings: [{ ...PEST_FINDING, bounding_box: null }] })),
      ),
    );
    render();
    await userEvent.click(screen.getByTestId('mock-capture'));
    await userEvent.click(await screen.findByTestId('pest-finding-detail-link'));
    expect(navigateSpy).toHaveBeenCalledWith('/pflanzenschutz/pests/pest_spider_mite');
  });

  it('contributes the captured photo to the gallery with the matched pest key', async () => {
    contributePestImageMock.mockResolvedValue({});
    server.use(
      http.post(DETECT_URL, () =>
        HttpResponse.json(detection({ findings: [PEST_FINDING] })),
      ),
    );
    render();
    await userEvent.click(screen.getByTestId('mock-capture'));

    const addBtn = await screen.findByTestId('pest-detection-add-to-gallery');
    await userEvent.click(addBtn);

    expect(contributePestImageMock).toHaveBeenCalledTimes(1);
    const [pestKey, file] = contributePestImageMock.mock.calls[0];
    expect(pestKey).toBe('pest_spider_mite');
    expect(file).toBeInstanceOf(File);
    await vi.waitFor(() => expect(screen.getByTestId('pest-detection-add-to-gallery')).toBeDisabled());
  });

  it('blocks the page for a consent-bound cloud adapter in light mode', () => {
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
    render(cloudState);
    expect(screen.getByTestId('pest-light-mode')).toBeInTheDocument();
    expect(screen.queryByTestId('mock-capture')).not.toBeInTheDocument();
  });
});
