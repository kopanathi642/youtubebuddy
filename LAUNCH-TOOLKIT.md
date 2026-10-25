# Focused launch toolkit

The post-login dashboard and both workspace sidebars now feature ten launch studios, one Buddy AI Director and a central five-role model hub at `/launch/`.

| Studio | Workspace |
| --- | --- |
| AI Image Generator | `/image/create/` |
| AI Image Editor | `/studios/image-editor/` |
| AI Video Generator | `/studio/create/` |
| Shorts Generator | `/studio/shorts/` |
| AI Video Editor | `/studios/video-editor/` |
| Thumbnail & Graphic Studio | `/studios/design/` |
| Captions & Translation | `/studios/captions/` |
| Audio & Voice Studio | `/studios/audio/` |
| Storyboard & Cinema | `/studios/story/` |
| YouTube Channel Intelligence | `/studios/youtube/` |

## Complete sidebar directory

“All 360 tools” expands into the exact 360 numbered inventory entries, organized in 30 categories with 12 entries each. Search matches tool names, numbers and categories, without a result cap. Selecting a tool opens its exact details at `/master/?tool=N`. Entries retain the full inventory's readiness states; navigation does not make planned or infrastructure-dependent tools operational. Existing specialized routes and category workspaces remain available.

## Five capability roles

Reasoning, image, video, vision and speech/audio are capability roles, not five verified live provider connections. The launch configuration is shared across the dashboard, sidebar and model hub. The hub reads the existing authenticated `/studio/providers` report only when requested and a backend is configured. It does not perform inference, upload files, enable remote inference or start paid jobs.

Configuration, provider-reported availability and verified task output are distinct. Missing role reports are not inferred from another role. Provider secrets must remain on the server. Actual task-specific adapters, rights-cleared models, credentials, quotas and representative output evaluations are required before a role can be considered production-ready. The present static deployment has no processing server connected; it cannot run Python/GPU workers itself. Live YouTube authorization also still requires its OAuth/server configuration.

## Training roadmap

Launch with existing model adapters and local editing operations. Add one specialized model only with properly licensed data and held-out evaluations. Consider further fine-tuning after collecting suitable data, compute, benchmarks and a sustainable budget. This change trains no foundation model and makes no accuracy or free 24/7 GPU-service guarantee.

## Verification

42 frontend logic tests pass, including exact catalog parity, all ten destinations, five-role coverage, login return safety and conservative provider readiness. TypeScript and the production static export pass. Lint reports zero errors and 18 warnings. The static route audit is recorded with the deployment release notes. These checks do not prove live inference or OAuth success. Browser interaction verification for this increment remains incomplete because automatic approval review previously rejected browser access on a usage limit; no alternative browser path was used.
