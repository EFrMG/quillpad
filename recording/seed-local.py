#!/usr/bin/env python3
"""Seed the local triage records the README shorts need, through the install's own scripts.

    python3 recording/seed-local.py [--install triage-o-mator]

Run it once on a freshly synced install whose ledger has no decisions. It reads GitHub for evidence, batches and tracking, and posts one comment on issue #26 so that the tracked item has new activity. Everything else it writes is local to the install.
"""

import argparse
import datetime
import json
import subprocess
import sys
import time
from pathlib import Path

HUMAN = "Maya Ortiz"
AGENT = "agent:Maya Ortiz"

# kind, number, labels, action, confidence, reason, notes, by
DECISIONS = [
    ("issue", 2, ["bug"], "none", "high", "Confirmed: a tag with a space is saved but read back as two tags. Two competing fixes are open, so no comment is needed until one is chosen.", "", HUMAN),
    ("pr", 3, ["bug"], "none", "medium", "Fixes #2 by quoting tags, but changes the header format without a migration.", "Read the full diff. `parse_filter` now uses `csv`, and the header separator changes from spaces to commas. Existing multi-tag notes would read back as a single tag. Competes with #4.", AGENT),
    ("pr", 4, ["bug"], "none", "medium", "Fixes #2 by saving tags as slugs; keeps the header format.", "Read the full diff. Ten changed lines, no format change, and existing notes keep working. The visible tag text changes (`To do` becomes `to-do`). Competes with #3.", AGENT),
    ("pr", 8, ["enhancement", "ready"], "none", "high", "Small, tested and additive: `list --json` leaves the default output alone.", "Read the full diff and the new test. The JSON path reuses the existing tag filter. One reviewer already ran it against real notes. No open questions.", AGENT),
    ("pr", 9, ["bug", "ready"], "none", "high", "Fixes the first-run crash in #10 with a test.", "Read the full diff. `store.home()` creates the directory, and the new test covers a missing `QUILLPAD_HOME`. Confirmed in a clean container by a reviewer.", AGENT),
    ("issue", 10, ["bug"], "none", "high", "Reproducible first-run crash with a full traceback. PR #9 fixes it and is ready.", "", AGENT),
    ("pr", 11, ["enhancement"], "close", "medium", "Replaces the plain-file store that the README promises. Needs a maintainer decision on direction before more review.", "Read the full diff. `list` and `search` read only the database, so hand-edited Markdown is ignored. No migration and no benchmark against #18.", AGENT),
    ("pr", 12, ["documentation"], "close", "high", "The same README change is already on main.", "The branch's only change, the pipx install paragraph, matches main after commit a99ef9d.", AGENT),
    ("issue", 19, ["enhancement"], "none", "high", "Clear request with an obvious precedent in `git commit`. Worth doing; no comment needed.", "", HUMAN),
    ("issue", 21, ["enhancement", "good first issue"], "none", "medium", "Self-contained: a `tags` command plus a completion script.", "", AGENT),
    ("issue", 22, ["enhancement"], "none", "low", "Built-in sync would be the project's first network feature.", "The reporter's need is partly met by pointing `QUILLPAD_HOME` at a synced folder (see #16).", AGENT),
    ("pr", 25, ["enhancement", "ready"], "none", "high", "Two lines using argparse's built-in version action.", "Read the full diff. Version comes from `quillpad.__version__`. A reviewer checked that subcommands still parse.", AGENT),
]

BATCH_KEYS = [("issue", 15), ("issue", 16), ("issue", 17), ("pr", 18), ("issue", 20)]
BATCH_PROPOSALS = {
    ("issue", 15): (["bug"], "none", "high", "Clear and reproducible from the description: a prefix match wins over an exact slug match.", "`store.find` returns the first slug that starts with the argument. Sorting puts `plan` before `planning-retro`, so the report may depend on file names; still, exact matches are never preferred."),
    ("issue", 16): (["documentation", "good first issue"], "none", "high", "The variable exists in `store.home()` and the README does not mention it.", "One README paragraph would close this. It also answers part of #22."),
    ("issue", 17): (["question"], "comment", "medium", "Ask for the note size, timings and browser: the title says export fails, the body says it is slow.", "Nothing in `export.py` limits size. The HTML export wraps the whole body in one `<pre>`, which matches the browser struggling."),
    ("pr", 18): (["enhancement"], "none", "medium", "Plausible speed-up that keeps plain files; needs a look at index invalidation.", "The index is rebuilt when any note is newer than it, but a deleted note stays in the index until then. Related to #26 and an alternative to #11."),
    ("issue", 20): (["question"], "comment", "low", "Works as designed, but the error could say that the argument is a slug. Ask whether a clearer message would settle it.", ""),
}

