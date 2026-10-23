# YouTube Buddy — Fix & Test Report

Base: `origin/refactor/architecture-redesign`. Branch: `fix/audit-repairs` (18 commits, history preserved).

## Critical / security
| Issue | Fix |
|---|---|
| Any signed-in user could delete or read arbitrary server files via client-supplied `storage_path` (`/uploads/metadata` → `DELETE /videos/{id}`, transcription, shorts) — reproduced | Paths confined to the upload dir on registration, on use and before unlink |
| Uploads accepted any file (an `.exe` was stored) | Extension allow-list + magic-byte check (415 on failure) |
| Passwords stored as unsalted SHA-256 | bcrypt (SHA-256 pre-hash for long passphrases); legacy hashes verify and upgrade on next login |
| Demo credentials / dev-login active whenever `DEBUG` (default true) | Only when `ENVIRONMENT` is development/test; `DEBUG` defaults off; production refuses wildcard CORS, weak JWT secret and demo login |
| API responses leaked absolute server paths | Responses expose `url` instead of `storage_path` / `result_path` |
| Signup accepted any password | 8–128 characters enforced server-side |
| 23 npm advisories (`next` critical, `axios` high) | `npm audit fix` → 6 remaining (Firebase gRPC server code, nested PostCSS); only fixable with `--force` |

## Functional bugs
- `next build` failed on 3 ESLint errors.
- `PUT /user/profile` returned 500 (camelCase/snake_case mismatch).
- Deleting a video that had renders returned 500 (FK null); now cascades and removes rendered files.
- Profile and Settings pages were static mockups (Settings showed a fake API key). Now wired: profile save, real API-key create/revoke, persisted preferences.
- Export Short had no handler; now polls the render and opens the real mp4.
- "Create New Video", Filter, Agent Edit did nothing / linked to 404s; Sidebar Billing/Settings, Explore cards and footer links were 404s.
- Forgot-password always claimed success; now uses Firebase when configured, otherwise says it isn't set up.
- AI endpoints returned fabricated content with no keys, presented as real; responses now carry `simulated: true` and the UI says "Demo output".
- Error toasts showed generic axios text; they now show the server's reason.
- Documented Postgres URL could not work (`asyncpg` missing); docker-compose mixed dev mounts into production.

## Test results (all run, not assumed)
| Suite | Result |
|---|---|
| Browser (real Chromium, production build): `tests-e2e/full_suite.mjs` | **44 / 44** |
| Link audit (61 rendered internal links): `tests-e2e/links.mjs` | **all resolve** |
| Live API + security, SQLite: `tests-e2e/verify_backend.py` | **27 / 27** |
| Live API + security, PostgreSQL 16 via asyncpg | **23 / 23** (4 SQLite-only checks skipped) |
| `tsc --noEmit`, `next lint`, `next build` | clean (only `<img>` warnings) |

## Deployment requirements
- Backend: Python 3.12, ffmpeg, `pip install -r backend/requirements.txt`.
- Production env: `ENVIRONMENT=production`, `JWT_SECRET` (≥32 chars), `ALLOWED_ORIGINS=https://your-frontend`, `DATABASE_URL=postgresql+asyncpg://…`, `REDIS_URL`/Celery URLs, and at least one AI key. Never set `ENABLE_DEMO_LOGIN`.
- Frontend: `NEXT_PUBLIC_API_URL`, Firebase `NEXT_PUBLIC_*` keys (for Google login / password reset). Build with `npm ci && npm run build` (`.npmrc` sets `legacy-peer-deps`).
- Serve `/uploads` and `/rendered` from private object storage/CDN in production; they are currently public by (unguessable) filename.

## Known limitations / not verified
- Not exercised (need your credentials/services): real AI providers, Whisper transcription/captions, Google sign-in, YouTube connect, Redis + Celery worker, Docker images.
- Terms / Privacy / Cookie / About / Blog / Docs etc. are placeholders — **real legal text is required before launch**.
- Profile bio is stored on-device only (needs a DB migration for a backend column).
- Not implemented (absent in the original, out of scope): face tracking, smart vertical crop, silence removal; highlight detection exists only as an LLM prompt.
- Test builds in the sandbox used mocked Google Fonts (no internet); real builds need network access to fonts.googleapis.com.
