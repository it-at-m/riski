<script setup lang="ts">
import type Document from "@/types/Document";
import type Proposal from "@/types/Proposal";

import { computed } from "vue";

const props = defineProps<{
  proposals: Proposal[];
  documents: Document[];
}>();

const sortedProposals = computed(() => {
  return [...props.proposals].sort((a, b) => {
    if (!a.date && !b.date) return 0;
    if (!a.date) return 1;
    if (!b.date) return -1;
    return new Date(b.date).getTime() - new Date(a.date).getTime();
  });
});

function formatDate(dateString: string | null): string {
  if (!dateString) return "";
  try {
    const date = new Date(dateString);
    return date.toLocaleDateString("de-DE", {
      year: "numeric",
      month: "2-digit",
      day: "2-digit",
    });
  } catch {
    return "";
  }
}

function fileSizeAsString(fileSize: number): string {
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
  <div class="data-section">
    <h2 class="m-dataset-item__headline headline">Daten</h2>
    <div
      v-if="sortedProposals.length > 0"
      class="source-section"
    >
      <h3 class="source-subheading">Anträge</h3>
      <ul class="source-list">
        <li
          v-for="proposal in sortedProposals"
          :key="proposal.identifier"
          class="source-item"
        >
          <div class="source-item-header">
            <span class="source-identifier">{{ proposal.identifier }}</span>
            <span
              v-if="proposal.date"
              class="source-date"
              >{{ formatDate(proposal.date) }}</span
            >
          </div>
          <a
            :href="proposal.risUrl"
            target="_blank"
            rel="noopener noreferrer"
            class="source-link"
          >
            {{ proposal.name }}
            <svg
              aria-hidden="true"
              width="12"
              height="12"
              viewBox="0 0 16 16"
              fill="currentColor"
              class="external-icon"
            >
              <path
                d="M8.636 3.5a.5.5 0 0 0-.5-.5H1.5A1.5 1.5 0 0 0 0 4.5v10A1.5 1.5 0 0 0 1.5 16h10a1.5 1.5 0 0 0 1.5-1.5V7.864a.5.5 0 0 0-1 0V14.5a.5.5 0 0 1-.5.5h-10a.5.5 0 0 1-.5-.5v-10a.5.5 0 0 1 .5-.5h6.636a.5.5 0 0 0 .5-.5z"
              />
              <path
                d="M16 .5a.5.5 0 0 0-.5-.5h-5a.5.5 0 0 0 0 1h3.793L6.146 9.146a.5.5 0 1 0 .708.708L15 1.707V5.5a.5.5 0 0 0 1 0v-5z"
              />
            </svg>
          </a>
          <p
            v-if="proposal.subject"
            class="source-subject"
          >
            {{ proposal.subject }}
          </p>
        </li>
      </ul>
    </div>
    <div
      v-if="documents.length > 0"
      class="source-section"
    >
      <h3 class="source-subheading">Dokumente</h3>
      <ul class="source-list">
        <li
          v-for="document in documents"
          :key="document.risUrl"
          class="source-item"
        >
          <div class="source-item-content">
            <a
              :href="document.risUrl"
              target="_blank"
              rel="noopener noreferrer"
              class="source-link"
            >
              {{ document.name }}
              <svg
                aria-hidden="true"
                width="12"
                height="12"
                viewBox="0 0 16 16"
                fill="currentColor"
                class="external-icon"
              >
                <path
                  d="M8.636 3.5a.5.5 0 0 0-.5-.5H1.5A1.5 1.5 0 0 0 0 4.5v10A1.5 1.5 0 0 0 1.5 16h10a1.5 1.5 0 0 0 1.5-1.5V7.864a.5.5 0 0 0-1 0V14.5a.5.5 0 0 1-.5.5h-10a.5.5 0 0 1-.5-.5v-10a.5.5 0 0 1 .5-.5h6.636a.5.5 0 0 0 .5-.5z"
                />
                <path
                  d="M16 .5a.5.5 0 0 0-.5-.5h-5a.5.5 0 0 0 0 1h3.793L6.146 9.146a.5.5 0 1 0 .708.708L15 1.707V5.5a.5.5 0 0 0 1 0v-5z"
                />
              </svg>
            </a>
            <span class="source-filesize">{{
              fileSizeAsString(document.size)
            }}</span>
          </div>
        </li>
      </ul>
    </div>
  </div>
</template>

<style scoped>
.data-section {
  background: #fff;
  border: 1px solid #eef2f6;
  border-radius: 10px;
  padding: 12px 14px 8px;
}

.source-section {
  margin-bottom: 10px;
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

.source-item-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  margin-bottom: 6px;
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

.source-date {
  font-size: 0.82em;
  color: #666;
  white-space: nowrap;
  font-weight: 500;
}

.source-subject {
  margin: 6px 0 0;
  font-size: 0.88em;
  color: #555;
  line-height: 1.4;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
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
  color: #3A5368;
  white-space: nowrap;
  margin-left: auto;
}
</style>
