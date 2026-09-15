# Typed JSONB Projection for Hot Expansion Paths

## Summary

This submission reduces repeated JSONB object traversal in the two most
expensive challenge recipes. `table1` and `table2` now project the required
keys once per source row with PostgreSQL's native `jsonb_to_record` function
and reuse the resulting typed fields throughout each statement.

The remaining four recipes retain their original direct JSONB extraction.
Local profiling showed that converting those smaller projections added more
record-construction overhead than it removed.

## Bottleneck

The baseline recipes repeatedly evaluate expressions such as:

```sql
source_row.raw -> 'values' ->> 'integer_column_12'
```

`table1` reads 20 payload fields and reuses several of them in expressions and
join predicates. `table2` addresses 56 position-related fields through a
14-row lateral `VALUES` relation. These were the two slowest statements in a
100,000-row local run:

| Destination | Baseline wall time |
|---|---:|
| `table1` | 6.687 s |
| `table2` | 8.159 s |

## Implementation

- `03_table1.sql` expands the required JSON object into one lateral record.
- `06_table2.sql` expands its 56 required fields into one lateral record before
  constructing the 14 candidate positions.
- The SQL safety validator explicitly permits the native, stable
  `pg_catalog.jsonb_to_record` function while continuing to reject non-native,
  volatile, security-definer, and procedure calls.
- The recipe test asserts that `jsonb_to_record` is discovered by the SQL
  parser, preserving the existing dependency and safety checks.

No generator code, seed, input rows, destination constraints, validation,
versioning, or dump behavior was removed or bypassed.

## Local benchmark

Environment:

- Official deterministic generator, unchanged
- 100,000 `raw_data` rows, `group001`
- PostgreSQL 18.6 in Ubuntu WSL 2
- Six official recipes in the required order
- Warm database cache; destination tables truncated with identities restarted
  before every run

Observed full-batch SQL wall times:

| Recipes | Run 1 | Run 2 | Median |
|---|---:|---:|---:|
| Original commit `43ab8d4` | 17.596 s | 19.189 s | 18.393 s |
| This submission | 16.613 s | 16.544 s | 16.579 s |

The observed median improvement was **9.9%**. Individual paired observations
ranged from 5.6% to 13.8%, so the official standardized benchmark should be
treated as authoritative.

Both variants produced exactly the same destination counts:

| Table | Rows |
|---|---:|
| `table1` | 100,000 |
| `table2` | 232,386 |
| `table3` | 4 |
| `table4` | 26 |
| `table5` | 100,000 |
| `table6` | 100,000 |

Run the structural tests with:

```bash
python -m unittest discover -s tests -v
```

The standard-library-only diagnostic runner is available at
`tools/sql_benchmark.py`. It expects the official `kaggle_challenge` database
on the local PostgreSQL Unix socket and empty destination tables. Pass
`--revision 43ab8d4` to benchmark the original recipes or `--per-statement` to
identify per-destination costs.

## Integrity and resource use

The change is entirely set-based and introduces no persistent staging table,
temporary copy, cache, or extra index. Peak storage remains effectively the
same as the baseline. The source scope, destination locks, repeatable-read
transaction, dependency manifest, affected-row telemetry, and version
registration path are unchanged.

## Failure recovery and limitations

The existing Expand operation is atomic: failure before commit rolls back all
six destinations, and version finalization begins only after the data commit.
This submission does not add mid-operation persistent checkpoints, so an
interrupted expansion must still restart from the beginning. That is the main
known limitation and means this entry focuses on the performance and resource
efficiency portions of the rubric rather than claiming resumable execution.

Results were measured at 100,000 rows on local WSL hardware. They should not be
extrapolated linearly to the organizers' largest workloads.

## Exact submission revision

The public Kaggle Writeup identifies the immutable Git commit used for judging.
That commit—not later changes on the repository's default branch—is the
authoritative submission snapshot.
