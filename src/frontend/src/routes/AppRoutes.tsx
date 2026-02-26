import { Route, Navigate, createBrowserRouter, createRoutesFromElements } from 'react-router-dom';
import { lazy, Suspense } from 'react';
import MainLayout from '@/layouts/MainLayout';
import LoadingSkeleton from '@/components/common/LoadingSkeleton';

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
const NotFoundPage = lazy(() => import('@/pages/NotFoundPage'));

export const router = createBrowserRouter(
  createRoutesFromElements(
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

      <Route
        path="*"
        element={
          <Suspense fallback={<LoadingSkeleton variant="card" />}>
            <NotFoundPage />
          </Suspense>
        }
      />
    </Route>,
  ),
);
