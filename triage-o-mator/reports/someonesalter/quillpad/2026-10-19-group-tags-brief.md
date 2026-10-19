# Group brief: tags with spaces

[issue #2](https://github.com/someonesalter/quillpad/issues/2) has two competing fixes.

| | [PR #3](https://github.com/someonesalter/quillpad/pull/3) | [PR #4](https://github.com/someonesalter/quillpad/pull/4) |
| --- | --- | --- |
| Approach | Quote tags | Slugify tags |
| Header format | Changes to commas | Unchanged |
| Existing notes | Break without a migration | Keep working |
| Visible tag | As typed | `To do` becomes `to-do` |

## Recommendation

Take #4. It is smaller and does not touch the file format. Close #3 once #4 lands.
