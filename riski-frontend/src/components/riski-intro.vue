<script setup lang="ts"></script>

<template>
  <div
    class="m-intro m-intro-static-image"
    style="background-color: var(--color-neutrals-blue-xlight)"
  >
    <div class="container">
      <div class="muc-intro-content padded-intro">
        <h1 class="m-intro-vertical__title">RIS KI Suche (Beta-Version)</h1>

        <div class="m-intro-vertical__content">
          <div class="intro-info">
            <p>
              Hier können Sie Ihre Frage zu öffentlich verfügbaren Inhalten aus
              dem Ratsinformationssystem (RIS) stellen. Die Suche liefert ihnen
              dann eine zusammenfassende Antwort sowie relevante Dokumente und
              die Bezeichnungen relevanter Anträge.
            </p>
            <div style="margin-bottom: 24px"></div>
            <slot></slot>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.padded-intro {
  padding-left: 20%;
  padding-right: 20%;
}

@media screen and (max-width: 768px) {
  .padded-intro {
    padding-left: 0;
    padding-right: 0;
  }
}

.intro-info {
  font-size: 16px;
  font-weight: 400;
  padding-bottom: 48px;
  line-height: 24px;
  word-wrap: break-word;
}

.intro-highlight {
  font-weight: 700;
}

.m-intro-static-image {
  padding-bottom: 0;
  margin-bottom: 0;
  padding-top: 0;
}
</style>
