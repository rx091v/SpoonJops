FROM mcr.microsoft.com/playwright/python:v1.53.0-noble

WORKDIR /app

COPY backend/requirements.txt /app/backend/requirements.txt
RUN pip install --upgrade pip \
    && pip install -r /app/backend/requirements.txt

COPY backend /app/backend
COPY worker /app/worker
COPY browser /app/browser
COPY shared /app/shared
COPY prompts /app/prompts

ENV PYTHONPATH=/app
