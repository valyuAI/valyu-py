# Changelog

## 2.13.0

- DeepResearch: new `"instant"` mode (`DeepResearchMode.INSTANT`), the quickest and lowest-cost mode. It does not support `hitl` checkpoints and is not available for batches.
- DeepResearch: create and status responses expose `research_mode`. When a response carries `research_mode` but no `mode`, `mode` is filled from it, so `status.mode` reads `"instant"` for an instant task.
- DeepResearch: a status response that does not match the SDK's model now fails immediately with `success=False` and the validation message. Previously it was retried as a network error, and `wait()` kept polling until `max_wait_time`.
- DeepResearch: a successful create always returns `deepresearch_id`. A field that does not match the SDK's model is dropped instead of turning the response into `success=False`, which invited a retry that created and billed a second task.
- DeepResearch: `wait(on_interaction=...)` calls the callback once per interaction and waits the normal poll interval after responding. Previously it re-polled immediately and could call the callback, and submit a response, again for the same interaction.
- Batch and Workflows: a `success` key in a response body no longer fails the call with a duplicate-argument `TypeError`.
- Response parsing tolerates values newer than the SDK: an unknown task or batch status, mode, interaction type, `output_type` or output format is kept as a plain string instead of failing the whole response. Known values still parse to their enum members.

## 2.12.4

- DeepResearch: `files[].context` limit raised from 10,000 to 50,000 characters per file, with a new 100,000-character limit on the combined context across all files in a request.

## 2.12.3

- DeepResearch: conditional status polling. `status()`, `wait()` and `stream()` send the last `ETag` as `If-None-Match` and reuse the cached response on `304 Not Modified`. Servers that send no `ETag` are polled exactly as before.
- DeepResearch: `wait()` and `stream()` follow the server's `Retry-After` hint when no `poll_interval` is given (clamped to 1-30 seconds, default 5); `poll_interval` now defaults to `None` and an explicit value always wins.
- DeepResearch: a `Retry-After` on a 429/503 lengthens the jittered exponential backoff.
- DeepResearch: `on_progress` and stream progress callbacks are not repeated for a poll answered 304 Not Modified.
