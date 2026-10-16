# Recording fixture

These helpers prepare the small Quillpad repository used in triage-o-mator's README shorts. `branches.py` and `github-items.py` created its branches and 26 GitHub items once; do not rerun them to refresh local recording state.

## Prepare local records

Use a separate checkout and solo install under `/tmp/` while rehearsing. Install the current triage-o-mator code, pin the install to `someonesalter/quillpad`, and sync its ledger and GitHub label catalog before seeding:

```sh
python3 /workspace/quillpad/recording/seed-local.py --install /tmp/YOUR-CHECKOUT/triage-o-mator
```

The seed requires all 26 fixture items, with only issues #23 and #24 closed, the fixture labels, and no existing local review work. It reads GitHub for evidence and revisions, enriches batches, and enrolls issue #26 with its existing comments as a baseline. It never publishes labels, comments, closures or reopenings. Suggestions and briefs are prepared recording examples, not an agent evaluation.

The result should have:

- 12 of 24 open items triaged, with one Pending review request on #22.
- A current 3/5 score on PR #13, with its notes, comments and diff.
- A draft group containing issue #2 and PRs #3/#4.
- Five briefs: one master, one item, one group and two batches. Each batch checkpoint contains exactly the eight items named in its brief.
- One batch containing #15, #16, #17, PR #18 and #20, with proposals still unapplied.
- Current closure proposals for PRs #11/#12; #11 retains its question and evidence gap.
- Issue #26 tracked, with no unread activity until a later comment is posted.

Inspect the result through the current scripts and TUI before saving a new baseline. If a read fails partway through seeding, inspect the partial state and restart from the clean pre-seed baseline; the seed refuses to overwrite existing work.

## Retakes

Run the snapshot helper from the checkout that owns the recording install; it always targets the `triage-o-mator/` beside `recording/`:

```sh
recording/snapshot.sh save v05-prepared
# Exit the app and preserve any later local work before restoring:
recording/snapshot.sh restore v05-prepared
```

Restoring replaces local config, data and reports. It does not restore GitHub labels or item states and cannot remove published comments. Keep the older `seeded.tgz` until a replacement has been verified. That archive contains historical observations; restoring it cannot make old scores or proposals current.

Record browsing first, local changes next and publication last. Post follow-up activity explicitly during the Notifications short, after the tracking baseline exists. A new comment remains on GitHub after a retake. Reopening a PR changes its revision, so sync and prepare a fresh closure proposal before another publishing take.
