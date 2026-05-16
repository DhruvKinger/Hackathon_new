FROM python:3.11-slim

WORKDIR /app

RUN mkdir -p /app /eval_assets

RUN apt-get update \
    && apt-get install -y --no-install-recommends git unzip \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir \
    click>=8,<9 \
    GitPython>=3.1,<4 \
    matplotlib>=3.8,<4 \
    radon>=6,<7 \
    pytest>=8,<9

ENV PYTHONUNBUFFERED=1
