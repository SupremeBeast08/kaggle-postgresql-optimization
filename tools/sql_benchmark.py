#!/usr/bin/env python3
"""Minimal local benchmark for the six official expansion recipes.

Run this as a PostgreSQL role that owns the generated challenge database. The
script intentionally depends only on Python's standard library and ``psql``.
"""

from __future__ import annotations

import argparse
import subprocess
import time
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
RECIPE_DIR = PROJECT_ROOT / "SQL files"
DESTINATIONS = (
    ("01_table3.sql", "table3"),
    ("02_table4.sql", "table4"),
    ("03_table1.sql", "table1"),
    ("04_table5.sql", "table5"),
    ("05_table6.sql", "table6"),
    ("06_table2.sql", "table2"),
)
SOURCE_SQL = """(
    SELECT *
    FROM public.raw_data
    WHERE raw_schema IN ('group001')
)"""


def run_psql(sql: str) -> str:
    completed = subprocess.run(
        [
            "psql",
            "-h",
            "/var/run/postgresql",
            "-U",
            "postgres",
            "-d",
            "kaggle_challenge",
            "-X",
            "-qAt",
            "-v",
            "ON_ERROR_STOP=1",
            "-f",
            "-",
        ],
        input=sql,
        text=True,
        capture_output=True,
        check=False,
    )
    if completed.returncode:
        raise RuntimeError(completed.stderr.strip() or "psql failed")
    return completed.stdout


def read_recipe(file_name: str, revision: str | None) -> str:
    if revision is None:
        return (RECIPE_DIR / file_name).read_text(encoding="utf-8")
    completed = subprocess.run(
        [
            "git",
            "-c",
            f"safe.directory={PROJECT_ROOT}",
            "show",
            f"{revision}:SQL files/{file_name}",
        ],
        cwd=PROJECT_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    if completed.returncode:
        raise RuntimeError(completed.stderr.strip() or "git show failed")
    return completed.stdout


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--revision",
        help="Read recipes from this Git revision instead of the working tree.",
    )
    parser.add_argument(
        "--per-statement",
        action="store_true",
        help="Commit and report each destination separately for diagnosis.",
    )
    args = parser.parse_args()
    statements = []
    for file_name, _table_name in DESTINATIONS:
        recipe = read_recipe(file_name, args.revision)
        statements.append(recipe.replace("{{source}}", SOURCE_SQL))

    started = time.perf_counter()
    if args.per_statement:
        for statement, (_file_name, table_name) in zip(statements, DESTINATIONS):
            statement_started = time.perf_counter()
            run_psql(
                "BEGIN ISOLATION LEVEL REPEATABLE READ;\n"
                + statement
                + "\nCOMMIT;\n"
            )
            print(
                f"{table_name} wall time: "
                f"{time.perf_counter() - statement_started:.3f} s"
            )
    else:
        run_psql(
            "BEGIN ISOLATION LEVEL REPEATABLE READ;\n"
            + "\n".join(statements)
            + "\nCOMMIT;\n"
        )
    elapsed = time.perf_counter() - started
    counts = run_psql(
        "SELECT table_name || '=' || row_count FROM (\n"
        + " UNION ALL ".join(
            f"SELECT '{table_name}' AS table_name, count(*) AS row_count FROM public.{table_name}"
            for _file_name, table_name in DESTINATIONS
        )
        + "\n) AS counts ORDER BY table_name;\n"
    )
    print(counts, end="")
    print(f"SQL BATCH WALL TIME: {elapsed:.3f} s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
