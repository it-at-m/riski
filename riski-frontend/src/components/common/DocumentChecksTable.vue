<script setup lang="ts">
import type { DocumentCheckResult } from "@/types/RiskiAnswer.ts";

import { computed, ref } from "vue";

const props = defineProps<{
  documentChecks: DocumentCheckResult[];
  documentUrlMap: Map<string, string>;
}>();

const showReasons = ref(false);

const acceptedDocuments = computed(() =>
  props.documentChecks.filter((check) => check.relevant)
);

const rejectedDocuments = computed(() =>
  props.documentChecks.filter((check) => !check.relevant)
);

const hasReasoning = computed(() =>
  props.documentChecks.some((check) => check.reason && check.reason !== "")
);

const resolveDocUrl = (check: DocumentCheckResult): string | undefined => {
  // First, check if the URL is directly on the check object
  if (check.url) {
    return check.url;
  }

  // Fallback: try to find URL in the documentUrlMap
  const url = props.documentUrlMap.get(check.name);
  if (url) {
    return url;
  }

  // Last resort: try to extract document ID from name pattern and match
  const match = check.name.match(/A\s*(\d+)/);
  if (match && match[1]) {
    for (const [, mapUrl] of props.documentUrlMap.entries()) {
      if (mapUrl && mapUrl.includes(match[1])) {
        return mapUrl;
      }
    }
  }

  return undefined;
};
</script>

<template>
  <section
    class="step-doc-checks"
    aria-labelledby="doc-checks-heading"
  >
    <div class="doc-checks-header-row">
      <button
        v-if="hasReasoning"
        type="button"
        class="doc-checks-toggle"
        :aria-expanded="showReasons"
        aria-controls="doc-checks-content"
        @click="showReasons = !showReasons"
        style="margin-left: auto; display: block;"
      >
        {{ showReasons ? "Begründung ausblenden" : "Begründung anzeigen" }}
      </button>
    </div>

    <div id="doc-checks-content">
      <!-- Accepted Documents -->
      <div
        v-if="acceptedDocuments.length > 0"
        class="doc-section"
      >
        <table
          class="doc-checks-table"
          aria-labelledby="accepted-docs-heading"
        >
          <caption class="sr-only">
            Liste der
            {{
              acceptedDocuments.length
            }}
            relevanten Dokumente
          </caption>
          <thead>
            <tr>
              <th scope="col">Relevante Dokumente</th>
              <th
                v-if="showReasons"
                scope="col"
              >
                Begründung
              </th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="(check, ci) in acceptedDocuments"
              :key="ci"
            >
              <td class="doc-check-name">
                <a
                  v-if="resolveDocUrl(check)"
                  :href="resolveDocUrl(check)"
                  target="_blank"
                  rel="noopener noreferrer"
                  class="doc-check-link"
                  :aria-label="`Dokument öffnen: ${check.name} (öffnet in neuem Fenster)`"
                >
                  {{ check.name }}
                  <span
                    class="external-link-icon"
                    aria-hidden="true"
                    >↗</span
                  >
                </a>
                <span v-else>{{ check.name }}</span>
              </td>
              <td
                v-if="showReasons"
                class="doc-check-reason"
              >
                {{ check.reason || "–" }}
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Rejected Documents -->
      <div
        v-if="rejectedDocuments.length > 0"
        class="doc-section"
      >
        <table
          class="doc-checks-table"
          aria-labelledby="rejected-docs-heading"
        >
          <caption class="sr-only">
            Liste der
            {{
              rejectedDocuments.length
            }}
            nicht relevanten Dokumente
          </caption>
          <thead>
            <tr>
              <th scope="col">Nicht relevante Dokumente</th>
              <th
                v-if="showReasons"
                scope="col"
              >
                Begründung
              </th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="(check, ci) in rejectedDocuments"
              :key="ci"
            >
              <td class="doc-check-name">
                <a
                  v-if="resolveDocUrl(check)"
                  :href="resolveDocUrl(check)"
                  target="_blank"
                  rel="noopener noreferrer"
                  class="doc-check-link"
                  :aria-label="`Dokument öffnen: ${check.name} (öffnet in neuem Fenster)`"
                >
                  {{ check.name }}
                  <span
                    class="external-link-icon"
                    aria-hidden="true"
                    >↗</span
                  >
                </a>
                <span v-else>{{ check.name }}</span>
              </td>
              <td
                v-if="showReasons"
                class="doc-check-reason"
              >
                {{ check.reason || "–" }}
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </section>
</template>

<style scoped>
.step-doc-checks {
  margin-top: 4px;
  padding-left: 28px;
}

.doc-checks-header-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  margin-bottom: 8px;
}

.doc-checks-toggle {
  border: none;
  background: none;
  color: #555;
  font-size: 0.82em;
  cursor: pointer;
  padding: 0;
}

.doc-checks-toggle:hover {
  color: #333;
}

.doc-section {
  margin-bottom: 12px;
}

.doc-section:last-child {
  margin-bottom: 0;
}

.doc-checks-table {
  font-size: 0.86em;
}

.doc-check-name {
  font-weight: 500;
}

.doc-check-reason {
  color: #666;
  font-style: italic;
}

.doc-check-link {
  color: #005a9f;
  text-decoration: none;
}

.doc-check-link:hover {
  text-decoration: underline;
  color: #003d6e;
}

.external-link-icon {
  display: inline-block;
  margin-left: 4px;
  font-size: 0.85em;
  vertical-align: super;
  line-height: 0;
}

.sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border-width: 0;
}
</style>
