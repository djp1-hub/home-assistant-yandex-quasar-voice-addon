ARG BUILD_FROM
FROM ${BUILD_FROM}

RUN apk add --no-cache android-tools python3

COPY app /app
COPY rootfs /
RUN chmod 0755 /etc/services.d/yandex-quasar-voice/run

WORKDIR /app
