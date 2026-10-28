FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    MODEL_PATH=/app/models/champion/model.joblib

WORKDIR /app

# 1) dependências e código (camada que muda menos)
COPY pyproject.toml ./
COPY src ./src
RUN pip install --no-cache-dir .

# 2) artefato do modelo campeão (camada que muda a cada promoção)
COPY models/champion ./models/champion

EXPOSE 8000

HEALTHCHECK --interval=15s --timeout=3s --start-period=10s \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"

CMD ["uvicorn", "mlops_demo.api:app", "--host", "0.0.0.0", "--port", "8000"]
