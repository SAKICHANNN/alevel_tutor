FROM python:3.9-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1-mesa-glx libglib2.0-0 libsm6 libxext6 libxrender-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PYTHONPATH=/app
ENV GRADIO_SERVER_NAME=0.0.0.0
ENV OLLAMA_HOST=host.docker.internal
ENV LMSTUDIO_BASE_URL=http://host.docker.internal:1234/v1

EXPOSE 7860

CMD ["python3", "web/app.py"]
