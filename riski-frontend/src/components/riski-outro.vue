<script setup lang="ts">
import { MucButton } from "@muenchen/muc-patternlab-vue";

defineProps<{
  frontendVersion: string;
  version: string;
  documentationUrl: string;
}>();

const openKIMuenchen = (url: string) => {
  window.open(url, "_blank")?.focus();
};
</script>

<template>
  <div
    class="feedback-container"
    style="background-color: var(--color-neutrals-blue-xlight)"
  >
    <div class="container">
      <div
        class="m-callout feedback-callout callout-margin"
        style="background-color: #ffffff"
      >
        <div class="m-callout__inner">
          <div class="m-callout__body">
            <div class="m-callout__body__inner">
              <div class="m-callout__headline">
                <h2>Lernen Sie unsere KI-Suche besser kennen!</h2>
              </div>

              <div class="m-callout__content">
                <div>
                  <p class="docs-paragraph">
                    In einer Beta-Version testen wir aktuell eine Suche mit
                    Künstlicher Intelligenz. Wie das genau funktioniert,
                    erklären wir Ihnen auf unserer Dokumentations-Webseite.
                  </p>
                  <muc-button
                    variant="secondary"
                    class="open-extern-button"
                    icon="ext-link"
                    @click="openKIMuenchen(documentationUrl)"
                  >
                    ki.muenchen.de besuchen
                  </muc-button>
                  <div class="version-row">
                    <div class="version-badge">
                      <span class="version-label">Frontend</span>
                      <span class="version-number">{{ frontendVersion }}</span>
                    </div>
                    <div class="version-badge">
                      <span class="version-label">Backend</span>
                      <span class="version-number">{{ version }}</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.feedback-container {
  padding-bottom: 40px;
  padding-top: 40px;
}

.callout-margin {
  margin-left: 20%;
  margin-right: 20%;
}

.m-callout__content ul li {
  padding-left: 0;
}

.feedback-callout {
  padding-top: 32px;
  margin-top: 0;
}

.open-extern-button {
  margin-top: 16px;
}

.docs-paragraph {
  margin-bottom: 16px;
}

.version-row {
  margin-top: 24px;
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

.version-badge {
  display: inline-flex;
  align-items: center;
  font-size: 0.7rem;
  color: #909090;
  padding: 0;
}

.version-label {
  font-weight: 400;
  margin-right: 4px;
  font-size: 0.7rem;
}

.version-number {
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
}

@media screen and (max-width: 768px) {
  .callout-margin {
    margin-left: 0%;
    margin-right: 0%;
  }
}
</style>
