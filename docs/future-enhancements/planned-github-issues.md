
● Created 6 GitHub issues for the PageIndex-inspired improvements:

  | #                                                     | Issue                                 | Labels                                     | Priority  |
  |-------------------------------------------------------|---------------------------------------|--------------------------------------------|-----------|
  | https://github.com/hiivmind/hiivmind-corpus/issues/9  | Reasoning Transparency in Navigation  | low-effort, high-value                     | 1 (first) |
  | https://github.com/hiivmind/hiivmind-corpus/issues/10 | Node Summaries for Index Entries      | low-effort                                 | 2         |
  | https://github.com/hiivmind/hiivmind-corpus/issues/11 | Hierarchical Tree Index Format        | medium-effort, high-value                  | 3         |
  | https://github.com/hiivmind/hiivmind-corpus/issues/12 | OpenAPI/GraphQL Schema-Aware Indexing | medium-effort, high-value, new-source-type | 4         |
  | https://github.com/hiivmind/hiivmind-corpus/issues/13 | PDF Source Type                       | medium-effort, high-value, new-source-type | 5         |
  | https://github.com/hiivmind/hiivmind-corpus/issues/14 | PageIndex Integration                 | medium-effort, separate-repo               | 6 (last)  |

  Dependency chain:
  #9 Reasoning ──┐
                 │
  #10 Summaries ─┼──► #11 Tree Format ──► #12 API Indexing
                 │           │
                 │           └──► #13 PDF Source ──► #14 PageIndex (separate repo)

  Recommended implementation order: Start with #9 (standalone, immediate UX win), then #10, then #11 as the foundation for the remaining features.
