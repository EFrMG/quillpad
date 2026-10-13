# CI fixture for checks and logs

The `CI fixture` GitHub Actions workflow supplies two independent synthetic checks for fixture PR #9:

| Check                           | Expected conclusion | Log markers                                                      |
| ------------------------------- | ------------------- | ---------------------------------------------------------------- |
| `Fixture / passes`              | `success` (exit 0)  | `QUILLPAD_CI_FIXTURE_PASS_BEGIN`, `QUILLPAD_CI_FIXTURE_PASS_END` |
| `Fixture / fails intentionally` | `failure` (exit 1)  | `QUILLPAD_CI_FIXTURE_FAIL_BEGIN`, `QUILLPAD_CI_FIXTURE_FAIL_END` |

The failing job also emits a GitHub error annotation containing `QUILLPAD_CI_FIXTURE_FAIL`. The workflow's overall result is deliberately a failure. These results test check summaries, job selection and log acquisition; they say nothing about the application's correctness. Both jobs use static shell output, a two-minute timeout and read-only repository permissions. They require no checkout, dependencies or secrets.

## Run and inspect

Publishing the workflow on `fix/missing-notes-dir`, PR #9's head branch, triggers it on that pushed commit. Pushes to other branches do not trigger this fixture. The run's head SHA should match the PR's new head SHA; the push trigger avoids associating the checks with a synthetic PR merge commit.

After the first published run, use **Actions → CI fixture → the run → Re-run all jobs** to produce another attempt for the same commit. Each attempt should retain the two expected conclusions and markers. There is no manual workflow-dispatch trigger.

For read-only inspection, these GitHub CLI commands show the checks and identify the matching run:

```sh
gh pr checks 9 --repo someonesalter/quillpad
gh run list --repo someonesalter/quillpad --workflow ci-fixture.yml --branch fix/missing-notes-dir
gh run view RUN_ID --repo someonesalter/quillpad
```

`gh pr checks` returns a nonzero status for the expected failing check. Replace `RUN_ID` with the run whose head SHA matches the selected PR revision. When testing an offline reader or Reposition index, acquire check metadata and the selected failed job's excerpts explicitly, then confirm the success/failure conclusions and the failure markers. Keep the run attempt and job identity with the captured logs so reruns and the two checks cannot be confused.

From a working triage-o-mator install, acquire the check metadata with a bounded read:

```sh
bin/pr-checks --expected-repo someonesalter/quillpad --number 9 --mode refresh --request-budget 20
```

Select the failed check row and preserve the returned snapshot, source repository and internal check ID. Use `bin/pr-check-log locate` with those exact pins and a request budget, then run its returned fetch command for that one failed job. `bin/pr-checks --expected-repo someonesalter/quillpad --number 9 --snapshot CHECKS_HASH --include-failure-logs` reads the captured excerpt offline, as does the TUI Checks tab. Log capture currently supports failed jobs; the passing fixture is represented by its check metadata.
