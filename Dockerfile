FROM python:3.11.0-slim

ENV PYTHONUNBUFFERED 1

WORKDIR /app

COPY uv.lock pyproject.toml ./
RUN pip install --upgrade pip && \
    pip install uv

ARG DEV=false
RUN if [ "$DEV" = "true" ] ; then uv pip install -r uv.lock --extras dev ; else uv pip install -r uv.lock ; fi

COPY ./app/ ./
COPY ./ml/model/ ./ml/model/

ENV PYTHONPATH "${PYTHONPATH}:/app"

EXPOSE 8080
CMD uvicorn main:app --host 0.0.0.0 --port 8080
