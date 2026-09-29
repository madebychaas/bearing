# Bearing — agent instructions

Bearing is an evolving product. Treat the existing product as the source of truth and improve it in place.

Before broad product work:

1. Read `product/PRODUCT_VISION.md` for the enduring product direction.
2. Read `product/NEXT.md` for the current mission.
3. Review the existing implementation and preserve what already works.

## How to work

- Work autonomously toward the current mission. Do not wait for implementation-level instructions when the product intent is clear.
- Prefer improving the existing architecture over rewriting or redesigning for its own sake.
- Evaluate the actual viewer experience, not only the implementation or test suite.
- Follow complete flows end-to-end when judging whether work is successful.
- Make small, meaningful Git commits at stable checkpoints.
- Run the relevant tests before committing stable milestones.
- Keep runtime state, credentials, caches, transient generated output, machine-specific configuration, and archival reference material out of Git.
- Do not introduce runtime or repository dependencies on archival/reference projects.

## Product discipline

Bearing should become simpler and more coherent as it improves, not merely more capable.

Do not add features because they are technically interesting. New work should materially strengthen the current mission or the product vision.

Protect the primary viewing experience from production controls, internal machinery, excessive metadata, dashboards, and unnecessary interface complexity.

Stop for the user only when work requires:

- a destructive or difficult-to-reverse action,
- an external account action,
- an unavailable credential or permission,
- or a genuine product decision that cannot safely be inferred.

Otherwise, keep going.
