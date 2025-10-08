<template>
  <label class="switch">
    <input
      v-model="modelValue"
      type="checkbox"
    />
    <span class="slider round"></span>
  </label>
</template>

<script setup lang="ts">
/**
 * Input value from the input component.
 */
const modelValue = defineModel<boolean>({ default: false });
</script>
<style scoped>
.switch {
  position: relative;
  display: inline-block;
  width: 60px;
  height: 34px;
}

.switch input {
  opacity: 0;
  width: 0;
  height: 0;
}

.slider {
  position: absolute;
  cursor: pointer;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  -webkit-transition: 0.4s;
  transition: 0.4s;
  background-color: var(--color-brand-main-blue);
}

.slider:before {
  position: absolute;
  content: "";
  height: 26px;
  width: 26px;
  left: 4px;
  bottom: 4px;
  background-color: var(--color-neutrals-blue-xlight);
  -webkit-transition: 0.4s;
  transition: 0.4s;
}

input:focus + .slider {
  box-shadow: 0 0 1px var(--color-brand-main-blue);
}

input:checked + .slider:before {
  -webkit-transform: translateX(26px);
  -ms-transform: translateX(26px);
  transform: translateX(26px);
}

/* Rounded sliders */
.slider.round {
  border-radius: 34px;
}

.slider.round:before {
  border-radius: 50%;
}
</style>
