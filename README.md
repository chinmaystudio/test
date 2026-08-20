# NeuroClass AI Group Attendance Engine

This repository implements a local-first, trainable-by-enrollment facial-recognition attendance backend for NeuroClass. It uses a pretrained InsightFace/ArcFace embedding pipeline rather than a separate neural-network class for every student. Adding a student therefore adds embeddings to the index and does not require retraining the recognition network.

> **Biometric safety note:** ordinary face recognition is not a liveness guarantee. Obtain appropriate consent and notices, restrict access, minimize retention, and add a real anti-spoofing model before treating automated results as authoritative.

## Architecture decisions

| Decision | MVP implementation | Production direction |
|---|---|---|
| Detection | InsightFace RetinaFace through `FaceAnalysis` | GPU-backed InsightFace service with tuned detector size |
| Recognition | ArcFace embeddings from the `buffalo_l` model | Versioned model artifacts and offline threshold calibration |
| Search | FAISS inner-product index over normalized 512-dimensional vectors | PostgreSQL + pgvector adapter in `db/postgres.py` |
| Group tracking | Lightweight IoU tracker with stable track IDs | ByteTrack or DeepSORT when camera motion and crowd density require it |
| Temporal verification | Sliding window, minimum observations, score stability | Session-level track lifecycle and calibrated quality weighting |
| Browser transport | Periodic JPEG frames for the MVP | WebSocket or WebRTC when lower latency and higher throughput are required |
| Liveness | Explicit replaceable hook, disabled by default | Blink/head-motion challenge or dedicated face anti-spoofing model |

RetinaFace and ArcFace are used because the system needs open-set identity matching, not a closed-set classifier. The detector returns multiple face boxes and landmarks. InsightFace aligns the face internally before producing a normalized embedding. FAISS inner product is equivalent to cosine similarity when both vectors are L2-normalized. Thresholds in this repository are configuration defaults only; use `evaluation/evaluate.py` with held-out data to select an operating point that prioritizes low false acceptance.

## Repository layout

```text
api/main.py                 FastAPI REST endpoints
core/detector.py            Multi-face detection
core/embedder.py            ArcFace embedding generation
core/quality.py             Size, detector-score, and blur rejection
core/matching.py            Threshold policy and unknown rejection
core/temporal.py            Multi-frame identity confirmation
core/tracker.py             Lightweight track association
core/liveness.py            Replaceable anti-spoofing interface
core/attendance_engine.py   Group attendance orchestration
db/database.py              Local FAISS + JSON metadata store
db/attendance.py            Local SQLite attendance store
db/postgres.py              Optional pgvector SQL adapter
models/schemas.py           API request and response contracts
evaluation/evaluate.py      Validation metrics and threshold sweep
scripts_enroll.py           CLI enrollment
tests/                      Unit tests that do not require model downloads
dataset/                    Training, validation, and test data folders
```

## Windows-first local setup

Python 3.10 or 3.11 is recommended. From PowerShell:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
uvicorn api.main:app --reload
```

The first InsightFace inference downloads the configured model pack. A CPU-only laptop can run the MVP, but group recognition throughput depends on image resolution, detector size, CPU/GPU availability, and how often embeddings are refreshed. Group images should preserve enough pixels per face; lowering resolution too aggressively improves speed at the cost of missed small faces and lower-quality embeddings.

## Dataset and enrollment protocol

Use separate images for enrollment and evaluation. A practical starting point is five to ten enrollment images per student covering mild pose, glasses, and lighting variation. Keep validation and test images or videos disjoint from enrollment images and, ideally, capture them in a different session. Never use the same image for both registration and testing.

```text
dataset/
  training/
    STU024/img01.jpg
  validation/
    STU024/val01.jpg
    unknown/unknown01.jpg
  test/
    STU024/test01.jpg
    unknown/unknown02.jpg
```

Enroll a student with the CLI:

```powershell
python scripts_enroll.py `
  --student-id STU024 `
  --name Aarav `
  --roll-number 24 `
  --classroom-id CSE-A `
  --images dataset/training/STU024
```

