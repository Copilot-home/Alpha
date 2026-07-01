#!/usr/bin/env python3
"""Self-contained GitHub automation helper.

Replaces the external `actions/github-script`, `actions/labeler`,
`actions/stale`, `actions/first-interaction` and `codelytv/pr-size-labeler`
actions with plain REST API calls so the workflows run even when the repo's
Actions allow-list blocks third-party actions.

Auth: GITHUB_TOKEN (or GH_TOKEN). Event payload: GITHUB_EVENT_PATH.
"""
from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone

API = "https://api.github.com"
TOKEN = os.getenv("GITHUB_TOKEN") or os.getenv("GH_TOKEN") or ""
REPO = os.getenv("GITHUB_REPOSITORY", "")
OWNER, _, NAME = REPO.partition("/")


def _event() -> dict:
    path = os.getenv("GITHUB_EVENT_PATH")
    if path and os.path.exists(path):
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    return {}


def api(method: str, path: str, body: dict | None = None, accept: str | None = None):
    url = path if path.startswith("http") else f"{API}{path}"
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Authorization", f"Bearer {TOKEN}")
    req.add_header("Accept", accept or "application/vnd.github+json")
    req.add_header("X-GitHub-Api-Version", "2022-11-28")
    req.add_header("User-Agent", "daiof-gh-bot")
    if data is not None:
        req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req) as resp:
            raw = resp.read().decode()
            return json.loads(raw) if raw else {}
    except urllib.error.HTTPError as exc:
        print(f"  ! API {method} {path} -> {exc.code}: {exc.read().decode()[:300]}")
        return None


def paged(path: str) -> list:
    out: list = []
    page = 1
    sep = "&" if "?" in path else "?"
    while True:
        chunk = api("GET", f"{path}{sep}per_page=100&page={page}")
        if not chunk:
            break
        out.extend(chunk)
        if len(chunk) < 100:
            break
        page += 1
    return out


def add_labels(num: int, labels: list[str]):
    if labels:
        api("POST", f"/repos/{REPO}/issues/{num}/labels", {"labels": labels})
        print(f"  + labels on #{num}: {', '.join(labels)}")


def comment(num: int, text: str):
    api("POST", f"/repos/{REPO}/issues/{num}/comments", {"body": text})
    print(f"  + comment on #{num}")


# --------------------------------------------------------------------------- #
# PR auto review / merge (was auto-pr-review.yml github-script)
# --------------------------------------------------------------------------- #
def cmd_pr_review():
    pr = _event().get("pull_request", {})
    if not pr:
        return
    num = pr["number"]
    if pr.get("user", {}).get("login") == "github-actions[bot]":
        print("Skipping organism self-PR")
        return
    files = paged(f"/repos/{REPO}/pulls/{num}/files") or []
    auto_approve = True
    notes: list[str] = []
    for f in files:
        if f.get("additions", 0) > 500:
            auto_approve = False
            notes.append(f"⚠ Large change in {f['filename']}: {f['additions']} additions")
        if "secret" in f["filename"] or ".env" in f["filename"]:
            auto_approve = False
            notes.append(f"🔒 Sensitive file detected: {f['filename']}")
    if notes:
        comment(num, "🧬 **Organism Auto-Review**\n\n" + "\n".join(notes) +
                "\n\n*Automated review by Digital Organism*")
    if auto_approve and len(files) < 10 and pr.get("additions", 0) < 200:
        api("POST", f"/repos/{REPO}/pulls/{num}/reviews",
            {"event": "APPROVE",
             "body": "✅ **Auto-approved by Organism**\n\nSmall, focused PR. "
                     "Safe to merge.\n\n*Automated approval by Digital Organism*"})
        add_labels(num, ["auto-approved", "ready-to-merge"])
        print(f"  approved #{num}")


def cmd_pr_merge():
    ev = _event()
    if ev.get("review", {}).get("state") != "approved":
        return
    pr = ev.get("pull_request", {})
    num = pr.get("number")
    if not num:
        return
    labels = api("GET", f"/repos/{REPO}/issues/{num}/labels") or []
    if any(l.get("name") == "auto-approved" for l in labels):
        res = api("PUT", f"/repos/{REPO}/pulls/{num}/merge",
                  {"merge_method": "squash",
                   "commit_title": f"🧬 {pr.get('title', '')}"})
        if res is not None:
            print(f"  ✅ PR #{num} auto-merged")


# --------------------------------------------------------------------------- #
# Issue auto label / respond (was auto-issue-management.yml)
# --------------------------------------------------------------------------- #
def cmd_issue_label():
    issue = _event().get("issue", {})
    if not issue:
        return
    title = (issue.get("title") or "").lower()
    body = (issue.get("body") or "").lower()
    labels: list[str] = []
    if "bug" in title or "bug" in body:
        labels.append("bug")
    if "feature" in title or "enhancement" in title:
        labels.append("enhancement")
    if "documentation" in title or "docs" in title:
        labels.append("documentation")
    if "question" in title or "how to" in body:
        labels.append("question")
    if "urgent" in title or "critical" in title:
        labels.append("priority: high")
    if "good first" in title or "beginner" in body:
        labels.append("good first issue")
    labels.append("auto-labeled")
    add_labels(issue["number"], labels)


