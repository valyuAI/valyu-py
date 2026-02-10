# Contents API Async Mode - SDK Documentation Update Guide

This guide describes how to update SDK documentation to reflect the async Contents API changes.

---

## 1. API Reference / Method Signature

### `contents()` method

**Location**: API reference, method docs (e.g. docstring, README, dedicated API docs)

**Update the signature** to include new parameters:

```
contents(
    urls: List[str],
    summary: Optional[Union[bool, str, Dict]] = None,
    extract_effort: Optional[str] = None,
    response_length: Optional[str | int] = None,
    max_price_dollars: Optional[float] = None,
    screenshot: bool = False,
    async_mode: bool = False,
    webhook_url: Optional[str] = None,
    wait: bool = False,
    poll_interval: int = 5,
    max_wait_time: int = 3600,
) -> Union[ContentsResponse, ContentsJobCreateResponse, ContentsJobStatus]
```

**Add parameter docs**:

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `async_mode` | `bool` | No | Use async processing. Required for >10 URLs. When `True`, returns job immediately unless `wait=True`. |
| `webhook_url` | `str` | No | HTTPS URL for completion notification (async only). Store the returned `webhook_secret` for signature verification. |
| `wait` | `bool` | No | When `async_mode=True`, poll until complete and return final results. Default: return job immediately. |
| `poll_interval` | `int` | No | Seconds between polls when `wait=True`. Default: 5. |
| `max_wait_time` | `int` | No | Max seconds to wait when `wait=True`. Default: 3600. |

**Update URL limits**:

- Sync: 1–10 URLs (default)
- Async: 1–50 URLs (when `async_mode=True` or when >10 URLs)

**Update return type description**:

- Sync: `ContentsResponse` (200/206)
- Async, `wait=False`: `ContentsJobCreateResponse` (job_id, webhook_secret)
- Async, `wait=True`: `ContentsJobStatus` (terminal status with results)

---

## 2. New Methods

### `get_contents_job(job_id: str) -> ContentsJobStatus`

**Add to API reference**:

Fetches the current status of an async contents job.

| Parameter | Type | Description |
|-----------|------|-------------|
| `job_id` | `str` | Job ID from async `contents()` response |

### `wait_for_contents_job(job_id, poll_interval=5, max_wait_time=3600, on_progress=None) -> ContentsJobStatus`

**Add to API reference**:

Polls until the job reaches a terminal state (completed, partial, failed).

| Parameter | Type | Description |
|-----------|------|-------------|
| `job_id` | `str` | Job ID to wait for |
| `poll_interval` | `int` | Seconds between polls |
| `max_wait_time` | `int` | Max wait time in seconds |
| `on_progress` | `Callable[[ContentsJobStatus], None]` | Optional progress callback |

**Raises**: `TimeoutError` if `max_wait_time` exceeded; `ValueError` if job fails.

---

## 3. Type Reference Updates

### Result types (breaking change)

**Update `ContentsResult`**:

Results are now a union of success and failed:

- `ContentsResultSuccess`: `url`, `status="success"`, `title`, `content`, `length`, `source`, `screenshot_url`, `summary`, etc.
- `ContentsResultFailed`: `url`, `status="failed"`, `error`

**Document the migration**:

```
# Before - all results were successful
for result in response.results:
    print(result.title)

# After - check status before accessing success-only fields
for result in response.results:
    if result.status == "success":
        print(result.title)
    else:
        print(f"Failed: {result.url} - {result.error}")
```

### New types

**Add type docs**:

- `ContentsJobCreateResponse`: `success`, `job_id`, `status`, `urls_total`, `webhook_secret`, `tx_id`
- `ContentsJobStatus`: `success`, `job_id`, `status`, `urls_total`, `urls_processed`, `urls_failed`, `results` (when terminal), `actual_cost_dollars`, `error`

**Job status values**: `pending`, `processing`, `completed`, `partial`, `failed`

---

## 4. Webhook Verification

**Add section**: How to verify webhook signatures

```python
from valyu import verify_contents_webhook

def handle_webhook(request):
    payload = request.body
    signature = request.headers.get("X-Webhook-Signature")
    timestamp = request.headers.get("X-Webhook-Timestamp")

    if not verify_contents_webhook(payload, signature, timestamp, WEBHOOK_SECRET):
        return 401
```

**Include**:

- `verify_contents_webhook(payload, signature, timestamp, secret)` function
- Where to get `webhook_secret` (from job creation when `webhook_url` is set)
- Header names: `X-Webhook-Signature`, `X-Webhook-Timestamp`

---

## 5. Code Examples

### Add async examples

**Async with `wait=True`** (blocks until complete):

```python
result = valyu.contents(
    urls=[...],
    async_mode=True,
    wait=True,
)
for r in result.results:
    if r.status == "success":
        print(r.title)
```

**Async with polling**:

```python
job = valyu.contents(urls=[...], async_mode=True)
print(f"Job ID: {job.job_id}")

status = valyu.get_contents_job(job.job_id)
while status.status not in ("completed", "partial", "failed"):
    time.sleep(5)
    status = valyu.get_contents_job(job.job_id)
```

**Async with webhook**:

```python
job = valyu.contents(
    urls=[...],
    async_mode=True,
    webhook_url="https://yourserver.com/webhook",
)
WEBHOOK_SECRET = job.webhook_secret
```

### Update existing examples

Ensure every `for result in response.results:` loop checks `result.status` before accessing `title`, `content`, etc.

---

## 6. Migration / Changelog

**Add migration notes**:

1. **Result handling**: All results include `status`. Check `result.status == "success"` before using success-only fields.
2. **>10 URLs**: Requires `async_mode=True`. Previously returned an error; now supported via async.
3. **Failed URLs**: Failed URLs are returned in `results` with `status="failed"` and `error`, instead of being omitted.

---

## 7. Checklist for doc updates

- [ ] API reference: `contents()` signature and parameters
- [ ] API reference: `get_contents_job()` and `wait_for_contents_job()`
- [ ] Type reference: `ContentsResult` success/failed variants
- [ ] Type reference: `ContentsJobCreateResponse`, `ContentsJobStatus`
- [ ] Webhook verification section
- [ ] Async examples (wait, polling, webhook)
- [ ] Existing examples: add `status` checks
- [ ] Migration/changelog notes
- [ ] URL limits table (sync 1–10, async 1–50)
