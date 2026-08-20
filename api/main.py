from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import cv2
import numpy as np
import time
from core.detector import FaceDetector
from core.embedder import FaceEmbedder
from core.attendance_engine import AttendanceEngine
from db.database import LocalDatabase
from db.profiles import ProfileStore
from models.schemas import StudentEnrollment, EnrollmentResponse, FrameResponse

app = FastAPI(title="NeuroClass Attendance API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://neuro-class.vercel.app", 
        "http://localhost:3000",
        "http://localhost:5173"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global instances (in production, use dependency injection)
db = LocalDatabase()
detector = FaceDetector()
embedder = FaceEmbedder()
engine = AttendanceEngine(db)
profile_store = ProfileStore()

@app.post("/students/enroll", response_model=EnrollmentResponse)
async def enroll_student(
    student_id: str = Form(...),
    name: str = Form(...),
    roll_number: str = Form(...),
    classroom_id: str = Form(...),
    files: list[UploadFile] = File(...)
):
    added = 0
    for file in files:
        contents = await file.read()
        nparr = np.frombuffer(contents, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        faces = detector.detect(img)
        if len(faces) != 1:
            continue # Reject if not exactly one face
            
        face = faces[0]
        is_good, msg = detector.check_quality(face)
        if not is_good:
            continue
            
        emb = embedder.generate_embedding(img, face)
        if emb is not None:
            db.add_embedding(emb, {
                "student_id": student_id,
                "name": name,
                "roll_number": roll_number,
                "classroom_id": classroom_id
            })
            added += 1
            
    if added == 0:
        raise HTTPException(status_code=400, detail="No valid faces found for enrollment.")
        
    return EnrollmentResponse(success=True, message=f"Enrolled {name}", embeddings_added=added)

@app.post("/attendance/frame", response_model=FrameResponse)
async def process_frame(classroom_id: str = Form(...), file: UploadFile = File(...)):
    contents = await file.read()
    nparr = np.frombuffer(contents, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    
    results = engine.process_frame(img, classroom_id)
    
    return FrameResponse(
        classroom_id=classroom_id,
        timestamp=time.time(),
        results=results
    )

@app.get("/students/{student_id}/profile")
async def get_profile_summary(student_id: str):
    """Return safe profile statistics without exposing biometric embeddings."""
    profile = profile_store.get_profile(student_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return {
        "student_id": profile.student_id,
        "classroom_id": profile.classroom_id,
        "profile_version": profile.profile_version,
        "enrollment_observations": len(profile.enrollment_embeddings),
        "verified_observations": len(profile.verified_embeddings),
        "last_updated": profile.last_updated,
    }

@app.post("/students/{student_id}/profile/rollback")
async def rollback_profile(student_id: str, target_version: int):
    if not profile_store.rollback_profile(student_id, target_version):
        raise HTTPException(status_code=404, detail="Target profile version not found")
    return {"success": True, "student_id": student_id, "rolled_back_to": target_version}

@app.post("/students/{student_id}/profile/reset")
async def reset_profile(student_id: str):
    profile = profile_store.get_profile(student_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    profile.verified_embeddings = []
    profile.profile_version += 1
    profile.last_updated = time.time()
    profile_store.save_profile(profile, reason="teacher_reset_adaptive_observations")
    return {"success": True, "student_id": student_id, "profile_version": profile.profile_version}
