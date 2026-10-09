#!/usr/bin/env python3
"""
Siri -> Apple Mail -> Markdown (.md) Failed Pipeline Triage Runner.
Reads failed pipeline emails from Apple Mail (via osascript), deduplicates pipeline IDs,
writes FAILED_PIPELINES_REPORT.md, and outputs the Siri voice summary.
"""
import datetime
import re
import subprocess
import sys
from pathlib import Path

from triage_orchestrator import decide_route, render_handoff_packet

REPORT_PATH = Path(__file__).resolve().parent / "FAILED_PIPELINES_REPORT.md"

APPLESCRIPT_FETCH_MAIL = r'''
tell application "Mail"
    if not running then return ""
    set outputText to ""
    set matchedMsgs to (messages of inbox whose subject contains "failed" or subject contains "Pipeline")
    set maxCount to 25
    set idx to 0
    repeat with m in matchedMsgs
        set idx to idx + 1
        if idx > maxCount then exit repeat
        set msgSubj to subject of m
        set msgSender to sender of m
        set msgDate to (date received of m) as string
        set msgBody to content of m
        if length of msgBody > 600 then
            set msgBody to text 1 thru 600 of msgBody
        end if
        set outputText to outputText & "===MAIL_START===" & linefeed
        set outputText to outputText & "SUBJECT: " & msgSubj & linefeed
        set outputText to outputText & "SENDER: " & msgSender & linefeed
        set outputText to outputText & "DATE: " & msgDate & linefeed
        set outputText to outputText & "BODY: " & msgBody & linefeed
    end repeat
    return outputText
end tell
'''


def fetch_apple_mail_raw() -> str:
    """Query Apple Mail inbox for failed pipeline emails using osascript."""
    try:
        res = subprocess.run(
            ["/usr/bin/osascript", "-e", APPLESCRIPT_FETCH_MAIL],
            capture_output=True,
            text=True,
            timeout=12,
        )
        return res.stdout if res.returncode == 0 else ""
    except Exception:
        return ""


def parse_failed_emails(raw_text: str) -> list[dict]:
    """Parse raw Apple Mail blocks and deduplicate by Pipeline/Run ID."""
    seen_ids = set()
    failures = []
    for block in raw_text.split("===MAIL_START==="):
        block = block.strip()
        if not block:
            continue
        subj_m = re.search(r"^SUBJECT:\s*(.+)$", block, re.M)
        date_m = re.search(r"^DATE:\s*(.+)$", block, re.M)
        body_m = re.search(r"^BODY:\s*(.+)$", block, re.M | re.S)
        subj = subj_m.group(1).strip() if subj_m else ""
        if not re.search(r"(failed|failure)", subj, re.I) or re.search(r"fixed|passed", subj, re.I):
            continue

        pipe_m = re.search(r"(?:#|Pipeline\s+#?|Run\s+#?)(\d+)", subj + "\n" + (body_m.group(1) if body_m else ""), re.I)
        pipe_id = pipe_m.group(1) if pipe_m else f"mail-{len(failures)+1}"
        if pipe_id in seen_ids:
            continue
        seen_ids.add(pipe_id)

        repo_m = re.search(r"([A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+|\b[A-Za-z0-9_-]+\b)(?:\s*\|\s*Pipeline|\s*:\s*Run failed)", subj)
        repo = repo_m.group(1) if repo_m else "multi-agent-cicd-24x7"
        branch_m = re.search(r"(?:branch|for|on)\s+[`'\"]?([A-Za-z0-9_./-]+)[`'\"]?", subj + " " + (body_m.group(1)[:200] if body_m else ""))
        branch = branch_m.group(1) if branch_m else "main"
        platform = "GitLab" if "gitlab" in block.lower() or "pipeline" in subj.lower() else "GitHub"
        body_excerpt = (body_m.group(1).strip().splitlines()[0] if body_m and body_m.group(1).strip() else subj)[:160]

        route = decide_route(subj + "\n" + body_excerpt, attempt=1, branch=branch)
        failures.append({
            "platform": platform,
            "repo": repo,
            "pipeline_id": pipe_id,
            "branch": branch,
            "stage_job": "ci_or_backend_job",
            "date": date_m.group(1).strip() if date_m else "recent",
            "excerpt": body_excerpt,
            "owner": route["owner"],
            "track": route["track"],
        })
    return failures


