FROM mcr.microsoft.com/devcontainers/python:1-3.12-bookworm

# Install uv and uvx from official Astral image
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /usr/local/bin/

# Install PostgreSQL client (for pg_isready) and Node.js LTS (with npm) + pnpm
RUN rm -f /etc/apt/sources.list.d/yarn.list \
    && apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates curl gnupg postgresql-client \
    && curl -fsSL https://deb.nodesource.com/setup_lts.x | bash - \
    && apt-get install -y --no-install-recommends nodejs \
    && npm install -g pnpm \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Pre-create workspace and named-volume mount directories with non-root ownership,
# and configure pnpm to keep its store inside the container instead of the host mount
RUN mkdir -p /workspace/backend/.venv /workspace/frontend/node_modules /home/vscode/.local/share/pnpm/store \
    && chown -R vscode:vscode /workspace /home/vscode/.local \
    && su - vscode -c "pnpm config set store-dir /home/vscode/.local/share/pnpm/store --global"

# Copy mode avoids cross-filesystem hardlink warnings with named Docker volumes
ENV UV_LINK_MODE=copy
