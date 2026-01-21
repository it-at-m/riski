FROM registry.access.redhat.com/ubi10/ubi-minimal:latest

USER root
RUN microdnf install -y glibc-all-langpacks && microdnf clean all
RUN mkdir -p /home/app && chown -R 1000:0 /home/app

ENV HOME=/home/app
ENV LANG=de_DE.UTF-8 \
    LC_ALL=de_DE.UTF-8 \
    LANGUAGE=de_DE:de

RUN locale -a | grep -q de_DE.utf8 || (echo "de_DE.UTF-8 locale not found" && exit 1)

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/


WORKDIR /app
# Give permissions to all so random UID can write
# This should be compatible with OpenShift and plain K8s
RUN chown -R root:0 /app && chmod -R g=u /app

ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy

COPY riski-extractor/pyproject.toml riski-extractor/uv.lock ./
COPY riski-core/pyproject.toml /app/riski-core/

WORKDIR /app/extractor
COPY riski-extractor /app/extractor/
COPY riski-core /app/riski-core/

RUN --mount=type=cache,target=/home/app/.cache/uv \
    uv sync --no-dev --locked

ENV PATH="/app/extractor/.venv/bin:$PATH"

ENTRYPOINT ["python", "app.py"]
