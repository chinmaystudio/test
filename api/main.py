from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import cv2
import numpy as np
import time
from core.detector import FaceDetector
from core.embedder import FaceEmbedder
from core.attendance_engine import AttendanceEngine
from db.database import LocalDatabase
from models.schemas import StudentEnrollment, EnrollmentResponse, FrameResponse

app = FastAPI(title="NeuroClass Attendance API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, restrict to neuro-class.vercel.app
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global instances (in production, use dependency injection)
db = LocalDatabase()
detector = FaceDetector()
embedder = FaceEmbedder()
engine = AttendanceEngine(db)

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