ITEM_13_NOTES = "Read the full diff and all three comments. The age column is added to the default `list` output, which a reviewer says will break scripts; the author agreed to move it behind a flag but has not pushed that yet. A second reviewer notes that modification time is unreliable after a restore or sync."

GROUP_TITLE = "Tags with spaces: quote them or slugify them?"
GROUP_DESCRIPTION = "Issue #2 has two fixes that cannot both land. PR #3 keeps the tag text and changes the header format; PR #4 keeps the format and changes the tag text. Maintainers need to pick one direction before either is reviewed further."
GROUP_MEMBERS = [
    ("issue", 2, "The report. Confirmed by a second user."),
    ("pr", 3, "Quotes tags. Changes the header separator to commas with no migration, so existing multi-tag notes break."),
    ("pr", 4, "Slugifies tags. Ten lines, no format change; the tag shown is no longer the text typed."),
]

CLOSE_11 = """Thank you for the work on this, and for the search numbers.

We are going to close this pull request rather than review it further. quillpad's main promise is that notes are plain Markdown files that stay readable and editable without the tool. With this change, `list` and `search` read only the database, so a note edited by hand is no longer picked up.

If slow search is the problem to solve, #18 keeps plain files and adds an index. A comparison of the two on a large notes directory would be very welcome there.
"""

CLOSE_12 = """Thanks for this. The same change, recommending `pipx` and keeping `pip` as the alternative, is already on `main`, so there is nothing left for this pull request to add and we are closing it.
"""


def brief_texts(repo, date, batches):
    base = f"https://github.com/{repo}"

    def issue(number):
        return f"[issue #{number}]({base}/issues/{number})"

    def pr(number):
        return f"[PR #{number}]({base}/pull/{number})"

    issues_brief = f"""# Batch brief: older issues

Screened eight issues. Two need a maintainer.

## Needs a decision

- {issue(2)}: tags with spaces are saved but cannot be filtered. Two fixes compete, {pr(3)} and {pr(4)}; see the group brief.
- {issue(22)}: built-in sync would be the first feature that talks to a network. Flagged for Pending review.

## Ready to act on

- {issue(10)}: first-run crash, fixed by {pr(9)}.
- {issue(16)}: `QUILLPAD_HOME` works and is undocumented. A good first issue.

## Likely duplicates

- {issue(14)} repeats {issue(1)}: search ignores accented characters.

Nothing else in this batch needs a maintainer call.
"""

    prs_brief = f"""# Batch brief: open pull requests

Screened eight pull requests.

## Ready to merge

- {pr(8)} adds `list --json` with a test.
- {pr(9)} fixes the first-run crash in {issue(10)}.
- {pr(25)} adds `--version`.

## Recommend closing

- {pr(12)}: its README change is already on `main`.
- {pr(11)}: replaces plain-file storage with SQLite. See the item brief.

## Still in review

- {pr(13)}: the author agreed to move the age column behind a flag.
- {pr(18)}: search index; check what happens when a note is deleted.
"""

    item_brief = f"""# PR #11: Rewrite storage on top of SQLite

{pr(11)} moves notes into a SQLite database and searches them with FTS5.

## Recommendation

Close it, with thanks, unless the maintainers want to give up plain-file storage.

## The case for

Search on 8,000 notes goes from about a second to instant. {issue(26)} shows that slow search is a real complaint.

## The case against

The README says notes "stay readable without quillpad". After this change the Markdown file is a copy that the tool no longer reads:

```python
def load_all():
    from quillpad import db

    return db.load_all()
```

A note edited by hand is not picked up, and there is no migration for existing directories.

## What would change the call

A benchmark against {pr(18)}, which keeps plain files and adds an index. Nobody has run one.
"""

    group_brief = f"""# Group brief: tags with spaces

{issue(2)} has two competing fixes.

| | {pr(3)} | {pr(4)} |
| --- | --- | --- |
| Approach | Quote tags | Slugify tags |
| Header format | Changes to commas | Unchanged |
| Existing notes | Break without a migration | Keep working |
| Visible tag | As typed | `To do` becomes `to-do` |

## Recommendation

Take #4. It is smaller and does not touch the file format. Close #3 once #4 lands.
"""

    master = f"""# Maintainer brief

Two batches screened, 16 items. Four things need you.

## Decide

1. **Tags with spaces.** {issue(2)} has two fixes, {pr(3)} and {pr(4)}. They cannot both land. The group brief recommends #4.
2. **SQLite storage.** {pr(11)} trades plain files for fast search. The item brief recommends closing it and pointing to {pr(18)}.
3. **Sync.** {issue(22)} asks for built-in sync, the first network feature. Flagged for Pending review.

## Merge

{pr(8)}, {pr(9)} and {pr(25)} are small, tested and reviewed.

```sh
gh pr merge 8 --squash
gh pr merge 9 --squash
gh pr merge 25 --squash
```

## Close

{pr(12)} is already on `main`. {issue(14)} duplicates {issue(1)}.
"""

    return {
        f"{date}-batch-{batches[0]}-brief.md": issues_brief,
        f"{date}-batch-{batches[1]}-brief.md": prs_brief,
        f"{date}-pr-11-brief.md": item_brief,
        f"{date}-group-tags-brief.md": group_brief,
        f"{date}-master-brief.md": master,
    }


