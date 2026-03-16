<script setup lang="ts">
defineProps<{
  documentationUrl: string;
  contactUrl: string;
  impressumUrl: string;
  townhallbulletinUrl: string;
}>();
</script>
<template>
  <footer>
    <div class="footer-bottom-fullsize flex-shrink-0">
      <div
        class="container"
        style="padding-top: 8px; padding-bottom: 8px"
      >
        <div class="row justify-content-between">
          <div class="col-12 col-md-6 col-lg-auto text-center text-lg-left">
            <ul
              class="footer-link-list list-group list-group-horizontal-lg list-group-flush list-unstyled"
            >
              <!-- TODO: Kontakt anpassen? -->
              <li>
                <a
                  target="_blank"
                  rel="noopener"
                  :href="contactUrl"
                  >Kontakt</a
                >
              </li>
              <li>
                <a
                  target="_blank"
                  rel="noopener"
                  :href="impressumUrl"
                  >Impressum &amp; Datenschutz</a
                >
              </li>
            </ul>
          </div>
          <div class="col-12 col-md-6 col-lg-auto text-center text-lg-right">
            <ul
              class="footer-link-list list-group list-group-horizontal-lg list-group-flush list-unstyled"
            >
              <li>
                <a
                  target="_blank"
                  rel="noopener"
                  :href="townhallbulletinUrl"
                  >Rathaus-Umschau</a
                >
              </li>
              <li>
                <a
                  target="_blank"
                  rel="noopener"
                  :href="documentationUrl"
                  >Hilfe und FAQ</a
                >
              </li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  </footer>
</template>
