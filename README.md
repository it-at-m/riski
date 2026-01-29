# RIS-KI

Find information in munich's political information system RIS with the help of ai.

## Project Information

[![Made with love by it@M][made-with-love-shield]][itm-opensource]
[![GitHub license][license-shield]][license]

<!-- Tech Stack -->

### Technology Stack

![Supported python versions][python-versions-shield]
![Supported npm versions][npm-versions-shield]
[![uv][uv-shield]][uv]
[![FastAPI][fastapi-shield]][fastapi]
[![vue][vue-shield]][vue]
[![Postgres][postgres-shield]][postgres]
[![LangGraph][langgraph-shield]][langgraph]

<!-- CI -->

### Build Status

[![Backend tests][backend-tests-shield]][backend-tests]

<!-- Container Images -->

### Container Images

[![Extractor][extractor-version-shield]][extractor-container]
[![Backend][backend-version-shield]][backend-container]

<!-- ABOUT THE PROJECT -->

[made-with-love-shield]: https://img.shields.io/badge/made%20with%20%E2%9D%A4%20by-it%40M-blue?style=for-the-badge
[license-shield]: https://img.shields.io/github/license/it-at-m/riski?style=for-the-badge&color=blue
[python-versions-shield]: https://img.shields.io/badge/python-3.13-blue?style=for-the-badge
[npm-versions-shield]: https://img.shields.io/badge/node-20+-blue?style=for-the-badge
[uv-shield]: https://img.shields.io/badge/⚡-uv-blue?style=for-the-badge
[fastapi-shield]: https://img.shields.io/badge/fastapi-blue?style=for-the-badge&logo=fastapi&logoColor=white
[vue-shield]: https://shields.io/badge/Vue.js-blue?logo=vuedotjs&style=for-the-badge&logoColor=white
[postgres-shield]: https://img.shields.io/badge/postgres-blue?&style=for-the-badge&logo=postgresql&logoColor=white
[langgraph-shield]: https://img.shields.io/badge/LangGraph-blue?&style=for-the-badge&logo=langgraph&logoColor=white
[extractor-version-shield]: https://img.shields.io/github/v/tag/it-at-m/riski?filter=extractor*&label=riski-extractor&style=for-the-badge&color=blue
[backend-version-shield]: https://img.shields.io/github/v/tag/it-at-m/riski?filter=backend*&label=riski-backend&style=for-the-badge&color=blue
[backend-tests-shield]: https://github.com/it-at-m/riski/actions/workflows/backend-tests.yml/badge.svg
[backend-tests]: https://github.com/it-at-m/riski/actions/workflows/backend-tests.yml
[extractor-container]: https://github.com/it-at-m/riski/pkgs/container/riski%2Friski-extractor
[backend-container]: https://github.com/it-at-m/riski/pkgs/container/riski%2Friski-backend
[itm-opensource]: https://opensource.muenchen.de/
[license]: https://github.com/it-at-m/riski/blob/main/LICENSE
[uv]: https://github.com/astral-sh/uv
[fastapi]: https://fastapi.tiangolo.com/
[postgres]: https://www.postgresql.org/
[langgraph]: https://langchain-ai.github.io/langgraph/
[vue]: https://vuejs.org/

## Roadmap

See the [open issues](https://github.com/it-at-m/riski/issues) for a full list of proposed features (and known issues).

## Set up

_How to get started with this project_

## Documentation

### Development

#### Releasing backend or extractor images

Use the `tag-version.ps1` helper to create semantic tags that trigger the
GitHub Actions workflows responsible for building the `riski-backend` and
`riski-extractor` container images.

```powershell
./tag-version.ps1
```

1. Select the service (`backend` or `extractor`).
2. Choose the version bump (`major`, `minor`, or `patch`).
3. When prompted, decide whether the script should also bump the detected manifest (for example `riski-backend/pyproject.toml` or a `package.json`) to the same version. This keeps the package metadata, container tags, and badges in sync.
4. Confirm the suggested tag (for example `backend-1.2.0`).
5. Confirm pushing the tag to `origin` to start the corresponding Docker release workflow.

After a successful push, the workflow builds and publishes the image to GitHub Container Registry.

#### Syncing `riski-core` changes into other services

The Python services (`riski-backend`, `riski-document-pipeline`, `riski-extractor`) import the local `riski-core` package via path dependencies.
Whenever you change `riski-core`, rerun the dependency install inside each consumer so uv rebuilds the local package:

```powershell
uv sync --reinstall-package core
```

Run the command from the respective service folder (for example `riski-backend`) so `uv` picks up the correct `pyproject.toml`.

## Contributing

Contributions are what make the open source community such an amazing place to learn, inspire, and create. Any contributions you make are **greatly appreciated**.

If you have a suggestion that would make this better, please open an issue with the tag "enhancement", fork the repo and create a pull request. You can also simply open an issue with the tag "enhancement".
Don't forget to give the project a star! Thanks again!

1. Open an issue with the tag "enhancement"
2. Fork the Project
3. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
4. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
5. Push to the Branch (`git push origin feature/AmazingFeature`)
6. Open a Pull Request

More about this in the [CODE_OF_CONDUCT](/CODE_OF_CONDUCT.md) file.

## License

Distributed under the MIT License. See [LICENSE](LICENSE) file for more information.

## Contact

it@M - [kicc@muenchen.de](mailto:kicc@muenchen.de)
