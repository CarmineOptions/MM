FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN pip install --upgrade pip && pip install uv

COPY pyproject.toml uv.lock* ./

RUN uv pip install --system --no-cache-dir .

COPY . .

ENV PYTHONPATH=./

ENTRYPOINT ["python", "./MM/main.py"]