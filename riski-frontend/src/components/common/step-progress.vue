<script setup lang="ts">
import type { ExecutionStep } from "@/types/RiskiAnswer.ts";

import { computed } from "vue";

import DocumentChecksTable from "./DocumentChecksTable.vue";

const props = defineProps<{
  steps: ExecutionStep[];
}>();

const documentUrlMap = computed(() => {
  const map = new Map<string, string>();
  for (const step of props.steps) {
    for (const toolCall of step.toolCalls ?? []) {
      for (const doc of toolCall.result?.documents ?? []) {
        if (doc.name && doc.risUrl && !map.has(doc.name)) {
          map.set(doc.name, doc.risUrl);
        }
      }
    }
  }
  return map;
});

const documentCheckUrlMap = computed(() => {
  const map = new Map<string, string>();

  // Include all URLs from the main documentUrlMap
  for (const [name, url] of documentUrlMap.value.entries()) {
    map.set(name, url);
  }

  // Also look for URLs from document checks in tool results
  for (const step of props.steps) {
    for (const check of step.documentChecks ?? []) {
      if (!map.has(check.name)) {
        for (const s of props.steps) {
          for (const toolCall of s.toolCalls ?? []) {
            for (const doc of toolCall.result?.documents ?? []) {
              if (doc.name === check.name && doc.risUrl) {
                map.set(check.name, doc.risUrl);
                break;
              }
            }
          }
        }
      }
    }
  }

  return map;
});

const allChecksFailed = (step: ExecutionStep): boolean => {
  if (!step.documentChecks || step.documentChecks.length === 0) return false;
  return step.documentChecks.every((check) => check.relevant === false);
};

const cloneStep = (step: ExecutionStep): ExecutionStep => ({
  name: step.name,
  displayName: step.displayName,
  status: step.status,
  toolCalls: step.toolCalls
    ? step.toolCalls.map((toolCall) => ({
        ...toolCall,
        result: toolCall.result
          ? {
              documents: [...toolCall.result.documents],
              proposals: [...toolCall.result.proposals],
            }
          : undefined,
      }))
    : undefined,
  documentChecks: step.documentChecks
    ? step.documentChecks.map((check) => ({ ...check }))
    : undefined,
});

const mergeStepInto = (target: ExecutionStep, source: ExecutionStep) => {
  if (source.status === "failed") {
    target.status = "failed";
  } else if (source.status === "running" && target.status !== "failed") {
    target.status = "running";
  } else if (target.status === "running" && source.status === "completed") {
    target.status = "running";
  } else if (target.status !== "failed") {
    target.status = "completed";
  }

  if (source.displayName) {
    target.displayName = source.displayName;
  }

  if (source.toolCalls && source.toolCalls.length > 0) {
    if (!target.toolCalls) target.toolCalls = [];
    const toolCallMap = new Map(
      target.toolCalls.map((tool) => [tool.id, tool])
    );
    for (const tool of source.toolCalls) {
      const existing = toolCallMap.get(tool.id);
      if (existing) {
        existing.status = tool.status;
        if (tool.args) existing.args = tool.args;
        if (tool.result) existing.result = tool.result;
      } else {
        target.toolCalls.push(tool);
        toolCallMap.set(tool.id, tool);
      }
    }
  }

  if (source.documentChecks && source.documentChecks.length > 0) {
    if (!target.documentChecks) target.documentChecks = [];
    const docMap = new Map(
      target.documentChecks.map((check) => [check.name, check])
    );
    for (const check of source.documentChecks) {
      const existing = docMap.get(check.name);
      if (existing) {
        existing.relevant = check.relevant;
        existing.reason = check.reason;
      } else {
        target.documentChecks.push(check);
        docMap.set(check.name, check);
      }
    }
  }
};

