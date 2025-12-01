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

Compilation and Hot-Reloading for development (mock data)

```bash
npm run dev
```

Run the component against the real backend (expects `http://localhost:8080`)

```bash
npm run dev-no-mock
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
<riski-search-webcomponent></riski-search-webcomponent>
```

## AG-UI LangGraph Integration

The webcomponent now talks to the RISKI backend via the AG-UI LangGraph protocol.

- The backend endpoint must expose `POST /api/ag-ui/riskiagent` at the path `/api/ag-ui/riskiagent`.
- Configure the frontend to reach the backend by setting `VITE_VUE_APP_API_URL` in your `.env.*` file, e.g. `VITE_VUE_APP_API_URL=http://localhost:8080` (or rely on the Vite dev proxy when running `npm run dev-no-mock`).
- `npm run dev` keeps the existing mocked answer for UI work, while `npm run dev-no-mock` proxies `/api` calls to the backend on `http://localhost:8080` and streams the real LangGraph response.

No additional UI changes are necessary: triggering a search automatically connects to the LangGraph agent and renders the streamed answer once complete.
