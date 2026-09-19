FROM ghcr.io/php/pie:1.4.10-bin AS pie

FROM php:8.5.10-alpine AS base

FROM base AS development

RUN cp "$PHP_INI_DIR/php.ini-development" "$PHP_INI_DIR/php.ini"
COPY docker/php/php.ini $PHP_INI_DIR/conf.d/90-project.ini
COPY docker/php/php.ini-development $PHP_INI_DIR/conf.d/99-environment.ini

ARG USERNAME=dev
ARG USER_UID=1000
ARG USER_GID=1000

ARG WORKSPACE_DIR
RUN : "${WORKSPACE_DIR:?WORKSPACE_DIR build arg is required}"
ENV WORKSPACE_DIR=${WORKSPACE_DIR}

RUN apk add --no-cache bash git unzip

# PIE is mounted only for this RUN; it also enables the installed extension.
# Build dependencies are available only during installation.
RUN --mount=type=bind,from=pie,source=/pie,target=/usr/local/bin/pie \
    apk add --no-cache --virtual .xdebug-build-deps $PHPIZE_DEPS linux-headers libtool \
    && pie install --no-interaction --no-cache \
        --no-system-dependencies-check xdebug/xdebug:3.5.3 \
    && rm -rf /root/.pie \
    && apk del .xdebug-build-deps

COPY --from=composer:2.10.3 /usr/bin/composer /usr/local/bin/composer

    # Create the user.
RUN addgroup -g ${USER_GID} ${USERNAME} \
    && adduser -D -u ${USER_UID} -G ${USERNAME} -h /home/${USERNAME} ${USERNAME} \
    # Create the relevant directories.
    && mkdir -p ${WORKSPACE_DIR} /home/${USERNAME} \
    # Grant ownership of the created directories.
    && chown -R ${USERNAME}:${USERNAME} ${WORKSPACE_DIR} /home/${USERNAME}

WORKDIR ${WORKSPACE_DIR}

USER ${USERNAME}

CMD ["sleep", "infinity"]
