# https://stackoverflow.com/questions/53835198/integrating-python-poetry-with-docker/54763270#54763270
# Copyright (c) 2023  Parker Wahle - Licensed under MIT License (do whatever you want)

FROM python:3.12.3-alpine3.18 AS base

# Install system dependencies for Python and Playwright
RUN apk add -U tzdata --no-cache \
    && apk add --no-cache \
        gcc \
        musl-dev \
        libffi-dev \
        openssl-dev \
        make \
        git \
        curl \
        libstdc++ \
        chromium \
        nss \
        freetype \
        harfbuzz \
        ttf-freefont \
        font-noto-emoji \
    && pip install --upgrade pip

# --------------------------------------
# ---------- Copy and compile ----------
# We use a multi-stage build to reduce the size of the final image
FROM base AS builder

# Configure env variables for build/install
ENV PYTHONFAULTHANDLER=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONHASHSEED=random
ENV PIP_NO_CACHE_DIR=off
ENV PIP_DISABLE_PIP_VERSION_CHECK=on
ENV PIP_DEFAULT_TIMEOUT=120
ENV POETRY_VERSION=1.5.1

# Install Poetry
RUN pip install "poetry==$POETRY_VERSION"

# Copy only requirements to cache them in docker layer
WORKDIR /code
# Although it would be very convenient to only copy the pyproject.toml file so that we can cache the dependencies,
# Poetry requires the whole project to be present in order to install the dependencies
COPY . /code

# Install with poetry
RUN poetry config virtualenvs.create false \
  && poetry install --no-interaction --no-ansi --only main

# Build the package
RUN poetry build

# --------------------------------------
# ---------- Install & run! ------------
FROM base AS runner

# Set labels

# See https://github.com/opencontainers/image-spec/blob/master/annotations.md
LABEL name="sigalas-calendar-translator"
LABEL version="0.1.0"
LABEL vendor="Parker Wahle"
LABEL org.opencontainers.image.title="sigalas-calendar-translator"
LABEL org.opencontainers.image.version="0.1.0"
LABEL org.opencontainers.image.url="https://github.com/regulad/sigalas-calendar-translator"
LABEL org.opencontainers.image.documentation="https://sigalas-calendar-translator.readthedocs.io"

ENV PYTHONFAULTHANDLER=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONHASHSEED=random
ENV TZ=America/New_York

ARG USERNAME=sigalas_calendar_translator
ARG USER_UID=1008
ARG USER_GID=$USER_UID

RUN addgroup -g $USER_GID -S $USERNAME \
    && adduser -u $USER_UID -G $USERNAME -D -S $USERNAME

# Switch to non-root user (for security)
# This makes dockerfile_lint complain, but it's fine
# dockerfile_lint - ignore
USER $USERNAME

# Install the package in the user space
COPY --from=builder /code/dist/sigalas_calendar_translator-*.whl /tmp/
RUN pip install --user /tmp/sigalas_calendar_translator-*.whl

# Also install the playwright dependencies
RUN python -m playwright install

# Now do something!
CMD ["/home/sigalas-calendar-translator/.local/bin/sigalas-calendar-translator", "serve"]

# or expose a port:
# EXPOSE 8080/tcp
