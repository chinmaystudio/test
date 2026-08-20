# Deploying NeuroClass AI Attendance Engine for Free

Your frontend is currently deployed on **Vercel** (`https://neuro-class.vercel.app/`). However, you cannot deploy the FastAPI backend on Vercel for free because:
1. Vercel Serverless Functions have a strict **50MB deployment limit** and a **10-second timeout** on the free tier. The InsightFace model alone is >150MB, and processing a frame can take several seconds on CPU.
2. Vercel does not support persistent local storage (needed for the FAISS database and SQLite profiles).

To host this AI backend for free and connect it to your Vercel frontend, you have two primary options: **Hugging Face Spaces** (Recommended) or **Render**.

---

## Option 1: Hugging Face Spaces (Recommended for AI)

Hugging Face Spaces provides free Docker hosting specifically designed for machine learning models. It gives you 16GB RAM and 2 vCPUs on the free tier, which is enough to run this CPU-based pipeline.

### Step 1: Prepare the Repository
Hugging Face Spaces uses Docker. The `Dockerfile` is already in the repository. We just need to ensure the database files persist.

1. Go to [Hugging Face Spaces](https://huggingface.co/spaces) and create a new Space.
2. Select **Docker** as the Space SDK and choose **Blank**.
3. Choose **Public** (Free tier requires public spaces, but your data is isolated to the running container).

### Step 2: Push the Code
Clone the Hugging Face repository they provide and copy your backend code into it:
```bash
git clone https://huggingface.co/spaces/your-username/neuroclass-api
cp -r path/to/your/test/repo/* neuroclass-api/
cd neuroclass-api
git add .
git commit -m "Initial deploy"
git push
```

### Step 3: Configure CORS for Vercel
In `api/main.py`, update the CORS middleware to specifically allow your Vercel app:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://neuro-class.vercel.app", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Step 4: Persistent Storage
By default, Hugging Face Spaces resets the disk when the container restarts. To save your FAISS index and SQLite database permanently on the free tier, you must use Hugging Face datasets as storage, or upgrade to a persistent storage tier ($5/month). For a true free MVP, you can write a script to push the `.db` and `.bin` files to a private Hugging Face Dataset repository on shutdown, or use an external free PostgreSQL database (like Supabase).

---

## Option 2: Render (Free Web Service)

Render offers a free Web Service tier (512MB RAM, 0.1 CPU). **Warning:** 512MB RAM is likely too small to load the InsightFace ONNX models into memory, which typically require ~1GB+ RAM. If you use Render, the build will likely fail with an Out Of Memory (OOM) error.

---

## Option 3: Local Tunneling (Best for Development & MVP)

Since this is a heavy computer vision application, the absolute best free option while you are developing is to run the FastAPI server on your local PC (which has the CPU/GPU power) and expose it to the internet so your Vercel app can talk to it.

1. Run your server locally:
   ```bash
   python -m uvicorn api.main:app --reload --port 8000
   ```
2. Install **Cloudflared** or **Ngrok** (both are free):
   ```bash
   cloudflared tunnel --url http://localhost:8000
   ```
3. Cloudflare will give you a secure `https://something.trycloudflare.com` URL.
4. Put that URL into your Vercel frontend environment variables (e.g., `NEXT_PUBLIC_API_URL`).

---

## Integrating with the React Frontend

In your Vercel React app, you need to capture webcam frames and send them to the API.

```javascript
// In your React Component
const captureAndSendFrame = async (imageBlob) => {
  const formData = new FormData();
  formData.append('classroom_id', 'CLASS_A');
  formData.append('file', imageBlob, 'frame.jpg');

  try {
    const response = await fetch('https://YOUR_BACKEND_URL/attendance/frame', {
      method: 'POST',
      body: formData,
    });
    const data = await response.json();
    console.log("Attendance Results:", data.results);
    // Update UI with recognized students
  } catch (error) {
    console.error("Error sending frame:", error);
  }
};
```

### Summary Recommendation
- **For immediate free testing:** Use Local Tunneling (Ngrok/Cloudflare).
- **For free 24/7 cloud hosting:** Deploy to Hugging Face Spaces (Docker), but configure an external free Postgres database (like Supabase or Neon) to store the embeddings permanently.
