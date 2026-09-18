import { lazy, type ComponentType, type LazyExoticComponent } from 'react';
import type { WidgetKey } from '@/config/dashboardWidgetCatalog';

/**
 * REQ-045 — maps each widget key to a lazily-loaded component (UI-NFR-003
 * bundle budget: widget code is only fetched when a widget is actually
 * rendered). Widgets without a bespoke component fall back to GenericWidget,
 * which renders their catalog label/description + any aggregated numbers.
 */

export interface WidgetComponentProps {
  instanceId: string;
  widgetKey: string;
  config?: Record<string, unknown>;
  /**
   * True while the dashboard is in personalization/edit mode (#461). Widgets that
   * render entity deep links (rows/tiles) must render them inert in edit mode so
   * drag/resize and the kebab menu are never hijacked by navigation.
   */
  editMode?: boolean;
}

type WidgetComponent = LazyExoticComponent<ComponentType<WidgetComponentProps>>;

const GenericWidget = lazy(() => import('./widgets/GenericWidget')) as WidgetComponent;
const QuickActionsWidget = lazy(() => import('./widgets/QuickActionsWidget')) as WidgetComponent;
// DASH-2 (#488) — dedicated rich, filterable plant-instance grid.
const PlantGridWidget = lazy(() => import('./widgets/PlantGridWidget')) as WidgetComponent;
// Existing REQ-022 widget — prop-less, extra props are ignored.
const WinterProtectionWidget = lazy(() => import('./WinterProtectionWidget')) as WidgetComponent;
// REQ-046 weather widget — prop-less, extra props are ignored.
const WeatherForecastWidget = lazy(() => import('./widgets/WeatherForecastWidget')) as WidgetComponent;
// REQ-031 §6.3 daily tip — prop-less, extra props are ignored. Wired here in
// #1461 (review SCR-004): the component had been written and tested and was
// mounted nowhere, so `daily_tip` resolved to the generic shell and the card the
// spec describes had never been on screen. A widget that exists in the catalogue
// and resolves to GenericWidget is indistinguishable from one that is merely not
// built yet — `test_the_daily_tip_widget_resolves_to_its_own_component` below
// keeps this one from drifting back.
const DailyTipCard = lazy(() => import('../ai/DailyTipCard')) as WidgetComponent;

export const widgetRegistry: Record<WidgetKey, WidgetComponent> = {
  quick_actions: QuickActionsWidget,
  winter_protection: WinterProtectionWidget,
  weather_forecast: WeatherForecastWidget,
  daily_tip: DailyTipCard,
  // The remaining widgets share the generic shell until their bespoke REQ-009
  // views land. They still receive their widgetKey/config props.
  active_plants_summary: GenericWidget,
  tasks_today: GenericWidget,
  care_reminders: GenericWidget,
  onboarding_progress: GenericWidget,
  ipm_alerts: GenericWidget,
  harvest_forecast: GenericWidget,
  next_calendar_events: GenericWidget,
  community_activity: GenericWidget,
  tank_status: GenericWidget,
  phase_timeline: GenericWidget,
  plant_grid: PlantGridWidget,
};

export function getWidgetComponent(widgetKey: string): WidgetComponent | null {
  return (widgetRegistry as Record<string, WidgetComponent>)[widgetKey] ?? null;
}