class Install:
    def __init__(self, root):
        self.root = root.absolute()
        self.repo = (self.root / "config/repo").read_text().strip()
        self.data = self.root / "data" / self.repo
        self.reports = self.root / "reports" / self.repo

    def run(self, script, *args, expected=True):
        command = [str(self.root / "bin" / script)]
        if expected:
            command += ["--expected-repo", self.repo]

        result = subprocess.run(command + [str(arg) for arg in args], cwd=self.root, capture_output=True, text=True)
        if result.returncode:
            sys.exit(f"{script} {' '.join(map(str, args))} failed:\n{result.stderr}{result.stdout}")

        return result.stdout

    def json(self, script, *args, expected=True):
        return json.loads(self.run(script, *args, expected=expected))

    def ledger(self):
        return [json.loads(line) for line in (self.data / "ledger.jsonl").read_text().splitlines()]

    def snapshot(self, kind, number):
        profile = "pr-comparison" if kind == "pr" else "discussion"

        return self.json("cache", "fetch", "--kind", kind, "--number", number, "--profile", profile, "--mode", "cache-preferred", "--request-budget", 50)["snapshot_id"]

    def new_batch(self, *args):
        before = set(self.data.glob("batches/*.items.jsonl"))
        time.sleep(1.1)  # batch IDs have one-second resolution
        self.run("batch", *args, expected=False)
        (created,) = set(self.data.glob("batches/*.items.jsonl")) - before

        return created.name.removesuffix(".items.jsonl")


def decisions(install):
    for kind, number, labels, action, confidence, reason, notes, by in DECISIONS:
        args = ["--number", number, "--kind", kind, "--action", action, "--confidence", confidence, "--reason", reason, "--by", by, "--batch-id", "seed"]
        for label in labels:
            args += ["--proposed-label", label]

        if notes:
            args += ["--agent-notes", notes]

        install.run("apply", *args)

    install.run("review-request", "mark", "--kind", "issue", "--number", 22, "--by", AGENT, "--reason", "First network feature: needs a maintainer decision on scope")


def scored_item(install):
    install.run("apply", "--number", 13, "--kind", "pr", "--agent-notes", ITEM_13_NOTES)
    install.run("item-score", "set", "--kind", "pr", "--number", 13, "--snapshot", install.snapshot("pr", 13), "--correctness", 1, "--safeguards", 1, "--reviewability", 1,
                "--reason", "Correctness 1: the age is right today, but modification time is unreliable after a restore or sync. Safeguards 1: no test, and the default output changes. Reviewability 1: ten focused lines.",
                "--suggestion", "Wait for the author to move the column behind a flag, then review again.", "--by", AGENT)


def group(install):
    output = install.run("group", "create", "--title", GROUP_TITLE, "--description", GROUP_DESCRIPTION, "--by", AGENT)
    (created,) = [entry for entry in install.json("group", "list") if entry["title"] == GROUP_TITLE]
    for kind, number, notes in GROUP_MEMBERS:
        install.run("group", "add", created["id"], "--kind", kind, "--number", number, "--notes", notes, "--by", AGENT)

    return created["id"], output


