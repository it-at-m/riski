<script setup lang="ts">
import type RiskiAnswer from "@/types/RiskiAnswer.ts";
import { MucButton,  MucIcon  } from "@muenchen/muc-patternlab-vue";
import DOMPurify from "dompurify";
import { marked } from "marked";
import { computed, ref } from "vue";

import RiskiDataSection from "@/components/common/riski-data-section.vue";
import StepProgress from "@/components/common/step-progress.vue";
const props = defineProps<{
  riskiAnswer?: RiskiAnswer;
  isStreaming?: boolean;
}>();

const emit = defineEmits<{
  suggest: [query: string];
}>();
const aiResponse = computed(() => {
  const raw = props.riskiAnswer?.response || "";
  return DOMPurify.sanitize(marked.parse(raw) as string);
});
const proposals = computed(() => props.riskiAnswer?.proposals || []);
const documents = computed(() => props.riskiAnswer?.documents || []);
const steps = computed(() => props.riskiAnswer?.steps || []);
const errorInfo = computed(() => props.riskiAnswer?.errorInfo);
const hasError = computed(() => !!errorInfo.value);
const hasData = computed(
  () => proposals.value.length > 0 || documents.value.length > 0
);
const visibleSteps = computed(() =>
  steps.value.filter(
    (step) => step.name !== "collect_results" && step.name !== "guard"
  )
);

const showStepDetails = ref(true);
const hasProgress = computed(() => visibleSteps.value.length > 0);

/** User-facing heading for the error callout */
const errorHeading = computed(() => {
  switch (errorInfo.value?.errorType) {
    case "no_tool_call":
      return "Frage nicht verstanden";
    case "no_documents_found":
      return "Keine Dokumente gefunden";
    case "no_relevant_documents":
      return "Keine relevanten Dokumente";
    case "content_policy_violation":
      return "Anfrage nicht zulässig";
    case "server_error":
      return "Serverfehler";
    default:
      return "Kein Ergebnis";
  }
});

/** Short hint how the user can resolve the error */
const errorHint = computed(() => {
  switch (errorInfo.value?.errorType) {
    case "no_tool_call":
      return "Versuchen Sie es mit einer konkreteren Frage.";
    case "no_documents_found":
      return "Versuchen Sie es mit anderen Suchbegriffen.";
    case "no_relevant_documents":
      return "Versuchen Sie es mit einer präziseren Fragestellung.";
    case "content_policy_violation":
      return "Ihre Anfrage verstößt gegen die Inhaltsrichtlinien. Bitte stellen Sie eine andere Frage.";
    case "server_error":
      return "Bitte versuchen Sie es später erneut oder wenden Sie sich an den Support.";
    default:
      return "Bitte versuchen Sie es erneut.";
  }
});

const progressSummary = computed(() => {
  const total = visibleSteps.value.length;
  if (!total) return "";

  const completed = visibleSteps.value.filter(
    (step) => step.status === "completed"
  ).length;
  const hasFailed = visibleSteps.value.some((step) => step.status === "failed");
  const isRunning = visibleSteps.value.some(
    (step) => step.status === "running"
  );

  if (hasFailed) {
    return `Recherche mit Fehlern (${completed}/${total} Schritte)`;
  }
  if (isRunning) {
    return `Recherche läuft (${completed}/${total} Schritte)`;
  }
  return `Recherche abgeschlossen (${completed}/${total} Schritte)`;
});

const progressStatusIcon = computed(() => {
  if (!hasProgress.value) return "";
  if (visibleSteps.value.some((step) => step.status === "failed")) return "warning";
  if (visibleSteps.value.some((step) => step.status === "running")) return "hourglass";
  return "check";
});

const copySuccess = ref(false);

async function copyAnswer() {
  const raw = props.riskiAnswer?.response || "";
  try {
    await navigator.clipboard.writeText(raw);
    copySuccess.value = true;
    setTimeout(() => {
      copySuccess.value = false;
    }, 2000);
  } catch {
    // Fallback for environments without clipboard API
    const textarea = document.createElement("textarea");
    textarea.value = raw;
    textarea.style.position = "fixed";
    textarea.style.opacity = "0";
    document.body.appendChild(textarea);
    textarea.select();
    document.execCommand("copy");
    document.body.removeChild(textarea);
    copySuccess.value = true;
    setTimeout(() => {
      copySuccess.value = false;
    }, 2000);
  }
}
</script>