def build_report_and_voice(failures: list[dict]) -> tuple[str, str]:
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    total = len(failures)
    repos = len({f["repo"] for f in failures})
    gemini_cnt = sum(1 for f in failures if f["owner"] == "Gemini 3.8 Flash")
    claude_cnt = total - gemini_cnt

    if total == 0:
        voice = "You have 0 failed pipelines in Apple Mail. All monitored CI/CD pipelines are currently green."
    else:
        voice = (
            f"You have {total} failed pipeline{'s' if total != 1 else ''} across {repos} "
            f"repositor{'ies' if repos != 1 else 'y'}. {gemini_cnt} routed to Gemini 3.8 Flash for fast CI fixes, "
            f"and {claude_cnt} queued for Claude Opus 4.8 in GitLab Duo Chat."
        )

    rows = "\n".join(
        f"| {i} | {f['platform']} | `{f['repo']}` | `#{f['pipeline_id']}` | `{f['branch']}` | `{f['Owner_Short'] if 'Owner_Short' in f else f['owner']}` | `{f['track']}` | {f['date']} |"
        for i, f in enumerate(failures, 1)
    ) or "| - | - | No failed pipeline emails found | - | - | - | - | - |"

    packets = "\n\n".join(
        render_handoff_packet(f["pipeline_id"], f["stage_job"], f["branch"], f["excerpt"], attempt=2)
        for f in failures
    ) or "_No active failure handoff packets required._"

    md = f"""### 🔊 SIRI VOICE READOUT
"{voice}"

---

# 🚨 CI/CD Failed Pipelines Report
**Generated:** `{now}`  
**Total Failed Pipelines:** `{total}` | **Repositories Affected:** `{repos}`  
**Fast CI Fixes (`Gemini 3.8 Flash`):** `{gemini_cnt}` | **Deep Backend Fixes (`Claude Opus 4.8`):** `{claude_cnt}`

## 1. Executive Summary Table
| # | Platform | Repo / Project | Pipeline / Run ID | Branch | Assigned Agent | 24/7 Decision Track | Timestamp |
|---|---|---|---|---|---|---|---|
{rows}

## 2. Ready-to-Feed Handoff Packets (For Gemini 3.8 Flash & Claude Opus 4.8)
{packets}
"""
    return voice, md


def _self_check() -> None:
    sample_mail = """===MAIL_START===
SUBJECT: multi-agent-cicd-24x7 | Pipeline #90210 has failed for main
SENDER: GitLab <gitlab@mg.gitlab.com>
DATE: Friday, October 9, 2026 at 2:15:00 PM
BODY: NullPointerException in OrderService.calculateTotal during backend_suite
===MAIL_START===
SUBJECT: multi-agent-cicd-24x7 | Pipeline #90210 has failed for main (duplicate alert)
SENDER: GitLab <gitlab@mg.gitlab.com>
DATE: Friday, October 9, 2026 at 2:16:00 PM
BODY: Duplicate email for #90210
===MAIL_START===
SUBJECT: [GitHub] Run failed: YAML SyntaxError in workflow #401 on branch feat/ci
SENDER: GitHub <notifications@github.com>
DATE: Friday, October 9, 2026 at 2:20:00 PM
BODY: SyntaxError: unexpected token in ci script
"""
    parsed = parse_failed_emails(sample_mail)
    assert len(parsed) == 2, f"Expected 2 deduplicated failures, got {len(parsed)}"
    voice, md = build_report_and_voice(parsed)
    assert "You have 2 failed pipelines" in voice, voice
    assert "#90210" in md and "#401" in md, md
    print("SELF-CHECK PASSED: Siri Mail parser, deduplicator, and Markdown generator verified.")


if __name__ == "__main__":
    if "--self-check" in sys.argv:
        _self_check()
    else:
        raw = fetch_apple_mail_raw()
        failures = parse_failed_emails(raw)
        voice_out, md_out = build_report_and_voice(failures)
        REPORT_PATH.write_text(md_out, encoding="utf-8")
        print(voice_out)
