# NeuroClass Captured-Frame Accuracy Report

## Executive Summary

The captured photo was being detected but not reliably recognized because the Render attendance engine applied a five-observation temporal confirmation gate to a one-shot teacher capture. A single manual photo could therefore remain `REVIEW` or `UNKNOWN` even when the ArcFace similarity was strong. The recognition path has now been separated into two server-side modes: conservative `live` preview and teacher-triggered `manual` capture.

> **Security boundary:** The browser still captures pixels and sends them through Vercel. InsightFace detection, ArcFace embedding generation, classroom filtering, similarity matching, and authoritative confirmation remain on Render. No embedding is sent to the browser.

## Accuracy Improvements

The Render service now uses ArcFace-consistent landmark alignment through `insightface.utils.face_align.norm_crop` before recognition. When a frame contains small faces and the first detector pass returns no faces, the server performs one bounded upscaling retry and maps the returned boxes and landmarks back to the original frame.

Teacher-triggered manual captures use the same similarity and classroom policy as live preview, but they do not wait for five temporal observations. They require a high-confidence match from the captured frame, which is the correct behavior for an explicit teacher action. Live preview remains temporal-gated to reduce one-frame false positives.

The Vercel gateway now forwards `capture_mode` to Render. The frontend sends `live` for preview frames and `manual` for a teacher photo. Manual confirmed results are then reviewed through the server-side observation route and materialized into the `attendance` table, so the Attendance Log reflects persisted attendance rather than only local UI state.

## 100-Student Validation

The benchmark enrolled 100 identities, treated 50 enrolled identities as present, 50 enrolled identities as absent, and used 50 additional identities as unknown impostors. Each enrolled identity used two images for enrollment and a separate held-out image for the capture test. A 50-face composite image was also created as a classroom-style detection stress test.

The test used the actual `buffalo_s` ArcFace model and the actual `AttendanceEngine` in manual-capture mode. The public LFW data was obtained from the CC BY 4.0 Figshare mirror described in the references below. This is an engineering stress test, not a real NeuroClass classroom accuracy guarantee.

| Metric | Result |
| --- | ---: |
| Enrolled identities | 100 |
| Present test identities | 50 |
| Absent enrolled identities | 50 |
| Unknown impostors | 50 |
| Recognition accuracy on genuine held-out images | 88.0% |
| False rejection rate | 12.0% |
| False acceptance rate on unknown impostors | 0.0% |
| Average genuine-image inference latency | 48.0 ms |
| P95 genuine-image inference latency | 75.0 ms |
| Composite faces submitted | 50 |
| Composite results returned | 55 |
| Composite full-frame latency | 1,016.6 ms |

The 88.0% result is an improvement-oriented engineering measurement on public unconstrained images. It should not be presented as the accuracy of a real classroom deployment. The composite returned more face results than the 50 intended cells because the stitched image is not a natural classroom image and some cells can contain detector artifacts or duplicate detections.

## Deployment and Retest

The source changes have been prepared in both repositories. Deploy the AI service from `chinmaystudio/test` and the frontend/backend product from `chinmaystudio/neuroclass`. After deployment, refresh the teacher portal and use the following flow:

1. Open the classroom Attendance tab and open an attendance session.
2. Start **Live Face Preview**. Green boxes show detected faces but do not by themselves mark attendance.
3. Click **Capture Photo & Analyze**. The captured frame uses manual confirmation mode, and confirmed students should appear in the Attendance Log and be persisted to the attendance table.
4. Capture as many photos as needed. Per-session deduplication prevents repeated entries for the same canonical UUID student.
5. Click **Close session**. The server aggregates the roster, attendance rows, observation count, present count, absent count, and attendance rate. The UI displays the summary and offers a downloadable JSON report.

If a specific student is still rejected, improve the enrollment samples first: use five sharp, well-lit images with the student looking toward the camera at small angle changes, and ensure the face occupies a sufficient portion of the frame. The `buffalo_s` model is selected for Render Free memory limits; `buffalo_l` may improve accuracy on a suitably provisioned GPU but cannot be loaded alongside `buffalo_s` in the 512 MB deployment.

## References

[1]: https://figshare.com/articles/dataset/lfw_tgz/3829986 "scikit-learn LFW dataset lfw.tgz, Figshare"

[2]: https://creativecommons.org/licenses/by/4.0/ "Creative Commons Attribution 4.0 International License"

[3]: https://www.tensorflow.org/datasets/catalog/lfw "Labeled Faces in the Wild dataset overview"
