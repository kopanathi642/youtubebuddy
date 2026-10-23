# End-to-end tests

Real-browser (headless Chromium) and live-API tests for YouTube Buddy.

## Prerequisites
- Backend running on :8000 (SQLite dev mode: `ENVIRONMENT=development`, `CELERY_TASK_ALWAYS_EAGER=true`)
- Frontend running on :3000 (`next start` after `next build`)
- `ffmpeg` on PATH

## Run
```bash
cd tests-e2e
npm install
npm run make-video            # creates test.mp4
python verify_backend.py      # 27 backend/API checks (needs `pip install requests`)
node full_suite.mjs           # 44 browser checks
node links.mjs                # verifies every rendered internal link resolves
```
Env overrides: `BASE_URL`, `API_URL`, `DEV_DB` (path to the backend SQLite file), `TEST_VIDEO`.

The suites create throwaway users (`full_<timestamp>@example.com`) and uploads; run them against a
development database only, never production.
