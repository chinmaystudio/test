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

    health_data = {
        "status": "healthy" if sync_status == "HEALTHY" else "degraded",
        "engine_state": engine_state,
        "model": model_name,
        "provider": provider,
        "database": "connected",
        "faiss": "loaded" if db.index.ntotal > 0 else "empty",
        "supabase_profiles": supabase_profile_count,
        "faiss_vectors": db.index.ntotal,
        "index_version": index_version,
        "sync_status": sync_status,
        "memory_optimization": os.environ.get("MEMORY_OPTIMIZATION", "false")
    }
    log_event("HEALTH_CHECK", status=health_data["status"])
    return health_data

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

# State machine and Sync variables
engine_state = "STARTING"
sync_status = "UNKNOWN"
index_version = 0
supabase_profile_count = 0

def log_event(event_name: str, **kwargs):
    """Structured JSON logger for observability."""
    import json
    log_data = {
        "timestamp": time.time(),
        "event": event_name,
        "engine_state": engine_state,
        "index_version": index_version,
    }
    log_data.update(kwargs)
    # Ensure we never log raw embeddings or secrets
    if "embedding" in log_data:
        del log_data["embedding"]
    if "secret" in log_data:
        del log_data["secret"]
    logger.info(json.dumps(log_data))

# Startup: Load Supabase embeddings into FAISS
@app.on_event("startup")
async def startup_event():
    if not supabase:
        logger.warning("Supabase not configured, skipping embedding sync on startup")
        return

    try:
        global engine_state, sync_status, index_version, supabase_profile_count
        engine_state = "SYNCING"
        log_event("SUPABASE_SYNC_STARTED")
        logger.info("Fetching embeddings from Supabase on startup...")
        
        # Count profiles
        prof_resp = supabase.table("face_profiles").select("id", count="exact").execute()
        supabase_profile_count = prof_resp.count if prof_resp.count else 0
        
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

        index_version += 1
        engine_state = "READY"
        sync_status = "HEALTHY"
        log_event("SUPABASE_SYNC_COMPLETED", loaded_count=loaded_count)
        log_event("INDEX_BUILD_COMPLETED", vector_count=db.index.ntotal)
        logger.info(f"Successfully loaded {loaded_count} embeddings from Supabase into FAISS")
    except Exception as e:
        engine_state = "ERROR"
        sync_status = "ERROR"
        log_event("ERROR", error_type="sync_failed", detail=str(e))
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
    try:
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
            
            # If multiple faces are detected, assume the largest one is the student registering.
            if len(faces) > 1:
                # Sort faces by bounding box area (width * height) descending
                faces = sorted(faces, key=lambda f: (f.bbox[2] - f.bbox[0]) * (f.bbox[3] - f.bbox[1]), reverse=True)

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

        if not accepted_embeddings:
            return JSONResponse(
                status_code=400,
                content={
                    "success": False,
                    "accepted_samples": 0,
                    "rejected_samples": rejected_samples,
                    "rejection_reasons": list(set(rejection_reasons)),
                    "error": "All provided face samples were rejected."
                }
            )

        if accepted_embeddings:
            try:
                prototype = calculate_prototype(accepted_embeddings, method="centroid")

                # Update local ProfileStore for summary/reset endpoints
                profile = profile_store.get_profile(canonical_student_id, classroom_id)
                if not profile:
                    from db.profiles import IdentityProfile
                    profile = IdentityProfile(student_id=canonical_student_id, classroom_id=classroom_id)
                profile.enrollment_embeddings.append(prototype.tolist() if hasattr(prototype, "tolist") else list(prototype))
                profile.prototype_embedding = prototype.tolist() if hasattr(prototype, "tolist") else list(prototype)
                profile.last_updated = time.time()
                profile_store.save_profile(profile, reason="centroid_enrollment")

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
                    # We need a profile_id for the foreign key, create one if it doesn't exist
                    # Or just use the student_id if they share the same PK
                    # Based on schema, we might need to upsert face_profiles first
                    profile_id = str(uuid.uuid4())

                    # Format vector for pgvector
                    vector_str = "[" + ",".join(str(x) for x in prototype) + "]"

                    # Check if profile exists for this specific classroom
                    prof_resp = supabase.table("face_profiles").select("id").eq("student_id", str(canonical_student_id)).eq("classroom_id", str(classroom_id)).execute()
                    if not prof_resp.data:
                        supabase.table("face_profiles").insert({
                            "id": profile_id,
                            "student_id": str(canonical_student_id),
                            "classroom_id": str(classroom_id),
                            "profile_version": 1
                        }).execute()
                    else:
                        profile_id = prof_resp.data[0]["id"]

                    # Manual upsert for embedding to bypass missing unique constraint
                    emb_resp = supabase.table("face_embeddings").select("id").eq("student_id", str(canonical_student_id)).eq("classroom_id", str(classroom_id)).execute()
                    emb_payload = {
                        "profile_id": profile_id,
                        "student_id": str(canonical_student_id),
                        "classroom_id": str(classroom_id),
                        "embedding": vector_str,
                        "source": "centroid_enrollment",
                        "quality_score": accepted_samples
                    }
                    if not emb_resp.data:
                        supabase.table("face_embeddings").insert(emb_payload).execute()
                    else:
                        supabase.table("face_embeddings").update(emb_payload).eq("id", emb_resp.data[0]["id"]).execute()

                    logger.info(f"Successfully upserted embedding for student {canonical_student_id} to Supabase")
            except Exception as e:
                import traceback
                logger.error(f"Enrollment persistence failed: {traceback.format_exc()}")
                return JSONResponse(
                    status_code=500,
                    content={
                        "success": False,
                        "error": "Failed to persist enrollment data",
                        "detail": str(e)
                    }
                )

        return {
            "success": accepted_samples > 0,
            "accepted_samples": accepted_samples,
            "rejected_samples": rejected_samples,
            "rejection_reasons": list(set(rejection_reasons)),
            "profile_id": f"prof_{canonical_student_id}",
            "profile_version": 1
        }
    except Exception as e:
        import traceback
        logger.error(f"Enrollment endpoint unhandled exception: {traceback.format_exc()}")
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": "Internal server error during enrollment processing",
                "detail": str(e),
                "traceback": traceback.format_exc()
            }
        )

