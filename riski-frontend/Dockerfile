FROM node:22.21.1-alpine@sha256:b2358485e3e33bc3a33114d2b1bdb18cdbe4df01bd2b257198eb51beb1f026c5 AS builder

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

FROM registry.access.redhat.com/ubi10/nginx-126:10.1-1763382165@sha256:4c3e5e60d785e6e8bb25a13320fffae720cf0a5d1c3d161c2fb98567421da840

# Copy built web components
COPY --from=builder /build/dist /usr/share/nginx/html
COPY --from=builder /build/dist/src/index.html /usr/share/nginx/html/index.html
# Make writable directories for arbitrary UID
RUN mkdir -p /tmp/nginx \
    && chmod -R 777 /tmp \
    && chmod -R 777 /usr/share/nginx/html

EXPOSE 80

# Start the web server
CMD ["nginx", "-g", "daemon off;"]