import json
import sqlite3
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

import numpy as np


@dataclass
class IdentityProfile:
    student_id: str
    classroom_id: str
    enrollment_embeddings: List[List[float]] = field(default_factory=list)
    verified_embeddings: List[List[float]] = field(default_factory=list)
    prototype_embedding: Optional[List[float]] = None
    profile_version: int = 1
    last_updated: float = field(default_factory=time.time)

    def get_all_embeddings(self) -> List[List[float]]:
        return self.enrollment_embeddings + self.verified_embeddings


class ProfileStore:
    def __init__(self, path: str = "data/profiles.db"):
        import os
        os.makedirs(os.path.dirname(path), exist_ok=True)
        self.path = Path(path)
        self.connection = sqlite3.connect(self.path, check_same_thread=False)
            self.connection.execute("""
                CREATE TABLE IF NOT EXISTS profiles (
                    student_id TEXT,
                    classroom_id TEXT NOT NULL,
                    data TEXT NOT NULL,
                    version INTEGER NOT NULL,
                    last_updated REAL NOT NULL,
                    PRIMARY KEY (student_id, classroom_id)
                )
            """)
            self.connection.execute("""
                CREATE TABLE IF NOT EXISTS profile_versions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    student_id TEXT NOT NULL,
                    classroom_id TEXT,
                    version INTEGER NOT NULL,
                    data TEXT NOT NULL,
                    reason TEXT NOT NULL,
                    created_at REAL NOT NULL
                )
            """)
        self.connection.commit()

    def get_profile(self, student_id: str, classroom_id: str = None) -> Optional[IdentityProfile]:
        if classroom_id:
            row = self.connection.execute(
                "SELECT data FROM profiles WHERE student_id = ? AND classroom_id = ?", (student_id, classroom_id)
            ).fetchone()
        else:
            row = self.connection.execute(
                "SELECT data FROM profiles WHERE student_id = ? ORDER BY last_updated DESC LIMIT 1", (student_id,)
            ).fetchone()
        if not row:
            return None
        data = json.loads(row[0])
        return IdentityProfile(**data)

    def save_profile(self, profile: IdentityProfile, reason: str = "update") -> None:
        data_json = json.dumps(profile.__dict__)
        self.connection.execute(
            """INSERT OR REPLACE INTO profiles (student_id, classroom_id, data, version, last_updated)
               VALUES (?, ?, ?, ?, ?)""",
            (profile.student_id, profile.classroom_id, data_json, profile.profile_version, profile.last_updated)
        )
        self.connection.execute(
            """INSERT INTO profile_versions (student_id, classroom_id, version, data, reason, created_at)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (profile.student_id, profile.classroom_id, profile.profile_version, data_json, reason, time.time())
        )
        self.connection.commit()

    def rollback_profile(self, student_id: str, target_version: int) -> bool:
        row = self.connection.execute(
            "SELECT data FROM profile_versions WHERE student_id = ? AND version = ?",
            (student_id, target_version)
        ).fetchone()
        if not row:
            return False
        data = json.loads(row[0])
        profile = IdentityProfile(**data)
        profile.profile_version += 1
        profile.last_updated = time.time()
        self.save_profile(profile, reason=f"rollback_to_v{target_version}")
        return True

    def close(self):
        self.connection.close()
