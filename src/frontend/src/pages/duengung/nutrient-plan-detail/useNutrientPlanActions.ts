import { useState, useCallback, useMemo } from 'react';
import { useTranslation } from 'react-i18next';
import { useNotification } from '@/hooks/useNotification';
import { useApiError } from '@/hooks/useApiError';
import type { ChannelPreset } from '@/pages/giessprotokoll/WateringLogCreateDialog';
import * as planApi from '@/api/endpoints/nutrient-plans';
import type { FertilizerRemoveAllPayload } from '../FertilizerGanttChart';
import type { DosageEntry } from '../ChannelFertilizerDialog';
import type {
  NutrientPlan,
  NutrientPlanPhaseEntry,
  Fertilizer,
  DeliveryChannel,
  DeliveryChannelCreate,
  FertilizerDosage,
} from '@/api/types';

interface UseNutrientPlanActionsArgs {
  key: string | undefined;
  plan: NutrientPlan | null;
  entries: NutrientPlanPhaseEntry[];
  fertilizers: Fertilizer[];
  /** Silent/loud reload of the plan data owned by {@link useNutrientPlanData}. */
  load: (silent?: boolean) => Promise<void>;
}

/**
 * Write-side controller for the nutrient-plan detail page (AP-20). Owns every
 * phase-entry / delivery-channel / fertilizer-dosage dialog's view-state and the
 * async mutation handlers that refresh the page (via the injected `load`) after a
 * change, plus the row-expansion state and the watering-log dialog. Behaviour is a
 * verbatim extraction of the former inline controller — no logic changes.
 */
