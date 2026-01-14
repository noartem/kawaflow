FROM python:3.12-slim-bookworm

RUN python -m pip install --no-cache-dir uv

WORKDIR /app

COPY pyproject.toml .
COPY uv.lock .

RUN uv sync --locked

COPY . .

CMD ["uv", "run", "pytest", "-q"]
