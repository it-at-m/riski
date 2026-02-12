<script setup lang="ts">
import type RiskiAnswer from "@/types/RiskiAnswer";

import { MucCallout } from "@muenchen/muc-patternlab-vue";
import customIconsSprite from "@muenchen/muc-patternlab-vue/assets/icons/custom-icons.svg?raw";
import mucIconsSprite from "@muenchen/muc-patternlab-vue/assets/icons/muc-icons.svg?raw";
import { nextTick, ref } from "vue";

import SearchService from "@/api/SearchService";
import riskiIconsSprite from "@/assets/custom-icons.svg?raw";
import RiskiResponseCard from "@/components/common/riski-response-card.vue";
import riskiIntro from "@/components/riski-intro.vue";
import riskiSearchbar from "@/components/riski-searchbar.vue";
import { EXAMPLE_QUESTIONS } from "@/util/constants";

let abortController = new AbortController();

const found_answer = ref<RiskiAnswer>();
const resultsArea = ref<HTMLElement | null>(null);

const loading = ref<boolean>(false);
const initial = ref<boolean>(true);
const fehler = ref<string>("");
const searchquery = ref<string>("");

/**
 * Callback function for a successfully processed document with the answer chain.
 * Called progressively as streaming data arrives.
 *
 * @param {RiskiAnswer} answer - The processed document (may be partial).
 */
const onProcessedCallback = (answer: RiskiAnswer) => {
  const isFirstResult = found_answer.value == undefined;
  found_answer.value = answer;

  // Scroll results into view on first partial result
  if (isFirstResult) {
    nextTick(() => {
      resultsArea.value?.scrollIntoView({ behavior: "smooth", block: "start" });
    });
  }
};

/**
 * Callback function for the completion of all search callbacks
 */
const onCompleteCallback = () => {
  loading.value = false;
};
const resetAbortController = () => {
  if (loading.value) {
    abortController.abort();
    abortController = new AbortController();
  }
};

const resetInitialState = () => {
  resetAbortController();
  found_answer.value = undefined;
  loading.value = false;
  fehler.value = "";
  initial.value = true;
};

const resetLoadingState = () => {
  found_answer.value = undefined;
  loading.value = true;
  fehler.value = "";
};

/**
 * Submits a query for searching documents.
 *
 * @param {string} query - The query string to search for.
 */
const submitQuery = (query: string) => {
  searchquery.value = query;
  if (query === "") {
    return;
  }
  initial.value = false;
  resetAbortController();
  resetLoadingState();

  SearchService.search(
    query,
    onProcessedCallback,
    onCompleteCallback,
    abortController.signal
  ).catch((e: string) => {
    fehler.value = e;
  });
};
</script>

