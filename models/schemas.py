from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel


class StudentEnrollment(BaseModel):
    # Canonical NeuroClass public.students.id. Aliases such as STU001 are invalid.
    student_id: UUID
    name: str
    roll_number: str
    classroom_id: str


class EnrollmentResponse(BaseModel):
    success: bool
    message: str
    embeddings_added: int


class AttendanceResult(BaseModel):
    track_id: int
    student_id: Optional[UUID] = None
    name: Optional[str] = None
    similarity: float
    status: str
    confidence: str
    verification: Optional[str] = None
    bbox: List[float]


class FrameResponse(BaseModel):
    classroom_id: str
    timestamp: float
    results: List[AttendanceResult]
