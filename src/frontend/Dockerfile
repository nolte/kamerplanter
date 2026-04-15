# Stage 1: Build
FROM node:24-alpine AS build
WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci --prefer-offline 2>/dev/null || npm install

COPY . .
RUN npm run build

# Stage 2: Serve with nginx
FROM nginx:1.30-alpine

LABEL org.opencontainers.image.title="kamerplanter-frontend" \
      org.opencontainers.image.description="Kamerplanter frontend UI for plant lifecycle management" \
      org.opencontainers.image.source="https://github.com/nolte/kamerplanter" \
      org.opencontainers.image.vendor="Kamerplanter" \
      org.opencontainers.image.licenses="MIT"

COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY docker-entrypoint.d/ /docker-entrypoint.d/

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
