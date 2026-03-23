"use client";

import Layout from "@/components/ui/Layout";
import SettingsProviders from "@/components/settings/SettingsProviders";
import ArchitectureFlowPanel from "@/components/settings/flow/ArchitectureFlowPanel";
import RuntimeSettingsPanel from "@/components/settings/RuntimeSettingsPanel";
import MultiAgentSettingsPanel from "@/components/settings/MultiAgentSettingsPanel";

function SettingsContent() {
  return (
    <div className="w-full max-w-full space-y-6">
      <div>
        <h1 className="text-xl font-bold text-gray-900 dark:text-gray-100">高级配置</h1>
        <p className="text-sm text-gray-500 dark:text-gray-400 mt-1 max-w-3xl">
          架构图为只读拓扑；点击节点在弹窗中修改运行时或多智能体选项。深度研究子 Agent 在弹窗内统一编辑后，使用「保存全部」一次提交。
        </p>
      </div>

      <section className="space-y-2" aria-labelledby="arch-heading">
        <h2 id="arch-heading" className="text-sm font-semibold text-gray-700 dark:text-gray-200">
          系统架构（React Flow）
        </h2>
        <ArchitectureFlowPanel />
      </section>

      <details className="group rounded-xl border border-dashed border-gray-200 dark:border-gray-700 bg-gray-50/50 dark:bg-gray-900/30">
        <summary className="cursor-pointer px-4 py-3 text-sm font-medium text-gray-700 dark:text-gray-200 list-none flex items-center justify-between">
          <span>展开备用：完整表单视图（与弹窗同源数据）</span>
          <span className="text-xs text-gray-400 group-open:hidden">点击展开</span>
        </summary>
        <div className="px-4 pb-4 space-y-6 border-t border-gray-100 dark:border-gray-800 pt-4">
          <section className="space-y-2">
            <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wide">运行时</h3>
            <RuntimeSettingsPanel />
          </section>
          <section className="space-y-2">
            <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wide">多智能体</h3>
            <MultiAgentSettingsPanel />
          </section>
        </div>
      </details>
    </div>
  );
}

export default function SettingsPage() {
  return (
    <Layout allowScroll>
      <SettingsProviders>
        <SettingsContent />
      </SettingsProviders>
    </Layout>
  );
}
