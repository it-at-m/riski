<script setup lang="ts">
import type { ExecutionStep } from "@/types/RiskiAnswer.ts";

import { computed, ref } from "vue";

import ToolResultList from "./ToolResultList.vue";

const props = defineProps<{
  steps: ExecutionStep[];
}>();

const showReasons = ref(false);

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

const hasReasoning = computed(() =>
  props.steps.some((step) =>
    step.documentChecks?.some((check) => check.reason && check.reason !== "")
  )
);

const allChecksFailed = (step: ExecutionStep): boolean => {
  if (!step.documentChecks || step.documentChecks.length === 0) return false;
  return step.documentChecks.every((check) => check.relevant === false);
};

const resolveDocUrl = (name: string): string | undefined =>
  documentUrlMap.value.get(name);

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

          <!-- Show retrieved documents & proposals from tool result (live) -->
          <ToolResultList
            v-if="
              tool.result &&
              ((tool.result.proposals && tool.result.proposals.length > 0) ||
                (tool.result.documents && tool.result.documents.length > 0))
            "
            :result="tool.result"
          />
        </div>
      </div>

      <!-- Per-document relevance checks (guard step) -->
      <div
        v-if="step.documentChecks && step.documentChecks.length > 0"
        class="step-doc-checks"
      >
        <div class="doc-checks-header-row">
          <span class="doc-checks-title">Dokumentprüfung</span>
          <button
            v-if="hasReasoning"
            type="button"
            class="doc-checks-toggle"
            @click="showReasons = !showReasons"
          >
            {{ showReasons ? "Begründung ausblenden" : "Begründung anzeigen" }}
          </button>
        </div>
        <div
          class="doc-checks-grid"
          role="table"
        >
          <div
            class="doc-checks-header"
            role="row"
          >
            <div
              class="doc-checks-cell doc-checks-label"
              role="columnheader"
            >
              Dokument
            </div>
            <div
              class="doc-checks-cell doc-checks-label"
              role="columnheader"
            >
              Relevant
            </div>
            <div
              v-if="showReasons"
              class="doc-checks-cell doc-checks-label"
              role="columnheader"
            >
              Begründung
            </div>
          </div>
          <div
            v-for="(check, ci) in step.documentChecks"
            :key="ci"
            class="doc-checks-row"
            role="row"
          >
            <div
              class="doc-checks-cell doc-check-name"
              role="cell"
            >
              <a
                v-if="resolveDocUrl(check.name)"
                :href="resolveDocUrl(check.name)"
                target="_blank"
                rel="noopener noreferrer"
                class="doc-check-link"
              >
                {{ check.name }}
              </a>
              <span v-else>{{ check.name }}</span>
            </div>
            <div
              class="doc-checks-cell doc-check-status"
              role="cell"
            >
              <span class="doc-check-icon">
                <template v-if="check.relevant">✅</template>
                <template v-else>❌</template>
              </span>
              <span>{{ check.relevant ? "Ja" : "Nein" }}</span>
            </div>
            <div
              v-if="showReasons"
              class="doc-checks-cell doc-check-reason"
              role="cell"
            >
              {{ check.reason || "–" }}
            </div>
          </div>
        </div>
      </div>
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

.step-doc-checks {
  margin-top: 4px;
  padding-left: 28px;
}

.doc-checks-header-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  margin-bottom: 4px;
}

.doc-checks-title {
  font-size: 0.88em;
  font-weight: 600;
  color: #555;
}

.doc-checks-toggle {
  border: none;
  background: none;
  color: #555;
  font-size: 0.82em;
  cursor: pointer;
  padding: 0;
}

.doc-checks-toggle:hover {
  color: #333;
}

.doc-checks-grid {
  display: grid;
  gap: 2px;
  font-size: 0.86em;
  color: #444;
}

.doc-checks-header,
.doc-checks-row {
  display: grid;
  grid-template-columns: minmax(140px, 2fr) minmax(80px, 0.7fr) minmax(
      140px,
      2fr
    );
  align-items: center;
  gap: 6px;
  padding: 3px 6px;
  border-radius: 4px;
}

.doc-checks-header {
  background: #f2f2f2;
  font-size: 0.84em;
  text-transform: uppercase;
  letter-spacing: 0.02em;
  color: #666;
}

.doc-checks-row {
  background: #fff;
  border: 1px solid #eee;
}

.doc-checks-cell {
  display: flex;
  align-items: center;
  gap: 6px;
  min-width: 0;
}

.doc-checks-label {
  font-weight: 600;
}

.doc-check-icon {
  min-width: 18px;
  text-align: center;
  flex-shrink: 0;
}

.doc-check-name {
  font-weight: 500;
}

.doc-check-status {
  font-weight: 500;
}

.doc-check-reason {
  color: #666;
  font-style: italic;
}

.doc-check-link {
  color: #005a9f;
  text-decoration: none;
}

.doc-check-link:hover {
  text-decoration: underline;
  color: #003d6e;
}
</style>