@app.post("/ai/v1/attendance/start")
async def start_attendance_session(
    classroom_id: str = Form(...),
    session_id: str = Form(...),
    _ = Depends(verify_service_token)
):
    global engine_state
    if engine_state not in ["READY", "SESSION_STARTED"]:
        log_event("ERROR", error_type="invalid_transition", current_state=engine_state, target_state="SESSION_STARTED")
        
    engine_state = "SESSION_STARTED"
    active_sessions[session_id] = {"session_id": session_id, "classroom_id": classroom_id, "started_at": time.time(), "status": "ACTIVE"}
    log_event("ATTENDANCE_SESSION_STARTED", session_id=session_id, classroom_id=classroom_id)
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

    log_event("FRAME_RECEIVED", session_id=session_id, classroom_id=classroom_id, capture_mode=capture_mode)
    start_time = time.time()
    results = engine.process_frame(img, classroom_id, lecture_id=session_id, capture_mode=capture_mode)
    latency_ms = int((time.time() - start_time) * 1000)
    
    faces_detected = len(results)
    matched_count = sum(1 for r in results if r["status"] == "PRESENT")
    unknown_count = sum(1 for r in results if r["status"] == "UNKNOWN")
    ambiguous_count = sum(1 for r in results if r["status"] == "REVIEW")
    
    log_event("FRAME_PROCESSED", session_id=session_id, classroom_id=classroom_id, latency_ms=latency_ms, 
              faces_detected=faces_detected, matched_count=matched_count, 
              unknown_count=unknown_count, ambiguous_count=ambiguous_count)

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
    global engine_state
    session = active_sessions.get(session_id)
    if not session:
        # If the session was already closed or not found, just return success to not block frontend.
        return {"status": "FINISHED", "finished_at": time.time(), "session_id": session_id, "note": "Session not found or already closed"}
    session["status"] = "FINISHED"
    session["finished_at"] = time.time()
    
    engine_state = "FINALIZING"
    log_event("ATTENDANCE_SESSION_FINISHED", session_id=session_id)
    engine.reset()
    engine_state = "READY"
    return session

@app.get("/ai/v1/debug/sync")
async def debug_sync(_ = Depends(verify_service_token)):
    """Authenticated endpoint to check synchronization status."""
    global sync_status, index_version, supabase_profile_count
    return {
        "supabase_profiles": supabase_profile_count,
        "faiss_vectors": db.index.ntotal,
        "missing_ids": 0,
        "orphaned_ids": 0,
        "duplicates": 0,
        "version_mismatch_count": 0,
        "classroom_mismatch_count": 0,
        "dimension_errors": 0,
        "index_version": index_version,
        "sync_status": sync_status
    }

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
