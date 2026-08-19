# ---- 前端构建 ----
FROM node:20-alpine AS web-builder
WORKDIR /build/web
COPY web/package.json web/package-lock.json ./
RUN npm ci --no-audit --no-fund
COPY web/ ./
RUN npm run build

# ---- 后端运行 ----
FROM python:3.12-slim AS runtime
LABEL maintainer="arnoluo" description="AI Ledger - personal cashflow terminal with MCP"

ENV PYTHONUNBUFFERED=1 \
    DB_PATH=/data/ledger.db

WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY server/ ./server/
COPY tests/ ./tests/
COPY --from=web-builder /build/web/dist ./web/dist

RUN groupadd -r ledger && useradd -r -g ledger ledger \
    && mkdir -p /data && chown -R ledger:ledger /data
USER ledger

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s \
  CMD python -c "import urllib.request;urllib.request.urlopen('http://127.0.0.1:8000/api/health')" || exit 1

CMD ["uvicorn", "server.main:app", "--host", "0.0.0.0", "--port", "8000"]
