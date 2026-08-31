FROM php:8.4-cli-alpine

# Copy the extension installer script from the official tool image
COPY --from=mlocati/php-extension-installer /usr/bin/install-php-extensions /usr/local/bin/

# Install system utilities and PHP extensions
RUN apk add --no-cache \
    bash \
    git \
    openssh-client \
    curl \
    zip \
    unzip \
    cronie \
    net-tools \
    python3 \
    supervisor \
    figlet \
    sudo \
    && install-php-extensions \
        bcmath \
        bz2 \
        calendar \
        ctype \
        dom \
        exif \
        fileinfo \
        ftp \
        gettext \
        gd \
        iconv \
        mbstring \
        mysqli \
        opcache \
        pcntl \
        pdo_mysql \
        pdo_sqlite \
        phar \
        posix \
        shmop \
        simplexml \
        soap \
        sockets \
        sqlite3 \
        sysvmsg \
        sysvsem \
        sysvshm \
        tokenizer \
        xmlreader \
        xmlwriter \
        xsl \
        zip \
        memcached \
        msgpack \
        igbinary \
        session \
        openssl \
        apcu

# Copy Composer directly from the official Composer image
COPY --from=composer:latest /usr/bin/composer /usr/local/bin/

WORKDIR /var/www/app

# Set unlimited memory for Composer builds
ENV COMPOSER_MEMORY_LIMIT=-1

# Docker Cache Layering: Install dependencies first
COPY ./composer.json composer.lock* ./
RUN composer install --prefer-dist --no-progress --no-autoloader

# Copy application files (filtered by your .dockerignore)
COPY . .

# Generate optimized production autoloader
RUN composer dump-autoload --optimize