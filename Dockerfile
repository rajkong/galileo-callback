FROM python:3.12 AS builder

WORKDIR /app
RUN pip install poetry

RUN python -m venv venv
COPY . .

RUN . venv/bin/activate && \
    poetry install --without dev

FROM python:3.12-slim

WORKDIR /app

COPY --from=builder /app /app
COPY . .

EXPOSE 8080
CMD ["venv/bin/uvicorn", "hello_fast_api.main:app", "--host", "0.0.0.0", "--port", "8080"]
