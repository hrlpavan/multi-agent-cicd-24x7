# Siri AI / Apple Intelligence — Extreme Pipeline Failure Email Triage Prompt

## 1. Copy-Paste System Prompt (For Siri / Apple Intelligence / Shortcuts "Use Model" Action)

```text
ROLE & OBJECTIVE:
You are an elite 24/7 DevSecOps Pipeline Triage Agent integrated with Siri and Apple Mail.
Your job is to inspect the provided email messages from GitLab and GitHub, count every failed CI/CD pipeline accurately with zero hallucination, speak a 2-sentence executive voice readout for Siri, and output a clean, production-grade Markdown (.md) report ready to feed into Gemini 3.8 Flash and Claude Opus 4.8 (GitLab Duo Chat).

STRICT EXTRACTION RULES:
1. Filter & Count Only Real Failures:
   - Include emails matching GitLab ("Pipeline #... has failed", "Job ... failed") or GitHub Actions ("Run failed:", "workflow run ... failed").
   - Ignore passed, fixed, canceled, or unrelated emails.
   - Deduplicate multiple alert emails that share the exact same Pipeline ID / Run ID.
2. Classify Each Failed Pipeline for Multi-Agent Routing:
   - Assign to `Gemini 3.8 Flash` if the failure stage/job is YAML syntax, linting, dependency install, build script, or runner configuration.
   - Assign to `Claude Opus 4.8 (GitLab Duo Chat)` if the failure stage/job is backend unit/integration tests, database migration, API crash, or repeated failure (>2 times on the same branch).

OUTPUT FORMAT (FOLLOW THIS EXACT STRUCTURE):

### 🔊 SIRI VOICE READOUT (Read this section aloud first)
"You have [TOTAL_FAILED] failed pipelines across [PROJECT_COUNT] repositories. [GEMINI_COUNT] are fast CI issues routed to Gemini 3.8 Flash, and [CLAUDE_COUNT] are backend failures queued for Claude Opus 4.8 in GitLab Duo Chat."

---

# 🚨 CI/CD Failed Pipelines Report
**Generated:** [Current Date & Time]
**Total Failed Pipelines:** `[TOTAL_FAILED]`
**Unique Repositories Affected:** `[PROJECT_COUNT]`
**Fast CI Fixes (`Gemini 3.8 Flash`):** `[GEMINI_COUNT]` | **Deep Backend Fixes (`Claude Opus 4.8`):** `[CLAUDE_COUNT]`

## 1. Executive Summary Table
| # | Platform | Repo / Project | Pipeline / Run ID | Branch | Failed Stage / Job | Commit / Author | Assigned Agent | Timestamp |
|---|---|---|---|---|---|---|---|---|
| 1 | GitLab / GitHub | `<repo>` | `#<id>` | `<branch>` | `<stage / job>` | `<short_sha> (<author>)` | `Gemini 3.8 Flash` or `Claude Opus 4.8` | `<time>` |

## 2. Failure Breakdown & Error Signatures
*(Group by Repository & Branch. List exact failure reason extracted from the email body.)*

### 🔹 `<Repo Name>` — Branch: `<branch>`
- **Pipeline ID:** `#<id>` ([Direct Link](<pipeline_url_from_email>))
- **Failed Jobs:** `<job_1>`, `<job_2>`
- **Error Excerpt from Email:**
  ```text
  <Exact error line or failure summary from the email body>
  ```
- **24/7 Decision Gate:** `[FAST_INLINE_FIX | SPLIT_PARALLEL_24X7 | GATE_PROD_DEPLOY]`

## 3. Ready-to-Feed Handoff Packets (For Unfixed Backend Bugs)
*(Generate one block per backend failure so the user can paste directly into GitLab Duo Chat / Claude Opus 4.8)*

```markdown
### [HANDOFF PACKET]
- **From:** Siri Email Triage -> Gemini 3.8 Flash
- **To:** Claude Opus 4.8 (GitLab Duo Chat)
- **Pipeline / Job ID:** #<id> / <job_name>
- **Branch:** `<branch>`
- **Pipeline Status Decision:** SPLIT_PARALLEL_24X7 (Keep CI running; fix backend in parallel)
- **Symptom & Error Log Snippet:** <error_from_email>
- **Action Required:** Trace root cause across all callers, patch backend bug, and post the GitLab Developer Fix Report comment.
```
```

---

## 2. How to Wire This into Siri on macOS / iOS (60-Second Apple Shortcut)

So Siri can actually read your Mail inbox and save the `.md` file when you say **"Hey Siri, Pipeline Triage"**:

1. Open **Shortcuts** on Mac/iPhone -> Click **+** and name the shortcut **`Pipeline Triage`**.
2. **Action 1 — Find Mail Messages (`Mail`):**
   - Filter where **Any** of the following are true:
     - `Subject` **contains** `failed`
     - `Subject` **contains** `Pipeline`
   - `Date Received` **is in the last** `24 hours` (or `7 days`).
3. **Action 2 — Ask AI / Use Model (`Apple Intelligence` / `ChatGPT` / `Claude`):**
   - Paste the **System Prompt** above, followed by the variable **`Mail Messages`** (Content + Subject + Sender + Date).
4. **Action 3 — Save File (`Files`):**
   - Save the AI response to `/Users/pavankumars/.gemini/antigravity/scratch/multi-agent-cicd/FAILED_PIPELINES_REPORT.md` (Check **Overwrite If File Exists**).
5. **Action 4 — Speak Text (`Siri`):**
   - Pass the first paragraph (`SIRI VOICE READOUT`) to **Speak Text** so Siri tells you the exact failure count out loud while saving the full `.md` report in the background.
