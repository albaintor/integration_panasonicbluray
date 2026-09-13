# Panasonic Bluray integration for Remote Two Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## Unreleased

_Changes in the next release_

---

## v1.3.3 - 2026-09-13
### Changed
- Reduced remote-control latency with a FIFO command queue and immediate acknowledgement for non-power commands.
- Prioritized user commands over status polling and replaced immediate post-command polling with a 750 ms debounced refresh.
- Added optimistic media-state updates for play, pause, stop and eject commands.
- Added a fast response path for Panasonic key commands when `X-MEI-RESULT` is available, with body parsing as fallback.
- Updated `ucapi` to the 0.7.x series.

## v0.0.1 - 2024-03-16
### Initial release

## v1.0.0 - 2024-07-22
### Optimizations for battery usage and upload to remote