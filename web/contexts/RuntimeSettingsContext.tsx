"use client";

import { createContext, useCallback, useContext, useEffect, useMemo, useState, type ReactNode } from "react";
import { apiClient, type RuntimeConfigResponse, type RuntimeMode } from "@/lib/api";

type Ctx = {
  config: RuntimeConfigResponse | null;
  loading: boolean;
  saving: boolean;
  error: string | null;
  refresh: () => Promise<void>;
  applyPreset: (mode: RuntimeMode) => Promise<boolean>;
  saveModules: (patch: Record<string, boolean>) => Promise<boolean>;
  saveParams: (patch: Record<string, unknown>) => Promise<boolean>;
  setLocalConfig: (updater: (prev: RuntimeConfigResponse | null) => RuntimeConfigResponse | null) => void;
};

const RuntimeSettingsContext = createContext<Ctx | null>(null);

export function RuntimeSettingsProvider({ children }: { children: ReactNode }) {
  const [config, setConfig] = useState<RuntimeConfigResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    setError(null);
    const res = await apiClient.getRuntimeSettings();
    if (res.error) {
      setError(res.error);
      return;
    }
    if (res.data) setConfig(res.data);
  }, []);

  useEffect(() => {
    let m = true;
    setLoading(true);
    refresh().finally(() => {
      if (m) setLoading(false);
    });
    return () => {
      m = false;
    };
  }, [refresh]);

  const applyPreset = useCallback(async (mode: RuntimeMode) => {
    setSaving(true);
    try {
      const res = await apiClient.updateRuntimeSettings({ mode });
      if (res.error) throw new Error(res.error);
      if (res.data) setConfig(res.data);
      return true;
    } catch {
      return false;
    } finally {
      setSaving(false);
    }
  }, []);

  const saveModules = useCallback(
    async (patch: Record<string, boolean>) => {
      if (!config) return false;
      setSaving(true);
      try {
        const modules = { ...(config.modules || {}), ...patch };
        const res = await apiClient.updateRuntimeSettings({ mode: "custom", modules });
        if (res.error) throw new Error(res.error);
        if (res.data) setConfig(res.data);
        return true;
      } catch {
        return false;
      } finally {
        setSaving(false);
      }
    },
    [config]
  );

  const saveParams = useCallback(
    async (patch: Record<string, unknown>) => {
      if (!config) return false;
      setSaving(true);
      try {
        const params = { ...(config.params || {}), ...patch };
        const res = await apiClient.updateRuntimeSettings({ mode: "custom", params });
        if (res.error) throw new Error(res.error);
        if (res.data) setConfig(res.data);
        return true;
      } catch {
        return false;
      } finally {
        setSaving(false);
      }
    },
    [config]
  );

  const setLocalConfig = useCallback((updater: (prev: RuntimeConfigResponse | null) => RuntimeConfigResponse | null) => {
    setConfig(updater);
  }, []);

  const value = useMemo(
    () => ({
      config,
      loading,
      saving,
      error,
      refresh,
      applyPreset,
      saveModules,
      saveParams,
      setLocalConfig,
    }),
    [config, loading, saving, error, refresh, applyPreset, saveModules, saveParams, setLocalConfig]
  );

  return <RuntimeSettingsContext.Provider value={value}>{children}</RuntimeSettingsContext.Provider>;
}

export function useRuntimeSettings() {
  const v = useContext(RuntimeSettingsContext);
  if (!v) throw new Error("useRuntimeSettings must be used within RuntimeSettingsProvider");
  return v;
}
