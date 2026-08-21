from fastapi import FastAPI, File, UploadFile, Form, HTTPException, Depends
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import cv2
import numpy as np
import time
from uuid import UUID
from core.detector import FaceDetector
from core.embedder import FaceEmbedder
from core.batch_embedder import BatchFaceEmbedder
from core.attendance_engine import AttendanceEngine
from db.database import LocalDatabase
from db.profiles import ProfileStore
from learning.prototype import calculate_prototype
from models.schemas import StudentEnrollment, EnrollmentResponse, FrameResponse

app = FastAPI(title="NeuroClass Attendance API")

import os
import uuid
import logging
from core.model_manager import model_manager
from supabase import create_client, Client

logger = logging.getLogger("uvicorn.error")

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")

supabase: Client | None = None
if SUPABASE_URL and SUPABASE_KEY:
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        logger.info("Supabase client initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize Supabase client: {e}")

@app.get("/health")
async def health_check():
    # Attempt to load the model to verify memory fits on startup
    try:
        model_manager.get_app()
        model_name = model_manager._current_model_name
    except Exception as e:
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "error": str(e),
                "model": os.environ.get("MODEL_NAME", "buffalo_s"),
                "provider": model_manager.provider,
                "memory_optimization": os.environ.get("MEMORY_OPTIMIZATION", "false")
            }
        )

    provider = model_manager.provider

    return {
        "status": "healthy",
        "model": model_name,
        "provider": provider,
        "database": "connected",
        "faiss": "loaded" if db.index.ntotal > 0 else "empty",
        "profiles": db.index.ntotal,
        "memory_optimization": os.environ.get("MEMORY_OPTIMIZATION", "false")
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
batch_embedder = BatchFaceEmbedder()
engine = AttendanceEngine(db)
profile_store = ProfileStore()
active_sessions = {}

# Startup: Load Supabase embeddings into FAISS
@app.on_event("startup")
async def startup_event():
    if not supabase:
        logger.warning("Supabase not configured, skipping embedding sync on startup")
        return

    try:
        logger.info("Fetching embeddings from Supabase on startup...")
        # Paginate if > 1000 in the future, but for now fetch all
        response = supabase.table("face_embeddings").select("*").execute()
        rows = response.data

        loaded_count = 0
        for row in rows:
            try:
                # pgvector returns embedding as a string or list of floats
                emb_data = row.get("embedding")
                if not emb_data:
                    continue

                if isinstance(emb_data, str):
                    # pgvector format: "[0.1,0.2,...]"
                    import ast
                    vector = np.array(ast.literal_eval(emb_data), dtype=np.float32)
                else:
                    vector = np.array(emb_data, dtype=np.float32)

                if vector.shape != (512,):
                    continue

                metadata = {
                    "student_id": row.get("student_id"),
                    "classroom_id": row.get("classroom_id"),
                    "profile_type": "centroid",
                    "supabase_id": row.get("id")
                }

                db.add_embedding(vector, metadata)
                loaded_count += 1
            except Exception as e:
                logger.error(f"Failed to load embedding for row {row.get('id')}: {e}")

        logger.info(f"Successfully loaded {loaded_count} embeddings from Supabase into FAISS")
    except Exception as e:
        logger.error(f"Failed to fetch embeddings from Supabase: {e}")

from api.auth import verify_service_token

@app.post("/ai/v1/enrollment")
async def enroll_student(
    _ = Depends(verify_service_token),
    student_id: UUID = Form(...),
    classroom_id: str = Form(...),
    registration_session_id: str = Form(...),
    files: list[UploadFile] = File(...)
):
    # Only public.students.id is accepted; aliases such as STU001 are rejected
    # before any biometric data is processed.
    canonical_student_id = str(student_id)
    accepted_samples = 0
    rejected_samples = 0
    rejection_reasons = []
    accepted_embeddings = []

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

        try:
            from insightface.utils.face_align import norm_crop
            crop = norm_crop(img, face.kps, image_size=112) if getattr(face, "kps", None) is not None else None
        except Exception:
            crop = None
        if crop is None:
            x1, y1, x2, y2 = [int(value) for value in face.bbox]
            crop = img[max(0, y1):max(y1 + 1, y2), max(0, x1):max(x1 + 1, x2)]
            if crop.size:
                crop = cv2.resize(crop, (112, 112), interpolation=cv2.INTER_CUBIC)
        emb = batch_embedder.generate_embeddings_batch([crop], batch_size=1)[0] if crop is not None and crop.size else None
        if emb is not None:
            accepted_embeddings.append(emb.tolist() if hasattr(emb, "tolist") else list(emb))
            accepted_samples += 1
        else:
            rejected_samples += 1
            rejection_reasons.append("EMBEDDING_FAILED")

    if accepted_embeddings:
        prototype = calculate_prototype(accepted_embeddings, method="centroid")

        # Add to local FAISS
        db.add_embedding(prototype, {
            "student_id": canonical_student_id,
            "classroom_id": classroom_id,
            "registration_session_id": registration_session_id,
            "sample_count": accepted_samples,
            "profile_type": "centroid"
        })

        # Upsert to Supabase
        if supabase:
            try:
                # We need a profile_id for the foreign key, create one if it doesn't exist
                # Or just use the student_id if they share the same PK
                # Based on schema, we might need to upsert face_profiles first
                profile_id = str(uuid.uuid4())

                # Format vector for pgvector
                vector_str = "[" + ",".join(str(x) for x in prototype) + "]"

                # Check if profile exists
                prof_resp = supabase.table("face_profiles").select("id").eq("student_id", canonical_student_id).execute()
                if not prof_resp.data:
                    supabase.table("face_profiles").insert({
                        "id": profile_id,
                        "student_id": canonical_student_id,
                        "classroom_id": classroom_id,
                        "version": 1
                    }).execute()
                else:
                    profile_id = prof_resp.data[0]["id"]

                # Upsert embedding
                supabase.table("face_embeddings").upsert({
                    "profile_id": profile_id,
                    "student_id": canonical_student_id,
                    "classroom_id": classroom_id,
                    "embedding": vector_str,
                    "source": "centroid_enrollment",
                    "quality_score": accepted_samples
                }, on_conflict="student_id,classroom_id").execute()

                logger.info(f"Successfully upserted embedding for student {canonical_student_id} to Supabase")
            except Exception as e:
                logger.error(f"Failed to upsert embedding to Supabase: {e}")

    return {
        "success": accepted_samples > 0,
        "accepted_samples": accepted_samples,
        "rejected_samples": rejected_samples,
        "rejection_reasons": list(set(rejection_reasons)),
        "profile_id": f"prof_{canonical_student_id}",
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
    session_id: str = Form(...),
    capture_mode: str = Form("live"),
    file: UploadFile = File(...),
    _ = Depends(verify_service_token)
):
    contents = await file.read()
    nparr = np.frombuffer(contents, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    results = engine.process_frame(img, classroom_id, lecture_id=session_id, capture_mode=capture_mode)

    return FrameResponse(
        classroom_id=classroom_id,
        timestamp=time.time(),
        results=results
    )

@app.post("/ai/v1/proctoring/exam-frame")
async def process_exam_frame(
    classroom_id: str = Form(...),
    session_id: str = Form(...),
    target_student_id: UUID = Form(...),
    file: UploadFile = File(...),
    _ = Depends(verify_service_token)
):
    """Verify an exam candidate using the already-enrolled classroom profile.

    The browser sends only an image to this service through the portal backend;
    embeddings remain in the server-side FAISS/Supabase pipeline.
    """
    contents = await file.read()
    nparr = np.frombuffer(contents, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    if img is None:
        raise HTTPException(status_code=400, detail="Invalid image")
    results = engine.process_frame(img, classroom_id, lecture_id=session_id, capture_mode="manual")
    target = str(target_student_id)
    candidate = next((item for item in results if str(item.get("student_id")) == target), None)
    if not candidate:
        return {"verified": False, "state": "UNKNOWN_FACE", "reason": "Registered student was not matched", "similarity": 0.0}
    status = str(candidate.get("status", "REVIEW"))
    return {
        "verified": status == "PRESENT",
        "state": "VERIFIED" if status == "PRESENT" else "REVIEW",
        "reason": None if status == "PRESENT" else "Face match requires review",
        "similarity": float(candidate.get("similarity", 0.0)),
        "confidence": candidate.get("confidence"),
    }

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
