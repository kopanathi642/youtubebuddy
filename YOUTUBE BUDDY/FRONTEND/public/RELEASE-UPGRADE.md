# Creative studio upgrade — 24 October 2026

This upgrade is based on the actual kopanathi642/youtubebuddy source at commit 7da379f26de4caadffe7f3aa88f6434de6bbd2e3. It preserves the original dark interface, routes and code, with a new /create workspace. It does not claim that all 360 catalog capabilities work or that the product exceeds Higgsfield in output quality.

## Working additions and corrections

- Framer Motion tabs, panel transitions, interactive motion presets, keyboard-accessible dialogs, focus handling and reduced-motion support.
- Real browser image animation: push in/out, pan left/right and drift; smooth/linear easing; 16:9, 9:16 and square output; brightness/contrast; 2–15 second WebM recording; cancellation and PNG still export. These are conventional 2D transforms, not AI scene generation. Source images stay on the device and outputs must be downloaded before leaving/reloading.
- A real task-specific text classifier in a browser Web Worker. Labeled-data validation, deduplication, deterministic splits, validation-based smoothing, held-out metrics, baseline comparison, exportable versions, explicit promotion and rollback by promoting an earlier version. Browser storage is not a durable cloud backup. No generative foundation model was trained or fine-tuned.
- A deterministic natural-language plan builder extracts requested count, ratio, duration and supported language names. Plans expose source dependencies and unavailable steps; they do not claim autonomous execution or LLM understanding.
- Canonical registry of the exact 360 requested capabilities with namespaced IDs, input/output contracts, engine, configuration, resource, permission and test requirements. Twelve catalog entries have implemented processing paths: eleven CPU operations plus browser image animation. The other 348 remain planned or require configuration; none is a working generative engine merely because its card exists.
- CPU FFmpeg engine: trim/split to up to ten ranges, slow motion (muted output), freeze-frame extraction, center crops to portrait/square/landscape, audio loudness normalization, metadata inspection, ratio validation, corruption/decode checking and export validation. Limits: source <=300 seconds; FFmpeg timeout 120 seconds. Center crop does not track a subject.
- Authenticated CPU job submission/status/queued cancellation, owner-scoped records, request idempotency, two-active-job owner limit, no fictitious percentages, Redis/Celery execution boundary and persisted output metadata. Running jobs cannot safely be cancelled by this worker; crash recovery and queue service deployment still require operational validation.
- Alembic baseline + additive tool_jobs migration. New production startup no longer creates tables implicitly. Migration tests preserve existing user data across the additive upgrade/downgrade.
- Invalid tokens can no longer become a demo user; token expiration is enforced; demo login requires an explicit development/test setting and remains blocked in production.
- Private files are not mounted publicly. Media grants are short-lived, resource-scoped, signed and recheck an active owner's database records at download time. Chunk registration checks the server-assigned owner prefix. Arbitrary image URL downloads are rejected.
- Canned text, procedural image posters and canned Whisper transcripts are rejected instead of being returned as AI output. Explicit provider choices are not silently replaced. Remote inference is disabled by default. Model weights are not automatically pulled; image/Whisper models require configured local checkpoint directories.
- Frontend dependency upgrades: Next.js 16.4.3, Firebase 13.1.0, Zod 4.6.7 and related patched dependencies. Production dependency audit reports zero known vulnerabilities at verification time. This is not a complete security certification.

## Run the original application locally

Backend (Python 3.12 was tested; FFmpeg and ffprobe must be installed):

    cd backend
    python -m venv .venv
    # Activate .venv using the command for your OS.
    pip install -r requirements.txt
    # Copy .env.example to .env and use your own settings.
    alembic upgrade head
    uvicorn app.main:app --host 127.0.0.1 --port 8000

Frontend (Node 24 was tested):

    cd FRONTEND
    npm ci
    npm run dev

Open http://localhost:3000/create. For development the frontend uses localhost:8000. For a separate HTTPS deployment set NEXT_PUBLIC_API_URL to the actual backend origin before building. Do not invent an API domain. Browser-only motion and training do not need a backend account. CPU jobs and private uploads do; create/sign into your own configured backend account.

Google/Firebase login and YouTube authorization need the owner's Firebase/OAuth configuration. Bundled fallback project identifiers have been removed. The previously delivered local-first editing workbench is preserved in the Sites package at /workbench/ with its IndexedDB data format unchanged.

## Existing database migration

Back up the database and private media first. If the original tables already exist, inspect and compare them with migrations/versions/0001_legacy_baseline.py. After confirming that they match, stamp the legacy baseline:

    alembic stamp 0001
    alembic upgrade head

Do not run the initial-create migration against an unstamped legacy database. Do not blindly stamp a database whose schema differs. New installations can run `alembic upgrade head` directly. The additive 0002 revision does not delete or alter original tables.

## Worker setup

Use PostgreSQL, persistent Redis and the configured Celery worker from docker-compose.yml, or run your own services. The worker command is:

    celery -A app.core.celery_app.celery_app worker --loglevel=info --concurrency=1

