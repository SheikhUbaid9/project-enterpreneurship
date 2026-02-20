FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /workspace

COPY shared ./shared
COPY mcp-gateway-service ./mcp-gateway-service

RUN pip install --no-cache-dir -e ./shared && \
    pip install --no-cache-dir -r ./mcp-gateway-service/requirements.txt

WORKDIR /workspace/mcp-gateway-service

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
