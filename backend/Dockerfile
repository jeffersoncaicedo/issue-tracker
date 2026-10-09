# syntax=docker/dockerfile:1
# ---------- Etapa 1: dependencias ----------
FROM python:3.12-slim AS builder
ENV PIP_NO_CACHE_DIR=1 PIP_DISABLE_PIP_VERSION_CHECK=1
WORKDIR /build
COPY requirements.txt .
RUN pip install --prefix=/install -r requirements.txt

# ---------- Etapa 2: runtime mínimo ----------
FROM python:3.12-slim AS runtime
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8080
WORKDIR /app
COPY --from=builder /install /usr/local
COPY app ./app
COPY scripts ./scripts

# Usuario sin privilegios (principio de mínimo privilegio)
RUN useradd --create-home --uid 10001 appuser
RUN mkdir -p /app/data /app/cache && chown -R appuser:appuser /app/data /app/cache
USER appuser

EXPOSE 8080
# Cloud Run inyecta $PORT; --proxy-headers para respetar X-Forwarded-*
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT} --proxy-headers --forwarded-allow-ips='*'"]
