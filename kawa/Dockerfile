FROM python:3.12-slim

WORKDIR /app

RUN pip install uv ruff

COPY pyproject.toml ./

RUN uv pip install --system -e .[test]

COPY . .

CMD ["ruff", "check", "."]