Redis AOF persistence and worker restart policy are configured. They do not create a cloud server or a high-availability guarantee. Render/upload volumes must be backed up independently of the database. No live Redis/Celery deployment was available in this environment; actual CPU engine outputs were verified directly, while queue submission and service availability remain deployment requirements.

## AI model setup

Optional Python model libraries are separated into requirements-ai.txt so the default install does not download large model runtimes. Install them only after checking hardware and licenses. Set LOCAL_IMAGE_MODEL_PATH and LOCAL_WHISPER_MODEL_PATH to existing licensed checkpoint directories. Inference uses local-files-only loading. Text generation needs an installed Ollama model matching OLLAMA_MODEL. No model download is triggered automatically.

The image adapter supports local SDXL text-to-image. It does not implement inpainting, subject identity preservation or image-to-video simply by reusing text prompts. No generative video/audio engine is installed. Generators remain unavailable until a compatible engine and real output are verified. Provider credentials must stay on the backend. Remote providers require ALLOW_REMOTE_INFERENCE=True after the owner reviews cost/privacy; no provider's current free quota is assumed or guaranteed.

## Verification

- Original frontend baseline built; 31 baseline schema/caption/video tests passed before modifications.
- Full non-live backend suite: 811 passed, 3 skipped, 17 live tests deselected. Live inference and external-account tests were not paid for or fabricated. Legacy tests that expected canned AI outputs were corrected to require an explicit unavailable error. The demo-login cache test now opts into demo mode explicitly.
- Catalog tests cover all 360 contracts and rejection of all 348 unavailable server operations. These are capability-boundary tests, not successful generation tests.
- Each of the eleven implemented FFmpeg CPU operations produced and validated real results from a generated test video. Private-media ownership and migration preservation checks passed.
- Seven new frontend logic tests passed: all five motion transforms, bounds, ratios, intent constraints, request-specific plans, actual classifier training/inference malformed-data rejection and the public demo login.
- Browser motion workflow: imported a real PNG fixture, selected 9:16 and a two-second pan, recorded WebM, downloaded it and verified VP9 at 720 × 1280 with ffprobe.
- Browser plan: “three vertical Shorts”, 20 seconds, Telugu + English extracted correctly; speaker tracking, silence removal and automatic subtitles remained blocked explicitly.
- Browser Model Lab: real worker training on an explicitly labeled synthetic 40-row fixture completed; 28 train, 6 validation, 6 test examples; 6/6 test predictions vs 3/6 majority baseline. A new “computer software code” input predicted “tech”. Promotion and saved version state were inspected. Synthetic smoke-test accuracy is not a real-world quality claim.
- TypeScript and production static export build passed. Source lint has no errors, with image-element performance advisories. The image elements display unknown-size provider output intentionally; no fabricated image is substituted.
- `pip check` passed. npm production dependency audit: 0 known vulnerabilities at verification time.

## Not completed or not verified

The entire 360-tool product; Higgsfield quality parity; image/video foundation-model fine-tuning; professional multitrack timeline/VFX/3D; actual generative media quality; speaker tracking; automatic silence removal; live Google/YouTube flows; deployed backend, PostgreSQL, Redis, object storage or GPU workers; custom GoDaddy domains; cloud backup restoration; production load tests; full end-to-end queue/crash recovery; comprehensive authorization of every inherited endpoint. Existing API keys, billing and external publishing paths also need a focused production audit before a public multi-user launch.

## Hosting and free 24/7 operation

The published artifact is the actual frontend build plus browser-local tools. It is separate from heavy compute. No paid cloud service, GPU allocation, domain change or billing account was enabled. No always-on server was provisioned. Free unlimited image/video inference, storage and guaranteed uptime cannot be promised. An owner-controlled machine can process locally while powered on; unattended cloud work needs a real host, provider limits, durable storage and monitoring.

## GitHub and delivery

Changes are prepared on the local codex/studio-reliability branch from the supplied repository. The owner connected GitHub during implementation. The delivery message records the resulting review branch and pull request after successful publishing. CI is included; its remote status must be checked separately from the local tests. No main-branch merge is performed automatically.

The Sites deployment preserves its existing owner-private audience. The new workspace is /create/. Domain youtubebuddy.in is not configured. Original Higgsfield source, assets and proprietary model weights were not copied; its public cinematic workflow descriptions informed the broad interaction categories only.

## Public demo login requested by the owner

- ID: demo@youtubebuddy.com
- Password: Demo@12345

The /demo page opens an explicitly labeled browser-only sandbox. These public credentials are not a backend session and grant no access to private account data, YouTube or backend jobs. Demo model versions use a separate browser storage key. Exit demo restores the ordinary local workspace. Production backend demo authentication remains blocked.

For owner-local backend testing only, .env.demo.example provides the same single demo account and a separate demo.db database. Copy it explicitly to .env in a development environment if wanted. Never deploy this public test credential file as a public backend configuration.
