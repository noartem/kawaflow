FROM php:8.5-fpm-bookworm AS base

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y \
        git curl zip unzip \
        libpng-dev libjpeg-dev libwebp-dev \
        libzip-dev libicu-dev libpq-dev \
        libonig-dev \
        libsqlite3-dev \
        mariadb-client \
        pkg-config \
        && rm -rf /var/lib/apt/lists/*

RUN docker-php-ext-configure gd --with-jpeg --with-webp && \
    docker-php-ext-install -j"$(nproc)" bcmath mbstring pdo_sqlite pdo_pgsql intl zip pcntl sockets

COPY --from=composer:2.9 /usr/bin/composer /usr/local/bin/composer

WORKDIR /var/www/html


FROM base AS vendor

COPY composer.json composer.lock ./
RUN composer install \
    --no-dev \
    --no-interaction \
    --no-progress \
    --optimize-autoloader


FROM base AS dev

ENV APP_ENV=local \
    APP_DEBUG=true \
    APP_URL=http://localhost

RUN curl -fsSL https://deb.nodesource.com/setup_25.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

COPY composer.json composer.lock ./
RUN composer install \
    --no-interaction \
    --no-progress \
    --no-scripts

COPY package.json package-lock.json ./
RUN npm install --no-progress

COPY . .

RUN composer run-script post-autoload-dump \
    && composer run-script post-update-cmd

RUN ln -snf /var/www/html/storage/app/public /var/www/html/public/storage \
    && mkdir -p public/build \
    && chown -R www-data:www-data storage bootstrap/cache public

USER root

EXPOSE 9000


FROM node:25-alpine AS frontend

WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci --no-progress

COPY resources ./resources
COPY components.json vite.config.ts tsconfig.json eslint.config.js ./
COPY public ./public
RUN npm run build


FROM base AS prod

ENV APP_ENV=production \
    APP_DEBUG=false \
    APP_URL=http://localhost

COPY --from=vendor /var/www/html/vendor /var/www/html/vendor
COPY --from=frontend /app/public/build /var/www/html/public/build
COPY . .

RUN ln -snf /var/www/html/storage/app/public /var/www/html/public/storage \
    && chown -R www-data:www-data storage bootstrap/cache public/build

USER www-data

EXPOSE 9000


FROM nginx:1.35-alpine AS nginx

WORKDIR /var/www/html

COPY --from=prod /var/www/html/public /var/www/html/public
COPY docker/nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80
