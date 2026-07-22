FROM python:3.12-slim

WORKDIR /app

# Install git (required for cloning forks after forking) and clean up apt caches
RUN apt-get update \
    && apt-get install -y --no-install-recommends git \
    && rm -rf /var/lib/apt/lists/*

# Copy project metadata and source
COPY pyproject.toml ./
COPY src ./src

# Install the CLI
RUN pip install --no-cache-dir .

ENTRYPOINT ["airepo"]
