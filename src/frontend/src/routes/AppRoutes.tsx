import { Route, Navigate, createBrowserRouter, createRoutesFromElements } from 'react-router-dom';
import { lazy, Suspense } from 'react';
import MainLayout from '@/layouts/MainLayout';
import LoadingSkeleton from '@/components/common/LoadingSkeleton';
import ProtectedRoute from '@/auth/ProtectedRoute';
import PublicOnlyRoute from '@/auth/PublicOnlyRoute';

// Auth pages
const LoginPage = lazy(() => import('@/pages/auth/LoginPage'));
const RegisterPage = lazy(() => import('@/pages/auth/RegisterPage'));
const EmailVerificationPage = lazy(() => import('@/pages/auth/EmailVerificationPage'));
const PasswordResetRequestPage = lazy(
  () => import('@/pages/auth/PasswordResetRequestPage'),
);
const PasswordResetConfirmPage = lazy(
  () => import('@/pages/auth/PasswordResetConfirmPage'),
);
const AccountSettingsPage = lazy(() => import('@/pages/auth/AccountSettingsPage'));

// Tenant pages
const TenantCreatePage = lazy(() => import('@/pages/tenants/TenantCreatePage'));
const TenantSettingsPage = lazy(() => import('@/pages/tenants/TenantSettingsPage'));
const InvitationAcceptPage = lazy(() => import('@/pages/tenants/InvitationAcceptPage'));

const DashboardPage = lazy(() => import('@/pages/DashboardPage'));
const BotanicalFamilyListPage = lazy(
  () => import('@/pages/stammdaten/BotanicalFamilyListPage'),
);
const BotanicalFamilyDetailPage = lazy(
  () => import('@/pages/stammdaten/BotanicalFamilyDetailPage'),
);
const SpeciesListPage = lazy(() => import('@/pages/stammdaten/SpeciesListPage'));
const SpeciesDetailPage = lazy(() => import('@/pages/stammdaten/SpeciesDetailPage'));
const CultivarDetailPage = lazy(() => import('@/pages/stammdaten/CultivarDetailPage'));
const CompanionPlantingPage = lazy(
  () => import('@/pages/stammdaten/CompanionPlantingPage'),
);
const CropRotationPage = lazy(() => import('@/pages/stammdaten/CropRotationPage'));
const SiteListPage = lazy(() => import('@/pages/standorte/SiteListPage'));
const SiteDetailPage = lazy(() => import('@/pages/standorte/SiteDetailPage'));
const LocationDetailPage = lazy(() => import('@/pages/standorte/LocationDetailPage'));
const SubstrateListPage = lazy(() => import('@/pages/standorte/SubstrateListPage'));
const SubstrateDetailPage = lazy(() => import('@/pages/standorte/SubstrateDetailPage'));
const BatchDetailPage = lazy(() => import('@/pages/standorte/BatchDetailPage'));
const SlotDetailPage = lazy(() => import('@/pages/standorte/SlotDetailPage'));
const PlantInstanceListPage = lazy(
  () => import('@/pages/pflanzen/PlantInstanceListPage'),
);
const PlantInstanceDetailPage = lazy(
  () => import('@/pages/pflanzen/PlantInstanceDetailPage'),
);
const CalculationsPage = lazy(() => import('@/pages/pflanzen/CalculationsPage'));
const PlantingRunListPage = lazy(
  () => import('@/pages/durchlaeufe/PlantingRunListPage'),
);
const PlantingRunDetailPage = lazy(
  () => import('@/pages/durchlaeufe/PlantingRunDetailPage'),
);
const TankListPage = lazy(() => import('@/pages/standorte/TankListPage'));
const TankDetailPage = lazy(() => import('@/pages/standorte/TankDetailPage'));
const FertilizerListPage = lazy(() => import('@/pages/duengung/FertilizerListPage'));
const FertilizerDetailPage = lazy(() => import('@/pages/duengung/FertilizerDetailPage'));
const NutrientPlanListPage = lazy(() => import('@/pages/duengung/NutrientPlanListPage'));
const NutrientPlanDetailPage = lazy(() => import('@/pages/duengung/NutrientPlanDetailPage'));
const NutrientCalculationsPage = lazy(
  () => import('@/pages/duengung/NutrientCalculationsPage'),
);
const FeedingEventListPage = lazy(
  () => import('@/pages/duengung/FeedingEventListPage'),
);
const FeedingEventDetailPage = lazy(
  () => import('@/pages/duengung/FeedingEventDetailPage'),
);
const WateringEventListPage = lazy(
  () => import('@/pages/standorte/WateringEventListPage'),
);
// REQ-010 IPM
const PestListPage = lazy(() => import('@/pages/pflanzenschutz/PestListPage'));
const DiseaseListPage = lazy(() => import('@/pages/pflanzenschutz/DiseaseListPage'));
const TreatmentListPage = lazy(
  () => import('@/pages/pflanzenschutz/TreatmentListPage'),
);
// REQ-007 Harvest
const HarvestBatchListPage = lazy(
  () => import('@/pages/ernte/HarvestBatchListPage'),
);
const HarvestBatchDetailPage = lazy(
  () => import('@/pages/ernte/HarvestBatchDetailPage'),
);
// REQ-006 Tasks
const TaskQueuePage = lazy(() => import('@/pages/aufgaben/TaskQueuePage'));
const TaskDetailPage = lazy(() => import('@/pages/aufgaben/TaskDetailPage'));
const WorkflowTemplateListPage = lazy(
  () => import('@/pages/aufgaben/WorkflowTemplateListPage'),
);