def cmd_issue_respond():
    issue = _event().get("issue", {})
    if not issue:
        return
    msg = (
        "👋 **Welcome to DAIOF Framework!**\n\n"
        "Thank you for opening this issue! The Digital Organism has received "
        "your submission.\n\n"
        "🧬 **Next Steps:**\n- Issue has been automatically labeled\n"
        "- Our team will review within 24-48 hours\n"
        "- You'll be notified of any updates\n\n"
        "📚 **Helpful Resources:**\n"
        f"- [Documentation](https://github.com/{REPO}#readme)\n"
        f"- [Contributing Guide](https://github.com/{REPO}/blob/main/CONTRIBUTING.md)\n"
        f"- [Examples](https://github.com/{REPO}/tree/main/examples)\n\n"
        "*Automated response by Digital Organism* 🤖"
    )
    comment(issue["number"], msg)


# --------------------------------------------------------------------------- #
# Community engagement (was community-engagement.yml)
# --------------------------------------------------------------------------- #
def cmd_community_recognize():
    pr = _event().get("pull_request", {})
    if not pr or not pr.get("merged"):
        return
    num = pr["number"]
    msg = (
        f"🎉 **Thank you @{pr['user']['login']}!**\n\n"
        "Your contribution has been merged and is now part of the Digital "
        "Organism! 🧬\n\n"
        "**Impact**:\n"
        f"- {pr.get('additions', 0)} additions, {pr.get('deletions', 0)} deletions\n"
        f"- {pr.get('changed_files', 0)} files changed\n"
        f"- Merged into `{pr['base']['ref']}` branch\n\n"
        "🏆 **Recognition**: You're now part of the DAIOF contributor community!\n"
    )
    if pr.get("additions", 0) > 100:
        msg += "🌟 **Major Contribution** - Significant impact on the framework!\n"
    if pr.get("changed_files", 0) >= 5:
        msg += "🎯 **Multi-faceted Work** - Touched multiple areas of the codebase!\n"
    msg += "\n*Automated recognition by Digital Organism*"
    comment(num, msg)
    if (pr.get("additions", 0) > 50 or pr.get("changed_files", 0) >= 3 or
            ("feature" in pr.get("title", "").lower() and pr.get("additions", 0) > 20)):
        api("POST", f"/repos/{REPO}/issues/{num}/reactions", {"content": "rocket"})
        print(f"  ⭐ reaction on quality PR #{num}")


def cmd_community_stats():
    since = datetime.now(timezone.utc) - timedelta(days=7)
    iso = since.isoformat()
    issues = paged(f"/repos/{REPO}/issues?state=all&since={iso}")
    prs = paged(f"/repos/{REPO}/pulls?state=all")
    new_issues = sum(1 for i in issues if not i.get("pull_request")
                     and i["created_at"] > iso)
    closed_issues = sum(1 for i in issues if not i.get("pull_request")
                        and i["state"] == "closed" and (i.get("closed_at") or "") > iso)
    new_prs = sum(1 for p in prs if p["created_at"] > iso)
    merged_prs = sum(1 for p in prs if p.get("merged_at") and p["merged_at"] > iso)
    contributors = {x["user"]["login"] for x in (*issues, *prs) if x.get("user")}
    print("📊 Weekly Stats:")
    print(f"   Issues: {new_issues} new, {closed_issues} closed")
    print(f"   PRs: {new_prs} new, {merged_prs} merged")
    print(f"   Contributors: {len(contributors)} unique")
    with open("community_stats.json", "w", encoding="utf-8") as fh:
        json.dump({"newIssues": new_issues, "closedIssues": closed_issues,
                   "newPRs": new_prs, "mergedPRs": merged_prs,
                   "contributors": len(contributors), "week": iso}, fh)


def cmd_community_newcomer():
    issue = _event().get("issue", {})
    if not issue:
        return
    author = issue["user"]["login"]
    authored = api("GET", f"/repos/{REPO}/issues?creator={author}&state=all") or []
    if len(authored) != 1:
        return
    msg = (
        f"🎉 **Welcome to DAIOF, @{author}!**\n\n"
        "Thank you for opening your first issue! You're now part of our digital "
        "organism community. 🧬\n\n"
        "**What happens next**:\n1. Review within 24-48 hours\n"
        "2. Bugs get investigated and fixed\n3. Feature requests get discussed\n"
        "4. Questions get answered\n\n"
        f"**Want to contribute code?** 💻 See the "
        f"[Contributing Guide](https://github.com/{REPO}/blob/main/CONTRIBUTING.md)\n\n"
        "*Automated welcome by Digital Organism*"
    )
    comment(issue["number"], msg)
    add_labels(issue["number"], ["first-time-contributor"])


