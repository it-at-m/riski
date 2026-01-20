# Smallest ubi10 image
FROM registry.access.redhat.com/ubi10/ubi-micro:latest@sha256:fc8e116afac12a9164be775e21483da7b6e86f91d8e9e6e79dee23afe4e58468

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Install the project into `/app`
WORKDIR /app

# Enable bytecode compilation
ENV UV_COMPILE_BYTECODE=1

# Copy from the cache instead of linking since it's a mounted volume
ENV UV_LINK_MODE=copy

# Leverage layer cache: nur Lockfiles/Metadaten zuerst
COPY riski-document-pipeline/pyproject.toml riski-document-pipeline/uv.lock /app/document-pipeline/
COPY riski-core/pyproject.toml /app/riski-core/

WORKDIR /app/document-pipeline


COPY riski-document-pipeline/ /app/document-pipeline/
COPY riski-core/ /app/riski-core/

# Install the project
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --no-dev --locked
ARG IMAGE_CREATED="unknown"
ARG IMAGE_REVISION="unknown"
ARG IMAGE_VERSION="unknown"
LABEL org.opencontainers.image.authors='Landeshauptstadt München <opensource@muenchen.de>' \
    org.opencontainers.image.vendor='Landeshauptstadt München' \
    org.opencontainers.image.created="$IMAGE_CREATED" \
    org.opencontainers.image.revision="$IMAGE_REVISION" \
    org.opencontainers.image.version="$IMAGE_VERSION" \
    org.opencontainers.image.url='https://github.com/it-at-m/riski/pkgs/container/riski-document-pipeline' \
    org.opencontainers.image.documentation='https://github.com/it-at-m/riski/README.md' \
    org.opencontainers.image.source='https://github.com/it-at-m/riski' \
    org.opencontainers.image.licenses='MIT' \
    org.opencontainers.image.title='riski-document-pipeline' \
    org.opencontainers.image.description="Python application for OCR processing of PDF documents from munich's political information system RIS"

# Give permissions to all so random UID can write
# This should be compatible with OpenShift and plain K8s
RUN chown -R root:0 /app && chmod -R g=u /app

ENV PATH="/app/document-pipeline/.venv/bin:$PATH"

# Disable tqdm for cleaner logs
ENV TQDM_DISABLE=1
ENV HF_HUB_DISABLE_PROGRESS_BARS=1

# Disable python warnings
ENV PYTHONWARNINGS="ignore"

ENV APP_VERSION=${IMAGE_VERSION}

WORKDIR /app/document-pipeline
ENTRYPOINT ["python", "main.py"]
