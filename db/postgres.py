"""Optional production adapter for PostgreSQL + pgvector.

The local MVP uses FAISS. This adapter documents the minimal schema and leaves
connection lifecycle to the host application so credentials are never exposed
through the API.
"""

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional


@dataclass
class PostgresEmbedding:
    student_id: str
    name: str
    roll_number: str
    classroom_id: str
    embedding: list[float]
    quality_score: float
    created_at: datetime


CREATE_SCHEMA_SQL = """
CREATE EXTENSION IF NOT EXISTS vector;
CREATE TABLE IF NOT EXISTS face_embeddings (
    id BIGSERIAL PRIMARY KEY,
    student_id TEXT NOT NULL,
    name TEXT NOT NULL,
    roll_number TEXT NOT NULL,
    classroom_id TEXT NOT NULL,
    embedding vector(512) NOT NULL,
    quality_score REAL NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS face_embeddings_classroom_idx ON face_embeddings(classroom_id);
CREATE TABLE IF NOT EXISTS attendance (
    classroom_id TEXT NOT NULL,
    lecture_id TEXT NOT NULL,
    student_id TEXT NOT NULL,
    status TEXT NOT NULL,
    similarity REAL NOT NULL,
    verification TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (classroom_id, lecture_id, student_id)
);
"""


class PostgresRepository:
    """SQL contract for a production implementation using psycopg or SQLAlchemy."""
    def __init__(self, connection):
        self.connection = connection

    def search(self, embedding: list[float], classroom_id: str, limit: int = 1):
        query = """
        SELECT student_id, name, 1 - (embedding <=> %s::vector) AS similarity
        FROM face_embeddings
        WHERE classroom_id = %s
        ORDER BY embedding <=> %s::vector
        LIMIT %s
        """
        vector = "[" + ",".join(str(float(x)) for x in embedding) + "]"
        with self.connection.cursor() as cursor:
            cursor.execute(query, (vector, classroom_id, vector, limit))
            return [dict(student_id=row[0], name=row[1], similarity=float(row[2])) for row in cursor.fetchall()]
