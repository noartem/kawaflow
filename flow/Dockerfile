FROM python:3.12-slim-bookworm
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

COPY kawa/ /tmp/kawa/
RUN uv venv
RUN uv pip install -e /tmp/kawa