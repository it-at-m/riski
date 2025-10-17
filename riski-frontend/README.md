## DLF Frontend

Builds a custom webcomponent that can be used. Build with:

- [Vue.js](https://vuejs.org/)
- [Refarch-Webcomponent-Starter](https://github.com/it-at-m/refarch-templates/tree/main/refarch-webcomponent)
- [Muc-Patternlab als Komponentenlibrary](https://it-at-m.github.io/muc-patternlab-vue/)

## Installation

Installation of dependencies

```
npm install
```

Compilation and Hot-Reloading for development

```
npm run dev
```

Compilation and minification for production

```
npm run build
```

Linting of source code files (ESLint and Prettier)

```
npm run lint
```

Automatic fixing of source code files (Linting and formatting)

```
npm run fix
```

Customization of configuration

See [Configuration Reference](https://vitejs.dev/config/).

# Usage

1. Add Import to page:
   `<script src="pathtoloader/loader.js" type="module"></script>`
2. Add Element to page

```html
<dlf-search-webcomponent></dlf-search-webcomponent>
```
