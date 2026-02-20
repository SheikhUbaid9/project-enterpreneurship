FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /workspace

COPY shared ./shared
COPY auth-service ./auth-service

RUN pip install --no-cache-dir -e ./shared && \
    pip install --no-cache-dir -r ./auth-service/requirements.txt

WORKDIR /workspace/auth-service

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001"]
