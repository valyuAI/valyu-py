# Changelog

## 2.12.3

- DeepResearch: add the `instant` mode ($0.05 per task) to `DeepResearchMode`, batch and workflow mode types. `lite` stays accepted as deprecated.
- DeepResearch: conditional status polling. `status()`, `wait()` and `stream()` send the last `ETag` as `If-None-Match` and reuse the cached response on `304 Not Modified`.
- DeepResearch: `wait()` and `stream()` follow the server's `Retry-After` hint when no `poll_interval` is given (clamped to 1-30 seconds); `poll_interval` now defaults to `None` and an explicit value always wins.
- DeepResearch: a `Retry-After` on a 429/503 lengthens the jittered exponential backoff.
- DeepResearch: `on_progress` and stream progress callbacks fire only when the task's response changed.
- Docs: per-mode prices corrected (heavy is $2.50 per task).
