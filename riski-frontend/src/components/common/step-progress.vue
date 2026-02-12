<script setup lang="ts">
import type { ExecutionStep } from "@/types/RiskiAnswer.ts";

defineProps<{
  steps: ExecutionStep[];
}>();

function formatStepName(name: string): string {
  const map: Record<string, string> = {
    retrieve_documents: "Dokumente durchsuchen",
    model: "Antwort formulieren",
    tools: "Informationen beschaffen",
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
  <div v-if="steps.length > 0" class="steps-container">
    <div v-for="(step, index) in steps" :key="index" class="step-item">
      <div class="step-header">
        <span class="step-status-icon">
          <template v-if="step.status === 'running'">⏳</template>
          <template v-else-if="step.status === 'completed'">✅</template>
          <template v-else-if="step.status === 'failed'">❌</template>
        </span>
        <span class="step-name">{{
          step.displayName || formatStepName(step.name)
        }}</span>
        <span v-if="step.status === 'running'" class="step-running-hint">läuft…</span>
      </div>

      <div v-if="step.toolCalls && step.toolCalls.length > 0" class="step-tools">
        <div v-for="tool in step.toolCalls" :key="tool.id" class="tool-call">
          <div class="tool-summary">
            <span class="tool-status-icon">
              <template v-if="tool.status === 'running'">🔄</template>
              <template v-else>✔️</template>
            </span>
            {{ formatToolName(tool.name) }}
            <span v-if="tool.args" class="tool-args">– „{{ tool.args }}"</span>
          </div>

          <!-- Show retrieved documents & proposals from tool result (live) -->
          <div v-if="tool.result && ((tool.result.proposals.length > 0) || (tool.result.documents.length > 0))"
            class="tool-results">
            <div v-if="tool.result.proposals.length > 0" class="result-group">
              <span class="result-label">{{ tool.result.proposals.length }} Anträge gefunden</span>
              <ul class="result-list">
                <li v-for="proposal in tool.result.proposals" :key="proposal.identifier">
                  <a v-if="proposal.risUrl" :href="proposal.risUrl" target="_blank" rel="noopener noreferrer"
                    class="result-link" :title="proposal.name">{{ proposal.identifier }} – {{ truncate(proposal.name)
                    }}</a>
                  <span v-else>{{ proposal.identifier }} – {{ truncate(proposal.name) }}</span>
                </li>
              </ul>
            </div>
            <div v-if="tool.result.documents.length > 0" class="result-group">
              <span class="result-label">{{ tool.result.documents.length }} Dokumente gefunden</span>
              <ul class="result-list">
                <li v-for="doc in tool.result.documents" :key="doc.risUrl || doc.name">
                  <a v-if="doc.risUrl" :href="doc.risUrl" target="_blank" rel="noopener noreferrer" class="result-link"
                    :title="doc.name">{{ truncate(doc.name) }}</a>
                  <span v-else>{{ truncate(doc.name) }}</span>
                </li>
              </ul>
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

.tool-results {
  margin-top: 6px;
  padding-left: 24px;
  font-size: 0.88em;
}

.result-group {
  margin-bottom: 6px;
}

.result-label {
  font-weight: 500;
  color: #555;
  font-size: 0.92em;
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
  color: #005a9f;
  text-decoration: none;
}

.result-link:hover {
  text-decoration: underline;
  color: #003d6e;
}
</style>
