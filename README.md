# Trustify

**AI-Powered Source Code Security Scanner**

Trustify scans GitHub repositories and uploaded ZIP archives for security vulnerabilities, leaked secrets, and code quality issues using a suite of industry-standard static analysis tools — all enhanced with Google Gemini AI for plain-English explanations and guided remediation.

---

## Features

- **SAST scanning** with [Semgrep](https://semgrep.dev/) — detects security vulnerabilities across Python, JavaScript, TypeScript, and more
- **Secret detection** with [Gitleaks](https://github.com/gitleaks/gitleaks) — scans both working tree and full git commit history
- **Code quality** with [Pylint](https://pylint.org/) — lints Python files for style, logic, and common bugs
- **JavaScript linting** with [ESLint](https://eslint.org/) + `eslint-plugin-security` — catches unsafe patterns in JS/TS
- **AI Remediation** via Google Gemini 2.0 Flash — converts raw findings into plain English, explains impact, and provides numbered fix steps
- **Risk dashboard** — real-time scan progress, severity breakdown (Critical / Warning / Info), file drilldown view, and downloadable JSON reports
- **Scan history** — paginated table of all past scans with per-scan detail pages

---

## Architecture

```
┌──────────────────────────────────────────────────┐
│                   Browser                        │
│      React + Vite + TailwindCSS frontend         │
│              localhost:3000                      │
└────────────────────┬─────────────────────────────┘
                     │ REST API
┌────────────────────▼─────────────────────────────┐
│           FastAPI Backend  (Python 3.12)          │
│                localhost:8000                     │
│                                                  │
│  ┌─────────┐ ┌──────────┐ ┌─────────┐ ┌───────┐ │
│  │ Semgrep │ │ Gitleaks │ │ Pylint  │ │ESLint │ │
│  │(native) │ │(native)  │ │(native) │ │(npx)  │ │
│  └─────────┘ └──────────┘ └─────────┘ └───────┘ │
│                                                  │
│           Google Gemini 2.0 Flash (AI)           │
└────────────────────┬─────────────────────────────┘
                     │
┌────────────────────▼─────────────────────────────┐
│              MongoDB 7.0                         │
│  Stores: scans, findings, AI summaries           │
└──────────────────────────────────────────────────┘
```

All scanning tools run **natively inside the backend container** — no Docker-in-Docker, no socket mounts.

---

## Prerequisites

- [Docker](https://docs.docker.com/get-docker/) + [Docker Compose](https://docs.docker.com/compose/) v2
- A **Google Gemini API key** — get one free at [aistudio.google.com](https://aistudio.google.com/)

---

## Quick Start

### 1. Clone the repository

```bash
git clone <your-repo-url>
cd trustify
```

### 2. Configure environment variables

```bash
cp .env.example .env
```

Open `.env` and set your Gemini API key:

```env
GEMINI_API_KEY=your_key_here
```

### 3. Build and start all services

```bash
docker compose up --build
```

This builds the backend image (installs Semgrep, Pylint, Gitleaks, Node/ESLint) and the frontend Nginx image, then starts MongoDB.

| Service  | URL                     |
|----------|-------------------------|
| Frontend | http://localhost:3000   |
| Backend API | http://localhost:8000 |
| API Docs (Swagger) | http://localhost:8000/docs |

### 4. Stop the app

```bash
docker compose down
```

To also remove stored scan data (MongoDB volume):

```bash
docker compose down -v
```

---

## Development Workflow

### Hot-reloading backend

The `./backend` directory is bind-mounted into the container, so any Python file changes are picked up immediately by uvicorn's `--reload` flag — no rebuild needed.

### Rebuilding after dependency changes

If you modify `requirements.txt` or the `Dockerfile`:

```bash
docker compose up --build
```

### Run the tool test suite (inside the container)

```bash
docker exec trustify_backend python run_test.py
```

This creates a temporary test workspace and runs all four tool runners, printing their raw output.

---

## Environment Variables

| Variable | Required | Default | Description |
|---|---|---|---|
| `GEMINI_API_KEY` | **Yes** | — | Google Gemini API key for AI remediation |
| `MONGO_URI` | No | `mongodb://mongodb:27017/trustify` | MongoDB connection string |
| `WORKSPACE_DIR` | No | `/tmp/trustify_workspaces` | Where repos/ZIPs are extracted for scanning |
| `ENVIRONMENT` | No | `development` | App environment flag |

---

## Project Structure

```
trustify/
├── backend/
│   ├── main.py               # FastAPI app entry point
│   ├── models.py             # Pydantic / MongoDB models
│   ├── config.py             # Settings loaded from env
│   ├── requirements.txt      # Python dependencies
│   ├── Dockerfile
│   ├── run_test.py           # Tool runner smoke tests
│   └── tools/
│       ├── orchestrator.py   # Coordinates all tool runners
│       ├── semgrep_runner.py
│       ├── pylint_runner.py
│       ├── gitleaks_runner.py
│       └── eslint_runner.py
├── frontend/
│   ├── src/
│   │   ├── App.jsx
│   │   ├── pages/            # Dashboard, History, ScanDetail
│   │   ├── components/       # Navbar, ScanCard, FindingRow, CodeViewer…
│   │   └── api/              # Axios client
│   ├── public/
│   │   └── logo.png          # Bug mascot
│   └── index.html
├── docker-compose.yml
├── .env.example
└── .gitignore
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React 18, Vite, TailwindCSS v3, Lucide React |
| Backend | FastAPI, Python 3.12, Motor (async MongoDB) |
| Database | MongoDB 7.0 |
| SAST | Semgrep (pip) |
| Secrets | Gitleaks v8 (binary) |
| Linting | Pylint (pip), ESLint v8 (npx) |
| AI | Google Gemini 2.0 Flash via `google-generativeai` |
| Infra | Docker Compose |