<template>
  <link href="https://assets.muenchen.de/mde/1.0.6/css/muenchende-style.css" rel="stylesheet" />
  <main>
    <div>
      <div v-html="mucIconsSprite" />
      <div v-html="customIconsSprite" />
      <div v-html="riskiIconsSprite" />

      <riski-intro>
        <riski-searchbar id="riski-searchbar" :submit-query="submitQuery" :query="searchquery"
          :on-clear="resetInitialState" />
        <ul v-if="initial" class="example-chips" role="list" aria-label="Beispielfragen">
          <li v-for="question in EXAMPLE_QUESTIONS" :key="question">
            <button class="example-chip" @click="submitQuery(question)">
              {{ question }}
            </button>
          </li>
        </ul>
      </riski-intro>

      <div class="container">
        <div class="m-component__grid">
          <div class="main-body-container">
            <div ref="resultsArea" role="region" aria-label="Suchergebnisse" :aria-busy="loading">
              <!-- Accessibility: move aria-live to a small status element so
                   screen readers only announce milestones (e.g. when loading
                   completes) instead of every streaming update. Bind the
                   attribute so it's 'polite' only when loading transitions to
                   false; otherwise keep it 'off'. -->
              <div class="sr-status" aria-atomic="true" :aria-live="loading ? 'off' : 'polite'"
                style="position: absolute; left: -9999px; width: 1px; height: 1px; overflow: hidden;">
                <!-- Announce when results are ready -->
                <span
                  v-if="!loading && (found_answer != undefined || (!initial && found_answer == undefined && fehler == ''))">
                  Ergebnisse gefunden
                </span>
              </div>
              <div v-if="
                loading == false &&
                found_answer == undefined &&
                initial == false &&
                fehler == ''
              ">
                <muc-callout type="warning">
                  <template #header>Wir haben leider keine Antwort gefunden.</template>
                  <template #content>
                    Entschuldigung. Für ihre Frage konnte unsere Künstliche
                    Intelligenz leider kein passendes Ergebnis finden.
                    Vielleicht versuchen Sie es noch einmal mit einer anderen
                    Frage?
                  </template>
                </muc-callout>
              </div>
              <div v-if="found_answer != undefined || loading">
                <riski-response-card :riski-answer="found_answer" :is-streaming="loading"></riski-response-card>
              </div>
              <div v-if="fehler != ''">
                <muc-callout title="Fehler" type="error">
                  <template #header>Ein Fehler ist aufgetreten.</template>
                  <template #content>
                    {{ fehler }}
                  </template>
                </muc-callout>
              </div>
            </div>
            <div style="height: 48px"></div>
            <muc-callout title="Disclaimer" type="info" class="heading disclaimer-callout">
              <template #header>Rechtliche Hinweise</template>
              <template #content>
                Die von diesem System bereitgestellten Informationen dienen als
                erste Orientierung und es kann nicht zugesichert werden, dass
                diese tatsächlich korrekt sind. Wir arbeiten daran, dass die
                Informationen so korrekt wie möglich sind, können dafür jedoch
                keine Gewähr geben. Überprüfen sie die Ergebnisse daher bitte
                mittels der angegebenen Anträge und Dokumente selbständig um die
                Korrektheit zu garantieren, wo dies wichtig ist.
              </template>
            </muc-callout>
          </div>
        </div>
      </div>
    </div>
  </main>
</template>

<style>
@import "@muenchen/muc-patternlab-vue/assets/css/custom-style.css";
@import "@muenchen/muc-patternlab-vue/style.css";
@import "@muenchen/muc-patternlab-vue/muc-patternlab-vue.css";

.heading {
  margin-bottom: 0.5em;
}

.disclaimer-callout {
  margin-left: 0.375rem;
  margin-right: 0.375rem;
}

.example-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  list-style: none;
  /* remove bullets */
  margin: 12px 0 0 0;
  /* keep top spacing, remove default list margins */
  padding: 0;
  /* remove default list padding */
}

.example-chip {
  display: inline-flex;
  align-items: center;
  padding: 6px 14px;
  border: 1px solid #c0d0e0;
  border-radius: 20px;
  background: #fff;
  color: #005a9f;
  font-size: 0.88em;
  cursor: pointer;
  transition:
    background-color 0.15s ease,
    border-color 0.15s ease,
    box-shadow 0.15s ease;
  white-space: nowrap;
}

.example-chip:hover {
  background-color: #e5eef5;
  border-color: #005a9f;
}

.example-chip:focus-visible {
  outline: 2px solid #005a9f;
  outline-offset: 2px;
}

.example-chip:active {
  background-color: #d0e0f0;
  box-shadow: inset 0 1px 2px rgba(0, 0, 0, 0.1);
}

.main-body-container {
  margin-left: 20%;
  margin-right: 20%;
  display: flex;
  flex-direction: column;
  justify-content: center;
  width: 100%;
  padding-bottom: 56px;
  padding-top: 56px;
}

@media screen and (max-width: 768px) {
  .main-body-container {
    padding-top: 40px;
    padding-bottom: 40px;
  }
}

@media screen and (max-width: 768px) {
  .main-body-container {
    margin-left: 0%;
    margin-right: 0%;
  }
}
</style>
