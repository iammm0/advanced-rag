"use client";

import { createContext, useCallback, useContext, useEffect, useMemo, useState, type ReactNode } from "react";
import { apiClient, type AgentConfigItem, type Model } from "@/lib/api";

export type AgentDraft = {
  inference_model: string;
  embedding_model: string;
  system_prompt: string;
  enabled: boolean;
};

type DraftMap = Record<string, AgentDraft>;

type Ctx = {
  agents: AgentConfigItem[];
  draft: DraftMap;
  models: Model[];
  modelNames: string[];
  loading: boolean;
  saving: boolean;
  refresh: () => Promise<void>;
  setDraftField: (agentType: string, field: keyof AgentDraft, value: string | boolean) => void;
  saveAgent: (agentType: string) => Promise<boolean>;
  saveAll: () => Promise<boolean>;
  resetPromptBuiltin: (agentType: string) => Promise<boolean>;
  dirtyAgentTypes: string[];
};

const DeepResearchAgentsContext = createContext<Ctx | null>(null);

function draftsEqual(a: AgentDraft, b: AgentDraft) {
  return (
    a.inference_model === b.inference_model &&
    a.embedding_model === b.embedding_model &&
    a.system_prompt === b.system_prompt &&
    a.enabled === b.enabled
  );
}

export function DeepResearchAgentsProvider({ children }: { children: ReactNode }) {
  const [agents, setAgents] = useState<AgentConfigItem[]>([]);
  const [baseline, setBaseline] = useState<DraftMap>({});
  const [draft, setDraft] = useState<DraftMap>({});
  const [models, setModels] = useState<Model[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  const refresh = useCallback(async () => {
    const [cfgRes, mRes] = await Promise.all([apiClient.listAgentConfigs(), apiClient.listModels()]);
    if (mRes.data?.models) setModels(mRes.data.models);
    if (cfgRes.error) throw new Error(cfgRes.error);
    const list = cfgRes.data?.agents || [];
    setAgents(list);
    const d: DraftMap = {};
    for (const a of list) {
      d[a.agent_type] = {
        inference_model: a.inference_model ?? "",
        embedding_model: a.embedding_model ?? "",
        system_prompt: a.system_prompt ?? "",
        enabled: a.enabled,
      };
    }
    setDraft(d);
    setBaseline(d);
  }, []);

  useEffect(() => {
    let m = true;
    setLoading(true);
    refresh()
      .catch(() => {})
      .finally(() => {
        if (m) setLoading(false);
      });
    return () => {
      m = false;
    };
  }, [refresh]);

  const modelNames = useMemo(() => models.map((x) => x.name).sort(), [models]);

  const setDraftField = useCallback((agentType: string, field: keyof AgentDraft, value: string | boolean) => {
    setDraft((prev) => ({
      ...prev,
      [agentType]: { ...prev[agentType], [field]: value },
    }));
  }, []);

  const saveAgent = useCallback(async (agentType: string) => {
    const row = draft[agentType];
    if (!row) return false;
    setSaving(true);
    try {
      const res = await apiClient.updateAgentConfig(agentType, {
        inference_model: row.inference_model.trim() || null,
        embedding_model: row.embedding_model.trim() || null,
        system_prompt: row.system_prompt.trim() || null,
        enabled: row.enabled,
        clear_system_prompt: false,
      });
      if (res.error) throw new Error(res.error);
      await refresh();
      return true;
    } catch {
      return false;
    } finally {
      setSaving(false);
    }
  }, [draft, refresh]);

  const saveAll = useCallback(async () => {
    const types = Object.keys(draft).filter((t) => baseline[t] && !draftsEqual(draft[t], baseline[t]));
    if (types.length === 0) return true;
    setSaving(true);
    try {
      for (const agentType of types) {
        const row = draft[agentType];
        const res = await apiClient.updateAgentConfig(agentType, {
          inference_model: row.inference_model.trim() || null,
          embedding_model: row.embedding_model.trim() || null,
          system_prompt: row.system_prompt.trim() || null,
          enabled: row.enabled,
          clear_system_prompt: false,
        });
        if (res.error) throw new Error(res.error);
      }
      await refresh();
      return true;
    } catch {
      return false;
    } finally {
      setSaving(false);
    }
  }, [draft, baseline, refresh]);

  const resetPromptBuiltin = useCallback(
    async (agentType: string) => {
      setSaving(true);
      try {
        const res = await apiClient.updateAgentConfig(agentType, { clear_system_prompt: true });
        if (res.error) throw new Error(res.error);
        await refresh();
        return true;
      } catch {
        return false;
      } finally {
        setSaving(false);
      }
    },
    [refresh]
  );

  const dirtyAgentTypes = useMemo(() => {
    return Object.keys(draft).filter((t) => baseline[t] && !draftsEqual(draft[t], baseline[t]));
  }, [draft, baseline]);

  const value = useMemo(
    () => ({
      agents,
      draft,
      models,
      modelNames,
      loading,
      saving,
      refresh,
      setDraftField,
      saveAgent,
      saveAll,
      resetPromptBuiltin,
      dirtyAgentTypes,
    }),
    [
      agents,
      draft,
      models,
      modelNames,
      loading,
      saving,
      refresh,
      setDraftField,
      saveAgent,
      saveAll,
      resetPromptBuiltin,
      dirtyAgentTypes,
    ]
  );

  return <DeepResearchAgentsContext.Provider value={value}>{children}</DeepResearchAgentsContext.Provider>;
}

export function useDeepResearchAgents() {
  const v = useContext(DeepResearchAgentsContext);
  if (!v) throw new Error("useDeepResearchAgents must be used within DeepResearchAgentsProvider");
  return v;
}
