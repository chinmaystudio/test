import sqlite3
from pathlib import Path
from typing import Optional


class AttendanceStore:
    """Local SQLite store; production deployments can use the same unique key in PostgreSQL."""
    def __init__(self, path: str = "attendance.db"):
        self.path = Path(path)
        self.connection = sqlite3.connect(self.path)
        self.connection.execute("""
            CREATE TABLE IF NOT EXISTS attendance (
                classroom_id TEXT NOT NULL,
                lecture_id TEXT NOT NULL,
                student_id TEXT NOT NULL,
                status TEXT NOT NULL,
                similarity REAL NOT NULL,
                verification TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (classroom_id, lecture_id, student_id)
            )
        """)
        self.connection.commit()

    def mark_present(self, classroom_id: str, lecture_id: str, student_id: str,
                     similarity: float, verification: str = "AUTO") -> bool:
        cursor = self.connection.execute(
            "INSERT OR IGNORE INTO attendance(classroom_id, lecture_id, student_id, status, similarity, verification) VALUES (?, ?, ?, 'PRESENT', ?, ?)",
            (classroom_id, lecture_id, student_id, float(similarity), verification),
        )
        self.connection.commit()
        return cursor.rowcount == 1

    def list_for_lecture(self, classroom_id: str, lecture_id: str) -> list[dict]:
        rows = self.connection.execute(
            "SELECT classroom_id, lecture_id, student_id, status, similarity, verification, created_at FROM attendance WHERE classroom_id = ? AND lecture_id = ? ORDER BY created_at",
            (classroom_id, lecture_id),
        ).fetchall()
        columns = ["classroom_id", "lecture_id", "student_id", "status", "similarity", "verification", "created_at"]
        return [dict(zip(columns, row)) for row in rows]

    def close(self) -> None:
        self.connection.close()
