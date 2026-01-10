FROM node:22.21.1-alpine@sha256:0340fa682d72068edf603c305bfbc10e23219fb0e40df58d9ea4d6f33a9798bf AS builder

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

FROM nginx:stable-alpine@sha256:67c129e5545fd0c5fdbaf8e7039b8925d472679e94bd65f2a423578469e16718 as production-stage

# Copy built web components
COPY --from=builder /build/dist /usr/share/nginx/html
COPY --from=builder /build/dist/src/index.html /usr/share/nginx/html/index.html
EXPOSE 80

# Start the web server
CMD ["nginx", "-g", "daemon off;"]