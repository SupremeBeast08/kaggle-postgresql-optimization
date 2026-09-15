import unittest
import json
from pathlib import Path
from unittest.mock import patch

from services.postgres_service import PostgresAdminService


PROJECT_ROOT = Path(__file__).resolve().parents[1]
RECIPE_DIR = PROJECT_ROOT / "SQL files"
RECIPE_DESTINATIONS = (
    ("01_table3.sql", "public.table3"),
    ("02_table4.sql", "public.table4"),
    ("03_table1.sql", "public.table1"),
    ("04_table5.sql", "public.table5"),
    ("05_table6.sql", "public.table6"),
    ("06_table2.sql", "public.table2"),
)


class ChallengeExpansionRecipeTests(unittest.TestCase):
    def test_all_recipes_are_accepted_in_dependency_order(self):
        missing_files = [
            file_name
            for file_name, _table_name in RECIPE_DESTINATIONS
            if not (RECIPE_DIR / file_name).is_file()
        ]
        if missing_files:
            self.fail("Missing required expansion recipes: " + ", ".join(missing_files))
        destinations = [
            {
                "table_name": table_name,
                "version_title": "Synthetic expansion",
                "sql": (RECIPE_DIR / file_name).read_text(encoding="utf-8"),
            }
            for file_name, table_name in RECIPE_DESTINATIONS
        ]

        prepared = PostgresAdminService._prepare_cross_table_expansion(
            "public.raw_data",
            ["group001"],
            destinations,
        )

        self.assertEqual(
            [item["table_name"] for item in prepared["destinations"]],
            [table_name for _file_name, table_name in RECIPE_DESTINATIONS],
        )
        self.assertEqual(
            {
                item["table_name"]: item["read_relations"]
                for item in prepared["destinations"]
            },
            {
                "public.table3": [],
                "public.table4": [],
                "public.table1": [("public", "table3")],
                "public.table5": [("public", "table1")],
                "public.table6": [("public", "table1"), ("public", "table4")],
                "public.table2": [("public", "table1")],
            },
        )
        self.assertEqual(
            {
                function_name
                for item in prepared["destinations"]
                for _schema_name, function_name in item["function_references"]
            },
            {"ascii", "btrim", "jsonb_to_record", "left", "right", "round", "upper"},
        )

    def test_stable_jsonb_projection_is_the_only_stable_function_allowed(self):
        service = PostgresAdminService()
        destination = {
            "function_references": [(None, "jsonb_to_record")],
        }
        response = json.dumps(
            [
                {
                    "requested_schema": None,
                    "function_name": "jsonb_to_record",
                    "candidates": [
                        {
                            "schema_name": "pg_catalog",
                            "volatility": "s",
                            "security_definer": False,
                            "function_kind": "f",
                        }
                    ],
                }
            ]
        )

        with patch.object(service, "run_remote_command", return_value=response):
            service._validate_cross_table_expansion_functions(
                "challenge",
                [destination],
            )

        response = response.replace("jsonb_to_record", "current_setting")
        destination["function_references"] = [(None, "current_setting")]
        with patch.object(service, "run_remote_command", return_value=response):
            with self.assertRaisesRegex(RuntimeError, "approved native"):
                service._validate_cross_table_expansion_functions(
                    "challenge",
                    [destination],
                )


if __name__ == "__main__":
    unittest.main()
