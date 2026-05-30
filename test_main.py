"""Tests for the expense tracker data layer.

Run with:  py -m unittest        (or: python -m unittest)

Each test runs against a throwaway SQLite database in a temp directory, so
nothing touches the real `expenses.db`.
"""

import os
import tempfile
import unittest

import main


class ExpenseTrackerTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        # Redirect the module's paths at runtime to the temp dir.
        main.DB_PATH = os.path.join(self.tmp.name, "test.db")
        main.LEGACY_TXT = os.path.join(self.tmp.name, "expenses.txt")
        main.init_db()

    def tearDown(self):
        self.tmp.cleanup()

    # --- insert / list ---------------------------------------------------

    def test_insert_and_list(self):
        main.insert_expense("2026-01-01", "Food", 10.0, "lunch")
        rows = main.list_expenses()
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["category"], "Food")
        self.assertEqual(rows[0]["amount"], 10.0)
        self.assertEqual(rows[0]["note"], "lunch")

    def test_empty_note_stored_as_null(self):
        main.insert_expense("2026-01-01", "Food", 10.0, "")
        self.assertIsNone(main.list_expenses()[0]["note"])

    # --- totals / reports ------------------------------------------------

    def test_total(self):
        main.insert_expense("2026-01-01", "Food", 10.0)
        main.insert_expense("2026-01-02", "Gas", 5.5)
        self.assertEqual(main.total(), 15.5)

    def test_total_empty(self):
        self.assertEqual(main.total(), 0)

    def test_by_category_sums_and_orders(self):
        main.insert_expense("2026-01-01", "Food", 10.0)
        main.insert_expense("2026-01-02", "Food", 5.0)
        main.insert_expense("2026-01-03", "Gas", 20.0)
        rows = main.totals_by_category()
        totals = {r["category"]: r["total"] for r in rows}
        self.assertEqual(totals["Food"], 15.0)
        self.assertEqual(totals["Gas"], 20.0)
        self.assertEqual(rows[0]["category"], "Gas")  # ordered by total desc

    def test_by_month_groups_by_yyyy_mm(self):
        main.insert_expense("2026-01-15", "Food", 10.0)
        main.insert_expense("2026-02-10", "Gas", 20.0)
        main.insert_expense("2026-02-20", "Food", 5.0)
        totals = {r["month"]: r["total"] for r in main.totals_by_month()}
        self.assertEqual(totals["2026-01"], 10.0)
        self.assertEqual(totals["2026-02"], 25.0)

    # --- update / delete -------------------------------------------------

    def test_update(self):
        eid = main.insert_expense("2026-01-01", "Food", 10.0)
        self.assertTrue(main.update_expense(eid, "2026-01-01", "Dining", 12.0, "note"))
        row = main.get_expense(eid)
        self.assertEqual(row["category"], "Dining")
        self.assertEqual(row["amount"], 12.0)

    def test_update_missing_returns_false(self):
        self.assertFalse(main.update_expense(999, "2026-01-01", "X", 1.0, None))

    def test_delete(self):
        eid = main.insert_expense("2026-01-01", "Food", 10.0)
        self.assertTrue(main.delete_expense_by_id(eid))
        self.assertIsNone(main.get_expense(eid))

    def test_delete_missing_returns_false(self):
        self.assertFalse(main.delete_expense_by_id(999))

    # --- date parsing ----------------------------------------------------

    def test_parse_date_valid(self):
        self.assertEqual(main.parse_date("2026-05-30"), "2026-05-30")

    def test_parse_date_invalid(self):
        self.assertIsNone(main.parse_date("not-a-date"))
        self.assertIsNone(main.parse_date("2026-13-01"))

    # --- legacy migration ------------------------------------------------

    def test_migrate_imports_valid_rows_only(self):
        with open(main.LEGACY_TXT, "w") as f:
            f.write("Food,20\nGas,100\nbad line\n,5\nDrinks,not-a-number\n")
        imported = main.migrate_legacy_txt()
        self.assertEqual(imported, 2)
        self.assertEqual(main.total(), 120.0)
        # The legacy file is renamed so it is not re-imported.
        self.assertFalse(os.path.exists(main.LEGACY_TXT))
        self.assertTrue(os.path.exists(main.LEGACY_TXT + ".imported"))

    def test_migrate_skips_when_table_not_empty(self):
        main.insert_expense("2026-01-01", "X", 1.0)
        with open(main.LEGACY_TXT, "w") as f:
            f.write("Food,20\n")
        self.assertEqual(main.migrate_legacy_txt(), 0)
        self.assertEqual(main.total(), 1.0)


if __name__ == "__main__":
    unittest.main()
