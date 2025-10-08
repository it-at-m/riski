<script setup lang="ts">
import type DLFAnswer from "@/types/DLFAnswer";

import { MucCallout } from "@muenchen/muc-patternlab-vue";
import customIconsSprite from "@muenchen/muc-patternlab-vue/assets/icons/custom-icons.svg?raw";
import mucIconsSprite from "@muenchen/muc-patternlab-vue/assets/icons/muc-icons.svg?raw";
import { computed, nextTick, onMounted, ref } from "vue";

import type FrontendConfig from "./types/FrontendConfig";
import type { RetrievedDocument } from "./types/RetrievalResult";
import type RetrievalResult from "./types/RetrievalResult";
import type ScrubResult from "./types/ScrubResult";

import SearchService from "@/api/SearchService";
import dlfIconsSprite from "@/assets/custom-icons.svg?raw";
import riskiIntro from "@/components/riski-intro.vue";
import { DEFAULT_FRONTEND_CONFIG } from "@/util/constants";
import ConfigService from "./api/ConfigService";
import FeedbackState from "./types/FeedbackState";

let abortController = new AbortController();

const found_documents = ref<DLFAnswer[]>([]);
const loading_docs = ref<RetrievedDocument[]>([]);
const loading = ref<boolean>(false);
const initial = ref<boolean>(true);
const current_loading_step = ref<number>(0);
const progress_msg = ref<string>("Suche relevante Artikel");
const fehler = ref<string>("");
const feedback_state = defineModel({ default: FeedbackState.PENDING_SEARCH });
const current_run_id = ref<string>("");
const config = ref<FrontendConfig>(DEFAULT_FRONTEND_CONFIG);
const number_of_loading_steps = ref<number>(13);
const searchquery = ref<string>("");
const documentListRef = ref<HTMLElement | null>(null);

onMounted(() => {
  ConfigService.get().then((c) => {
    config.value = c;
  });
});

const loading_progress = computed(() => {
  return (current_loading_step.value / number_of_loading_steps.value) * 100;
});

/**
 * Callback function called when scrubbing is performed.
 * @param {ScrubResult} scrubResult - The result of the scrubbing operation.
 */
const onScrubbedCallback = (scrubResult: ScrubResult) => {
  current_loading_step.value = 2;
};

/**
 * Callback function for document retrieval.
 *
 * @param {RetrievalResult} retrievalResult - The retrieved documents.
 */
const onRetrievalCallback = (retrievalResult: RetrievalResult) => {
  current_run_id.value = retrievalResult.run_id;
  progress_msg.value = `Verarbeite relevante Artikel`;
  number_of_loading_steps.value =
    retrievalResult.retrieval_documents.length + 3;
  current_loading_step.value = 3;
  loading_docs.value = retrievalResult.retrieval_documents;
};

/**
 * Scrolls to the document list container with smooth behavior
 */
const scrollToResults = () => {
  nextTick(() => {
    if (documentListRef.value) {
      documentListRef.value.scrollIntoView({
        behavior: "smooth",
        block: "start",
      });
    }
  });
};

/**
 * Callback function for a succesfully processed document with the answer chain.
 *
 * @param {DLFAnswer} doc - The processed document.
 */
const onProcessedCallback = (doc: DLFAnswer) => {
  const isFirstDocument = found_documents.value.length === 0;
  found_documents.value.push(doc);
  current_loading_step.value = current_loading_step.value + 1;
  loading_docs.value = loading_docs.value.filter(
    (d) => d.name !== doc.doc_base_name
  );

  // Scroll to first result when it's found
  if (isFirstDocument) {
    feedback_state.value = FeedbackState.CONTEXTUAL;
    scrollToResults();
  }
};

/**
 * Callback function for a failed processing during the answer chain.
 *
 * @param {RetrievedDocument} failedDoc - The failed document.
 */
const onFailedCallback = (failedDoc: RetrievedDocument) => {
  current_loading_step.value = current_loading_step.value + 1;
  loading_docs.value = loading_docs.value.filter(
    (d) => d.name !== failedDoc.name
  );
};

/**
 * Callback function for the completion of all search callbacks (1 retrieval and n answer chains).
 */
const onCompleteCallback = () => {
  if(found_documents.value.length === 0) {
    feedback_state.value = FeedbackState.CONTEXTUAL;
  }
  loading.value = false;
};

const resetInitialState = () => {
  if (loading.value) {
    abortController.abort();
    abortController = new AbortController();
  }
  feedback_state.value = FeedbackState.PENDING_SEARCH;
  found_documents.value = [];
  loading_docs.value = [];
  loading.value = false;
  fehler.value = "";
  initial.value = true;
};

const resetLoadingState = () => {
  progress_msg.value = "Suche relevante Artikel";
  current_loading_step.value = 1;
  number_of_loading_steps.value = 12;
  found_documents.value = [];
  loading_docs.value = [];
  loading.value = true;
  fehler.value = "";
  feedback_state.value = FeedbackState.PENDING_SEARCH;
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
  if (loading.value) {
    abortController.abort();
    abortController = new AbortController();
  }
  resetLoadingState();

  SearchService.search(
    query,
    onProcessedCallback,
    onFailedCallback,
    onCompleteCallback,
    onRetrievalCallback,
    onScrubbedCallback,
    abortController.signal,
    config.value.scrubber_enabled
  ).catch((e: string) => {
    fehler.value = e;
  });
};

/**
 * Scores the given trace with user feedback
 *
 * @param {boolean} value - The value to score the result.
 */
const scoreResult = (value: boolean) => {
  if (current_run_id.value === "") {
    console.warn("No run_id available for scoring.");
  } else {
    SearchService.score({
      run_id: current_run_id.value,
      value: value,
    });
  }
};
</script>

<template>
  <link href="https://assets.muenchen.de/mde/1.0.6/css/muenchende-style.css" rel="stylesheet" />
  <main>
    <div>
      <div v-html="mucIconsSprite" />
      <div v-html="customIconsSprite" />
      <div v-html="dlfIconsSprite" />

      <riski-intro labelfor="riski-searchbar">
        <riski-searchbar id="riski-searchbar" :submit-query="submitQuery" :query="searchquery"
          :on-clear="resetInitialState" />
      </riski-intro>

      <div class="container">
        <div class="m-component__grid">
          <div class="main-body-container">            
            <div>
              <div v-if="
                loading == false &&
                found_documents.length == 0 &&
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
              <div v-if="fehler != ''">
                <muc-callout title="No documents found" type="error">
                  <template #header>Ein Fehler ist aufgetreten.</template>
                  <template #content>
                    {{ fehler }}
                  </template>
                </muc-callout>
              </div>              
            </div>
            <div style="height: 48px;"></div>
            <muc-callout title="Disclaimer" type="info" class="heading disclaimer-callout">
              <template #header>Rechtliche Hinweise</template>
              <template #content>
                Die von diesem System bereitgestellten Informationen dienen als
                erste Orientierung und können keine rechtliche oder
                fachspezifische Beratung ersetzen. 
                Die Stadt München übernimmt keine Gewähr für die Richtigkeit und
                Vollständigkeit der automatisch generierten Antworten und
                empfiehlt bei wichtigen Angelegenheiten den direkten Kontakt mit
                den zuständigen städtischen Behörden.
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



.content-container {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.progress-container {
  display: flex;
  justify-content: center;
}

@media screen and (max-width: 768px) {
  .main-body-container {
    margin-left: 0%;
    margin-right: 0%;
  }
}
</style>
