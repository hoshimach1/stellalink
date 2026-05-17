# syntax=docker/dockerfile:1.7
FROM python:3.12-slim

WORKDIR /app

ENV PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

COPY requirements.txt .
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install -r requirements.txt

COPY app ./app
RUN mkdir -p uploads/avatars

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
