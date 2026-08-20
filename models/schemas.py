from pydantic import BaseModel
from typing import List, Optional

class StudentEnrollment(BaseModel):
    student_id: str
    name: str
    roll_number: str
    classroom_id: str

class EnrollmentResponse(BaseModel):
    success: bool
    message: str
    embeddings_added: int

class AttendanceResult(BaseModel):
    track_id: int
    student_id: str
    name: str
    similarity: float
    status: str
    confidence: str
    bbox: List[float]

class FrameResponse(BaseModel):
    classroom_id: str
    timestamp: float
    results: List[AttendanceResult]
