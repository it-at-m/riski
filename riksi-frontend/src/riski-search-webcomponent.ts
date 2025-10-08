import { defineCustomElement } from "vue";

import RiskiSearchVueComponent from "@/riski-search-webcomponent.ce.vue";

// convert into custom element constructor
const RiskiSearchWebcomponent = defineCustomElement(RiskiSearchVueComponent);

// register
customElements.define("riski-search-webcomponent", RiskiSearchWebcomponent);
