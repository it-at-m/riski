<script setup lang="ts">
import logo from "@/assets/mde-Logo_Sonne.svg";
</script>

<template>
  <header class="header-sticky">  
    <a class="header-link" href="https://risi.muenchen.de">  
      <div class="header-fullsize flex-shrink-0">
        <div class="container">
          <div class="row align-items-center justify-content-between no-gutters">
            <!-- Logo + Title -->
            <div class="col-10 col-md-8 d-flex align-items-center">
              <div id="logo_sonne" class="d-none d-md-block mr-3">
                  <img
                  :src="logo"
                  alt="Logo muenchen.de"
                  style="width: 105px; padding-top: 3px;"
                  />
              </div>
              <div class="font-weight-bold">
                <div class="header-big text-break">Rats­Informations­System</div>
                <div class="header-small text-right">München</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </a>
  </header>
</template>

<style>
@import "/fonts/fonts.css";

:host {
  font-family: 'Open Sans', Arial, sans-serif;
}

/* minimal local tweaks, global colors/fonts come from bootstrap-risi.css */
.header-sticky {
  position: sticky;
  top: 0;
  z-index: 999;
  background-color: var(--color-white, #fff); /* fallback if variable missing */
}

.header-link,
.header-link:hover {
  text-decoration: none;
}

.header-big {
  font-weight: bold;
  font-size: 1.25rem; /* match RIS */
}

.header-small {
  font-size: 0.875rem; /* match RIS */
  line-height: 1;
}

.row {
    padding-left: 20%;
    padding-right: 20%;
}

.ml-3 {
  margin-left: 1rem;
}
</style>