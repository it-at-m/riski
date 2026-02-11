<script setup lang="ts">
import { ref, watch } from "vue";

import riskiSearchInput from "@/components/common/riski-search-input.vue";

const props = defineProps<{
  query: string;
  submitQuery: (query: string) => void;
  id: string;
  onClear: () => void;
}>();

const searchquery = ref<string>(props.query);

watch(
  () => props.query,
  (newVal) => {
    searchquery.value = newVal;
  },
  {
    immediate: true,
  }
);
</script>

<template>
  <form
    role="search"
    @submit.prevent="submitQuery(searchquery)"
    aria-label="RIS KI Suche"
  >
    <riski-search-input
      :id="id"
      v-model="searchquery"
      placeholder="Frage eingeben"
      suffix-icon="search"
      type="text"
      aria-label="Frage eingeben"
      @keyup.enter.stop.prevent="submitQuery(searchquery)"
      @suffix-click="submitQuery(searchquery)"
      @clear="onClear()"
    />
  </form>
</template>
