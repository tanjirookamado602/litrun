# Multi-arch edge container for litrun Universal Embedded Linux AI Runtime
# Supports linux/amd64 and linux/arm64 architectures

# Stage 1: Build C99 Native Engine & Python Wheel
FROM python:3.11-slim-bookworm AS builder

WORKDIR /build

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    make \
    libc6-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy C Native Core and compile shared library
COPY core/ ./core/
RUN make -C core all

# Copy SDK and build python wheel
COPY pyproject.toml README.md ./
COPY registry/ ./registry/
COPY sdk/ ./sdk/
RUN mkdir -p sdk/litrun/lib && cp core/lib/liblitrun_core.so sdk/litrun/lib/
RUN pip install --no-cache-dir build && python -m build --wheel --outdir /dist .


# Stage 2: Minimal Production Runtime
FROM python:3.11-slim-bookworm

LABEL org.opencontainers.image.title="litrun" \
      org.opencontainers.image.description="Universal Lightweight Embedded Linux AI Runtime" \
      org.opencontainers.image.url="https://github.com/assassinaj602/litrun" \
      org.opencontainers.image.source="https://github.com/assassinaj602/litrun" \
      org.opencontainers.image.licenses="MIT"

ENV LANG=C.UTF-8 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    LD_LIBRARY_PATH=/usr/local/lib/litrun:${LD_LIBRARY_PATH} \
    LITRUN_CACHE_DIR=/home/litrun/.cache/litrun

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Create non-root system user
RUN groupadd -r litrun && useradd -r -g litrun -d /home/litrun -m litrun

# Install precompiled C core library
RUN mkdir -p /usr/local/lib/litrun
COPY --from=builder /build/core/lib/liblitrun_core.so /usr/local/lib/litrun/

# Install litrun wheel
COPY --from=builder /dist/*.whl /tmp/
RUN pip install --no-cache-dir /tmp/*.whl && rm -f /tmp/*.whl

# Ensure core shared library is also placed inside python package lib dir
RUN PYTHON_SITE=$(python -c "import site; print(site.getsitepackages()[0])") && \
    mkdir -p "${PYTHON_SITE}/litrun/lib" && \
    cp /usr/local/lib/litrun/liblitrun_core.so "${PYTHON_SITE}/litrun/lib/"

# Create persistence directories with proper permissions
RUN mkdir -p /data /home/litrun/.cache/litrun /home/litrun/.litrun && \
    chown -R litrun:litrun /data /home/litrun

WORKDIR /home/litrun
USER litrun

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

ENTRYPOINT ["litrun"]
CMD ["ui", "--host", "0.0.0.0", "--port", "8080"]

