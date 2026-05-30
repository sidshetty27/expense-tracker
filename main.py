"""Expense Tracker — a small command-line app backed by SQLite.

Data is stored in `expenses.db` (created automatically) next to this script.
Each expense has: id, date, category, amount, and an optional note.

The module is split into:
  * a data-access layer (pure DB functions, no console I/O) — easy to test
  * input helpers (validation)
  * command functions (wire input/output to the data layer)
  * the menu loop
"""

import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime

# Anchor paths to this script so the app works from any working directory.
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "expenses.db")
LEGACY_TXT = os.path.join(BASE_DIR, "expenses.txt")


# --- Data-access layer (no console I/O) ------------------------------------

@contextmanager
def get_connection():
    """Yield a connection (rows keyed by column name), committing then closing.

    Closing matters on Windows: an open handle keeps the DB file locked.
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db():
    """Create the schema if needed and import any legacy text data once."""
    with get_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS expenses (
                id       INTEGER PRIMARY KEY AUTOINCREMENT,
                date     TEXT    NOT NULL,
                category TEXT    NOT NULL,
                amount   REAL    NOT NULL,
                note     TEXT
            )
            """
        )
    migrate_legacy_txt()


def migrate_legacy_txt():
    """Import old `expenses.txt` rows (category,amount) into the DB once.

    Runs only when the table is empty and the legacy file exists, then renames
    the file so it is not imported again. Returns the number of rows imported.
    """
    if not os.path.exists(LEGACY_TXT):
        return 0

    with get_connection() as conn:
        count = conn.execute("SELECT COUNT(*) FROM expenses").fetchone()[0]
        if count > 0:
            return 0

        today = datetime.now().strftime("%Y-%m-%d")
        imported = 0
        with open(LEGACY_TXT, "r") as file:
            for line in file:
                line = line.strip()
                if not line:
                    continue
                parts = line.split(",")
                if len(parts) < 2:
                    continue
                category = parts[0].strip()
                if not category:
                    continue
                try:
                    amount = float(parts[1].strip())
                except ValueError:
                    continue
                conn.execute(
                    "INSERT INTO expenses (date, category, amount, note) VALUES (?, ?, ?, ?)",
                    (today, category, amount, "imported from expenses.txt"),
                )
                imported += 1

    if imported:
        os.rename(LEGACY_TXT, LEGACY_TXT + ".imported")
    return imported


def insert_expense(date, category, amount, note=None):
    """Insert one expense and return its new id."""
    with get_connection() as conn:
        cursor = conn.execute(
            "INSERT INTO expenses (date, category, amount, note) VALUES (?, ?, ?, ?)",
            (date, category, amount, note or None),
        )
        return cursor.lastrowid


def list_expenses():
    with get_connection() as conn:
        return conn.execute(
            "SELECT id, date, category, amount, note FROM expenses ORDER BY date, id"
        ).fetchall()


def get_expense(expense_id):
    with get_connection() as conn:
        return conn.execute(
            "SELECT id, date, category, amount, note FROM expenses WHERE id = ?",
            (expense_id,),
        ).fetchone()


def update_expense(expense_id, date, category, amount, note):
    """Update an expense. Returns True if a row was changed."""
    with get_connection() as conn:
        cursor = conn.execute(
            "UPDATE expenses SET date = ?, category = ?, amount = ?, note = ? WHERE id = ?",
            (date, category, amount, note, expense_id),
        )
        return cursor.rowcount > 0


def delete_expense_by_id(expense_id):
    """Delete an expense. Returns True if a row was removed."""
    with get_connection() as conn:
        cursor = conn.execute("DELETE FROM expenses WHERE id = ?", (expense_id,))
        return cursor.rowcount > 0


def total():
    with get_connection() as conn:
        return conn.execute("SELECT COALESCE(SUM(amount), 0) FROM expenses").fetchone()[0]


def totals_by_category():
    with get_connection() as conn:
        return conn.execute(
            "SELECT category, SUM(amount) AS total FROM expenses "
            "GROUP BY category ORDER BY total DESC"
        ).fetchall()


def totals_by_month():
    with get_connection() as conn:
        return conn.execute(
            "SELECT substr(date, 1, 7) AS month, SUM(amount) AS total FROM expenses "
            "GROUP BY month ORDER BY month"
        ).fetchall()


# --- Input helpers (with validation) --------------------------------------

def prompt_nonempty(label):
    while True:
        value = input(label).strip()
        if value:
            return value
        print("  Please enter a value.")


