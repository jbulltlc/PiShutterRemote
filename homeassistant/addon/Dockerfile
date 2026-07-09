ARG BUILD_FROM
FROM $BUILD_FROM

RUN apk add --no-cache \
    python3 \
    py3-pip \
    py3-virtualenv \
    git \
    build-base \
    linux-headers

WORKDIR /app

COPY . /app

RUN python3 -m venv /app/.venv \
    && /app/.venv/bin/pip install --upgrade pip \
    && /app/.venv/bin/pip install -e . \
    && /app/.venv/bin/pip install fastapi uvicorn

CMD ["/app/homeassistant/addon/run.sh"]