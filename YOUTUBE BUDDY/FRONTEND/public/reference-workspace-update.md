# Reference-led editor and channel analyzer

The video editor and channel analyzer now use the two supplied screenshots as layout and color references. No screenshot statistics, example channels, source clips or completed renders are copied into user projects.

## Editor

`/studios/video-editor/` has a focused blue/purple workspace: local media pool with actual type/search filtering and source thumbnails, program monitor with 16:9/9:16/1:1/4:5 framing guides, frame-step controls, timeline, color/audio inspector, workflow-assistant panel and export strip. Existing real import, playback, trim, split, sequence reorder, gain and preview-grade behavior is retained. The assistant uses existing local intent rules and links to actual workspaces; it starts no model job. The output download remains an edit-decision JSON, not a composited MP4. Framing guides do not crop source files.

## Channel analyzer

`/studios/youtube/` has channel navigation, a cinematic banner, source-aware metric cards, interactive daily chart, latest-reported-day bars, paginated actual daily values, evidence-based insights and downloadable displayed-window reports. Existing report import, read-only OAuth setup, insights/export and local rule evaluation remain available. Connection/import controls open from a clear header action.

Seven/28/90-day display windows are relative to the last reported date and use calendar dates. Missing dates and missing metrics break chart segments, zero remains a valid observed value, and net subscriber losses remain negative. Revenue, demographics, search terms and competitor data are explicitly unavailable when absent; there is no fabricated realtime feed or private algorithm score. View-window exports contain the actual filtered snapshot.

Wide screens default to a focused workspace. The All tools button restores the full navigation. Smaller screens stack panels and retain the working analyzer navigation. Original media and local reports are not uploaded by these UI changes.

## Validation and remaining limits

57 frontend logic tests pass, including three new calendar-window/chart-data tests. TypeScript, production static export and route audit pass; current changed-source lint has zero errors and two local-image warnings. Interactive browser verification remains incomplete after the earlier automatic approval usage-limit rejection. These changes do not deploy model workers, complete a multitrack compositor or configure Google OAuth. Live inference and channel authorization are not newly verified.
