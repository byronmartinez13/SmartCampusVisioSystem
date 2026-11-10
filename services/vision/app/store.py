import json
import sqlite3
import shutil
from contextlib import contextmanager
from . import settings


@contextmanager
def connection():
    conn = sqlite3.connect(settings.DATA_DIR / "jobs.sqlite3", timeout=30)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def initialize():
    settings.DATA_DIR.mkdir(parents=True, exist_ok=True)
    with connection() as conn:
        conn.execute("""CREATE TABLE IF NOT EXISTS jobs (
          id TEXT PRIMARY KEY, status TEXT NOT NULL, progress INTEGER NOT NULL DEFAULT 0,
          confidence REAL NOT NULL, error TEXT NOT NULL DEFAULT '',
          result TEXT, cancelled INTEGER NOT NULL DEFAULT 0,
          created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )""")
        # A single worker owns this service instance; restart interrupted analyses from input.
        conn.execute("UPDATE jobs SET status='queued',progress=0 WHERE status='processing' AND cancelled=0")
        conn.execute("UPDATE jobs SET status='cancelled' WHERE cancelled=1 AND status IN ('queued','processing')")


def get(job_id):
    with connection() as conn:
        row = conn.execute("SELECT * FROM jobs WHERE id=?", (job_id,)).fetchone()
    if row is None:
        return None
    value = dict(row)
    value["result"] = json.loads(value["result"]) if value["result"] else None
    return value


def delete(job_id):
    """Delete only terminal jobs; keep the row on file errors so deletion can retry."""
    from uuid import UUID
    job_id = str(UUID(str(job_id)))
    with connection() as conn:
        conn.execute('BEGIN IMMEDIATE')
        row = conn.execute('SELECT status FROM jobs WHERE id=?', (job_id,)).fetchone()
        if row and row['status'] not in ('completed', 'failed', 'cancelled'):
            raise ValueError('Espera a que el análisis termine de procesarse o cancelarse.')
        base = settings.DATA_DIR.resolve()
        directory = base / job_id
        if directory.is_symlink() or directory.resolve() != directory:
            raise ValueError('La carpeta del análisis no es válida para eliminar.')
        if directory.exists():
            shutil.rmtree(directory)
        conn.execute('DELETE FROM jobs WHERE id=?', (job_id,))


def insert(job_id, confidence):
    with connection() as conn:
        conn.execute("INSERT INTO jobs(id,status,confidence) VALUES(?,'queued',?)", (job_id, confidence))


def update(job_id, **fields):
    permitted = {"status", "progress", "error", "result", "cancelled"}
    if not fields.keys() <= permitted:
        raise ValueError("Invalid job fields")
    if "result" in fields:
        fields["result"] = json.dumps(fields["result"], allow_nan=False)
    with connection() as conn:
        conn.execute(f"UPDATE jobs SET {','.join(key + '=?' for key in fields)} WHERE id=?",
                     [*fields.values(), job_id])


def claim_next():
    with connection() as conn:
        conn.execute("BEGIN IMMEDIATE")
        row = conn.execute("SELECT id FROM jobs WHERE status='queued' AND cancelled=0 ORDER BY created_at,id LIMIT 1").fetchone()
        if not row:
            return None
        conn.execute("UPDATE jobs SET status='processing' WHERE id=?", (row["id"],))
        return row["id"]


def queue_size():
    with connection() as conn:
        return conn.execute("SELECT COUNT(*) FROM jobs WHERE status IN ('queued','processing')").fetchone()[0]
