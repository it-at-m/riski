<template>
  <svg
    :width="size"
    :height="size"
    viewBox="-10 -10 220 220"
    fill="none"
    color="#005a9f"
    xmlns="http://www.w3.org/2000/svg"
  >
    <defs>
      <linearGradient
        id="gradient"
        x1="0%"
        y1="0%"
        x2="100%"
        y2="0%"
      >
        <stop
          offset="0%"
          stop-color="currentColor"
          stop-opacity="1"
        />
        <stop
          offset="100%"
          stop-color="currentColor"
          stop-opacity="0.5"
        />
      </linearGradient>
    </defs>
    <circle
      id="progress-bar"
      cx="100"
      cy="100"
      fill="transparent"
      stroke="url(#gradient)"
      stroke-width="10"
      stroke-linecap="round"
      :r="radius"
      :stroke-dasharray="dashArray"
      :stroke-dashoffset="dashOffset"
    >
      <animateTransform
        attributeName="transform"
        attributeType="XML"
        type="rotate"
        from="0 100 100"
        to="360 100 100"
        dur="2s"
        repeatCount="indefinite"
      />
    </circle>
    <text
      x="100"
      y="108"
      text-anchor="middle"
      fill="#3a5368"
      font-size="15"
      font-weight="bold"
      dominant-baseline="middle"
    >
      <tspan
        x="100"
        dy="-40"
      >
        Wir suchen
      </tspan>
      <tspan
        x="100"
        dy="20"
      >
        nach den
      </tspan>
      <tspan
        x="100"
        dy="20"
      >
        passenden
      </tspan>
      <tspan
        x="100"
        dy="20"
      >
        Informationen ...
      </tspan>
    </text>
  </svg>
</template>

<script setup lang="ts">
import type { ComputedRef } from "vue";

import { computed } from "vue";

const { size = "300", percentage } = defineProps<{
  /**
   * Size of the spinner relative or absolute.
   * Typical units for styling size are allowed.
   */
  size: string;
  /**
   * Number that represents the progress.
   * Numbers lower than 0 result in '0%'.
   * Numbers greater than 100 result in '100%'.
   * An empty value results in an empty string.
   */
  percentage?: number;
}>();

const calculateDasharray = (r: number): number => {
  return Math.PI * r * 2;
};

const calculateDashoffset = (
  percentageShown: number,
  circumference: number
): number => {
  return ((100 - percentageShown) / 100) * circumference;
};

const radius = 90;
const dashArray = calculateDasharray(radius);
const dashOffset: ComputedRef<number> = computed(() => {
  let validated_percentage = 0;
  if (percentage || percentage === 0) {
    if (percentage < 0) validated_percentage = 0;
    else if (percentage > 100) validated_percentage = 100;
    else validated_percentage = Math.round(percentage);
  }
  return calculateDashoffset(validated_percentage, dashArray);
});
</script>
<style scoped></style>
