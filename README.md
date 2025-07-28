## Customize this file after creating the new REPO and remove this lines.
What to adjust:  
* Add the your project or repo name direct under the logo.
* Add a short and long desciption.
* Add links for your final repo to report a bug or request a feature.
* Add list of used technologies.
* If you have, add a roadmap or remove this section.
* Fill up the section for set up and documentation.
 * Start in this file only with documentation and link to the docs folder.
* Add more project shields. Use [shields.io](https://shields.io/) with style `for-the-badge`.

## ------- end to remove -------
<!-- add Project Logo, if existing -->

# repo or project name

[![Made with love by it@M][made-with-love-shield]][itm-opensource]
<!-- feel free to add more shields, style 'for-the-badge' -> see https://shields.io/badges -->

*Add a description from your project here.*


### Built With

The documentation project is built with technologies we use in our projects:

* *write here the list of used technologies*

## Roadmap

*if you have a ROADMAP for your project add this here*


See the [open issues](#) for a full list of proposed features (and known issues).


## Set up
*how can i start and fly this project*

## Documentation
*what insights do you have to tell*

```mermaid
graph TD;
    A-->B;
    A-->C;
    B-->D;
    C-->D;
```

use [diagrams](https://docs.github.com/en/get-started/writing-on-github/working-with-advanced-formatting/creating-diagrams).

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

it@M - opensource@muenchen.de

<!-- project shields / links -->
[made-with-love-shield]: https://img.shields.io/badge/made%20with%20%E2%9D%A4%20by-it%40M-yellow?style=for-the-badge
[itm-opensource]: https://opensource.muenchen.de/

# Template Python @ KICC / LHM

Python-Template mit allen relevanten Technologien.

[[_TOC_]]

## Prerequisites

- uv ist installiert: https://docs.astral.sh/uv/getting-started/installation/#standalone-installer

## Commands

### Pre-Commit Hooks

```bash
uv sync
# Pre-commit initalisieren
uv run pre-commit install

# Pre-commit manuell ausführen
uv run pre-commit run

# Pre-commit Hooks updaten
uv run pre-commit autoupdate
```

### Package Management

```bash
# Environment syncen
uv sync

# Package adden
uv add <package>

# Package entfernen
uv remove <package>

# Dev Package adden (remove gleich wie normal)
uv add --dev <package>

# Packages updaten
uv lock -U

# Manuell requirements.txt generieren
rm requirements.txt
uv pip compile --universal pyproject.toml -o requirements.txt
```

### Linting & Formatting

```bash
# Linter manuell ausführen inkl. autofix
uv run ruff check --fix

# Formatter manuell ausführen
uv run ruff format
```

### Applikation ausführen

```bash
# Applikation starten
uv run app.py -d
```

## Eingesetzte Technologien

| Verwendungszweck            | Paket / Technologien | Beschreibung                                                           |
| --------------------------- | -------------------- | ---------------------------------------------------------------------- |
| Programmiersprache          | [Python]             | -                                                                      |
| Paketverwaltung             | [uv]                 | Schnelle Paketverwaltung inkl. Environment & Python-Version-Management |
| Linting & Formatting        | [ruff]               | Schnelles Linting und Formatting für Python                            |
| Kontrolle der Code-Qualität | [pre-commit]         | Automatisierte Tests vor jedem Commit                                  |
| CI/CD                       | [GitLab CI]          | Automatisierte Builds und Deployments                                  |
| Containerisierung           | RedHat [S2I]         | Automaisierte Containerisierung in OpenShift                           |

<!-- Links for better editing in markdown -->

[Python]: https://www.python.org/
[uv]: https://docs.astral.sh/uv/
[ruff]: https://docs.astral.sh/ruff/
[pre-commit]: https://pre-commit.com/
[GitLab CI]: .gitlab-ci.yml
[S2I]: https://github.com/sclorg/s2i-python-container

<!-- End of links -->

### Standard-Pakete

Folgende Pakete sind "defaults", aber aktuell nicht im Projekt installiert:

| Verwendungszweck            | Paket                               | Beschreibung                                              |
| --------------------------- | ----------------------------------- | --------------------------------------------------------- |
| Webserver + -framework      | [uvicorn] + [FastAPI]               | ASGI-kompatibles Serverkit für Python                     |
| Simple WebUI                | [gradio]                            | WebUI für Python, basierend auf FastAPI, gut für ML-Demos |
| Datenvalidierung            | [Pydantic]                          | Datenvalidierung und -serialisierung                      |
| YAML-Parser                 | [PyYAML]                            | YAML Parser für Python                                    |
| Git-Integration             | [GitPython]                         | Git-Integration für Python                                |
| Logging                     | [PythonLogging]                     | Logging für Python                                        |
| HTTP-Client                 | [httpx]                             | HTTP-Client für Python                                    |
| Datenbank-ORM / SQL-Toolkit | [SQLAlchemy]                        | ORM für Python                                            |
| LLMs / Agents               | [LangChain] + [LangGraph]           | Framework für LLMs / Agents                               |
| Environment-Variablen       | [python-dotenv]                     | Environment-Variablen laden                               |
| SSL-Zertifikate             | [truststore]                        | SSL-Zertifikate injecten                                  |
| Retries bei Exceptions      | [stamina]                           | Wrapper um tenacity, der einfache Retries ermöglicht      |
| HTML-Parser                 | [beautifulsoup4]                    | HTML-Parser für Python                                    |
| Markdown-Converter          | [markdownify]                       | Markdown-Converter, basierend auf BeautifulSoup4          |
| Progressbars                | [tqdm]                              | Extensible progressbar mit weiter Verbreitung             |
| Datenanalyse                | [pandas]                            | Datenmanipulation und -analyse                            |
| Numerische Berechnungen     | [numpy]                             | Numerische Berechnungen und Arrays                        |
| Machine Learning            | [scikit-learn]                      | Framework für Machine Learning                            |
| Plotting                    | [matplotlib] / [seaborn] / [plotly] | Plotting-Frameworks für Python                            |
| Geodatenanalyse             | [geopy] + [geopandas]               | Geodatenanalyse und -manipulation                         |
| Transformer-Modelle         | [transformers]                      | NLP-Framework für Transformer-Modelle                     |
| Deep Learning               | [PyTorch]                           | Framework für Deep Learning und neuronale Netze           |

<!-- Links for better editing in markdown -->

[uvicorn]: https://www.uvicorn.org/
[FastAPI]: https://fastapi.tiangolo.com/
[gradio]: https://gradio.app/
[Pydantic]: https://docs.pydantic.dev/latest/
[PyYAML]: https://pyyaml.org/
[GitPython]: https://gitpython.readthedocs.io/en/stable/
[PythonLogging]: https://docs.python.org/3/library/logging.html
[httpx]: https://www.python-httpx.org/
[SQLAlchemy]: https://www.sqlalchemy.org/
[LangChain]: https://python.langchain.com/
[LangGraph]: https://langchain-ai.github.io/langgraph/
[python-dotenv]: https://pypi.org/project/python-dotenv/
[truststore]: https://pypi.org/project/truststore/
[stamina]: https://stamina.hynek.me/en/stable/
[beautifulsoup4]: https://www.crummy.com/software/BeautifulSoup/bs4/doc/
[markdownify]: https://github.com/matthewwithanm/python-markdownify/
[tqdm]: https://tqdm.github.io/
[pandas]: https://pandas.pydata.org/
[numpy]: https://numpy.org/
[transformers]: https://huggingface.co/docs/transformers/
[PyTorch]: https://pytorch.org/
[scikit-learn]: https://scikit-learn.org/stable/
[matplotlib]: https://matplotlib.org/stable/index.html
[seaborn]: https://seaborn.pydata.org/
[plotly]: https://plotly.com/python/
[geopy]: https://geopy.readthedocs.io/en/stable/
[geopandas]: https://geopandas.org/en/stable/#

<!-- End of links -->

### Standard-Komponenten

| Verwendungszweck   | Komponente   | SDK                    | Beschreibung                           | Template etc.     |
| ------------------ | ------------ | ---------------------- | -------------------------------------- | ----------------- |
| Vektor-Datenbank   | [Qdrant]     | [qdrant-client]        | Containerisierte Vektor-Datenbank      | [Qdrant-Template] |
| Cache              | [Valkey]     | [valkey-sdk]           | Containerisierte Key-Value-Datenbank   | TODO              |
| SQL-Datenbank      | [PostgreSQL] | [SQLAlchemy]           | Open Source SQL-Datenbank              | TODO              |
| ML Model Inference | [LiteLLM]    | [LangChain] via OpenAI | Zentraler Proxy für AI Model Inference | [LiteLLM-Repo]    |
| ML Tracing         | [Langfuse]   | [langfuse-sdk]         | Tracing für LLM-Applikationen etc.     | [Langfuse-Repo]   |

<!-- Links for better editing in markdown -->

[qdrant]: https://qdrant.tech/documentation/
[qdrant-client]: https://github.com/qdrant/qdrant-client
[qdrant-template]: https://git.muenchen.de/kicc/templates/qdrant-template
[valkey]: https://github.com/valkey-io/valkey
[valkey-sdk]: https://github.com/valkey-io/valkey-py
[PostgreSQL]: https://it-services.muenchen.de/sp?id=sc_cat_item&sys_id=a98ab0ce1b5fd594948e657f7b4bcbad&table=sc_cat_item
[SQLAlchemy]: https://www.sqlalchemy.org/
[LiteLLM]: https://docs.litellm.ai/docs/
[LiteLLM-Repo]: https://git.muenchen.de/kicc/rag/ki-services/litellm-helm
[Langfuse]: https://langfuse.com/docs
[langfuse-sdk]: https://langfuse.com/docs/sdk/python/decorators
[Langfuse-Repo]: https://git.muenchen.de/kicc/rag/ki-services/langfuse-helm

<!-- End of links -->

Perspektivisch sollen auch folgende Technologien eingesetzt werden:

- **pytest** (Unit-Tests)
- **locust** (Performance/Load-Tests)
