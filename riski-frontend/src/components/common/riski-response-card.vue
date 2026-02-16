<script setup lang="ts">
import type RiskiAnswer from "@/types/RiskiAnswer.ts";

import DOMPurify from "dompurify";
import { marked } from "marked";
import { computed, ref } from "vue";

import StepProgress from "@/components/common/step-progress.vue";

const props = defineProps<{
  riskiAnswer?: RiskiAnswer;
  isStreaming?: boolean;
}>();

const aiResponse = computed(() => {
  const raw = props.riskiAnswer?.response || "";
  return DOMPurify.sanitize(marked.parse(raw) as string);
});
const proposals = computed(() => props.riskiAnswer?.proposals || []);
const documents = computed(() => props.riskiAnswer?.documents || []);
const steps = computed(() => props.riskiAnswer?.steps || []);
const visibleSteps = computed(() =>
  steps.value.filter(
    (step) => step.name !== "collect_results" && step.name !== "guard",
  ),
);

const showStepDetails = ref(false);
const hasProgress = computed(() => visibleSteps.value.length > 0);
const progressSummary = computed(() => {
  const total = visibleSteps.value.length;
  if (!total) return "";

  const completed = visibleSteps.value.filter(
    (step) => step.status === "completed",
  ).length;
  const hasFailed = visibleSteps.value.some((step) => step.status === "failed");
  const isRunning = visibleSteps.value.some(
    (step) => step.status === "running",
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
  if (visibleSteps.value.some((step) => step.status === "failed")) return "❌";
  if (visibleSteps.value.some((step) => step.status === "running")) return "⏳";
  return "✅";
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
  <div class="response-section">
    <div class="response-header">
      <h3 class="m-dataset-item__headline headline">KI Antwort</h3>
      <span v-if="isStreaming" class="answer-status">Wird generiert…</span>
      <button v-if="aiResponse && !isStreaming" class="copy-button" :class="{ 'copy-success': copySuccess }"
        @click="copyAnswer" :aria-label="copySuccess ? 'Kopiert!' : 'Antwort kopieren'" :title="copySuccess ? 'Kopiert!' : 'Antwort in die Zwischenablage kopieren'
          ">
        <svg v-if="!copySuccess" aria-hidden="true" width="16" height="16" viewBox="0 0 16 16" fill="currentColor">
          <path
            d="M4 2a2 2 0 0 1 2-2h6a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V2zm2-1a1 1 0 0 0-1 1v8a1 1 0 0 0 1 1h6a1 1 0 0 0 1-1V2a1 1 0 0 0-1-1H6z" />
          <path
            d="M2 5a1 1 0 0 0-1 1v8a1 1 0 0 0 1 1h6a1 1 0 0 0 1-1v-1h1v1a2 2 0 0 1-2 2H2a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h1v1H2z" />
        </svg>
        <svg v-else aria-hidden="true" width="16" height="16" viewBox="0 0 16 16" fill="currentColor">
          <path
            d="M13.854 3.646a.5.5 0 0 1 0 .708l-7 7a.5.5 0 0 1-.708 0l-3.5-3.5a.5.5 0 1 1 .708-.708L6.5 10.293l6.646-6.647a.5.5 0 0 1 .708 0z" />
        </svg>
        <span class="copy-label">{{
          copySuccess ? "Kopiert!" : "Kopieren"
        }}</span>
      </button>
    </div>

    <!-- Skeleton placeholder while waiting for first content -->
    <div v-if="isStreaming && !aiResponse" class="ai_response ai_response--skeleton" aria-label="Antwort wird geladen">
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
    <div v-else-if="aiResponse" class="marked_text m-dataset-item__text ai_response" v-html="aiResponse"></div>

    <!-- Streaming indicator while text is still arriving -->
    <div v-if="isStreaming && aiResponse" class="streaming-indicator" aria-label="Antwort wird generiert">
      <span class="streaming-dot"></span>
      <span class="streaming-dot"></span>
      <span class="streaming-dot"></span>
    </div>
  </div>
  <br />
  <div v-if="hasProgress" class="progress-section">
    <div class="progress-header">
      <h3 class="m-dataset-item__headline headline">Recherchefortschritt</h3>
      <button class="progress-toggle" type="button" @click="showStepDetails = !showStepDetails">
        {{ showStepDetails ? "Details ausblenden" : "Details anzeigen" }}
      </button>
    </div>
    <div class="progress-summary">
      <span class="progress-status-icon">{{ progressStatusIcon }}</span>
      <span>{{ progressSummary }}</span>
    </div>
    <div v-if="showStepDetails" class="progress-details">
      <StepProgress :steps="steps" />
    </div>
  </div>
  <br />
  <div class="data-section">
    <h3 class="m-dataset-item__headline headline">Daten</h3>
    <div class="source-section">
      <h4 class="source-subheading">Anträge</h4>
      <ul v-if="proposals.length > 0" class="source-list">
        <li v-for="proposal in proposals" :key="proposal.identifier" class="source-item">
          <div class="source-item-content">
            <span class="source-identifier">{{ proposal.identifier }}</span>
            <a :href="proposal.risUrl" target="_blank" rel="noopener noreferrer" class="source-link">
              {{ proposal.name }}
              <svg aria-hidden="true" width="12" height="12" viewBox="0 0 16 16" fill="currentColor"
                class="external-icon">
                <path
                  d="M8.636 3.5a.5.5 0 0 0-.5-.5H1.5A1.5 1.5 0 0 0 0 4.5v10A1.5 1.5 0 0 0 1.5 16h10a1.5 1.5 0 0 0 1.5-1.5V7.864a.5.5 0 0 0-1 0V14.5a.5.5 0 0 1-.5.5h-10a.5.5 0 0 1-.5-.5v-10a.5.5 0 0 1 .5-.5h6.636a.5.5 0 0 0 .5-.5z" />
                <path
                  d="M16 .5a.5.5 0 0 0-.5-.5h-5a.5.5 0 0 0 0 1h3.793L6.146 9.146a.5.5 0 1 0 .708.708L15 1.707V5.5a.5.5 0 0 0 1 0v-5z" />
              </svg>
            </a>
          </div>
        </li>
      </ul>
      <div v-else-if="isStreaming" class="source-skeleton">
        <div class="source-item source-item--skeleton" v-for="n in 2" :key="n">
          <div class="source-item-content">
            <span class="skeleton-line skeleton-line--tag"></span>
            <span class="skeleton-line skeleton-line--medium"></span>
          </div>
        </div>
      </div>
    </div>
    <div class="source-section">
      <h4 class="source-subheading">Dokumente</h4>
      <ul v-if="documents.length > 0" class="source-list">
        <li v-for="document in documents" :key="document.risUrl" class="source-item">
          <div class="source-item-content">
            <a :href="document.risUrl" target="_blank" rel="noopener noreferrer" class="source-link">
              {{ document.name }}
              <svg aria-hidden="true" width="12" height="12" viewBox="0 0 16 16" fill="currentColor"
                class="external-icon">
                <path
                  d="M8.636 3.5a.5.5 0 0 0-.5-.5H1.5A1.5 1.5 0 0 0 0 4.5v10A1.5 1.5 0 0 0 1.5 16h10a1.5 1.5 0 0 0 1.5-1.5V7.864a.5.5 0 0 0-1 0V14.5a.5.5 0 0 1-.5.5h-10a.5.5 0 0 1-.5-.5v-10a.5.5 0 0 1 .5-.5h6.636a.5.5 0 0 0 .5-.5z" />
                <path
                  d="M16 .5a.5.5 0 0 0-.5-.5h-5a.5.5 0 0 0 0 1h3.793L6.146 9.146a.5.5 0 1 0 .708.708L15 1.707V5.5a.5.5 0 0 0 1 0v-5z" />
              </svg>
            </a>
            <span class="source-filesize">{{
              fileSizeAsString(document.size)
            }}</span>
          </div>
        </li>
      </ul>
      <div v-else-if="isStreaming" class="source-skeleton">
        <div class="source-item source-item--skeleton" v-for="n in 3" :key="n">
          <div class="source-item-content">
            <span class="skeleton-line skeleton-line--long"></span>
            <span class="skeleton-line skeleton-line--tag"></span>
          </div>
        </div>
      </div>
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

/* Source list styling */
.source-section {
  margin-bottom: 10px;
}

.data-section {
  background: #fff;
  border: 1px solid #eef2f6;
  border-radius: 10px;
  padding: 12px 14px 8px;
}

.source-subheading {
  margin: 4px 0 6px;
  font-size: 0.92em;
  font-weight: 600;
  color: #555;
}

.source-list {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.source-item {
  background-color: #f5f8fb;
  border: 1px solid #e0e7ef;
  border-radius: 8px;
  padding: 10px 14px;
  transition:
    background-color 0.15s ease,
    border-color 0.15s ease;
}

.source-item:hover {
  background-color: #e5eef5;
  border-color: #c0d0e0;
}

.source-item-content {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.source-identifier {
  font-weight: 600;
  color: #333;
  white-space: nowrap;
  font-size: 0.92em;
}

.source-link {
  color: #005a9f;
  text-decoration: none;
  font-weight: 500;
  display: inline-flex;
  align-items: center;
  gap: 4px;
}

.source-link:hover {
  text-decoration: underline;
  color: #003d6e;
}

.source-link:focus-visible {
  outline: 2px solid #005a9f;
  outline-offset: 2px;
  border-radius: 2px;
}

.external-icon {
  flex-shrink: 0;
  opacity: 0.6;
}

.source-filesize {
  font-size: 0.82em;
  color: #777;
  white-space: nowrap;
  margin-left: auto;
}
</style>
