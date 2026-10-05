# TS-003 — Husky Troubleshooting Images Not Rendering

## Contents

- [Status](#status)
- [Reported symptom](#reported-symptom)
- [Affected evidence](#affected-evidence)
- [Current findings](#current-findings)
- [Next item](#next-item)

## Status

**Open** — rendering problem reported; root cause and recovery are not yet known.

**GitHub issue:** [#1 — Husky troubleshooting images do not load properly](https://github.com/kirolossedra/RIS-Robotics/issues/1)

## Reported symptom

Images inside `robotics/husky/` are not loading properly when the documentation is viewed. The issue was reported on 2026-10-04.

## Affected evidence

The known inline images are referenced by [TS-001](TS-001-onboard-computer-no-power-reversed-polarity.md):

- `images/TS-001/01-husky-user-power-panel.jpg`
- `images/TS-001/02-onboard-computer-and-dc-input.jpg`
- `images/TS-001/03-12v-harness-overview.jpg`
- `images/TS-001/04-12v-split-harness-connectors.jpg`

## Current findings

All four image files exist in the repository, and their relative paths match the Markdown references in TS-001. This confirms the checked-out files and references are present; it does not establish why the images fail to render in the reported viewer.

No image was replaced, resized, or recompressed while recording this issue.

## Next item

Reproduce the failure in the viewer where it occurs. Then inspect the rendered Markdown request and image response to determine whether the cause is path resolution, hosting, or image decoding, and record the evidence and recovery here.
