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

---

## 2026-02-11 ADR-006: Three-Stage Summarization with Structured Extraction

**Status:** Accepted

**Context:**
A psychologist reviewing AI-generated summaries identified systematic failures: speaker misidentification (~15 instances), hallucinated emotions/events (~12), cross-chunk context loss (~8), and missed important themes (~10). The root cause: Stage 1's generic KEY_POINTS+SUMMARY format loses critical structure (who said what, exact emotions expressed, factual details), forcing Stage 2 to guess and hallucinate.

Research supports this: [TN-Eval (ACL 2025)](https://arxiv.org/html/2503.20648) found LLMs excel at completeness but struggle with faithfulness. The extract-then-abstract approach from [Clinical Text Summarization (PMC)](https://pmc.ncbi.nlm.nih.gov/articles/PMC10635391/) shows that structured extraction before synthesis significantly reduces hallucination.

**Decision:**
Replace the two-stage pipeline with a three-stage pipeline:
1. **Stage 1 — Structured Extraction**: Extract speakers, topics, emotions (with exact quotes), therapeutic moments, significant quotes, and factual details per chunk. Require quote-grounding for every claim.
2. **Stage 2 — Synthesis**: Generate key topics + detailed notes from structured extractions, with anti-hallucination instructions.
3. **Stage 3 — Faithfulness Verification**: Compare Stage 2 draft against Stage 1 extractions using a rubric (completeness, faithfulness, conciseness). Output corrected summary.

**Consequences:**
- (+) Quote-grounding in Stage 1 makes the pipeline self-grounding.
- (+) Stage 3 catches hallucinations AND omissions (research shows 20-40% reduction).
- (+) Structured extraction enables auditable summaries (every claim traceable to transcript).
- (-) ~2x token cost in Stage 1 (more structured output per chunk).
- (-) Stage 3 adds ~$0.002 and ~5s latency per session.
- (-) Parser must handle richer structured output (not just KEY_POINTS+SUMMARY).

---

## 2026-02-11 ADR-007: Hebrew-Only Prompts

**Status:** Accepted

**Context:**
The app serves Hebrew-speaking therapists. Maintaining both Hebrew and English versions of all prompts doubles maintenance effort and creates inconsistencies when only one version is updated.

**Decision:**
All new prompt development is Hebrew-only. Existing English prompts remain as dead-code fallback but receive no further updates. The language detector's auto-detect feature still exists but defaults to Hebrew.

**Consequences:**
- (+) Half the prompt maintenance effort.
- (+) Can optimize Hebrew phrasing without worrying about English equivalence.
- (-) If English-speaking therapists use the app in the future, prompts would need to be added.

---

## 2026-02-11 ADR-008: Summary Tiers for Subscription Model

**Status:** Accepted

**Context:**
Different therapists have different needs and willingness to pay. A one-size-fits-all summary is either too expensive for casual users or too shallow for clinical professionals.

**Decision:**
Three summary levels that map to subscription tiers:
- **Level 1 (Quick)**: Single-pass key topics. Free tier.
- **Level 2 (Standard)**: Structured extraction + synthesis. Standard subscription.
- **Level 3 (Clinical)**: Full pipeline with verification. Premium subscription.

During development/evaluation, all 3 levels are generated in one document for side-by-side comparison by the reviewing psychologist.

**Consequences:**
- (+) Natural monetization model — clear value differentiation between tiers.
- (+) Evaluation mode enables quality comparison.
- (+) Each tier has a distinct cost profile ($0.001 vs $0.005 vs $0.012).
- (-) Must maintain 3 pipeline configurations.
- (-) Need subscription management infrastructure (future).

---

## 2026-02-11 ADR-009: Rubric-Based Extraction and Verification Framework

**Status:** Accepted

**Context:**
The [TN-Eval](https://arxiv.org/html/2503.20648) rubric evaluates therapy notes on completeness, faithfulness, and conciseness. Research from [Self-Critique and Refinement (arXiv)](https://arxiv.org/abs/2512.05387) shows that using the same evaluation criteria for both generation and verification reduces hallucination by 20-40%.

**Decision:**
Use the same rubric dimensions (completeness, faithfulness, conciseness) across all three pipeline stages:
- **Stage 1**: "Extract ALL clinically relevant items (complete). Include exact quotes as evidence (faithful). Only extract what matters clinically (concise)."
- **Stage 2**: "Include all extracted items (complete). Only state what's in the extractions (faithful). No redundancy between sections (concise)."
- **Stage 3**: "Check: any extracted fact missing? (completeness). Any claim not in extractions? (faithfulness). Any redundant content? (conciseness)."

**Consequences:**
- (+) Consistent quality criteria across the entire pipeline.
- (+) Each stage has clear, measurable success criteria.
- (+) Evaluation rubric doubles as a generation guide.
- (-) Rubric must be translated into effective prompt instructions for each stage.
