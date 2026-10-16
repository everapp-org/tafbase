---
id: CONCEPT-taf-v1-006-01-the-subtitle-track
status: draft
subproject: taf
authored: 2026-10-16
authors:
  - George Petrov
  - Devin
---

# The subtitle track

## Definition

An `.srt` sidecar beside the run video: each narrated step
([[CONCEPT-dsl-v1-006-01-the-label]]) mapped onto video timecodes —
`1 / 00:00:04,200 --> 00:00:05,000 / Clicking 'Sign In' on 'Login'`.
The run replays *readable* — a watcher sees what the suite was doing,
not just where the mouse was.

## Why it exists

The old framework wired *all five* teardown paths to capture a video-
stop timestamp and call `createSubTitlesFile` — a writer that was only
ever committed commented out. The intent was fully built except for
the last function: narration existed (`canonicalName`), timestamps
existed (`setStartVideo`), the video existed — only the SRT serializer
was missing. In generated code it's nearly free: emitted steps know
their text and their clock, so a teardown writes the file.

## In this project

Planned — the narration half is lane H-8 (`label`), the video half is
lane J-10's artifact layout
([[CONCEPT-taf-v1-004-01-the-artifacts]]); the `.srt` writer is the
cheap tail of both.

## Touch it

Not yet — the prerequisites it needs are the labels and the video.

## Neighbors

[[CONCEPT-dsl-v1-006-01-the-label]],
[[CONCEPT-dsl-v1-003-01-the-dwell]] (a dwell is where a caption
breathes), [[CONCEPT-taf-v1-004-01-the-artifacts]].
