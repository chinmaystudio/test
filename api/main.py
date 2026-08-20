from fastapi import FastAPI, File, UploadFile, Form, HTTPException, Depends
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

@app.get("/health")
async def health_check():
    # Attempt to report the actual ONNX provider used by the embedder
    provider = "CPUExecutionProvider"
    if hasattr(engine, 'batch_embedder'):
        provider = engine.batch_embedder.provider
    elif hasattr(embedder, 'app') and hasattr(embedder.app, 'providers') and embedder.app.providers:
        provider = embedder.app.providers[0]

    return {
        "status": "healthy",
        "model": "buffalo_l",
        "provider": provider,
        "database": "connected",
        "faiss": "loaded" if db.index.ntotal > 0 else "empty",
        "profiles": db.index.ntotal
    }

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
active_sessions = {}

from api.auth import verify_service_token

@app.post("/ai/v1/enrollment")
async def enroll_student(
    _ = Depends(verify_service_token),
    student_id: str = Form(...),
    classroom_id: str = Form(...),
    registration_session_id: str = Form(...),
    files: list[UploadFile] = File(...)
):
    accepted_samples = 0
    rejected_samples = 0
    rejection_reasons = []

    for file in files:
        contents = await file.read()
        nparr = np.frombuffer(contents, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        if img is None:
            rejected_samples += 1
            rejection_reasons.append("INVALID_IMAGE")
            continue

        faces = detector.detect(img)
        if len(faces) == 0:
            rejected_samples += 1
            rejection_reasons.append("NO_FACE")
            continue
        if len(faces) > 1:
            rejected_samples += 1
            rejection_reasons.append("MULTIPLE_FACES")
            continue

        face = faces[0]
        is_good, msg = detector.check_quality(face)
        if not is_good:
            rejected_samples += 1
            if "small" in msg.lower():
                rejection_reasons.append("FACE_TOO_SMALL")
            elif "blur" in msg.lower():
                rejection_reasons.append("BLURRY")
            else:
                rejection_reasons.append("LOW_QUALITY")
            continue

        emb = embedder.generate_embedding(img, face)
        if emb is not None:
            db.add_embedding(emb, {
                "student_id": student_id,
                "classroom_id": classroom_id,
                "registration_session_id": registration_session_id
            })
            accepted_samples += 1
        else:
            rejected_samples += 1
            rejection_reasons.append("EMBEDDING_FAILED")

    return {
        "success": accepted_samples > 0,
        "accepted_samples": accepted_samples,
        "rejected_samples": rejected_samples,
        "rejection_reasons": list(set(rejection_reasons)),
        "profile_id": f"prof_{student_id}",
        "profile_version": 1
    }

@app.post("/ai/v1/attendance/start")
async def start_attendance_session(
    classroom_id: str = Form(...),
    session_id: str = Form(...),
    _ = Depends(verify_service_token)
):
    active_sessions[session_id] = {"session_id": session_id, "classroom_id": classroom_id, "started_at": time.time(), "status": "ACTIVE"}
    return active_sessions[session_id]

@app.post("/ai/v1/attendance/frame", response_model=FrameResponse)
async def process_frame(
    classroom_id: str = Form(...),
    file: UploadFile = File(...),
    _ = Depends(verify_service_token)
):
    contents = await file.read()
    nparr = np.frombuffer(contents, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    results = engine.process_frame(img, classroom_id)

    return FrameResponse(
        classroom_id=classroom_id,
        timestamp=time.time(),
        results=results
    )

@app.post("/ai/v1/attendance/finish")
async def finish_attendance_session(
    session_id: str = Form(...),
    _ = Depends(verify_service_token)
):
    session = active_sessions.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Attendance session not found")
    session["status"] = "FINISHED"
    session["finished_at"] = time.time()
    return session

@app.get("/ai/v1/profiles/{student_id}")
async def get_profile_summary(
    student_id: str,
    _ = Depends(verify_service_token)
):
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

@app.post("/ai/v1/profiles/{student_id}/rollback")
async def rollback_profile(
    student_id: str,
    target_version: int,
    _ = Depends(verify_service_token)
):
    if not profile_store.rollback_profile(student_id, target_version):
        raise HTTPException(status_code=404, detail="Target profile version not found")
    return {"success": True, "student_id": student_id, "rolled_back_to": target_version}

@app.post("/ai/v1/profiles/{student_id}/reset")
async def reset_profile(
    student_id: str,
    _ = Depends(verify_service_token)
):
    profile = profile_store.get_profile(student_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    profile.verified_embeddings = []
    profile.profile_version += 1
    profile.last_updated = time.time()
    profile_store.save_profile(profile, reason="teacher_reset_adaptive_observations")
    return {"success": True, "student_id": student_id, "profile_version": profile.profile_version}
