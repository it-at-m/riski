FROM node:22.22.0-alpine@sha256:a9cd9bac76cf2396abf14ff0d1c3671a8175fe577ce350e62ab0fc1678050176 AS builder

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

FROM nginx:stable-alpine@sha256:67cbbcc757a6ce913b33e515b020cfd3923897ad883c452903b1e3487a95a570 as production-stage

# Copy built web components
COPY --from=builder /build/dist /usr/share/nginx/html
COPY --from=builder /build/dist/src/index.html /usr/share/nginx/html/index.html
EXPOSE 80

# Start the web server
CMD ["nginx", "-g", "daemon off;"]