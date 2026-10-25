# Home and navigation update — 25 October 2026

The starting route restores the original animated landing hero. It does not automatically redirect remembered demo visitors into the production hub. The home page includes six workflow launchers and all 30 category links.

The top navigation has Image, Video, Audio, Editor, Canvas, Director, YouTube, Automation and All tools menus. Two-column dropdowns group individual tools and workspace links. Search indexes categories, original tools and all 807 feature requirements, with availability labels and a result-limit indicator. It does not advertise unconfigured competitor models as connected.

Tool entry links go through /login/?next=..., retaining a validated same-origin workspace destination. Successful account/demo login opens the selected destination; remembered demo visitors can re-enter without submitting public credentials again. WorkspaceEntry gates the local production hub, shared generator UI and CreateStudio. This is a navigation gate for the public browser demo, not backend authentication. Existing account/API authorization and owner-private hosting access are retained.

Validation: 30 frontend logic tests pass; production export succeeds; lint has zero errors and 13 advisory warnings. Static audit: 107 pages, 606 exported internal links and no missing targets. Home source and exported HTML include the restored hero and the full category directory. Route destination tests reject external redirects, auth loops and malformed paths.

Browser verification of this increment is incomplete. Automatic approval review rejected preview navigation because execution hit its usage limit. No alternative browser surface or indirect browser workaround was used. Earlier editor/generator screenshots describe the previous release and are not proof of this new home page.

Live model/server deployment, website Google OAuth configuration and full multitrack rendering remain separate unfinished work.
