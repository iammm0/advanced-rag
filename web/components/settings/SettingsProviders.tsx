"use client";

import type { ReactNode } from "react";
import { RuntimeSettingsProvider } from "@/contexts/RuntimeSettingsContext";
import { DeepResearchAgentsProvider } from "@/contexts/DeepResearchAgentsContext";

export default function SettingsProviders({ children }: { children: ReactNode }) {
  return (
    <RuntimeSettingsProvider>
      <DeepResearchAgentsProvider>{children}</DeepResearchAgentsProvider>
    </RuntimeSettingsProvider>
  );
}
