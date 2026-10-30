ARG BUILD_FROM
FROM ${BUILD_FROM}

ENV LANG=C.UTF-8

# Install build dependencies and tools
RUN apk add --no-cache \
    curl \
    gcc \
    musl-dev \
    linux-headers \
    jq

# Install litrun from PyPI
RUN pip3 install --no-cache-dir --upgrade pip && \
    pip3 install --no-cache-dir litrun

# Copy rootfs files
COPY rootfs /

# Make service script executable
RUN chmod a+x /etc/services.d/litrun/run

WORKDIR /data
EXPOSE 8080