const visibleSteps = computed(() => {
  const filtered = props.steps.filter(
    (step) =>
      step.name !== "collect_results" &&
      step.name !== "guard" &&
      step.name !== "tools"
  );

  const mergedSteps: ExecutionStep[] = [];
  const stepMap = new Map<string, ExecutionStep>();

  for (const step of filtered) {
    const existing = stepMap.get(step.name);
    if (!existing) {
      const clone = cloneStep(step);
      mergedSteps.push(clone);
      stepMap.set(step.name, clone);
      continue;
    }
    mergeStepInto(existing, step);
  }

  return mergedSteps;
});

function formatStepName(name: string): string {
  const map: Record<string, string> = {
    retrieve_documents: "Dokumente durchsuchen",
    get_agent_capabilities: "Fähigkeiten abrufen",
    model: "Antwort formulieren",
    guard: "Ergebnisse prüfen",
    check_document: "Ergebnisse prüfen",
    __start__: "Start",
  };
  return map[name] || name;
}

function formatToolName(name: string): string {
  const map: Record<string, string> = {
    retrieve_documents: "Dokumentensuche",
    get_agent_capabilities: "Fähigkeiten abrufen",
  };
  return map[name] || name;
}
</script>

<template>
  <div
    v-if="visibleSteps.length > 0"
    class="steps-container"
  >
    <div
      v-for="step in visibleSteps"
      :key="step.name"
      class="step-item"
      :class="{ 'step-item--zoom': allChecksFailed(step) }"
    >
      <div class="step-header">
        <span class="step-status-icon">
          <template v-if="step.status === 'running'">⏳</template>
          <template v-else-if="step.status === 'completed'">✅</template>
          <template v-else-if="step.status === 'failed'">❌</template>
        </span>
        <span class="step-name">{{
          step.displayName || formatStepName(step.name)
        }}</span>
        <span
          v-if="step.status === 'running'"
          class="step-running-hint"
          >läuft…</span
        >
      </div>

      <div
        v-if="step.toolCalls && step.toolCalls.length > 0"
        class="step-tools"
      >
        <div
          v-for="tool in step.toolCalls"
          :key="tool.id"
          class="tool-call"
        >
          <div class="tool-summary">
            <span class="tool-status-icon">
              <template v-if="tool.status === 'running'">🔄</template>
              <template v-else>✔️</template>
            </span>
            {{ formatToolName(tool.name) }}
            <span
              v-if="tool.args"
              class="tool-args"
              >– „{{ tool.args }}"</span
            >
          </div>
        </div>
      </div>

      <!-- Per-document relevance checks (guard step) -->
      <document-checks-table
        v-if="step.documentChecks && step.documentChecks.length > 0"
        :document-checks="step.documentChecks"
        :document-url-map="documentCheckUrlMap"
      />
    </div>
  </div>
</template>

<style scoped>
.steps-container {
  display: flex;
  flex-direction: column;
  gap: 6px;
  margin-bottom: 16px;
}

.step-item {
  padding: 6px 10px;
  background-color: #f9f9f9;
  border: 1px solid #eee;
  border-radius: 6px;
  transition:
    transform 0.2s ease,
    box-shadow 0.2s ease;
}

.step-item--zoom {
  transform: scale(1.02);
  box-shadow: 0 6px 14px rgba(0, 90, 159, 0.12);
  border-color: #c7d7ea;
  background-color: #f3f7fb;
}

.step-header {
  display: flex;
  align-items: center;
}

.step-status-icon {
  margin-right: 8px;
  min-width: 20px;
  text-align: center;
}

.step-name {
  font-weight: 500;
}

.step-running-hint {
  font-size: 0.85em;
  color: #888;
  margin-left: 6px;
  animation: pulse 1.5s ease-in-out infinite;
}

@keyframes pulse {
  0%,
  100% {
    opacity: 1;
  }

  50% {
    opacity: 0.4;
  }
}

.step-tools {
  margin-top: 4px;
  padding-left: 28px;
}

.tool-call {
  margin-bottom: 4px;
}

.tool-summary {
  font-size: 0.92em;
  color: #444;
}

.tool-status-icon {
  margin-right: 4px;
}

.tool-args {
  color: #888;
  font-style: italic;
}
</style>