# --------------------------------------------------------------------------- #
# Greet first-time contributors (was actions/first-interaction)
# --------------------------------------------------------------------------- #
def cmd_greet():
    ev = _event()
    if "issue" in ev:
        item, kind = ev["issue"], "issue"
    elif "pull_request" in ev:
        item, kind = ev["pull_request"], "pr"
    else:
        return
    author = item["user"]["login"]
    authored = api("GET", f"/repos/{REPO}/issues?creator={author}&state=all") or []
    # first-interaction: only greet if this is their first issue/PR
    if len(authored) > 1:
        return
    if kind == "issue":
        msg = ("👋 **Welcome to DAIOF Framework!**\n\nThank you for opening your "
               "first issue! A maintainer will review it shortly. 🎉")
    else:
        msg = ("🎊 **Congratulations on your first Pull Request!**\n\nThank you for "
               "contributing to DAIOF Framework! Automated checks will run and a "
               "maintainer will review your changes. 🚀")
    comment(item["number"], msg)


# --------------------------------------------------------------------------- #
# PR labeler: file-path based + size based (was actions/labeler + pr-size-labeler)
# --------------------------------------------------------------------------- #
def _load_labeler_config() -> dict:
    path = ".github/labeler.yml"
    if not os.path.exists(path):
        return {}
    try:
        import yaml  # may be available; optional
        with open(path, encoding="utf-8") as fh:
            return yaml.safe_load(fh) or {}
    except Exception:
        return {}


def _globs_for(rules) -> list[str]:
    globs: list[str] = []
    if isinstance(rules, list):
        for entry in rules:
            if isinstance(entry, str):
                globs.append(entry)
            elif isinstance(entry, dict):
                cf = entry.get("changed-files", entry)
                if isinstance(cf, list):
                    for sub in cf:
                        g = sub.get("any-glob-to-any-file") if isinstance(sub, dict) else sub
                        if isinstance(g, str):
                            globs.append(g)
                        elif isinstance(g, list):
                            globs.extend(g)
    return globs


def cmd_label():
    import fnmatch
    pr = _event().get("pull_request", {})
    if not pr:
        return
    num = pr["number"]
    files = paged(f"/repos/{REPO}/pulls/{num}/files") or []
    names = [f["filename"] for f in files]
    labels: list[str] = []
    for label, rules in _load_labeler_config().items():
        for glob in _globs_for(rules):
            if any(fnmatch.fnmatch(n, glob) for n in names):
                labels.append(str(label))
                break
    total = sum(f.get("additions", 0) + f.get("deletions", 0) for f in files)
    for limit, lbl in [(10, "size/xs"), (50, "size/s"), (200, "size/m"),
                       (500, "size/l")]:
        if total <= limit:
            labels.append(lbl)
            break
    else:
        labels.append("size/xl")
    add_labels(num, labels)


# --------------------------------------------------------------------------- #
# Stale bot (was actions/stale)
# --------------------------------------------------------------------------- #
def cmd_stale():
    days_stale = int(os.getenv("DAYS_BEFORE_STALE", "60"))
    days_close = int(os.getenv("DAYS_BEFORE_CLOSE", "7"))
    exempt = {x.strip() for x in os.getenv(
        "EXEMPT_LABELS", "pinned,security,help-wanted,good-first-issue").split(",") if x.strip()}
    ops = int(os.getenv("OPERATIONS_PER_RUN", "30"))
    now = datetime.now(timezone.utc)
    done = 0
    for issue in paged(f"/repos/{REPO}/issues?state=open"):
        if done >= ops:
            break
        num = issue["number"]
        names = {l["name"] for l in issue.get("labels", [])}
        if names & exempt:
            continue
        updated = datetime.fromisoformat(issue["updated_at"].replace("Z", "+00:00"))
        age = (now - updated).days
        if "stale" in names:
            if age >= days_close:
                comment(num, "This was automatically closed due to inactivity. "
                             "Feel free to reopen.\n\n*Automated by Digital Organism*")
                api("PATCH", f"/repos/{REPO}/issues/{num}", {"state": "closed"})
                done += 1
        elif age >= days_stale:
            comment(num, "👋 This has been automatically marked as **stale** due "
                         "to inactivity. Comment to keep it open.\n\n"
                         "*Automated by Digital Organism*")
            add_labels(num, ["stale"])
            done += 1
    print(f"stale: processed {done} item(s)")


COMMANDS = {
    "pr-review": cmd_pr_review,
    "pr-merge": cmd_pr_merge,
    "issue-label": cmd_issue_label,
    "issue-respond": cmd_issue_respond,
    "community-recognize": cmd_community_recognize,
    "community-stats": cmd_community_stats,
    "community-newcomer": cmd_community_newcomer,
    "greet": cmd_greet,
    "label": cmd_label,
    "stale": cmd_stale,
}


def main() -> int:
    if len(sys.argv) < 2 or sys.argv[1] not in COMMANDS:
        print(f"usage: gh_bot.py [{' | '.join(COMMANDS)}]")
        return 2
    if not TOKEN or not REPO:
        print("! GITHUB_TOKEN / GITHUB_REPOSITORY not set; skipping.")
        return 0
    COMMANDS[sys.argv[1]]()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
