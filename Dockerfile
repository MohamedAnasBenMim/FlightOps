FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/home/flightops/.local/bin:$PATH"

RUN groupadd --system flightops && useradd --system --gid flightops --create-home flightops
WORKDIR /app

COPY pyproject.toml README.md ./
COPY src ./src
COPY alembic.ini ./
COPY alembic ./alembic

RUN pip install --no-cache-dir . && chown -R flightops:flightops /app

USER flightops
EXPOSE 8000

CMD ["uvicorn", "flightops.main:app", "--host", "0.0.0.0", "--port", "8000"]
