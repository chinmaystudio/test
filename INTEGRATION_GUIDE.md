# NeuroClass Frontend and Backend Integration Guide

This guide explains how to connect your main `neuroclass` repository (Cloudflare Pages + Vercel) to this Render-hosted AI service.

## 1. Environment Variables

### Vercel Backend
Add these variables to your Vercel project settings:
```env
AI_SERVICE_URL=https://your-render-app.onrender.com
AI_SERVICE_SECRET=your_secure_random_string
```

### Cloudflare Pages Frontend
Add this to your Cloudflare Pages environment:
```env
VITE_API_URL=https://your-vercel-app.vercel.app
```
**CRITICAL:** Never expose `AI_SERVICE_SECRET` to the frontend.

## 2. Vercel AI Gateway

Your Vercel backend must proxy requests to Render so the browser never talks to Render directly. Create a file in your Vercel backend (e.g., `lib/ai-service.ts`):

```typescript
export async function sendToRenderAI(endpoint: string, formData: FormData) {
  const url = `${process.env.AI_SERVICE_URL}${endpoint}`;
  
  const response = await fetch(url, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${process.env.AI_SERVICE_SECRET}`,
      // Do not set Content-Type manually when using FormData in fetch; 
      // the browser/node-fetch sets the boundary automatically.
    },
    body: formData
  });
  
  if (!response.ok) {
    throw new Error(`AI Service Error: ${response.statusText}`);
  }
  
  return response.json();
}
```

## 3. Vercel Application Routes

### Enrollment Route (`api/students/face-registration.ts`)
```typescript
import { sendToRenderAI } from '../../lib/ai-service';

export default async function handler(req, res) {
  // 1. Authenticate user via Supabase
  // 2. Extract files and metadata from req
  // 3. Forward to Render:
  const result = await sendToRenderAI('/ai/v1/enrollment', formData);
  
  // 4. If result.success, write metadata to Supabase face_profiles
  // 5. Return success to Cloudflare
  res.status(200).json(result);
}
```

### Attendance Route (`api/attendance/frame.ts`)
```typescript
import { sendToRenderAI } from '../../lib/ai-service';

export default async function handler(req, res) {
  // 1. Authenticate teacher/session
  // 2. Forward frame to Render:
  const result = await sendToRenderAI('/ai/v1/attendance/frame', formData);
  
  // 3. Strip any sensitive vectors if they accidentally leak (Render strips them by default)
  // 4. Return bounding boxes and Match/Review/Unknown status to Cloudflare
  res.status(200).json(result);
}
```

## 4. Cloudflare Frontend Changes

Remove all `face-api.js` or `TinyFaceDetector` logic from your browser code. The browser only captures frames.

### Capture Loop (React)
```typescript
const captureFrame = async () => {
  if (!videoRef.current) return;
  
  const blob = await getBlobFromVideo(videoRef.current);
  const formData = new FormData();
  formData.append('classroom_id', classroomId);
  formData.append('file', blob, 'frame.jpg');
  
  // Send to Vercel, NOT Render
  const response = await fetch(`${import.meta.env.VITE_API_URL}/api/attendance/frame`, {
    method: 'POST',
    body: formData
  });
  
  const data = await response.json();
  drawBoundingBoxes(data.results);
};
```
