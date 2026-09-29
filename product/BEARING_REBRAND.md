# Bearing branding and repository handoff

September 29, 2026.

The product name is **Bearing**. The application remains in `channel/`, and the existing local address is http://127.0.0.1:8796/. The private repository is `madebychaas/bearing`; the existing branch name is retained.

This change is limited to product naming, repository/package metadata, documentation, and the media records needed to display the new name. No feature, editorial rule, playback algorithm, script content, layout, CSS, transition timing or preference behavior was redesigned.

## Branding changes

- Page title, accessible home label, masthead wordmark, brief attribution, story transition and preference-dialog heading now use Bearing.
- Studio display strings and headline-card branding now use Bearing. Presentation cache version labels include the brand so the existing producer creates new records instead of treating old branded media as current.
- Programme chapter labels, production log/error labels, source-fetch user-agent product name and the script desk's product name now use Bearing.
- The launcher is `Start Bearing.cmd`. Root and application READMEs, active product documentation and the private package manifest identify Bearing.
- Existing verified narration is reused for refreshed headline graphics and studio assembly. Older media remains on disk.

Compatibility identifiers (`CURRENT_*`, `current.preferences.v1`, internal selectors and machine paths) remain intact. Original art prompts and historical provenance retain their original wording; these are records of how assets were made, not current branding instructions. Dated audits describe the repository state at the time of those audits; the new repository handoff supersedes their observations about an unconfigured remote.

## Scope and repository hygiene

Broad feature development remains paused for the one-story end-to-end production milestone described in the root README. EasyNews is archival reference only and must not be inspected or used without an explicit comparison request.

Local runtimes, model files, credentials, browser evidence, production run caches, the archival reference snapshot and continuously regenerated headline/feed output are excluded from Git. The repository includes the application, tests, documentation, editorial source records and reviewed programme assets. See the root README for fresh-checkout setup and test prerequisites.
