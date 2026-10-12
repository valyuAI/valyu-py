# Changelog

## 2.12.4

- DeepResearch: `files[].context` limit raised from 10,000 to 50,000 characters per file, with a new 100,000-character limit on the combined context across all files in a request.

## 2.12.3

- DeepResearch: conditional status polling. `status()`, `wait()` and `stream()` send the last `ETag` as `If-None-Match` and reuse the cached response on `304 Not Modified`. Servers that send no `ETag` are polled exactly as before.
- DeepResearch: `wait()` and `stream()` follow the server's `Retry-After` hint when no `poll_interval` is given (clamped to 1-30 seconds, default 5); `poll_interval` now defaults to `None` and an explicit value always wins.
- DeepResearch: a `Retry-After` on a 429/503 lengthens the jittered exponential backoff.
- DeepResearch: `on_progress` and stream progress callbacks are not repeated for a poll answered 304 Not Modified.
