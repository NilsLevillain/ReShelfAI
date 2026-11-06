# Web image. Build from the repo root: docker build -f infra/web.Dockerfile -t reshelf-web .
# VITE_API_URL=/api makes the app probe /api/health and go live when the API answers.
# Without it the app serves the cached JSON in data/precomputed.
FROM node:20-slim AS build
RUN corepack enable && corepack prepare pnpm@9 --activate
WORKDIR /app

COPY design_system ./design_system
COPY data/precomputed ./data/precomputed
COPY apps/web/package.json apps/web/pnpm-lock.yaml ./apps/web/
WORKDIR /app/apps/web
RUN pnpm install --frozen-lockfile

COPY apps/web/ ./
ARG VITE_API_URL=/api
ENV VITE_API_URL=$VITE_API_URL
RUN pnpm build

FROM nginx:1.27-alpine
COPY infra/nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/apps/web/dist /usr/share/nginx/html
EXPOSE 80
