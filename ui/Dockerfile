FROM php:8.5-fpm-alpine AS base

RUN apk add --no-cache bash curl git icu-data-full icu-dev libpng-dev libzip-dev oniguruma-dev sqlite-dev shadow \
    && docker-php-ext-configure zip \
    && docker-php-ext-install -j"$(nproc)" bcmath mbstring opcache pdo_mysql pdo_sqlite zip \
    && rm -rf /var/cache/apk/*

COPY --from=composer:2.8 /usr/bin/composer /usr/local/bin/composer

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

RUN apk add --no-cache nodejs npm

COPY composer.json composer.lock ./
RUN composer install \
    --no-interaction \
    --no-progress

COPY package.json package-lock.json ./
RUN npm install --no-progress

COPY . .

RUN ln -snf /var/www/html/storage/app/public /var/www/html/public/storage \
    && mkdir -p public/build \
    && chown -R www-data:www-data storage bootstrap/cache public

USER www-data

EXPOSE 9000


FROM node:20-alpine AS frontend

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


FROM nginx:1.27-alpine AS nginx

WORKDIR /var/www/html

COPY --from=app /var/www/html/public /var/www/html/public
COPY docker/nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80
