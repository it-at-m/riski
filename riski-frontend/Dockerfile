FROM node:22.22.0-alpine@sha256:e4bf2a82ad0a4037d28035ae71529873c069b13eb0455466ae0bc13363826e34 AS builder

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

FROM nginx:stable-alpine@sha256:e35873a161d0a08cc31e55f160301ad1676eec6d0072d4feccf78b3e7469d3ae as production-stage

# Copy built web components
COPY --from=builder /build/dist /usr/share/nginx/html
COPY --from=builder /build/dist/src/index.html /usr/share/nginx/html/index.html
EXPOSE 80

# Start the web server
CMD ["nginx", "-g", "daemon off;"]