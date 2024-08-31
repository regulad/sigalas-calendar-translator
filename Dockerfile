# https://stackoverflow.com/questions/53835198/integrating-python-poetry-with-docker/54763270#54763270
# Copyright (c) 2023  Parker Wahle - Licensed under MIT License (do whatever you want)

FROM python:3.11-slim-bullseye AS base

# Install system dependencies for Python and Playwright
RUN apt-get update && apt-get install -y --no-install-recommends \
    tzdata \
    gcc \
    libffi-dev \
    libssl-dev \
    make \
    git \
    curl \
    chromium \
    libnss3 \
    libfreetype6 \
    libharfbuzz0b \
    fonts-freefont-ttf \
    fonts-noto-color-emoji \
    && rm -rf /var/lib/apt/lists/* \
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

RUN groupadd -g $USER_GID $USERNAME \
    && useradd -m -u $USER_UID -g $USER_GID -s /bin/bash $USERNAME

# Install playwright runtime dependencies (has to be as root)
RUN pip install playwright && playwright install-deps && pip uninstall -y playwright

# Switch to non-root user (for security)
USER $USERNAME

# extend our path to include python (for playwright)
ENV PATH="$HOME/.local/bin:$PATH"

# Install the package in the user space
COPY --from=builder /code/dist/sigalas_calendar_translator-*.whl /tmp/
RUN pip install --user /tmp/sigalas_calendar_translator-*.whl

# install the playwright browsers (has to be as the user)
RUN playwright install  # should be on path from installing using pip

# Now do something!
CMD ["sigalas-calendar-translator", "serve"]

# or expose a port:
# EXPOSE 8080/tcp
