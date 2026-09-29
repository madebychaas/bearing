# Latest is a video channel

**Current revision:** Latest now defaults to complete produced stories and retains the headline-video loop under Quick headlines. The full opening/story/closing structure, sound design, and current verification are documented in [STUDIO_PRODUCTION.md](STUDIO_PRODUCTION.md). The notes below describe the preceding headline-video implementation.

Implemented September 28, 2026. The user's correction was explicit: realtime news should be video too. Bearing now opens to Latest, a continuously updated narrated headline-video loop. Watch retains all eleven longer illustrated stories and their bespoke imagery. Neither channel plays over the other; leaving a view or opening preferences pauses it.

## The viewing experience

The video is the primary surface, with an Up next queue and a direct source link. Each headline has an original 1280 x 720 typographic graphic containing its exact source title, topic, publisher, and original publication timestamp. Quiet motion and two locally synthesized voice tracks produce actual H.264/AAC video files. It is explicitly a publisher headline briefing with AI narration, not live footage or an independently verified summary. Article excerpts and imagined factual context are excluded from this lane.

Interests, warm/measured voices, 0.85/1/1.15 playback rates, music, captions, and reduced movement work across both channels. Voice changes start with the next segment; pace and music change immediately. Less movement covers the moving frame with its exact static graphic while narration continues. Native video decoding carries audio and picture together. Space/K and N/right-arrow controls work in either channel, alongside touch and fullscreen controls.

The viewer defaults to their interests and the preceding 24 hours, with one- and six-hour options and All interests. Publication timestamps determine eligibility, never fetch times. Date-only, timezone-less, future, and stale reports do not enter the recent-video queue. Recent topics interleave, so a busy World feed does not fill the entire loop. The secondary source library stays newest-first.

## Updates and production

The browser reads available reporting, source health, and the complete video edition every 30 seconds and on return to the tab. Updated video editions wait until the current segment finishes. The secondary reading list retains its manual updates button. Manual refresh reads available local results and never overrides publisher polling limits.

`channel/production/latest_video.py` targets 32 recent stories across topics, attempts up to eight missing or revised clips per worker pass, and reuses output after checking hashes. Both voice videos must fully decode before the segment is published. Caption boundaries come from actual synthesized phrase samples. Publication is atomic. Changed headlines, attribution, or publication times get new media identifiers; earlier artifacts and editions remain archived. A failed replacement cannot republish the obsolete version. Expired clips leave both producer and viewer eligibility.

The local server performs the existing feed/Watch pass, then headline-video production, and waits one minute before its next pass. NPR, PBS, Guardian World and Culture, DW, France 24, Al Jazeera, and KERA have a five-minute polling target. BBC section feeds use fifteen minutes; agency feeds use thirty to sixty. A publisher's longer RSS TTL takes precedence. Conditional requests, backoff, source snapshots and revision history remain intact. All neural synthesis and media rendering use CPU; no graphics service or GPU was interrupted.

This is near-live publisher-feed news. Arrival time includes publisher feed delay, source polling, local scheduling, clip production, and up to thirty seconds of browser polling. It is not an instantaneous wire service. Sleep and failures extend the delay. For a future seconds-oriented provider, AP supports feed long polling but requires an account and appropriate rights. No paid feed or external publication was created in this revision.

The headline lane is a local personal playback feature, not commercial syndication clearance. Existing source policies and the longer Watch channel's editorial and bespoke-art approval gates are unchanged. Code-generated typography lets headline clips refresh without waiting for image generation; Watch continues to provide the richer illustrated stories.

## Evidence

The implementation passes 42 Python checks and 10 JavaScript checks. Actual media were rendered with both voices and completely decoded before publication. Browser verification covers advancing picture and embedded audio, automatic segment transitions, channel switching without overlapping playback, preferences, reduced movement, queued arrivals at story boundaries, fullscreen, and mobile layout. Test-only update fixtures are removed afterward. Production records and final screenshots are retained under the channel's ignored runs/output folders.

Physical speaker output and the subjective quality of the voice delivery have not been listening-tested. The local preview remains available at http://127.0.0.1:8796/#latest.
