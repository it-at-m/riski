# Small ubi10 image
FROM registry.access.redhat.com/ubi10/ubi-minimal:latest@sha256:2c20ac20ca1ecbbbd583603feabd9cc51e7e8ea5a82e5088e20a9494794b2574

COPY --from=ghcr.io/astral-sh/uv:latest@sha256:b46b03ddfcfbf8f547af7e9eaefdf8a39c8cebcba7c98858d3162bd28cf536f6 /uv /uvx /bin/

ENV UV_PROJECT_ENVIRONMENT=/app/oparl/.venv

# Install the project into `/app`
WORKDIR /app/oparl
# Enable bytecode compilation
ENV UV_COMPILE_BYTECODE=1

# Copy from the cache instead of linking since it's a mounted volume
ENV UV_LINK_MODE=copy

# Leverage layer cache: install transitive deps before copying app code
COPY riski-oparl/pyproject.toml riski-oparl/uv.lock ./
COPY riski-core /app/riski-core/

# Install the transitive dependencies
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --no-dev --locked --no-install-project

# Copy the application files
COPY riski-oparl /app/oparl
COPY riski-core /app/riski-core

# Install the project
RUN --mount=type=cache,target=/root/.cache/uv \
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
    org.opencontainers.image.url='https://github.com/it-at-m/riski/pkgs/container/riski%2Friski-oparl' \
    org.opencontainers.image.documentation='https://github.com/it-at-m/riski/README.md' \
    org.opencontainers.image.source='https://github.com/it-at-m/riski' \
    org.opencontainers.image.licenses='MIT' \
    org.opencontainers.image.title='riski-oparl' \
    org.opencontainers.image.description="OParl 1.1 publishing API for Munich's political information system RIS"

# Give permissions to all so random UID can write
# This should be compatible with OpenShift and plain K8s
RUN chown -R root:0 /app && chmod -R g=u /app

# Place executables in the environment at the front of the path
ENV PATH="/app/oparl/.venv/bin:$PATH"

# Disable python warnings (the core data model emits benign SQLAlchemy warnings)
ENV PYTHONWARNINGS="ignore"

# Bind to all interfaces inside the container
ENV RISKI_OPARL__SERVER_HOST=0.0.0.0
ENV RISKI_OPARL__SERVER_PORT=8082

EXPOSE 8082

# Reset the entrypoint, don't invoke `uv`
ENTRYPOINT ["/app/oparl/.venv/bin/python", "main.py"]
