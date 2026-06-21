FROM node:22.23.0-alpine@sha256:ab07539e0988b63558ff621f5fbe1077054c39d9809112974fb79993949d41cd AS builder

ENV GENERATE_SOURCEMAP=false
ENV NODE_OPTIONS=--max_old_space_size=4096

WORKDIR /build

# Copy only dependency files first for better caching
COPY package*.json .npmrc ./

# Install dependencies in a separate layer that's cached unless dependencies change
RUN --mount=type=cache,target=/root/.npm \
   npm ci --verbose

# Copy build configuration files (these change less frequently than source)
COPY tsconfig*.json vite.config.ts ./
COPY processes/ ./processes/
# Copy public assets (usually static)
COPY public/ ./public/

# Copy source code last (changes most frequently)
COPY src/ ./src/

# Build the application with cache mount for faster rebuilds
RUN --mount=type=cache,target=/build/node_modules/.vite \
    npm run build

FROM registry.access.redhat.com/ubi10/nginx-126:10.2-1781700996@sha256:11754bea4dfcdcca8f91b6004bf1cb81a6134181b3112e5bc1638bd386fe327f as production-stage

# Copy built web components
# UBI Nginx images use /opt/app-root/src as the default document root and run on port 8080
COPY --from=builder /build/dist /opt/app-root/src
COPY --from=builder /build/dist/src/index.html /opt/app-root/src/index.html
EXPOSE 8080

# Copy nginx configuration
COPY docker/nginx/*.conf "${NGINX_DEFAULT_CONF_PATH}"


ARG IMAGE_CREATED="unknown"
ARG IMAGE_REVISION="unknown"
ARG IMAGE_VERSION="unknown"
LABEL org.opencontainers.image.authors='Landeshauptstadt München <opensource@muenchen.de>' \
    org.opencontainers.image.vendor='Landeshauptstadt München' \
    org.opencontainers.image.created="$IMAGE_CREATED" \
    org.opencontainers.image.revision="$IMAGE_REVISION" \
    org.opencontainers.image.version="$IMAGE_VERSION" \
    org.opencontainers.image.url='https://github.com/it-at-m/riski/pkgs/container/riski%2Friski-frontend' \
    org.opencontainers.image.documentation='https://github.com/it-at-m/riski/README.md' \
    org.opencontainers.image.source='https://github.com/it-at-m/riski' \
    org.opencontainers.image.licenses='MIT' \
    org.opencontainers.image.title='riski-frontend' \
    org.opencontainers.image.description="Frontend for riski. Provides a web interface for interacting with the backend."

# Start the web server
CMD ["nginx", "-g", "daemon off;"]