<template>
  <!-- Error state from agent pipeline -->
  <div
    v-if="hasError && !isStreaming"
    class="error-section"
  >
    <div class="error-content">
      <svg
        class="error-icon"
        aria-hidden="true"
        width="18"
        height="18"
        viewBox="0 0 16 16"
        fill="currentColor"
      >
        <path
          d="M8 15A7 7 0 1 1 8 1a7 7 0 0 1 0 14zm0 1A8 8 0 1 0 8 0a8 8 0 0 0 0 16z"
        />
        <path
          d="M7.002 11a1 1 0 1 1 2 0 1 1 0 0 1-2 0zM7.1 4.995a.905.905 0 1 1 1.8 0l-.35 3.507a.552.552 0 0 1-1.1 0L7.1 4.995z"
        />
      </svg>
      <div>
        <p class="error-heading">{{ errorHeading }}</p>
        <p class="error-hint">{{ errorHint }}</p>
        <div
          v-if="
            errorInfo?.suggestions &&
            errorInfo.suggestions.length > 0 &&
            errorInfo.errorType !== 'content_policy_violation' &&
            errorInfo.errorType !== 'server_error'
          "
          class="error-suggestions"
        >
          <p class="error-suggestions-label">Alternative Suchvorschläge:</p>
          <ul
            class="suggestion-chips"
            role="list"
          >
            <li
              v-for="suggestion in errorInfo.suggestions"
              :key="suggestion"
            >
              <button
                class="suggestion-chip"
                @click="emit('suggest', suggestion)"
              >
                {{ suggestion }}
              </button>
            </li>
          </ul>
        </div>
      </div>
    </div>
  </div>

  <div
    v-if="!hasError"
    class="response-section"
  >
    <div class="response-header">
      <h2 class="m-dataset-item__headline headline">KI-Antwort</h2>
      <span
        v-if="isStreaming"
        class="answer-status"
        >Wird generiert…</span
      >
      <MucButton  v-if="aiResponse && !isStreaming" icon="copy-link" spinIconOnClick variant="secondary" @click=copyAnswer> Kopieren </MucButton>
    </div>

    <!-- Skeleton placeholder while waiting for first content -->
    <div
      v-if="isStreaming && !aiResponse"
      class="ai_response ai_response--skeleton"
      aria-label="Antwort wird geladen"
    >
      <div class="skeleton-line skeleton-line--long"></div>
      <div class="skeleton-line skeleton-line--medium"></div>
      <div class="skeleton-line skeleton-line--short"></div>
      <div class="streaming-indicator">
        <span class="streaming-dot"></span>
        <span class="streaming-dot"></span>
        <span class="streaming-dot"></span>
      </div>
    </div>

    <!-- Actual AI response content -->
    <div
      v-else-if="aiResponse"
      class="marked_text m-dataset-item__text ai_response"
      v-html="aiResponse"
    ></div>

    <!-- Streaming indicator while text is still arriving -->
    <div
      v-if="isStreaming && aiResponse"
      class="streaming-indicator"
      aria-label="Antwort wird generiert"
    >
      <span class="streaming-dot"></span>
      <span class="streaming-dot"></span>
      <span class="streaming-dot"></span>
    </div>
  </div>
  <br />
  <riski-data-section
    v-if="hasData"
    :proposals="proposals"
    :documents="documents"
  />
  <br />
  <div
    v-if="hasProgress"
    class="progress-section"
  >
    <div class="progress-header">
      <h2 class="m-dataset-item__headline headline">Recherchefortschritt</h2>
      <button
        class="progress-toggle"
        type="button"
        @click="showStepDetails = !showStepDetails"
      >
        {{ showStepDetails ? "Details ausblenden" : "Details anzeigen" }}
      </button>
    </div>
    <div class="progress-summary">
      <MucIcon :icon=progressStatusIcon></MucIcon>
      <span>{{ progressSummary }}</span>
    </div>
    <div
      v-if="showStepDetails"
      class="progress-details"
    >
      <step-progress :steps="visibleSteps" />
    </div>
  </div>
</template>

<style scoped>
.ai_response {
  margin: 0;
  padding: 14px 16px;
  background-color: #f9f9f9;
  border: 1px solid #eee;
  border-radius: 6px;
  width: 100%;
}

/* Markdown content styling inside AI response */
.ai_response :deep(h1),
.ai_response :deep(h2),
.ai_response :deep(h3),
.ai_response :deep(h4) {
  margin-top: 0.75em;
  margin-bottom: 0.25em;
}

.ai_response :deep(ul),
.ai_response :deep(ol) {
  padding-left: 1.5em;
  margin: 0.5em 0;
}

.ai_response :deep(p) {
  margin: 0.5em 0;
}

.ai_response :deep(p:first-child) {
  margin-top: 0;
}

.ai_response :deep(p:last-child) {
  margin-bottom: 0;
}

