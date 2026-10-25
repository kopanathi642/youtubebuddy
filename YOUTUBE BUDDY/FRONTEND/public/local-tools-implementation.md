# Direct local operations across the 360-tool inventory

Twenty numbered tools now open a dedicated browser-local workbench at `/tools/?tool=N`. The full sidebar uses this direct route for these tools; every other entry retains its implementation record. The master detail modal also includes a direct run link. Existing tool IDs, categories, backend contracts, landing page, demo entry and private audience remain intact.

| Numbers | Implemented local operation |
| --- | --- |
| 164 | Explicit subtitle timestamp offset; refuses negative times |
| 165 | Rule-based subtitle quality checks |
| 166, 167 | Actual SRT and WebVTT file export |
| 188, 331 | Exact solid-color text/caption contrast calculation |
| 194 | Image pixel sampling and quantized palette extraction |
| 212 | Metadata JSON schema/length checks with user-selected limits |
| 275 | SHA-256 content duplicate detection |
| 288, 300 | Actual ZIP packaging of selected assets and a manifest |
| 293 | Bounded JSON metadata import and normalized export |
| 294 | Existing SRT/WebVTT import and validation |
| 305, 306 | Browser-decoded image/video dimensions and target checks |
| 309 | Expected-file list versus selected files, including name ambiguity |
| 310 | Caption timing bounds versus actual selected media duration |
| 311 | Limited file signature, extension, size and hash inspection |
| 330 | Caption line length, duration and reading-speed analysis |
| 342 | Selected-file storage calculation |

These are bounded operations rather than claims that the full target feature is finished. For example, caption timing bounds do not measure spoken-word alignment, header checks do not fully decode corruption, a selected-assets ZIP is not a full Premiere project handoff, and selected-file byte totals are not cloud-account storage. The UI explains these limits before execution. The inventory records partial local workflows, not production-certified completion.

## Privacy, correctness and limits

All selected files stay in the browser. No provider credentials, model calls or uploads are involved. Files are limited to 100 selections and 50 MB combined; text/metadata inputs are limited to 2 MB. Archive entries use unique flat filenames and a manifest retaining original filenames. The ZIP writer includes CRC32 checksums and UTF-8 names. Object URLs and decoded image bitmaps are released. Media metadata reads have an explicit timeout. Output downloads contain actual computed results; no canned media are supplied.

Caption checks use existing supplied cues. They do not transcribe, translate or make AI grammar corrections. Palette sampling excludes sufficiently transparent pixels. Metadata limits are explicit user choices, not a guarantee of platform acceptance or SEO ranking. Unknown file signatures remain unknown.

## Verification

54 frontend logic tests pass. Eight new tests exercise distinct behaviors, including caption serialization roundtrips, timing bounds, invalid input rejection, exact inventory routing, actual pixel palettes, dimension checks and content-hash grouping. An independent Python ZIP reader reads the exported archive, validates CRCs and verifies UTF-8 filenames and original bytes. Changed-source lint has no errors. The production static export and link checks pass; exact deployment route totals are in the release notes.

Browser interaction verification remains incomplete because of the earlier automatic approval usage-limit rejection. Logic tests do not prove that every browser supports every selected media codec. No new backend code was changed; the prior 812 backend checks and CPU output fixtures remain evidence for their stated scopes, not live provider inference.

## Remaining completion blockers

This increment does not finish all 360 product targets. There is no GPU runtime, installed image/speech checkpoint or deployed authenticated processing server in the current environment. Model-dependent tools still require real model adapters, licensed weights and suitable compute or configured provider services. Generative video, live YouTube authorization, cloud collaboration, scheduling and complete composited renders remain incomplete. No foundation model training or Higgsfield-level output quality is claimed.
