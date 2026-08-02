# syntax=docker/dockerfile:1.7

FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    GRADIO_SERVER_NAME=0.0.0.0 \
    GRADIO_SERVER_PORT=7860 \
    HF_HOME=/cache/huggingface \
    TRANSFORMERS_CACHE=/cache/huggingface

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Install PyTorch separately so the Docker image uses the pinned CPU wheel.
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --upgrade pip \
    && pip install --index-url https://download.pytorch.org/whl/cpu torch==2.12.1

COPY requirements-docker.txt .
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install -r requirements-docker.txt

COPY pyproject.toml uv.lock README.md ./
COPY nutrichat ./nutrichat
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --no-deps .

COPY app.py .
COPY artifacts ./artifacts
COPY research_assets ./research_assets

EXPOSE 7860

CMD ["python", "app.py"]
