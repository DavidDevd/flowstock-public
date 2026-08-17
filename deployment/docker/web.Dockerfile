FROM node:24.14.0-bookworm-slim@sha256:d8e448a56fc63242f70026718378bd4b00f8c82e78d20eefb199224a4d8e33d8 AS builder

ENV COREPACK_HOME=/corepack
RUN corepack enable

WORKDIR /build
COPY package.json pnpm-lock.yaml pnpm-workspace.yaml tsconfig.base.json ./
COPY apps/web/package.json apps/web/package.json
COPY packages/api-contracts/package.json packages/api-contracts/package.json
COPY packages/ui-system/package.json packages/ui-system/package.json
RUN pnpm install --frozen-lockfile

COPY apps/web apps/web
COPY packages packages
RUN pnpm --filter @flowstock/web build

FROM nginx:1.31.3-alpine3.24@sha256:4a73073bd557c65b759505da037898b61f1be6cbcc3c2c3aeac22d2a470c1752 AS runtime

COPY deployment/docker/web-nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=builder /build/apps/web/dist /usr/share/nginx/html

EXPOSE 8080
HEALTHCHECK --interval=15s --timeout=3s --retries=5 \
  CMD wget -q -O - http://127.0.0.1:8080/ >/dev/null || exit 1
