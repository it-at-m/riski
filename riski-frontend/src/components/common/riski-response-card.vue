<script setup lang="ts">
import type RiskiAnswer from "@/types/RiskiAnswer.ts";

import StepProgress from "@/components/common/step-progress.vue";
import DOMPurify from "dompurify";
import { marked } from "marked";
import { computed } from "vue";

const props = defineProps<{
  riskiAnswer?: RiskiAnswer;
}>();

const aiResponse = computed(() => {
  const raw = props.riskiAnswer?.response || "";
  return DOMPurify.sanitize(marked.parse(raw) as string);
});
const proposals = computed(() => props.riskiAnswer?.proposals || []);
const documents = computed(() => props.riskiAnswer?.documents || []);
const steps = computed(() => props.riskiAnswer?.steps || []);

function fileSizeAsString(fileSize: number) {
  const units = ["B", "kB", "MB", "GB", "TB"];
  let unitIndex = 0;
  let size = fileSize;

  while (size >= 1000 && unitIndex < units.length - 1) {
    size /= 1000;
    unitIndex++;
  }

  return `${size.toFixed(2)} ${units[unitIndex]}`;
}
</script>

<template>
  <StepProgress :steps="steps" />

  <div>
    <h3 class="m-dataset-item__headline headline">KI Antwort</h3>
    <div class="marked_text m-dataset-item__text ai_response" v-html="aiResponse"></div>
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
</style>