def prompt_amount(label="Enter amount: "):
    while True:
        raw = input(label).strip()
        try:
            amount = float(raw)
        except ValueError:
            print("  Amount must be a number (e.g. 12.50).")
            continue
        if amount <= 0:
            print("  Amount must be greater than zero.")
            continue
        return amount


def prompt_date(label="Enter date (YYYY-MM-DD, blank = today): "):
    while True:
        raw = input(label).strip()
        if not raw:
            return datetime.now().strftime("%Y-%m-%d")
        if parse_date(raw):
            return parse_date(raw)
        print("  Use the format YYYY-MM-DD (e.g. 2026-05-30).")


def parse_date(raw):
    """Return a normalized YYYY-MM-DD string, or None if invalid."""
    try:
        return datetime.strptime(raw, "%Y-%m-%d").strftime("%Y-%m-%d")
    except ValueError:
        return None


def prompt_int(label):
    while True:
        raw = input(label).strip()
        try:
            return int(raw)
        except ValueError:
            print("  Please enter a whole number.")


# --- Command functions (console I/O) --------------------------------------

def add_expense():
    category = prompt_nonempty("Enter category: ")
    amount = prompt_amount()
    date = prompt_date()
    note = input("Enter note (optional): ").strip()
    insert_expense(date, category, amount, note)
    print("Expense added!")


def view_expenses():
    rows = list_expenses()
    if not rows:
        print("No expenses found.")
        return

    print(f"\n{'ID':<4}{'Date':<12}{'Category':<16}{'Amount':>10}  Note")
    print("-" * 60)
    for r in rows:
        print(
            f"{r['id']:<4}{r['date']:<12}{r['category']:<16}"
            f"{('$' + format(r['amount'], '.2f')):>10}  {r['note'] or ''}"
        )


def edit_expense():
    view_expenses()
    if not list_expenses():
        return
    expense_id = prompt_int("\nEnter the ID to edit: ")

    row = get_expense(expense_id)
    if row is None:
        print(f"No expense with ID {expense_id}.")
        return

    print("Leave a field blank to keep its current value.")
    category = input(f"Category [{row['category']}]: ").strip() or row["category"]

    amount_raw = input(f"Amount [{row['amount']}]: ").strip()
    amount = row["amount"]
    if amount_raw:
        try:
            amount = float(amount_raw)
        except ValueError:
            print("  Invalid amount; keeping the old value.")

    date_raw = input(f"Date [{row['date']}]: ").strip()
    date = parse_date(date_raw) or row["date"] if date_raw else row["date"]
    if date_raw and parse_date(date_raw) is None:
        print("  Invalid date; keeping the old value.")

    note_raw = input(f"Note [{row['note'] or ''}]: ").strip()
    note = note_raw if note_raw else row["note"]

    update_expense(expense_id, date, category, amount, note)
    print("Expense updated!")


def delete_expense():
    view_expenses()
    if not list_expenses():
        return
    expense_id = prompt_int("\nEnter the ID to delete: ")
    if delete_expense_by_id(expense_id):
        print("Expense deleted!")
    else:
        print(f"No expense with ID {expense_id}.")


def show_total():
    print(f"\nTotal Expenses: ${total():.2f}")


def report_by_category():
    rows = totals_by_category()
    if not rows:
        print("No expenses found.")
        return
    print("\nSpending by category:")
    for r in rows:
        print(f"  {r['category']:<20}${r['total']:.2f}")


def report_by_month():
    rows = totals_by_month()
    if not rows:
        print("No expenses found.")
        return
    print("\nSpending by month:")
    for r in rows:
        print(f"  {r['month']}   ${r['total']:.2f}")


# --- Menu loop -------------------------------------------------------------

MENU = """
Expense Tracker
1. Add Expense
2. View Expenses
3. Edit Expense
4. Delete Expense
5. Show Total
6. Report: by Category
7. Report: by Month
8. Exit"""

ACTIONS = {
    "1": add_expense,
    "2": view_expenses,
    "3": edit_expense,
    "4": delete_expense,
    "5": show_total,
    "6": report_by_category,
    "7": report_by_month,
}


def main():
    init_db()
    while True:
        print(MENU)
        choice = input("Choose an option: ").strip()
        if choice == "8":
            print("Goodbye!")
            break
        action = ACTIONS.get(choice)
        if action:
            action()
        else:
            print("Invalid option.")


if __name__ == "__main__":
    main()
