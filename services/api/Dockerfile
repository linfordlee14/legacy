# Immutable backend image (DEP-24): built once, promoted by digest from
# staging to production. Environment identity is injected at runtime via
# LEGACY_ENV (DEP-06); nothing environment-specific is baked in.
FROM python:3.12-slim

WORKDIR /app

RUN addgroup --system legacy && adduser --system --ingroup legacy legacy

COPY pyproject.toml README.md ./
COPY src ./src
RUN pip install --no-cache-dir .

USER legacy
EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=3s CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/healthz')"]

CMD ["uvicorn", "legacy_api.main:app", "--host", "0.0.0.0", "--port", "8000"]
