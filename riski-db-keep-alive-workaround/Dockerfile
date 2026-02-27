# mini for microdnf
FROM registry.access.redhat.com/ubi10/ubi-minimal:latest@sha256:a74a7a92d3069bfac09c6882087771fc7db59fa9d8e16f14f4e012fe7288554c

USER root
RUN microdnf install -y glibc-all-langpacks && microdnf clean all
RUN mkdir -p /home/app && chown -R 1000:0 /home/app

ENV HOME=/home/app
ENV LANG=de_DE.UTF-8 \
    LC_ALL=de_DE.UTF-8 \
    LANGUAGE=de_DE:de

RUN locale -a | grep -q de_DE.utf8 || (echo "de_DE.UTF-8 locale not found" && exit 1)

COPY --from=ghcr.io/astral-sh/uv:latest@sha256:94a23af2d50e97b87b522d3cea24aaf8a1faedec1344c952767434f69585cbf9 /uv /uvx /bin/

ENV UV_PROJECT_ENVIRONMENT=/app/db-keep-alive-workaround/.venv

WORKDIR /app
ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy

# Leverage layer cache
COPY riski-db-keep-alive-workaround/pyproject.toml riski-db-keep-alive-workaround/uv.lock ./

WORKDIR /app/db-keep-alive-workaround
COPY riski-db-keep-alive-workaround /app/db-keep-alive-workaround/

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
    org.opencontainers.image.url='https://github.com/it-at-m/riski/pkgs/container/riski%2Friski-db-keep-alive-workaround' \
    org.opencontainers.image.documentation='https://github.com/it-at-m/riski/README.md' \
    org.opencontainers.image.source='https://github.com/it-at-m/riski' \
    org.opencontainers.image.licenses='MIT' \
    org.opencontainers.image.title='riski-db-keep-alive-workaround' \
    org.opencontainers.image.description="Python application for keeping db connections healthy"

# Give permissions to all so random UID can write
# This should be compatible with OpenShift and plain K8s
RUN chown -R root:0 /app && chmod -R g=u /app

USER 1000:0

# Place executables in the environment at the front of the path
ENV PATH="/app/db-keep-alive-workaround/.venv/bin:$PATH"

# Disable tqdm for cleaner logs
ENV TQDM_DISABLE=1
ENV HF_HUB_DISABLE_PROGRESS_BARS=1

# Disable python warnings
ENV PYTHONWARNINGS="ignore"

ENV APP_VERSION=${IMAGE_VERSION}

# Reset the entrypoint, don't invoke `uv`
ENTRYPOINT ["/app/db-keep-alive-workaround/.venv/bin/python", "app.py"]