.ai_response :deep(code) {
  background-color: rgba(0, 0, 0, 0.06);
  padding: 0.15em 0.4em;
  border-radius: 4px;
  font-size: 0.9em;
}

.ai_response :deep(blockquote) {
  border-left: 3px solid #005a9f;
  padding-left: 12px;
  margin: 0.5em 0;
  color: #555;
}

/* Response header with copy button */
.response-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.answer-status {
  font-size: 0.85em;
  color: #666;
  margin-left: auto;
}

.copy-button {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 4px 10px;
  border: 1px solid #ccc;
  border-radius: 6px;
  background: #fff;
  color: #555;
  cursor: pointer;
  font-size: 0.82em;
  transition: all 0.2s ease;
}

.copy-button:hover {
  background: #f0f0f0;
  border-color: #999;
  color: #333;
}

.copy-button:focus-visible {
  outline: 2px solid #005a9f;
  outline-offset: 2px;
}

.copy-button.copy-success {
  border-color: #2e7d32;
  color: #2e7d32;
  background: #e8f5e9;
}

.copy-label {
  white-space: nowrap;
}

.progress-section {
  background: #f9fafb;
  border: 1px solid #eef2f6;
  border-radius: 10px;
  padding: 12px 14px;
}

.progress-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 4px;
}

.progress-toggle {
  border: none;
  background: none;
  color: #005a9f;
  font-size: 0.85em;
  cursor: pointer;
  padding: 0;
}

.progress-toggle:hover {
  text-decoration: underline;
}

.progress-summary {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 0.9em;
  color: #444;
}

.progress-status-icon {
  min-width: 18px;
  text-align: center;
}

.progress-details {
  margin-top: 8px;
}

/* Streaming indicator dots */
.streaming-indicator {
  display: flex;
  gap: 4px;
  padding: 8px 16px;
}

.streaming-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background-color: #005a9f;
  animation: streaming-bounce 1.4s ease-in-out infinite;
}

.streaming-dot:nth-child(2) {
  animation-delay: 0.2s;
}

.streaming-dot:nth-child(3) {
  animation-delay: 0.4s;
}

@keyframes streaming-bounce {
  0%,
  80%,
  100% {
    opacity: 0.3;
    transform: scale(0.8);
  }

  40% {
    opacity: 1;
    transform: scale(1);
  }
}

/* Skeleton loading placeholders */
.ai_response--skeleton {
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding: 20px 16px;
}

.skeleton-line {
  height: 12px;
  border-radius: 6px;
  background: linear-gradient(90deg, #d8e4ef 25%, #e8f0f7 50%, #d8e4ef 75%);
  background-size: 200% 100%;
  animation: skeleton-shimmer 1.5s ease-in-out infinite;
}

.skeleton-line--long {
  width: 90%;
}

.skeleton-line--medium {
  width: 65%;
}

.skeleton-line--short {
  width: 40%;
}

.skeleton-line--tag {
  width: 80px;
  height: 12px;
  flex-shrink: 0;
}

@keyframes skeleton-shimmer {
  0% {
    background-position: 200% 0;
  }

  100% {
    background-position: -200% 0;
  }
}

.source-skeleton {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.source-item--skeleton {
  opacity: 0.6;
}

.source-item--skeleton .source-item-content {
  gap: 10px;
}

/* Error state styling */
.error-section {
  margin-bottom: 16px;
}

.error-content {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  padding: 14px 16px;
  background-color: #f9f9f9;
  border: 1px solid #eee;
  border-radius: 6px;
}

.error-icon {
  flex-shrink: 0;
  color: #999;
  margin-top: 1px;
}

.error-heading {
  margin: 0;
  font-size: 0.95em;
  font-weight: 600;
  color: #444;
}

.error-hint {
  margin: 4px 0 0;
  font-size: 0.88em;
  color: #777;
}

.error-suggestions {
  margin-top: 12px;
}

.error-suggestions-label {
  margin: 0 0 6px;
  font-size: 0.85em;
  color: #666;
  font-weight: 500;
}

.suggestion-chips {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.suggestion-chip {
  display: inline-flex;
  align-items: center;
  padding: 5px 12px;
  border: 1px solid #005a9f;
  border-radius: 16px;
  background: #fff;
  color: #005a9f;
  font-size: 0.85em;
  cursor: pointer;
  transition:
    background 0.15s ease,
    color 0.15s ease;
  text-align: left;
}

.suggestion-chip:hover {
  background: #005a9f;
  color: #fff;
}

.suggestion-chip:focus-visible {
  outline: 2px solid #005a9f;
  outline-offset: 2px;
}
</style>
