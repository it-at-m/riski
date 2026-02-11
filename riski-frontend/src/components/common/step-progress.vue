<script setup lang="ts">
import type Document from "@/types/Document.ts";
import type Proposal from "@/types/Proposal.ts";
import type { ExecutionStep } from "@/types/RiskiAnswer.ts";

defineProps<{
  steps: ExecutionStep[];
}>();

function formatStepName(name: string): string {
  const map: Record<string, string> = {
    retrieve_documents: "Dokumente suchen",
    model: "Antwort generieren",
    tools: "Werkzeuge verwenden",
    __start__: "Start",
  };
  return map[name] || name;
}

function formatToolName(name: string): string {
  const map: Record<string, string> = {
    retrieve_documents: "Dokumentensuche",
  };
  return map[name] || name;
}

function truncate(text: string, maxLength: number = 60): string {
  return text.length > maxLength ? text.slice(0, maxLength) + "…" : text;
}
</script>

<template>
  <div
    v-if="steps.length > 0"
    class="steps-container"
  >
    <div
      v-for="step in steps"
      :key="step.name"
      class="step-item"
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
          <details :open="tool.status === 'running'">
            <summary class="tool-summary">
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
            </summary>

            <!-- Results: retrieved documents -->
            <div
              v-if="tool.result?.documents && tool.result.documents.length > 0"
              class="tool-results"
            >
              <span class="result-label"
                >Gefundene Dokumente ({{ tool.result.documents.length }}):</span
              >
              <ul class="result-list">
                <li
                  v-for="doc in tool.result.documents"
                  :key="doc.risUrl || doc.name"
                >
                  <a
                    v-if="doc.risUrl"
                    :href="doc.risUrl"
                    target="_blank"
                    rel="noopener noreferrer"
                    class="result-link"
                    :title="doc.name"
                    >{{ truncate(doc.name) }}</a
                  >
                  <span v-else>{{ truncate(doc.name) }}</span>
                </li>
              </ul>
            </div>

            <!-- Results: retrieved proposals -->
            <div
              v-if="tool.result?.proposals && tool.result.proposals.length > 0"
              class="tool-results"
            >
              <span class="result-label"
                >Gefundene Anträge ({{ tool.result.proposals.length }}):</span
              >
              <ul class="result-list">
                <li
                  v-for="proposal in tool.result.proposals"
                  :key="proposal.identifier"
                >
                  <a
                    v-if="proposal.risUrl"
                    :href="proposal.risUrl"
                    target="_blank"
                    rel="noopener noreferrer"
                    class="result-link"
                    :title="proposal.name"
                    >{{ proposal.identifier }} –
                    {{ truncate(proposal.name) }}</a
                  >
                  <span v-else
                    >{{ proposal.identifier }} –
                    {{ truncate(proposal.name) }}</span
                  >
                </li>
              </ul>
            </div>
          </details>
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
  cursor: pointer;
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

.tool-results {
  margin-top: 4px;
  padding-left: 8px;
  font-size: 0.88em;
}

.result-label {
  font-weight: 500;
  color: #555;
}

.result-list {
  margin: 2px 0 0 16px;
  padding: 0;
  list-style: disc;
}

.result-list li {
  margin-bottom: 2px;
}

.result-link {
  color: #1a73e8;
  text-decoration: none;
}

.result-link:hover {
  text-decoration: underline;
}
</style>
