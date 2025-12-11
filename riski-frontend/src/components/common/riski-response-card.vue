<script setup lang="ts">
import type Document from "@/types/Document.ts";
import type Proposal from "@/types/Proposal.ts";
import type RiskiAnswer from "@/types/RiskiAnswer.ts";

import { onMounted, ref } from "vue";

const props = defineProps<{
  riskiAnswer?: RiskiAnswer;
}>();

const aiResponse = ref<string>("");
const proposals = ref<Proposal[]>([]);
const documents = ref<Document[]>([]);

onMounted(() => {
  if (props.riskiAnswer) {
    aiResponse.value = props.riskiAnswer.ai_response;
    documents.value = props.riskiAnswer.documents;
    proposals.value = props.riskiAnswer.proposals;
  }
});

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
</script>

<template>
  <div>
    <h3 class="m-dataset-item__headline headline">KI Antwort</h3>
    <div class="marked_text m-dataset-item__text ai_response">
      {{ aiResponse }}
    </div>
  </div>
  <br />
  <div>
    <h3 class="m-dataset-item__headline headline">Anträge</h3>
    <div class="marked_text m-dataset-item__text ai_response">
      <ul>
        <li
          v-for="proposal in proposals"
          :key="proposal.identifier"
        >
          {{ proposal.identifier }} - {{ proposal.name }}
          <a :href="proposal.risUrl">{{ proposal.risUrl }}</a>
        </li>
      </ul>
    </div>
  </div>
  <br />
  <div>
    <h3 class="m-dataset-item__headline headline">Dokumente</h3>
    <div class="marked_text m-dataset-item__text ai_response">
      <ul>
        <li
          v-for="document in documents"
          :key="document.risUrl"
        >
          {{ document.name }} ({{ fileSizeAsString(document.size) }})
          <a :href="document.risUrl">{{ document.risUrl }}</a>
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
