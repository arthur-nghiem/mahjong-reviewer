# ── Stage 1: builder ──────────────────────────────────────────────────────────
FROM python:3.12-slim AS builder

WORKDIR /build

COPY pyproject.toml .
COPY src/ src/
COPY config/ config/

RUN pip install --upgrade pip \
 && pip install --prefix=/install . \
 && pip install --prefix=/install fastapi uvicorn[standard]

# ── Stage 2: runtime ──────────────────────────────────────────────────────────
FROM python:3.12-slim

RUN apt-get update \
 && apt-get install -y --no-install-recommends \
    curl \
    unzip \
 && curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip" \
 && unzip awscliv2.zip \
 && ./aws/install \
 && rm -rf awscliv2.zip aws \
 && apt-get clean \
 && rm -rf /var/lib/apt/lists/*

RUN useradd --no-log-init -m appuser

WORKDIR /app

COPY --from=builder /install /usr/local

COPY src/ src/
COPY config/ config/
COPY assets/ assets/
COPY static/ static/
COPY input/ input/
COPY api.py .
COPY entrypoint.sh .

RUN mkdir -p output data/models \
 && chown -R appuser:appuser /app

EXPOSE 8000

USER appuser

CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2", "--timeout-keep-alive", "300"]