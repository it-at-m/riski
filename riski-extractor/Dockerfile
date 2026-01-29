# Smallest ubi10 image
FROM registry.access.redhat.com/ubi10/ubi-micro:latest@sha256:fc8e116afac12a9164be775e21483da7b6e86f91d8e9e6e79dee23afe4e58468

USER root
RUN microdnf install -y glibc-all-langpacks && microdnf clean all
RUN mkdir -p /home/app && chown -R 1000:0 /home/app

ENV HOME=/home/app
ENV LANG=de_DE.UTF-8 \
    LC_ALL=de_DE.UTF-8 \
    LANGUAGE=de_DE:de

RUN locale -a | grep -q de_DE.utf8 || (echo "de_DE.UTF-8 locale not found" && exit 1)

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

ENV UV_PROJECT_ENVIRONMENT=/app/extractor/.venv

WORKDIR /app
ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy

# Leverage layer cache
COPY riski-extractor/pyproject.toml riski-extractor/uv.lock ./
COPY riski-core/pyproject.toml /app/riski-core/

WORKDIR /app/extractor
COPY riski-extractor /app/extractor/
COPY riski-core /app/riski-core/

RUN --mount=type=cache,target=/home/app/.cache/uv \
    uv sync --no-dev --locked

# Metadata for the image
ARG IMAGE_CREATED="unknown"
ARG IMAGE_REVISION="unknown"
ARG IMAGE_VERSION="unknown"
LABEL org.opencontainers.image.authors='Landeshauptstadt München <opensource@muenchen.de>' \
    org.opencontainers.image.vendor='Landeshauptstadt München' \
    org.opencontainers.image.created="$IMAGE_CREATED" \
    org.opencontainers.image.revision="$IMAGE_REVISION" \
    org.opencontainers.image.version="$IMAGE_VERSION" \
    org.opencontainers.image.url='https://github.com/it-at-m/riski/pkgs/container/riski-extractor' \
    org.opencontainers.image.documentation='https://github.com/it-at-m/riski/README.md' \
    org.opencontainers.image.source='https://github.com/it-at-m/riski' \
    org.opencontainers.image.licenses='MIT' \
    org.opencontainers.image.title='riski-extractor' \
    org.opencontainers.image.description="Python application for extracting information from munich's political information system RIS"

# Give permissions to all so random UID can write
# This should be compatible with OpenShift and plain K8s
RUN chown -R root:0 /app && chmod -R g=u /app

USER 1000:0

# Place executables in the environment at the front of the path
ENV PATH="/app/extractor/.venv/bin:$PATH"

# Disable tqdm for cleaner logs
ENV TQDM_DISABLE=1
ENV HF_HUB_DISABLE_PROGRESS_BARS=1

# Disable python warnings
ENV PYTHONWARNINGS="ignore"

ENV APP_VERSION=${IMAGE_VERSION}

# Reset the entrypoint, don't invoke `uv`
ENTRYPOINT ["/app/extractor/.venv/bin/python", "app.py"]