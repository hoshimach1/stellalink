# syntax=docker/dockerfile:1.7
FROM node:20-alpine AS builder
WORKDIR /app

COPY package*.json ./
COPY scripts/ ./scripts/
RUN --mount=type=cache,target=/root/.npm \
    npm ci --prefer-offline --no-audit --no-fund

COPY . .
RUN --mount=type=cache,target=/app/.nuxt/cache \
    --mount=type=cache,target=/app/node_modules/.cache \
    npm run build

FROM node:20-alpine
WORKDIR /app

COPY --from=builder /app/.output ./.output

ENV NODE_ENV=production
ENV PORT=3000

EXPOSE 3000
CMD ["node", ".output/server/index.mjs"]
