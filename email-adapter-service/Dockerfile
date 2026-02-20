FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /workspace

COPY shared ./shared
COPY email-adapter-service ./email-adapter-service

RUN pip install --no-cache-dir -e ./shared && \
    pip install --no-cache-dir -r ./email-adapter-service/requirements.txt

WORKDIR /workspace/email-adapter-service

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8002"]
