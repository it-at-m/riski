<script setup lang="ts">
import type Document from "@/types/Document.ts";
import type Proposal from "@/types/Proposal.ts";
import type RiskiAnswer from "@/types/RiskiAnswer.ts";

import { computed } from "vue";

const props = defineProps<{
  riskiAnswer?: RiskiAnswer;
}>();

const aiResponse = computed(() => props.riskiAnswer?.response || "");
const proposals = computed(() => props.riskiAnswer?.proposals || []);
const documents = computed(() => props.riskiAnswer?.documents || []);
const steps = computed(() => props.riskiAnswer?.steps || []);
const status = computed(() => props.riskiAnswer?.status || "");

function fileSizeAsString(fileSize: number) {
  const units = ["B", "kB", "MB", "GB", "TB"];
  let unitIndex = 0;
  let size = fileSize;

  // Convert to the next higher unit until the size is smaller then 1000
  while (size >= 1000 && unitIndex < units.length - 1) {
    size /= 1000;
    unitIndex++;
  }

  // Format the string to two digits after the decimal point
  return `${size.toFixed(2)} ${units[unitIndex]}`;
}

function formatStepName(name: string) {
  const map: Record<string, string> = {
    retrieve_documents: "Dokumente suchen",
    model: "Antwort generieren",
    tools: "Werkzeuge verwenden",
    __start__: "Start",
  };
  return map[name] || name;
}
</script>

<template>
  <div v-if="status" class="status-container">
    <div class="status-message">Status: {{ status }}</div>
  </div>

  <div v-if="steps.length > 0" class="steps-container">
    <div v-for="(step, index) in steps" :key="index" class="step-item">
      <div class="step-header">
        <span class="step-status-icon">
          <template v-if="step.status === 'running'">⏳</template>
          <template v-else-if="step.status === 'completed'">✅</template>
          <template v-else-if="step.status === 'failed'">❌</template>
        </span>
        <span class="step-name">{{ formatStepName(step.name) }}</span>
      </div>
      <div v-if="step.toolCalls && step.toolCalls.length > 0" class="step-details">
        <details>
          <summary>
            Geplante Werkzeuge ({{ step.toolCalls.length }})
          </summary>
          <ul>
            <li v-for="tool in step.toolCalls" :key="tool.id">
              {{ tool.name }} <span v-if="tool.args">({{ tool.args }})</span>
              <span v-if="tool.status === 'running'">...</span>
            </li>
          </ul>
        </details>
      </div>
    </div>
  </div>
  <br v-if="steps.length > 0" />

  <div>
    <h3 class="m-dataset-item__headline headline">KI Antwort</h3>
    <div class="marked_text m-dataset-item__text ai_response">
      {{ aiResponse }}
    </div>
  </div>
  <br />
  <div v-if="proposals.length > 0">
    <h3 class="m-dataset-item__headline headline">Anträge</h3>
    <div class="marked_text m-dataset-item__text ai_response">
      <ul>
        <li v-for="proposal in proposals" :key="proposal.identifier">
          {{ proposal.identifier }} - {{ proposal.name }}
          <a :href="proposal.risUrl" target="_blank" rel="noopener noreferrer">{{ proposal.risUrl }}</a>
        </li>
      </ul>
    </div>
  </div>
  <br v-if="proposals.length > 0" />
  <div v-if="documents.length > 0">
    <h3 class="m-dataset-item__headline headline">Dokumente</h3>
    <div class="marked_text m-dataset-item__text ai_response">
      <ul>
        <li v-for="document in documents" :key="document.risUrl">
          {{ document.name }} ({{ fileSizeAsString(document.size) }})
          <a :href="document.risUrl" target="_blank" rel="noopener noreferrer">{{ document.risUrl }}</a>
        </li>
      </ul>
    </div>
  </div>
</template>

<style scoped>
.ai_response {
  margin: 0;
  padding: 16px;
  background-color: #e5eef5;
  border-radius: 10px;
  width: 100%;
}

.status-container {
  margin-bottom: 10px;
  padding: 8px;
  background-color: #f0f0f0;
  border-radius: 4px;
}

.steps-container {
  display: flex;
  flex-direction: column;
  gap: 5px;
  margin-bottom: 20px;
}

.step-item {
  display: flex;
  align-items: center;
  padding: 4px 8px;
  background-color: #f9f9f9;
  border: 1px solid #eee;
  border-radius: 4px;
}

.step-status-icon {
  margin-right: 8px;
  min-width: 20px;
  text-align: center;
}

.step-name {
  font-weight: 500;
}
</style>
