# Architecture Decision Records

This document captures significant architecture decisions for the Note Taker project, including context, rationale, and consequences.

---

## 2026-02-10 ADR-001: Firestore for Session Metadata

**Status:** Accepted

**Context:**
Summarization was fire-and-forget (`asyncio.create_task`). When LLM calls failed, there was no tracking, no retry, and the user had to manually check Drive to see if a summary had been generated.

**Decision:**
Use Google Cloud Firestore for session metadata and job tracking. Only store metadata (file IDs, status, costs) -- never transcript content.

**Consequences:**
- (+) Enables status polling, retry tracking, and cost monitoring.
- (+) Same GCP project, no extra infrastructure required.
- (+) Cloud Run default service account has access out of the box.
- (-) Adds a dependency on Firestore.
- (-) Must encrypt refresh tokens before storing them for the retry worker.

---

## 2026-02-10 ADR-002: Encrypted Refresh Token Storage

**Status:** Accepted

**Context:**
The background retry worker needs to re-authenticate to the user's Google Drive. Refresh tokens are sensitive credentials that must not be stored in plaintext.

**Decision:**
Encrypt refresh tokens with Fernet (AES-128-CBC with HMAC) before storing in Firestore. The encryption key is stored as an environment variable (`FERNET_KEY`).

**Consequences:**
- (+) Tokens are safe at rest even if Firestore data is exposed.
- (+) `drive.file` scope limits access to only app-created files.
- (-) Key rotation requires re-encrypting all existing tokens.
- (-) If the encryption key is lost, stored tokens cannot be decrypted.

---

## 2026-02-10 ADR-003: Polling over WebSocket for Summary Status

**Status:** Accepted

**Context:**
The frontend needs to know when a summary is ready after a session ends. Three options were considered: WebSocket push, Server-Sent Events (SSE), and HTTP polling.

**Decision:**
Use simple HTTP polling every 5 seconds with a 5-minute timeout.

**Consequences:**
- (+) Simple to implement and reason about.
- (+) Works through all proxies, CDNs, and load balancers without special configuration.
- (+) No persistent server connections needed.
- (+) Graceful degradation -- if polling times out, the UI shows "check Drive later."
- (-) Slightly more server load than a push-based approach.
- (-) Maximum 5-minute visibility window (summary normally completes in ~30 seconds).

---

## 2026-02-10 ADR-004: Cloud Run Revision Tags for Staging

**Status:** Accepted

**Context:**
A staging environment is needed without affecting production. Three options were considered: a separate Cloud Run service, a separate GCP project, or revision tags on the existing service.

**Decision:**
Use `--no-traffic --tag staging` on the same Cloud Run services to create isolated staging URLs.

**Consequences:**
- (+) Zero cost when staging is not receiving traffic.
- (+) Same infrastructure and service accounts as production.
- (+) Clean promotion path -- just update traffic split to promote staging to production.
- (-) Shares the same Firestore database (isolated by collection prefix, e.g., `staging_sessions` vs `sessions`).

---

## 2026-02-10 ADR-005: LLM Retry with Exponential Backoff

**Status:** Accepted

**Context:**
On Feb 6, four summarization attempts failed due to transient `ConnectError` / `ReadError` between Cloud Run and the Anthropic API. There was no retry logic, so these failures were permanent.

**Decision:**
Add `retry_with_backoff()` to all LLM calls. Configuration: 3 retries with exponential backoff (2s, 4s, 8s). Non-retryable errors (HTTP 401, 402) fail immediately without retry.

**Consequences:**
- (+) Handles transient network issues automatically.
- (+) Clear error classification separates retryable from permanent failures.
- (-) Adds latency on failures (up to 14 seconds total wait across all retries).
- (-) Must ensure retried calls are idempotent (LLM inference calls are inherently idempotent).
