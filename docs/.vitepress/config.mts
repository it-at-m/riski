import { defineConfig } from "vitepress";
import { withMermaid } from "vitepress-plugin-mermaid";

// https://vitepress.dev/reference/site-config
const vitepressConfig = defineConfig({
  title: "RISKI Docs",
  description: "TBD",
  base: "/riski/",
  head: [
    [
      "link",
      {
        rel: "icon",
        href: `https://assets.muenchen.de/logos/lhm/icon-lhm-muenchen-32.png`,
      },
    ],
  ],
  lastUpdated: true,
  themeConfig: {
    // https://vitepress.dev/reference/default-theme-config
    nav: [
      { text: "Home", link: "/" },
      {
        text: "Docs",
        items: [
          {
            text: "Artificial intelligence for Munich",
            link: "https://ki.muenchen.de",
          },
        ],
      },
    ],
    sidebar: [
      {
        text: "ADR",
        link: "/adr",
        items: [
          {
            text: "01: System architecture",
            link: "/adr/architecture_overview",
          },
          {
            text: "02: Data Model",
            link: "/adr/datenmodell",
          },
          {
            text: "03: Extraction Pipeline",
            link: "/adr/extract_process",
          },
          {
            text: "04: Evaluation Docling",
            link: "/adr/eval_docling",
          },
        ],
      },
      {
        text: "Components",
        link: "/components",
        items: [
          {
            text: "Kafka message broker",
            link: "/components/kafka",
          },
        ],
      },
      {
        text: "RIS",
        link: "/ris",
        items: [
          {
            text: "Programmatic query of the RIS",
            link: "/ris/ris_verwendung",
          },
        ],
      },
    ],
    socialLinks: [{ icon: "github", link: "https://github.com/it-at-m/riski" }],
    footer: {
      message: `<a href="https://ki.muenchen.de/impressum">Impress and Contact</a>`,
    },
    outline: {
      level: "deep",
    },
    search: {
      provider: "local",
    },
  },
  markdown: {
    image: {
      lazyLoading: true,
    },
  },
});

export default withMermaid(vitepressConfig);
