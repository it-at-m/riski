<script setup lang="ts">
import type { ExecutionStep } from "@/types/RiskiAnswer.ts";

import { computed, ref } from "vue";

import DocumentChecksTable from "./DocumentChecksTable.vue";

const props = defineProps<{
  steps: ExecutionStep[];
}>();

const showCheckDetails = ref(false);

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

  for (const [name, url] of documentUrlMap.value.entries()) {
    map.set(name, url);
  }

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

/**
 * Maps the real step sequence (model → tools → model) to the three fixed
 * progress sections shown in the UI.
 *
 * Real structure:
 *   steps[0]: model  (displayName "Denke nach")      → ignored / pre-phase
 *   steps[1]: tools  (toolCalls: retrieve_documents)  → Archivsuche
 *   steps[2]: model  (displayName "Antwort generieren") → Antworterstellung
 *
 * Ergebnisprüfung: any step (usually tools or a dedicated step) that carries
 * documentChecks, OR the tools step itself once documents are retrieved.
 */
const progressSections = computed(() => {
  const allSteps = props.steps;

  const statusToProgress = (status?: string): number => {
    if (status === "completed") return 100;
    if (status === "running") return 60;
    return 0;
  };

  // Archivsuche: prefer the tools step that actually has a retrieve_documents
  // toolCall (arrives later); fall back to the last tools step seen so far.
  const toolsSteps = allSteps.filter((s) => s.name === "tools");
  const archiveStep =
    toolsSteps.findLast((s) =>
      s.toolCalls?.some((tc) => tc.name === "retrieve_documents")
    ) ?? toolsSteps[toolsSteps.length - 1];

  // Ergebnisprüfung: any step with documentChecks, or a check_document step
  const checkStep = allSteps.find(
    (s) =>
      (s.documentChecks && s.documentChecks.length > 0) ||
      s.name === "check_document"
  );

  // Antworterstellung: the LAST model step (the one that generates the answer)
  const modelSteps = allSteps.filter((s) => s.name === "model");
  // Antworterstellung: only the model step that comes AFTER the tools step.
  // We identify it by position: find the index of the last tools step, then
  // take the first model step that appears after it. This prevents the early
  // "Denke nach" model step from driving the Antworterstellung bar.
  const lastToolsIndex = allSteps.map((s) => s.name).lastIndexOf("tools");
  const answerStep =
    lastToolsIndex >= 0
      ? allSteps.slice(lastToolsIndex + 1).find((s) => s.name === "model")
      : modelSteps[modelSteps.length - 1];

  const checkProgress = (() => {
    if (!checkStep) return 0;
    if (checkStep.status === "completed") return 100;
    if (checkStep.documentChecks && checkStep.documentChecks.length > 0) {
      const total = checkStep.documentChecks.length;
      const done = checkStep.documentChecks.filter(
        (c) => c.relevant !== undefined
      ).length;
      if (checkStep.status === "running") {
        return Math.max(10, Math.round((done / total) * 100));
      }
    }
    return statusToProgress(checkStep.status);
  })();

  return [
    {
      label: "Archivsuche",
      progress: statusToProgress(archiveStep?.status),
      status: archiveStep?.status,
      step: archiveStep,
      hasChecks: false,
    },
    {
      label: "Ergebnisprüfung",
      progress: checkProgress,
      status: checkStep?.status,
      step: checkStep,
      hasChecks: (checkStep?.documentChecks?.length ?? 0) > 0,
    },
    {
      label: "Antworterstellung",
      progress: statusToProgress(answerStep?.status),
      status: answerStep?.status,
      step: answerStep,
      hasChecks: false,
    },
  ];
});
</script>

<template>
  <div
    v-if="props.steps.length > 0"
    class="progress-container"
  >
    <div
      v-for="section in progressSections"
      :key="section.label"
      class="progress-section"
    >
      <div class="progress-label">{{ section.label }}</div>

      <div class="progress-bar-track">
        <div
          class="progress-bar-fill"
          :class="{
            'progress-bar-fill--running': section.status === 'running',
            'progress-bar-fill--failed': section.status === 'failed',
          }"
          :style="{ width: section.progress + '%' }"
        />
      </div>

      <div
        v-if="section.label === 'Ergebnisprüfung'"
        class="check-details-toggle"
      >
        <button
          class="toggle-btn"
          @click="showCheckDetails = !showCheckDetails"
        >
          Details zur Prüfung
          <span class="toggle-icon">{{ showCheckDetails ? "▲" : "▼" }}</span>
        </button>

        <div
          v-if="showCheckDetails && section.step?.documentChecks?.length"
          class="check-details"
        >
          <document-checks-table
            :document-checks="section.step.documentChecks!"
            :document-url-map="documentCheckUrlMap"
          />
        </div>

        <div
          v-else-if="showCheckDetails"
          class="check-details check-details--empty"
        >
          Noch keine Prüfergebnisse verfügbar.
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.progress-container {
  padding: 20px 24px;
  background-color: #ffffff;
  font-family: "Source Sans Pro", "Segoe UI", sans-serif;
  max-width: 680px;
}

.progress-title {
  font-size: 1.4rem;
  font-weight: 700;
  color: #1a3a5c;
  margin: 0 0 24px 0;
}

.progress-section {
  margin-bottom: 20px;
}

.progress-label {
  font-size: 0.95rem;
  font-weight: 700;
  color: #1a3a5c;
  margin-bottom: 6px;
}

.progress-bar-track {
  width: 100%;
  height: 8px;
  background-color: #d6e2ef;
  border-radius: 4px;
  overflow: hidden;
}

.progress-bar-fill {
  height: 100%;
  background-color: #005a9f;
  border-radius: 4px;
  transition: width 0.5s ease;
}

.progress-bar-fill--running {
  background-color: #005a9f;
  /* animated shimmer for running state */
  background-image: linear-gradient(
    90deg,
    #005a9f 0%,
    #0074cc 50%,
    #005a9f 100%
  );
  background-size: 200% 100%;
  animation: shimmer 1.5s infinite;
}

.progress-bar-fill--failed {
  background-color: #c0392b;
}

@keyframes shimmer {
  0% {
    background-position: 200% 0;
  }
  100% {
    background-position: -200% 0;
  }
}

.check-details-toggle {
  margin-top: 6px;
}

.toggle-btn {
  background: none;
  border: none;
  color: #005a9f;
  font-size: 0.88rem;
  cursor: pointer;
  padding: 0;
  display: flex;
  align-items: center;
  gap: 4px;
  text-decoration: none;
}

.toggle-btn:hover {
  text-decoration: underline;
}

.toggle-icon {
  font-size: 0.75rem;
}

.check-details {
  margin-top: 8px;
  padding: 8px;
  background: #f3f7fb;
  border: 1px solid #c7d7ea;
  border-radius: 6px;
}

.check-details--empty {
  font-size: 0.88rem;
  color: #888;
  font-style: italic;
}
</style>
