# Question 4 helper: verify school.sql with plain Python, no SQLite install needed.
# script runs the same schema, sample data, and answer query through Python's
# built-in sqlite3 module against an in-memory database and prints the result.
# DB Browser for SQLite.

import os
import sqlite3

HERE = os.path.dirname(os.path.abspath(__file__))
SQL_PATH = os.path.join(HERE, "school.sql")

with open(SQL_PATH, encoding="utf-8") as f:
    lines = f.readlines()

# Drop sqlite3 CLI dot-commands (e.g. .headers, .mode) - they are not SQL - and
# strip "--" line comments so a stray semicolon inside a comment does not break
# the statement split below.
code_lines = []
for line in lines:
    if line.lstrip().startswith("."):
        continue
    code_lines.append(line.split("--", 1)[0])
sql = "".join(code_lines)

# Split into statements; the final one is the SELECT, run separately so we
# can fetch and print its rows.
statements = [stmt.strip() for stmt in sql.split(";") if stmt.strip()]
setup, final_query = statements[:-1], statements[-1]

conn = sqlite3.connect(":memory:")
cur = conn.cursor()

# Everything except the final SELECT: create tables and insert sample data.
cur.executescript(";\n".join(setup) + ";")

# The answer query.
cur.execute(final_query)
rows = cur.fetchall()

headers = [col[0] for col in cur.description]
print(" | ".join(headers))
for row in rows:
    print(row)

conn.close()
