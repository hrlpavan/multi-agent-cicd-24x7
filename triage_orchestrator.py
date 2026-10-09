#!/usr/bin/env python3
"""
24/7 Multi-Agent CI/CD & Backend Triage Orchestrator (Stdlib-only).
Routes failures between Gemini 3.8 Flash (CI/CD & fast fixes) and
Claude Opus 4.8 in GitLab Duo Chat (deep backend RCA & dev MR comments).
"""
import json
import os
import sys
import urllib.request

CRITICAL_MARKERS = ("DATALOSS", "AUTH_BYPASS", "MIGRATION_CORRUPT", "SECURITY_CRITICAL")
CI_CONFIG_MARKERS = ("YAML", "SyntaxError", "ModuleNotFoundError", "command not found", "Runner")


def decide_route(log_text: str, attempt: int = 1, branch: str = "feature") -> dict:
    """Return routing decision based on log signature, retry count, and branch."""
    if any(m in log_text for m in CRITICAL_MARKERS):
        return {
            "owner": "Claude Opus 4.8 (GitLab Duo Chat)",
            "track": "GATE_PROD_DEPLOY",
            "allow_ci_continue": branch != "main",
            "reason": "Critical backend/security failure detected; gating production deploy.",
        }
    if attempt <= 2 and any(m in log_text for m in CI_CONFIG_MARKERS):
        return {
            "owner": "Gemini 3.8 Flash",
            "track": "FAST_INLINE_FIX",
            "allow_ci_continue": True,
            "reason": f"Fast CI/config issue (attempt {attempt}/2); fix inline via Gemini 3.8 Flash.",
        }
    return {
        "owner": "Claude Opus 4.8 (GitLab Duo Chat) + Gemini 3.8 Flash",
        "track": "SPLIT_PARALLEL_24X7",
        "allow_ci_continue": True,
        "reason": "Backend bug unresolved; isolating job so CI continues 24x7 while Claude Opus 4.8 debugs.",
    }


def render_handoff_packet(pipeline_id: str, job_name: str, branch: str, log_text: str, attempt: int = 1) -> str:
    d = decide_route(log_text, attempt, branch)
    snippet = "\n".join(log_text.strip().splitlines()[-15:])
    return f"""### [HANDOFF PACKET]
- **From:** Gemini 3.8 Flash (CI/CD Monitor)
- **To:** {d['owner']}
- **Pipeline / Job ID:** #{pipeline_id} / `{job_name}`
- **Branch:** `{branch}`
- **Pipeline Status Decision:** `{d['track']}` ({d['reason']})
- **Symptom & Error Log Snippet:**
```text
{snippet}
```
- **Action Required:** Perform root-cause fix across all callers and post the Developer Fix Report comment."""


def post_gitlab_comment(body: str) -> bool:
    """Post handoff/fix report to GitLab MR or Commit using stdlib urllib if env vars exist."""
    api = os.environ.get("CI_API_V4_URL")
    proj = os.environ.get("CI_PROJECT_ID")
    mr_iid = os.environ.get("CI_MERGE_REQUEST_IID")
    token = os.environ.get("GITLAB_TOKEN")
    if not (api and proj and mr_iid and token):
        return False
    url = f"{api}/projects/{proj}/merge_requests/{mr_iid}/notes"
    req = urllib.request.Request(
        url,
        data=json.dumps({"body": body}).encode("utf-8"),
        headers={"PRIVATE-TOKEN": token, "Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        return 200 <= resp.status < 300


def _self_check() -> None:
    r1 = decide_route("SyntaxError: invalid syntax in ci script", attempt=1)
    assert r1["owner"] == "Gemini 3.8 Flash" and r1["track"] == "FAST_INLINE_FIX", r1

    r2 = decide_route("NullPointerException in OrderService.calculateTotal", attempt=1)
    assert r2["track"] == "SPLIT_PARALLEL_24X7" and r2["allow_ci_continue"] is True, r2

    r3 = decide_route("FATAL: AUTH_BYPASS in token verifier", attempt=1, branch="main")
    assert r3["track"] == "GATE_PROD_DEPLOY" and r3["allow_ci_continue"] is False, r3

    pkt = render_handoff_packet("1042", "backend_unit_test", "feat/orders", "AssertionError: 500 != 200", 2)
    assert "[HANDOFF PACKET]" in pkt and "SPLIT_PARALLEL_24X7" in pkt, pkt
    print("SELF-CHECK PASSED: All multi-agent routing decisions verified.")


if __name__ == "__main__":
    if "--self-check" in sys.argv:
        _self_check()
    else:
        log_input = sys.stdin.read() if not sys.stdin.isatty() else "Backend test failure in worker"
        packet = render_handoff_packet(
            os.environ.get("CI_PIPELINE_ID", "local"),
            os.environ.get("CI_JOB_NAME", "backend_job"),
            os.environ.get("CI_COMMIT_REF_NAME", "main"),
            log_input,
        )
        print(packet)
        post_gitlab_comment(packet)
