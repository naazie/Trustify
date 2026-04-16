FROM python:3.12-slim

# ── System deps ────────────────────────────────────────────────────────────────
# git        : needed by GitPython for cloning
# curl, wget : health checks / downloading tools
# nodejs, npm: for eslint
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    curl \
    wget \
    nodejs \
    npm \
    tar \
    && rm -rf /var/lib/apt/lists/*

# ── Install Gitleaks globally ─────────────────────────────────────────────────
RUN wget -qO gitleaks.tar.gz https://github.com/zricethezav/gitleaks/releases/download/v8.18.2/gitleaks_8.18.2_linux_x64.tar.gz && \
    tar -xzf gitleaks.tar.gz -C /usr/local/bin gitleaks && \
    rm gitleaks.tar.gz

WORKDIR /app

# ── Python deps (includes semgrep and pylint) ───────────────────────────────
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ── Application code ───────────────────────────────────────────────────────────
COPY . .

EXPOSE 8000

# ── Startup: just start server natively ───────────────────────────────────────
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