export function useNutrientPlanActions({ key, plan, entries, fertilizers, load }: UseNutrientPlanActionsArgs) {
  const { t } = useTranslation();
  const notification = useNotification();
  const { handleError } = useApiError();

  // Phase entry dialog state
  const [entryDialogOpen, setEntryDialogOpen] = useState(false);
  const [editingEntry, setEditingEntry] = useState<NutrientPlanPhaseEntry | null>(null);
  const [deleteEntryOpen, setDeleteEntryOpen] = useState(false);
  const [deletingEntry, setDeletingEntry] = useState<NutrientPlanPhaseEntry | null>(null);

  // DeliveryChannel dialog state
  const [channelDialogOpen, setChannelDialogOpen] = useState(false);
  const [channelDialogEntryKey, setChannelDialogEntryKey] = useState<string>('');
  const [channelDialogExistingIds, setChannelDialogExistingIds] = useState<string[]>([]);
  const [editingChannel, setEditingChannel] = useState<DeliveryChannel | null>(null);

  // Channel fertilizer dialog state
  const [fertDialogOpen, setFertDialogOpen] = useState(false);
  const [fertDialogEntryKey, setFertDialogEntryKey] = useState<string>('');
  const [fertDialogChannelId, setFertDialogChannelId] = useState<string>('');
  const [fertDialogExistingKeys, setFertDialogExistingKeys] = useState<string[]>([]);
  const [editingFertDosage, setEditingFertDosage] = useState<FertilizerDosage | null>(null);

  // Channel delete confirm
  const [deleteChannelOpen, setDeleteChannelOpen] = useState(false);
  const [deletingChannelEntryKey, setDeletingChannelEntryKey] = useState<string>('');
  const [deletingChannelId, setDeletingChannelId] = useState<string>('');

  // Remove fertilizer from all entries/channels confirm
  const [removeFertAllOpen, setRemoveFertAllOpen] = useState(false);
  const [removeFertAllPayload, setRemoveFertAllPayload] = useState<FertilizerRemoveAllPayload | null>(null);

  // Watering log dialog state
  const [wateringLogOpen, setWateringLogOpen] = useState(false);
  const [wateringLogChannel, setWateringLogChannel] = useState<ChannelPreset | undefined>(undefined);

  // Expanded rows for fertilizer dosages
  const [expandedEntries, setExpandedEntries] = useState<Set<string>>(new Set());

  const onDeleteEntry = useCallback(async () => {
    if (!key || !deletingEntry) return;
    try {
      await planApi.deletePhaseEntry(key, deletingEntry.key);
      notification.success(t('common.delete'));
      setDeleteEntryOpen(false);
      setDeletingEntry(null);
      load(true);
    } catch (err) {
      handleError(err);
    }
  }, [key, deletingEntry, notification, t, load, handleError]);

  const toggleExpanded = useCallback((entryKey: string) => {
    setExpandedEntries((prev) => {
      const next = new Set(prev);
      if (next.has(entryKey)) {
        next.delete(entryKey);
      } else {
        next.add(entryKey);
      }
      return next;
    });
  }, []);

  const onRemoveChannelFertilizer = useCallback(async (entryKey: string, channelId: string, fertilizerKey: string) => {
    try {
      await planApi.removeFertilizerFromChannel(entryKey, channelId, fertilizerKey);
      notification.success(t('common.delete'));
      load(true);
    } catch (err) {
      handleError(err);
    }
  }, [notification, t, load, handleError]);

  const onConfirmRemoveFertilizerFromAll = useCallback(async () => {
    if (!removeFertAllPayload) return;
    try {
      await Promise.all(
        removeFertAllPayload.targets.map((tgt) =>
          planApi.removeFertilizerFromChannel(tgt.entryKey, tgt.channelId, removeFertAllPayload.fertilizerKey),
        ),
      );
      notification.success(t('common.delete'));
      load(true);
    } catch (err) {
      handleError(err);
    } finally {
      setRemoveFertAllOpen(false);
      setRemoveFertAllPayload(null);
    }
  }, [removeFertAllPayload, notification, t, load, handleError]);

  const onSaveChannel = useCallback(async (channel: DeliveryChannelCreate) => {
    if (!key || !channelDialogEntryKey) return;
    try {
      const entry = entries.find((e) => e.key === channelDialogEntryKey);
      if (!entry) return;
      const existing = entry.delivery_channels.find((ch) => ch.channel_id === channel.channel_id);
      const merged = {
        ...channel,
        fertilizer_dosages: channel.fertilizer_dosages ?? existing?.fertilizer_dosages ?? [],
      };
      const updatedChannels = [
        ...entry.delivery_channels.filter((ch) => ch.channel_id !== channel.channel_id),
        merged,
      ];
      await planApi.updatePhaseEntry(key, channelDialogEntryKey, {
        delivery_channels: updatedChannels,
      });
      notification.success(t('common.save'));
      setChannelDialogOpen(false);
      setEditingChannel(null);
      load(true);
    } catch (err) {
      handleError(err);
    }
  }, [key, channelDialogEntryKey, entries, notification, t, load, handleError]);

  const onEditChannel = useCallback((entryKey: string, channel: DeliveryChannel) => {
    setChannelDialogEntryKey(entryKey);
    const entry = entries.find((e) => e.key === entryKey);
    setChannelDialogExistingIds(
      entry?.delivery_channels
        .filter((ch) => ch.channel_id !== channel.channel_id)
        .map((ch) => ch.channel_id) ?? [],
    );
    setEditingChannel(channel);
    setChannelDialogOpen(true);
  }, [entries]);

  const onDeleteChannel = useCallback(async () => {
    if (!key || !deletingChannelEntryKey || !deletingChannelId) return;
    try {
      const entry = entries.find((e) => e.key === deletingChannelEntryKey);
      if (!entry) return;
      const updatedChannels = entry.delivery_channels.filter(
        (ch) => ch.channel_id !== deletingChannelId,
      );
      await planApi.updatePhaseEntry(key, deletingChannelEntryKey, {
        delivery_channels: updatedChannels,
      });
      notification.success(t('common.delete'));
      setDeleteChannelOpen(false);
      setDeletingChannelId('');
      setDeletingChannelEntryKey('');
      load(true);
    } catch (err) {
      handleError(err);
    }
  }, [key, deletingChannelEntryKey, deletingChannelId, entries, notification, t, load, handleError]);

  const handleEntriesChange = useCallback(
    async (updatedEntries: NutrientPlanPhaseEntry[]) => {
      if (!key) return;
      try {
        const promises = updatedEntries
          .filter((updated) => {
            const original = entries.find((e) => e.key === updated.key);
            if (!original) return false;
            return JSON.stringify(original.delivery_channels) !== JSON.stringify(updated.delivery_channels);
          })
          .map((e) =>
            planApi.updatePhaseEntry(key, e.key, {
              delivery_channels: e.delivery_channels,
            }),
          );
        if (promises.length > 0) {
          await Promise.all(promises);
          load(true);
        }
      } catch (err) {
        handleError(err);
      }
    },
    [key, entries, load, handleError],
  );

  const onAddChannelFertilizer = useCallback((entryKey: string, channelId: string) => {
    const entry = entries.find((e) => e.key === entryKey);
    const channel = entry?.delivery_channels.find((ch) => ch.channel_id === channelId);
    setFertDialogEntryKey(entryKey);
    setFertDialogChannelId(channelId);
    setFertDialogExistingKeys(
      channel?.fertilizer_dosages.map((d) => d.fertilizer_key) ?? [],
    );
    setEditingFertDosage(null);
    setFertDialogOpen(true);
  }, [entries]);

  const onEditChannelFertilizer = useCallback((entryKey: string, channelId: string, dosage: FertilizerDosage) => {
    const entry = entries.find((e) => e.key === entryKey);
    const channel = entry?.delivery_channels.find((ch) => ch.channel_id === channelId);
    setFertDialogEntryKey(entryKey);
    setFertDialogChannelId(channelId);
    setFertDialogExistingKeys(
      channel?.fertilizer_dosages.map((d) => d.fertilizer_key) ?? [],
    );
    setEditingFertDosage(dosage);
    setFertDialogOpen(true);
  }, [entries]);

  const onSaveChannelFertilizer = useCallback(async (items: DosageEntry[]) => {
    try {
      if (editingFertDosage) {
        await planApi.removeFertilizerFromChannel(
          fertDialogEntryKey,
          fertDialogChannelId,
          editingFertDosage.fertilizer_key,
        );
      }
      for (const item of items) {
        await planApi.addFertilizerToChannel(fertDialogEntryKey, fertDialogChannelId, item);
      }
      notification.success(t('common.save'));
      setFertDialogOpen(false);
      setEditingFertDosage(null);
      load(true);
    } catch (err) {
      handleError(err);
    }
  }, [editingFertDosage, fertDialogEntryKey, fertDialogChannelId, notification, t, load, handleError]);

  const openAddEntry = useCallback(() => {
    setEditingEntry(null);
    setEntryDialogOpen(true);
  }, []);

  const openEditEntry = useCallback((entry: NutrientPlanPhaseEntry) => {
    setEditingEntry(entry);
    setEntryDialogOpen(true);
  }, []);

  const openDeleteEntry = useCallback((entry: NutrientPlanPhaseEntry) => {
    setDeletingEntry(entry);
    setDeleteEntryOpen(true);
  }, []);

  const openAddChannel = useCallback((entryKey: string, existingIds: string[]) => {
    setChannelDialogEntryKey(entryKey);
    setChannelDialogExistingIds(existingIds);
    setEditingChannel(null);
    setChannelDialogOpen(true);
  }, []);

  const openDeleteChannel = useCallback((entryKey: string, channelId: string) => {
    setDeletingChannelEntryKey(entryKey);
    setDeletingChannelId(channelId);
    setDeleteChannelOpen(true);
  }, []);

  const onRemoveFertilizerFromGantt = useCallback((fertilizerKey: string, isAuto: boolean, entriesSubset: NutrientPlanPhaseEntry[]) => {
    const autoMethods = new Set(['fertigation']);
    const targets: { entryKey: string; channelId: string }[] = [];
    for (const entry of entriesSubset) {
      for (const ch of entry.delivery_channels) {
        const chIsAuto = autoMethods.has(ch.application_method);
        if (chIsAuto !== isAuto) continue;
        if (ch.fertilizer_dosages.some((d) => d.fertilizer_key === fertilizerKey)) {
          targets.push({ entryKey: entry.key, channelId: ch.channel_id });
        }
      }
    }
    if (targets.length === 0) return;
    const fert = fertilizers.find((f) => f.key === fertilizerKey);
    setRemoveFertAllPayload({
      fertilizerKey,
      fertilizerName: fert?.product_name ?? fertilizerKey,
      targets,
    });
    setRemoveFertAllOpen(true);
  }, [fertilizers]);

  const onLogWatering = useCallback((ch: DeliveryChannel) => {
    const volumeLiters = ch.method_params
      ? ch.method_params.method === 'drench'
        ? ch.method_params.volume_per_feeding_liters
        : ch.method_params.method === 'foliar'
          ? ch.method_params.volume_per_spray_liters
          : null
      : null;
    setWateringLogChannel({
      channelId: ch.channel_id,
      channelLabel: ch.label || ch.channel_id,
      nutrientPlanKey: plan!.key,
      applicationMethod: ch.application_method as 'fertigation' | 'drench' | 'foliar' | 'top_dress',
      targetEcMs: ch.target_ec_ms,
      targetPh: ch.target_ph,
      fertilizers: ch.fertilizer_dosages
        .filter((d) => !d.optional)
        .sort((a, b) => a.mixing_order - b.mixing_order)
        .map((d) => ({ fertilizer_key: d.fertilizer_key, ml_per_liter: d.ml_per_liter })),
      volumeLiters,
    });
    setWateringLogOpen(true);
  }, [plan]);

  const closeEntryDialog = useCallback(() => {
    setEntryDialogOpen(false);
    setEditingEntry(null);
  }, []);

  const onEntrySaved = useCallback(() => {
    setEntryDialogOpen(false);
    setEditingEntry(null);
    load(true);
  }, [load]);

  const closeChannelDialog = useCallback(() => {
    setChannelDialogOpen(false);
    setEditingChannel(null);
  }, []);

  const closeFertDialog = useCallback(() => {
    setFertDialogOpen(false);
    setEditingFertDosage(null);
  }, []);

  const cancelDeleteEntry = useCallback(() => {
    setDeleteEntryOpen(false);
    setDeletingEntry(null);
  }, []);

  const cancelDeleteChannel = useCallback(() => {
    setDeleteChannelOpen(false);
    setDeletingChannelId('');
    setDeletingChannelEntryKey('');
  }, []);

  const cancelRemoveFertAll = useCallback(() => {
    setRemoveFertAllOpen(false);
    setRemoveFertAllPayload(null);
  }, []);

  const closeWateringLog = useCallback(() => {
    setWateringLogOpen(false);
    setWateringLogChannel(undefined);
  }, []);

  const onWateringLogged = useCallback(() => {
    setWateringLogOpen(false);
    setWateringLogChannel(undefined);
    notification.success(t('pages.wateringLogs.logged'));
  }, [notification, t]);

  return useMemo(
    () => ({
      expandedEntries, toggleExpanded,
      openAddEntry, openEditEntry, openDeleteEntry, openAddChannel, onEditChannel, openDeleteChannel,
      onAddChannelFertilizer, onEditChannelFertilizer, onRemoveChannelFertilizer, onRemoveFertilizerFromGantt,
      handleEntriesChange, onLogWatering,
      entryDialogOpen, editingEntry, closeEntryDialog, onEntrySaved,
      deleteEntryOpen, deletingEntry, onDeleteEntry, cancelDeleteEntry,
      channelDialogOpen, editingChannel, channelDialogExistingIds, onSaveChannel, closeChannelDialog,
      deleteChannelOpen, deletingChannelId, onDeleteChannel, cancelDeleteChannel,
      removeFertAllOpen, removeFertAllPayload, onConfirmRemoveFertilizerFromAll, cancelRemoveFertAll,
      fertDialogOpen, editingFertDosage, fertDialogExistingKeys, onSaveChannelFertilizer, closeFertDialog,
      wateringLogOpen, wateringLogChannel, onWateringLogged, closeWateringLog,
    }),
    [
      expandedEntries, toggleExpanded,
      openAddEntry, openEditEntry, openDeleteEntry, openAddChannel, onEditChannel, openDeleteChannel,
      onAddChannelFertilizer, onEditChannelFertilizer, onRemoveChannelFertilizer, onRemoveFertilizerFromGantt,
      handleEntriesChange, onLogWatering,
      entryDialogOpen, editingEntry, closeEntryDialog, onEntrySaved,
      deleteEntryOpen, deletingEntry, onDeleteEntry, cancelDeleteEntry,
      channelDialogOpen, editingChannel, channelDialogExistingIds, onSaveChannel, closeChannelDialog,
      deleteChannelOpen, deletingChannelId, onDeleteChannel, cancelDeleteChannel,
      removeFertAllOpen, removeFertAllPayload, onConfirmRemoveFertilizerFromAll, cancelRemoveFertAll,
      fertDialogOpen, editingFertDosage, fertDialogExistingKeys, onSaveChannelFertilizer, closeFertDialog,
      wateringLogOpen, wateringLogChannel, onWateringLogged, closeWateringLog,
    ],
  );
}
