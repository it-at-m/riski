<script setup lang="ts">
import riskiSpinner from "@/components/common/riski-spinner.vue";

defineProps<{
  progress: number;
  msg: string;
}>();
</script>

<template>
  <riski-spinner
    :percentage="progress"
    size="300"
  />
</template>

<style></style>
