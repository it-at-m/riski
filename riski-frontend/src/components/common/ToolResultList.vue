<script setup lang="ts">
import type { ToolCallResult } from "@/types/RiskiAnswer.ts";

import { ref } from "vue";

const props = defineProps<{
  result: ToolCallResult;
}>();

const isOpen = ref(false);

function toggle() {
  isOpen.value = !isOpen.value;
}

function truncate(text: string, maxLength = 60): string {
  return text.length > maxLength ? text.slice(0, maxLength) + "…" : text;
}
</script>

<template>
  <div class="mt-1 ps-4 small">
    <button
      class="btn btn-link btn-sm p-0 text-secondary fw-medium d-flex align-items-center gap-1 text-decoration-none"
      type="button" :aria-expanded="isOpen" aria-controls="tool-results-content" @click="toggle">
      <span aria-hidden="true" style="font-size: 0.75em; width: 12px; display: inline-block">{{ isOpen ? "▼" : "▶"
        }}</span>
      <span>
        <template v-if="result.proposals.length > 0">
          {{ result.proposals.length }} Anträge
        </template>
        <template v-if="result.proposals.length > 0 && result.documents.length > 0">,
        </template>
        <template v-if="result.documents.length > 0">
          {{ result.documents.length }} Dokumente
        </template>
        gefunden
      </span>
    </button>

    <div id="tool-results-content" v-show="isOpen" class="mt-1">
      <table v-if="result.proposals.length > 0" class="table table-sm table-bordered table-hover mb-2">
        <caption class="text-secondary fw-medium small">
          Anträge
        </caption>
        <thead class="table-light">
          <tr>
            <th scope="col">Kennung</th>
            <th scope="col">Titel</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="proposal in result.proposals" :key="proposal.identifier">
            <td class="text-nowrap">
              <a v-if="proposal.risUrl" :href="proposal.risUrl" target="_blank" rel="noopener noreferrer">{{
                proposal.identifier }}</a>
              <span v-else>{{ proposal.identifier }}</span>
            </td>
            <td :title="proposal.name">
              {{ truncate(proposal.name) }}
            </td>
          </tr>
        </tbody>
      </table>

      <table v-if="result.documents.length > 0" class="table table-sm table-bordered table-hover mb-2">
        <caption class="text-secondary fw-medium small">
          Dokumente
        </caption>
        <thead class="table-light">
          <tr>
            <th scope="col">Titel</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="doc in result.documents" :key="doc.risUrl || doc.name">
            <td :title="doc.name">
              <a v-if="doc.risUrl" :href="doc.risUrl" target="_blank" rel="noopener noreferrer">{{ truncate(doc.name)
                }}</a>
              <span v-else>{{ truncate(doc.name) }}</span>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>
