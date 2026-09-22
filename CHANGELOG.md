# Changelog

All notable changes to this kit are listed here, newest first. One entry per pull request, under `Unreleased`.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## Unreleased

### Added
- Initial ADW kit: shared runtime, phase scripts, prompt templates, zsh helper, tests (942373c).

### Changed
- Runner: stop the Claude CLI once its result file is written; no version probe or update traffic (33af881).
- Runner: harden the Claude runner and fix two README details (886c1b8).

### Fixed
- Classifier: accept a backticked `/kind` answer from `/classify` (d64d06a).
