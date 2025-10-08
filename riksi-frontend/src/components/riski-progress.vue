<script setup lang="ts">
import dlfSpinner from "@/components/common/dlf-spinner.vue";

defineProps<{
  progress: number;
  msg: string;
}>();
</script>

<template>
  <dlf-spinner
    :percentage="progress"
    size="300"
  />
</template>

<style></style>
