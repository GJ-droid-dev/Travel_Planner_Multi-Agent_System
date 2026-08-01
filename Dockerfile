FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir uv==0.5.31

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

COPY . .

EXPOSE 8000

CMD ["sh", "-c", "uv run uvicorn src.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
