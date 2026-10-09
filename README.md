# 24/7 Multi-Agent CI/CD & Backend Debugging Architecture
**Models:** `Gemini 3.8 Flash` (CI/CD & Fast Fix) + `Claude Opus 4.8` (GitLab Duo Chat Deep Backend Debugger & Scribe)

This repository contains both the **Multi-Agent Coordination Protocol** ([`MULTI_AGENT_PROTOCOL.md`](./MULTI_AGENT_PROTOCOL.md)) and the **Working 24/7 Split-Track CI/CD Architecture**:

- [`MULTI_AGENT_PROTOCOL.md`](./MULTI_AGENT_PROTOCOL.md) — Full role boundaries, decision matrix for unfixed backend bugs, `[HANDOFF PACKET]` schema, mandatory GitLab MR developer comment template, and copy-paste model activation prompts.
- [`triage_orchestrator.py`](./triage_orchestrator.py) — Zero-dependency Python routing engine that classifies failures between `Gemini 3.8 Flash` (fast inline CI/code fixes) and `Claude Opus 4.8` (deep backend RCA in GitLab Duo Chat), emits `[HANDOFF PACKET]`s, and posts MR notes via the GitLab API.
- [`.gitlab-ci.yml`](./.gitlab-ci.yml) — Working GitLab CI/CD pipeline configured for non-stop 24/7 execution with automatic handoff packet generation on backend failure.
- [`.github/workflows/multi-agent-ci.yml`](./.github/workflows/multi-agent-ci.yml) — Mirror GitHub Actions workflow verifying the routing engine on every push.

## Quick Verification
```bash
python3 triage_orchestrator.py --self-check
```