def briefs(install):
    date = datetime.date.today().isoformat()
    batches = [install.new_batch(8, "--include-triaged", "--unbriefed", "--order", "oldest", "--kind", kind) for kind in ("issue", "pr")]
    install.reports.mkdir(parents=True, exist_ok=True)
    texts = brief_texts(install.repo, date, batches)
    for name, text in texts.items():
        (install.reports / name).write_text(text)

    sources = []
    for batch in batches:
        name = f"{date}-batch-{batch}-brief.md"
        install.run("batch", "--mark-briefed", batch, "--brief", f"reports/{install.repo}/{name}", expected=False)
        install.run("batch", "--delete", batch, expected=False)
        sources.append(name)

    plan = install.json("briefs", "plan", *[arg for name in sources for arg in ("--brief", name)])
    brief_args = [arg for name in sources for arg in ("--brief", name)]
    install.run("briefs", "record-master", "--master", f"{date}-master-brief.md", *brief_args, "--plan-sha256", plan["plan_sha256"], "--by", AGENT)


def triage_batch(install):
    batch = install.new_batch(24)
    unwanted = [(row["kind"], row["number"]) for row in map(json.loads, (install.data / f"batches/{batch}.items.jsonl").read_text().splitlines()) if (row["kind"], row["number"]) not in BATCH_KEYS]
    if unwanted:
        install.run("batch", "--remove", batch, *[arg for kind, number in unwanted for arg in ("--key", f"{kind}:{number}")], expected=False)

    path = install.data / f"batches/{batch}.decisions.jsonl"
    rows = [json.loads(line) for line in path.read_text().splitlines()]
    for row in rows:
        labels, action, confidence, reason, notes = BATCH_PROPOSALS[(row["kind"], row["number"])]
        row.update(proposed_labels=labels, action=action, confidence=confidence, reason=reason, agent_notes=notes, proposed_by=AGENT)

    path.write_text("".join(json.dumps(row) + "\n" for row in rows))
    install.run("apply", path, "--only-untriaged", "--dry-run", expected=False)

    return batch


def closure(install, number, comment, extra):
    snapshot = install.snapshot("pr", number)
    checkpoint = install.json("item-context", "read", "--kind", "pr", "--number", number)["checkpoint"]
    seen = install.json("action-proposals", "inspect", "--kind", "pr", "--number", number)
    exports = install.data / "exports"
    exports.mkdir(parents=True, exist_ok=True)
    comment_file = exports / f"pr-{number}-close.md"
    comment_file.write_text(comment)
    install.run("action-proposals", "propose", "--kind", "pr", "--number", number, "--action", "close", "--observed-state", seen["state"], "--title", seen["title"], "--head-sha", seen["head_sha"],
                "--updated-at", seen["updated_at"], "--comment-file", comment_file, "--by", AGENT, "--context-checkpoint", checkpoint, "--evidence", f"pr:{number}:{snapshot}", *extra)

    return snapshot


def tracked(install):
    install.run("cache", "track-add", "--kind", "issue", "--number", 26)
    subprocess.run(["gh", "issue", "comment", "26", "-R", install.repo, "--body", "Same here with about 7,000 notes. PR #18 made it fast for me, though a note I deleted kept showing up until the next edit."], check=True, capture_output=True)
    time.sleep(3)
    install.run("cache", "track-check")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--install", type=Path, default=Path("triage-o-mator"))
    install = Install(parser.parse_args().install)

    if any(row.get("triaged_at") for row in install.ledger()):
        sys.exit("this ledger already has decisions; restore a clean snapshot or start from a fresh install")

    steps = [
        ("decisions and Pending review", lambda: decisions(install)),
        ("scored PR #13", lambda: scored_item(install)),
        ("draft group", lambda: group(install)),
        ("briefs", lambda: briefs(install)),
        ("agent batch", lambda: triage_batch(install)),
        ("closure proposal for PR #11", lambda: closure(install, 11, CLOSE_11, ["--decision-question", "Is quillpad willing to stop treating the Markdown files as the source of truth?", "--evidence-gap", "No benchmark compares this branch with PR #18 on the same notes directory."])),
        ("closure proposal for PR #12", lambda: closure(install, 12, CLOSE_12, [])),
        ("tracked issue #26 with a new comment", lambda: tracked(install)),
    ]
    for name, step in steps:
        print(f"seeding {name} ...", flush=True)
        step()

    print("done")


if __name__ == "__main__":
    main()
