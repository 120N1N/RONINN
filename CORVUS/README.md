# Corvus - Automated Pentest & Vulnerability Analysis Platform

Corvus is a sophisticated security orchestration platform designed for automated vulnerability scanning, mapping (OWASP), and risk analysis.

## Features
- **Multi-Tool Orchestration**: Seamless integration of Recon, Discovery, Fuzzing, and Scanning tools.
- **Real-time Monitoring**: WebSocket-based progress updates.
- **Agentic AI Deep Validate**: LLM-powered automatic fetching and DOM validation for Client-Side vulnerabilities to eliminate False Positives.
- **Vulnerability Analysis**: Automatic deduplication and normalization of findings with LLM assistance.
- **Per-User API Keys**: Secure, isolated LLM API key management for individual authenticated users.
- **JS Secret Extraction**: Deep parsing of JavaScript files for leaked secrets.
- **Modern Stack**: FastAPI, Celery, Redis, PostgreSQL, and React.
- **Dockerized**: One-command deployment.

## Tool Stack
- **Recon**: subfinder, assetfinder, httpx
- **Discovery**: gau, katana, jsfinder
- **Scanning**: nuclei, dalfox, sqlmap
- **Validation**: Playwright/Requests (Agentic Fetcher)
- **Custom**: JS Secret Extraction engine

## Quick Start (Docker)
1. Ensure you have Docker and Docker Compose installed.
2. Clone the repository.
3. Run the setup script:
   ```bash
   ./setup.sh
   ```
4. Access the API documentation at: `http://localhost:8000/api/docs`
5. Access the Frontend at: `http://localhost:3000`

## Manual Setup
If you want to run components individually:

### Backend
1. Install requirements: `pip install -r requirements.txt`
2. Run database migrations (or let FastAPI auto-create).
3. Start the server: `python -m backend.app`
4. Start the worker: `celery -A backend.queue.celery_app worker --loglevel=info`

### Frontend
1. Install dependencies: `cd frontend && npm install`
2. Start dev server: `npm run dev`

## Ethical Use
Corvus is intended for authorized security testing only. Scanning targets without explicit permission is illegal and unethical.

## 📚 Documentation
Corvus Red Edition uses MkDocs Material for professional documentation.

### Build Documentation
```bash
pip install mkdocs-material
mkdocs build
```

### Serve Locally
```bash
mkdocs serve
```
The documentation will be available at `http://127.0.0.1:8000`.

## License
MIT License