Enrollment accepts only images containing exactly one detectable face that passes the quality checks. Raw facial images are not persisted by the local embedding store; only embeddings and minimal metadata are saved.

## API

Run `uvicorn api.main:app --reload` and open `http://127.0.0.1:8000/docs` for interactive OpenAPI documentation. The MVP uses multipart form data for images so it can be called directly from a React camera component.

| Method | Endpoint | Purpose |
|---|---|---|
| POST | `/students/enroll` | Enroll a student with one or more image files |
| POST | `/attendance/frame` | Process one JPEG frame containing multiple faces |
| POST | `/attendance/start` | Reserved session lifecycle endpoint for the production integration |
| POST | `/attendance/finish` | Reserved session lifecycle endpoint for the production integration |
| GET | `/attendance/{lecture_id}` | Reserved attendance query endpoint |
| POST | `/attendance/verify` | Reserved teacher-review endpoint |

Example enrollment request:

```bash
curl -X POST http://127.0.0.1:8000/students/enroll \
  -F student_id=STU024 -F name=Aarav -F roll_number=24 -F classroom_id=CSE-A \
  -F files=@dataset/training/STU024/img01.jpg \
  -F files=@dataset/training/STU024/img02.jpg
```

Example frame request:

```bash
curl -X POST http://127.0.0.1:8000/attendance/frame \
  -F classroom_id=CSE-A \
  -F file=@classroom-frame.jpg
```

A result is shaped for a React dashboard:

```json
{
  "track_id": 17,
  "student_id": "STU024",
  "name": "Aarav",
  "similarity": 0.91,
  "status": "PRESENT",
  "confidence": "HIGH",
  "verification": "AUTO",
  "observations": 5,
  "already_confirmed": true,
  "bbox": [120, 80, 220, 200]
}
```

Classroom isolation is applied during vector search: a frame for classroom `CSE-A` is searched only against embeddings whose `classroom_id` is `CSE-A`. The frontend should select the classroom, create a lecture/session ID, capture periodic JPEG frames, display live results, expose uncertain faces for teacher review, and submit final attendance through an authenticated production endpoint.

## Evaluation and stress testing

Threshold calibration requires held-out genuine and unknown samples:

```powershell
python -m evaluation.evaluate --data dataset/validation
```

The script reports true/false positives and negatives, false-acceptance rate, false-rejection rate, precision, recall, F1, and average detector time across a threshold sweep. Select the threshold using validation data, then report final performance once on the untouched test set. Group stress testing should use recorded classroom frames at 5, 10, 20, 30, 40, and 50 visible students, and should measure detected faces, correct identities, unknowns, false matches, elapsed time, FPS, and memory. The dominant bottlenecks are face detection, embedding inference, and insufficient pixels per small face.

## Security and privacy checklist

The current local MVP intentionally does not implement authentication and must not be exposed publicly. Before connecting it to NeuroClass, add teacher authentication, classroom-level authorization, TLS, rate limiting, server-side validation, audit logs, encrypted embedding storage, deletion of biometric profiles, retention limits, and a consent/notice workflow appropriate to the deployment jurisdiction. Do not return embeddings through public APIs. Store only the minimum metadata required for attendance and keep review actions auditable.

## Docker

A basic container definition is included for Linux deployment. GPU runtime configuration and model-cache persistence should be added for production deployments. PostgreSQL + pgvector is an optional next step; the local FAISS store is the simplest development path.

## Limitations

This is an MVP foundation rather than a claim of perfect accuracy. Performance must be measured on the target camera, classroom lighting, camera distance, pose distribution, and demographic population. Unknown rejection, quality rejection, multi-frame verification, and teacher review are intentional safeguards, not substitutes for scientific validation or liveness detection.

## References

[1]: https://insightface.ai/ "InsightFace project"
[2]: https://github.com/deepinsight/insightface "InsightFace GitHub repository"
[3]: https://github.com/facebookresearch/faiss "FAISS similarity-search library"
[4]: https://github.com/pgvector/pgvector "pgvector PostgreSQL extension"
