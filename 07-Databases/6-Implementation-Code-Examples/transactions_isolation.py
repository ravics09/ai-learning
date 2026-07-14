"""
transactions_isolation.py
Hands-on demo of transactions, isolation levels, and safe retries in PostgreSQL.

WHY this file:
    Isolation is the concept most people can define but few can *use*. This shows
    three concrete things an interviewer loves:
      1. An atomic money transfer (all-or-nothing).
      2. Why SERIALIZABLE can raise a serialization error (40001) and how to
         retry it correctly.
      3. How to prevent "write skew" / lost updates with row locks
         (SELECT ... FOR UPDATE) as an alternative to SERIALIZABLE.

Prereqs:
    - pip install "psycopg[binary]"
    - export DATABASE_URL="postgresql://user:pass@localhost:5432/mydb"
"""

from __future__ import annotations

import os
import time

import psycopg
from psycopg import errors
from psycopg.rows import dict_row

DSN = os.environ.get("DATABASE_URL", "postgresql:///postgres")


def setup(conn: psycopg.Connection) -> None:
    """Create a tiny accounts table with a non-negative-balance invariant.

    WHY the CHECK constraint: it enforces the invariant at the DB level, so even
    a buggy transaction at a weak isolation level cannot persist a negative
    balance. Constraints are the cheapest, most reliable guardrail.
    """
    with conn.cursor() as cur:
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS accounts (
                id      INT PRIMARY KEY,
                balance NUMERIC(12,2) NOT NULL CHECK (balance >= 0)
            )
            """
        )
        cur.execute("TRUNCATE accounts")
        cur.execute("INSERT INTO accounts VALUES (1, 100), (2, 0)")
    conn.commit()


def transfer_atomic(conn: psycopg.Connection, src: int, dst: int, amount) -> None:
    """Move money in ONE transaction: both updates commit, or neither does.

    WHY explicit BEGIN/COMMIT semantics: if the second UPDATE violates the CHECK
    (or the process crashes between the two), Atomicity guarantees the first
    UPDATE is rolled back -- money is never created or destroyed.
    """
    with conn.transaction():  # BEGIN ... COMMIT (ROLLBACK on exception)
        with conn.cursor() as cur:
            cur.execute("UPDATE accounts SET balance = balance - %s WHERE id = %s",
                        (amount, src))
            cur.execute("UPDATE accounts SET balance = balance + %s WHERE id = %s",
                        (amount, dst))


def transfer_locked(conn: psycopg.Connection, src: int, dst: int, amount) -> bool:
    """Prevent lost updates / write skew with pessimistic row locks.

    WHY SELECT ... FOR UPDATE: it locks the source row so concurrent transfers
    serialize on it. We re-check the balance AFTER acquiring the lock, so two
    concurrent withdrawals can't both "see" enough money and overdraw.
    This is often simpler than SERIALIZABLE for a small, known set of rows.
    """
    with conn.transaction():
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute("SELECT balance FROM accounts WHERE id = %s FOR UPDATE",
                        (src,))
            row = cur.fetchone()
            if row is None or row["balance"] < amount:
                return False  # not enough funds; transaction rolls back cleanly
            cur.execute("UPDATE accounts SET balance = balance - %s WHERE id = %s",
                        (amount, src))
            cur.execute("UPDATE accounts SET balance = balance + %s WHERE id = %s",
                        (amount, dst))
    return True


def run_serializable_with_retry(dsn: str, work, max_retries: int = 5):
    """Run `work(conn)` at SERIALIZABLE, retrying on serialization failures.

    WHY retries: PostgreSQL SERIALIZABLE uses SSI, which does not block -- it
    *aborts* one transaction in a dangerous read/write cycle with SQLSTATE
    40001. The contract is: the application must simply retry the whole
    transaction. Without this loop, SERIALIZABLE code is incorrect under load.
    """
    for attempt in range(1, max_retries + 1):
        try:
            with psycopg.connect(dsn) as conn:
                conn.isolation_level = psycopg.IsolationLevel.SERIALIZABLE
                with conn.transaction():
                    work(conn)
            return  # success
        except errors.SerializationFailure:
            wait = 0.05 * (2 ** (attempt - 1))  # exponential backoff
            print(f"  serialization failure (40001), retry {attempt} after {wait:.2f}s")
            time.sleep(wait)
    raise RuntimeError("transaction failed after retries")


if __name__ == "__main__":
    with psycopg.connect(DSN) as conn:
        setup(conn)

        # 1) Atomic transfer succeeds.
        transfer_atomic(conn, src=1, dst=2, amount=30)

        # 2) Overdraw attempt: the CHECK constraint aborts the whole transaction,
        #    demonstrating Atomicity (the debit is rolled back too).
        try:
            transfer_atomic(conn, src=2, dst=1, amount=999)
        except errors.CheckViolation:
            conn.rollback()
            print("Overdraw correctly rejected; no partial update persisted.")

        # 3) Locked transfer re-checks funds under a row lock.
        ok = transfer_locked(conn, src=1, dst=2, amount=10)
        print("Locked transfer applied:", ok)

        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute("SELECT * FROM accounts ORDER BY id")
            print("Final balances:", cur.fetchall())