const NotFoundPage = lazy(() => import('@/pages/NotFoundPage'));

export const router = createBrowserRouter(
  createRoutesFromElements(
    <>
      {/* Public-only routes (redirect to dashboard when authenticated) */}
      <Route element={<PublicOnlyRoute />}>
        <Route
          path="login"
          element={
            <Suspense fallback={<LoadingSkeleton variant="card" />}>
              <LoginPage />
            </Suspense>
          }
        />
        <Route
          path="register"
          element={
            <Suspense fallback={<LoadingSkeleton variant="card" />}>
              <RegisterPage />
            </Suspense>
          }
        />
        <Route
          path="verify-email/:token"
          element={
            <Suspense fallback={<LoadingSkeleton variant="card" />}>
              <EmailVerificationPage />
            </Suspense>
          }
        />
        <Route
          path="password-reset"
          element={
            <Suspense fallback={<LoadingSkeleton variant="card" />}>
              <PasswordResetRequestPage />
            </Suspense>
          }
        />
        <Route
          path="password-reset/:token"
          element={
            <Suspense fallback={<LoadingSkeleton variant="card" />}>
              <PasswordResetConfirmPage />
            </Suspense>
          }
        />
      </Route>

      {/* Protected routes (require authentication) */}
      <Route element={<ProtectedRoute />}>
        <Route element={<MainLayout />}>
          <Route index element={<Navigate to="/dashboard" replace />} />
          <Route
            path="dashboard"
            element={
              <Suspense fallback={<LoadingSkeleton variant="card" />}>
                <DashboardPage />
              </Suspense>
            }
          />

          {/* Account Settings */}
          <Route
            path="settings"
            element={
              <Suspense fallback={<LoadingSkeleton variant="form" />}>
                <AccountSettingsPage />
              </Suspense>
            }
          />

          {/* REQ-024 Tenants */}
          <Route
            path="tenants/create"
            element={
              <Suspense fallback={<LoadingSkeleton variant="form" />}>
                <TenantCreatePage />
              </Suspense>
            }
          />
          <Route
            path="tenants/settings"
            element={
              <Suspense fallback={<LoadingSkeleton variant="form" />}>
                <TenantSettingsPage />
              </Suspense>
            }
          />
          <Route
            path="invitations/accept"
            element={
              <Suspense fallback={<LoadingSkeleton variant="card" />}>
                <InvitationAcceptPage />
              </Suspense>
            }
          />

          {/* REQ-001 Stammdaten */}
          <Route
            path="stammdaten/botanical-families"
            element={
              <Suspense fallback={<LoadingSkeleton variant="table" />}>
                <BotanicalFamilyListPage />
              </Suspense>
            }
          />
          <Route
            path="stammdaten/botanical-families/:key"
            element={
              <Suspense fallback={<LoadingSkeleton variant="form" />}>
                <BotanicalFamilyDetailPage />
              </Suspense>
            }
          />
          <Route
            path="stammdaten/species"
            element={
              <Suspense fallback={<LoadingSkeleton variant="table" />}>
                <SpeciesListPage />
              </Suspense>
            }
          />
          <Route
            path="stammdaten/species/:key"
            element={
              <Suspense fallback={<LoadingSkeleton variant="form" />}>
                <SpeciesDetailPage />
              </Suspense>
            }
          />
          <Route
            path="stammdaten/species/:speciesKey/cultivars/:cultivarKey"
            element={
              <Suspense fallback={<LoadingSkeleton variant="form" />}>
                <CultivarDetailPage />
              </Suspense>
            }
          />
          <Route
            path="stammdaten/companion-planting"
            element={
              <Suspense fallback={<LoadingSkeleton variant="table" />}>
                <CompanionPlantingPage />
              </Suspense>
            }
          />
          <Route
            path="stammdaten/crop-rotation"
            element={
              <Suspense fallback={<LoadingSkeleton variant="table" />}>
                <CropRotationPage />
              </Suspense>
            }
          />

          {/* REQ-002 Standorte */}
          <Route
            path="standorte/sites"
            element={
              <Suspense fallback={<LoadingSkeleton variant="table" />}>
                <SiteListPage />
              </Suspense>
            }
          />
          <Route
            path="standorte/sites/:key"
            element={
              <Suspense fallback={<LoadingSkeleton variant="form" />}>
                <SiteDetailPage />
              </Suspense>
            }
          />
          <Route
            path="standorte/locations/:key"
            element={
              <Suspense fallback={<LoadingSkeleton variant="form" />}>
                <LocationDetailPage />
              </Suspense>
            }
          />
          <Route
            path="standorte/substrates"
            element={
              <Suspense fallback={<LoadingSkeleton variant="table" />}>
                <SubstrateListPage />
              </Suspense>
            }
          />
          <Route
            path="standorte/substrates/:key"
            element={
              <Suspense fallback={<LoadingSkeleton variant="form" />}>
                <SubstrateDetailPage />
              </Suspense>
            }
          />
          <Route
            path="standorte/substrates/batches/:key"
            element={
              <Suspense fallback={<LoadingSkeleton variant="form" />}>
                <BatchDetailPage />
              </Suspense>
            }
          />
          <Route
            path="standorte/slots/:key"
            element={
              <Suspense fallback={<LoadingSkeleton variant="form" />}>
                <SlotDetailPage />
              </Suspense>
            }
          />

          {/* REQ-014 Watering Events */}
          <Route
            path="standorte/watering-events"
            element={
              <Suspense fallback={<LoadingSkeleton variant="table" />}>
                <WateringEventListPage />
              </Suspense>
            }
          />

          {/* REQ-014 Tanks */}
          <Route
            path="standorte/tanks"
            element={
              <Suspense fallback={<LoadingSkeleton variant="table" />}>
                <TankListPage />
              </Suspense>
            }
          />
          <Route
            path="standorte/tanks/:key"
            element={
              <Suspense fallback={<LoadingSkeleton variant="form" />}>
                <TankDetailPage />
              </Suspense>
            }
          />

          {/* REQ-003 Pflanzen */}
          <Route
            path="pflanzen/plant-instances"
            element={
              <Suspense fallback={<LoadingSkeleton variant="table" />}>
                <PlantInstanceListPage />
              </Suspense>
            }
          />
          <Route
            path="pflanzen/plant-instances/:key"
            element={
              <Suspense fallback={<LoadingSkeleton variant="form" />}>
                <PlantInstanceDetailPage />
              </Suspense>
            }
          />
          <Route
            path="pflanzen/calculations"
            element={
              <Suspense fallback={<LoadingSkeleton variant="card" />}>
                <CalculationsPage />
              </Suspense>
            }
          />

          {/* REQ-004 Düngung */}
          <Route
            path="duengung/fertilizers"
            element={
              <Suspense fallback={<LoadingSkeleton variant="table" />}>
                <FertilizerListPage />
              </Suspense>
            }
          />
          <Route
            path="duengung/fertilizers/:key"
            element={
              <Suspense fallback={<LoadingSkeleton variant="form" />}>
                <FertilizerDetailPage />
              </Suspense>
            }
          />
          <Route
            path="duengung/plans"
            element={
              <Suspense fallback={<LoadingSkeleton variant="table" />}>
                <NutrientPlanListPage />
              </Suspense>
            }
          />
          <Route
            path="duengung/plans/:key"
            element={
              <Suspense fallback={<LoadingSkeleton variant="form" />}>
                <NutrientPlanDetailPage />
              </Suspense>
            }
          />
          <Route
            path="duengung/calculations"
            element={
              <Suspense fallback={<LoadingSkeleton variant="card" />}>
                <NutrientCalculationsPage />
              </Suspense>
            }
          />

          {/* REQ-004 Feeding Events */}
          <Route
            path="duengung/feeding-events"
            element={
              <Suspense fallback={<LoadingSkeleton variant="table" />}>
                <FeedingEventListPage />
              </Suspense>
            }
          />
          <Route
            path="duengung/feeding-events/:key"
            element={
              <Suspense fallback={<LoadingSkeleton variant="form" />}>
                <FeedingEventDetailPage />
              </Suspense>
            }
          />

          {/* REQ-010 Pflanzenschutz */}
          <Route
            path="pflanzenschutz/pests"
            element={
              <Suspense fallback={<LoadingSkeleton variant="table" />}>
                <PestListPage />
              </Suspense>
            }
          />
          <Route
            path="pflanzenschutz/diseases"
            element={
              <Suspense fallback={<LoadingSkeleton variant="table" />}>
                <DiseaseListPage />
              </Suspense>
            }
          />
          <Route
            path="pflanzenschutz/treatments"
            element={
              <Suspense fallback={<LoadingSkeleton variant="table" />}>
                <TreatmentListPage />
              </Suspense>
            }
          />

          {/* REQ-007 Ernte */}
          <Route
            path="ernte/batches"
            element={
              <Suspense fallback={<LoadingSkeleton variant="table" />}>
                <HarvestBatchListPage />
              </Suspense>
            }
          />
          <Route
            path="ernte/batches/:key"
            element={
              <Suspense fallback={<LoadingSkeleton variant="form" />}>
                <HarvestBatchDetailPage />
              </Suspense>
            }
          />

          {/* REQ-006 Aufgaben */}
          <Route
            path="aufgaben/queue"
            element={
              <Suspense fallback={<LoadingSkeleton variant="card" />}>
                <TaskQueuePage />
              </Suspense>
            }
          />
          <Route
            path="aufgaben/tasks/:key"
            element={
              <Suspense fallback={<LoadingSkeleton variant="form" />}>
                <TaskDetailPage />
              </Suspense>
            }
          />
          <Route
            path="aufgaben/workflows"
            element={
              <Suspense fallback={<LoadingSkeleton variant="table" />}>
                <WorkflowTemplateListPage />
              </Suspense>
            }
          />

          {/* REQ-013 Durchläufe */}
          <Route
            path="durchlaeufe/planting-runs"
            element={
              <Suspense fallback={<LoadingSkeleton variant="table" />}>
                <PlantingRunListPage />
              </Suspense>
            }
          />
          <Route
            path="durchlaeufe/planting-runs/:key"
            element={
              <Suspense fallback={<LoadingSkeleton variant="form" />}>
                <PlantingRunDetailPage />
              </Suspense>
            }
          />

          <Route
            path="*"
            element={
              <Suspense fallback={<LoadingSkeleton variant="card" />}>
                <NotFoundPage />
              </Suspense>
            }
          />
        </Route>
      </Route>
    </>,
  ),
);
