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
}

type WidgetComponent = LazyExoticComponent<ComponentType<WidgetComponentProps>>;

const GenericWidget = lazy(() => import('./widgets/GenericWidget')) as WidgetComponent;
const QuickActionsWidget = lazy(() => import('./widgets/QuickActionsWidget')) as WidgetComponent;
// Existing REQ-022 widget — prop-less, extra props are ignored.
const WinterProtectionWidget = lazy(() => import('./WinterProtectionWidget')) as WidgetComponent;
// REQ-046 weather widget — prop-less, extra props are ignored.
const WeatherForecastWidget = lazy(() => import('./widgets/WeatherForecastWidget')) as WidgetComponent;

export const widgetRegistry: Record<WidgetKey, WidgetComponent> = {
  quick_actions: QuickActionsWidget,
  winter_protection: WinterProtectionWidget,
  weather_forecast: WeatherForecastWidget,
  // The remaining widgets share the generic shell until their bespoke REQ-009
  // views land. They still receive their widgetKey/config props.
  active_plants_summary: GenericWidget,
  tasks_today: GenericWidget,
  care_reminders: GenericWidget,
  daily_tip: GenericWidget,
  onboarding_progress: GenericWidget,
  ipm_alerts: GenericWidget,
  harvest_forecast: GenericWidget,
  next_calendar_events: GenericWidget,
  community_activity: GenericWidget,
  tank_status: GenericWidget,
  phase_timeline: GenericWidget,
  plant_grid: GenericWidget,
};

export function getWidgetComponent(widgetKey: string): WidgetComponent | null {
  return (widgetRegistry as Record<string, WidgetComponent>)[widgetKey] ?? null;
}
