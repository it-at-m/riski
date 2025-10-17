<script setup lang="ts">
import type RiskiAnswer from "@/types/RiskiAnswer";

import { MucCallout } from "@muenchen/muc-patternlab-vue";
import customIconsSprite from "@muenchen/muc-patternlab-vue/assets/icons/custom-icons.svg?raw";
import mucIconsSprite from "@muenchen/muc-patternlab-vue/assets/icons/muc-icons.svg?raw";
import { ref } from "vue";

import SearchService from "@/api/SearchService";
import riskiIconsSprite from "@/assets/custom-icons.svg?raw";
import riskiIntro from "@/components/riski-intro.vue";
import riskiSearchbar from "@/components/riski-searchbar.vue";
import RiskiResponseCard from "@/components/common/riski-response-card.vue";
import RiskiProgress from "@/components/riski-progress.vue";

let abortController = new AbortController();

const found_answer = ref<RiskiAnswer>();

const loading = ref<boolean>(false);
const initial = ref<boolean>(true);
const fehler = ref<string>("");
const searchquery = ref<string>("");

/**
 * Callback function for a succesfully processed document with the answer chain.
 *
 * @param {RiskiAnswer} answer - The processed document.
 */
const onProcessedCallback = (answer: RiskiAnswer) => {
  found_answer.value = answer;
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
      </riski-intro>

      <div class="container">
        <div class="m-component__grid">
          <div class="main-body-container">            
            <div>
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
              <div v-else-if="found_answer != undefined">
                  <riski-response-card :riski-answer="found_answer"></riski-response-card>
              </div>
              <div v-if="fehler != ''">
                <muc-callout title="No information found" type="error">
                  <template #header>Ein Fehler ist aufgetreten.</template>
                  <template #content>
                    {{ fehler }}
                  </template>
                </muc-callout>
              </div>
              <div class="progress-container">
                <riski-progress v-if="loading" :progress="40"></riski-progress>
              </div>
            </div>
            <div style="height: 48px;"></div>
            <muc-callout title="Disclaimer" type="info" class="heading disclaimer-callout">
              <template #header>Rechtliche Hinweise</template>
              <template #content>
                Die von diesem System bereitgestellten Informationen dienen als
                erste Orientierung und es kann nicht zugesichert werden, dass diese tatsächlich korrekt sind. 
                Wir arbeiten daran, dass die Informationen so korrekt wie möglich sind, können dafür jedoch keine Gewähr geben.
                Überprüfen sie die Ergebnisse daher bitte mittels der angegeben Anträge und Dokumente selbständig um die 
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

.heading {
  margin-bottom: 0.5em;
}

.disclaimer-callout {
  margin-left: 0.375rem;
  margin-right: 0.375rem;
}

.progress-container {
  display: flex;
  justify-content: center;
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
