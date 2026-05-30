# Expense Tracker

A simple command-line expense tracker written in Python, backed by SQLite.

## Features

- Add expenses with **category, amount, date, and an optional note**
- View all expenses in a table
- **Edit** and **delete** existing expenses by ID
- Reports: running **total**, spending **by category**, and spending **by month**
- Input validation (amounts must be positive numbers, dates must be `YYYY-MM-DD`)
- Automatically migrates data from the old `expenses.txt` format on first run

## Requirements

- Python 3 (uses only the standard library — `sqlite3` is built in)

## Usage

```bash
python main.py
```

Follow the on-screen menu. Data is stored in `expenses.db`, created automatically
next to `main.py`.

## Data

Each expense is a row in the `expenses` table:

| column   | type    | notes                          |
|----------|---------|--------------------------------|
| id       | INTEGER | primary key                    |
| date     | TEXT    | `YYYY-MM-DD`                   |
| category | TEXT    | e.g. Food, Gas                 |
| amount   | REAL    | positive number                |
| note     | TEXT    | optional                       |

If an `expenses.txt` file (old `category,amount` format) is present on first run,
its rows are imported and the file is renamed to `expenses.txt.imported`.

## Development

The data-access functions (insert, update, delete, totals, reports, migration)
are separated from console I/O, so they can be tested directly. Tests use the
standard-library `unittest` module and run against a throwaway database:

```bash
python -m unittest        # run all tests
python -m unittest -v     # verbose
```

## Project layout

| file           | purpose                                              |
|----------------|------------------------------------------------------|
| `main.py`      | app: data layer, input validation, commands, menu    |
| `test_main.py` | unit tests for the data layer                        |
| `expenses.db`  | SQLite database (generated, git-ignored)             |
