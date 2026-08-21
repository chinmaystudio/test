# NeuroClass 1,000-Student Accuracy Report

## Scope and Method

The recognition service was evaluated with **1,000 registered identities** and **680 unknown impostor identities** from the public LFW dataset mirrored on Figshare. Each registered identity used up to three images for enrollment and a held-out image for capture evaluation. Five hundred registered identities were designated as present and five hundred as absent for the roster scenario; the held-out capture evaluation measures genuine recognition across all 1,000 registered identities. This is an engineering stress test, not a real classroom accuracy or demographic-performance claim.

The benchmark used the existing `buffalo_s` ArcFace model, CPU execution, the NeuroClass detector, landmark alignment, normalized embeddings, classroom-filtered FAISS search, and one centroid vector per enrolled identity. The ArcFace backbone was not fine-tuned, and no second model was loaded.

## Results

| Metric | Result |
| --- | ---: |
| Registered identities | 1,000 |
| Unknown impostor identities | 680 |
| Registered profile vectors | 999 successful vectors |
| Embedding dimension | 512 |
| Raw vector storage | 1.95 MB |
| Mean accepted enrollment samples | 1.93 |
| Enrollment failures | 1 |
| RSS before index evaluation | 137.4 MB |
| RSS after index construction | 232.1 MB |
| Average capture inference latency | 44.4 ms |
| P95 capture inference latency | 57.0 ms |
| Captures with a detected face | 1,676 / 1,680 |

The benchmark showed a clear security/recall tradeoff. At the calibrated production default of **0.45**, genuine recognition was **95.2%**, the false-rejection rate was **4.8%**, and the false-acceptance rate was **0.588%** on this impostor sample. If the operating point requires zero false accepts on this benchmark, a threshold of **0.58** achieved **78.3% genuine recognition**, **21.7% false rejection**, and **0.0% false acceptance**.

| Operating point | Genuine accuracy | False rejection | False acceptance |
| --- | ---: | ---: | ---: |
| Recall-oriented calibrated default, threshold 0.45 | 95.2% | 4.8% | 0.588% |
| Zero-FAR point observed in this benchmark, threshold 0.58 | 78.3% | 21.7% | 0.0% |

The default remains configurable through `ATTENDANCE_AUTO_THRESHOLD` and `ATTENDANCE_REVIEW_THRESHOLD`. Institutions that prioritize security over recall should raise the automatic threshold and use the review workflow for borderline matches; institutions prioritizing fewer missed students should keep the calibrated 0.45 operating point and require teacher review for low-confidence results.

## Accuracy Changes

Enrollment now creates a normalized centroid prototype from the accepted samples and stores one 512-dimensional vector per student registration session. This keeps the profile index storage approximately constant at one vector per student while reducing sensitivity to any single enrollment image. Enrollment and attendance both use the same ArcFace landmark alignment path, and difficult small-face frames receive one bounded server-side upscaling retry.

Manual teacher captures use the same similarity policy as live recognition but do not wait for the five-frame temporal confirmation gate. Live preview remains temporally conservative. This prevents the prior failure mode in which the face was visible in the preview but a single teacher photo could never become `PRESENT`.

## Important Limitations

This benchmark uses public unconstrained photographs rather than the real enrolled students, camera, lighting, seating distance, and classroom background. A benchmark result cannot guarantee live classroom accuracy. The zero-FAR operating point is especially conservative and produces many false rejections. The 0.45 default improves recall but permits a small measured false-acceptance rate on this test set; the product should retain the `REVIEW` state and teacher confirmation path.

The model remains `buffalo_s` because the Render Free deployment has a 512 MB memory limit. Loading `buffalo_l` or fine-tuning the ArcFace backbone would violate the current storage/memory constraints. The implemented improvement is continual identity-profile adaptation and calibrated decision policy, not backbone fine-tuning.

## Deployment Steps

Deploy the latest `chinmaystudio/test` AI service commit to Render and the latest `chinmaystudio/neuroclass` commit to Vercel and Cloudflare Pages. Verify that the AI service environment includes `ATTENDANCE_AUTO_THRESHOLD=0.45`, `ATTENDANCE_REVIEW_THRESHOLD=0.35`, `MODEL_NAME=buffalo_s`, and `MEMORY_OPTIMIZATION=true`. Re-enroll the affected student with five sharp samples after deployment, then test the teacher workflow using live preview followed by repeated manual captures.

## References

[1]: https://figshare.com/articles/dataset/lfw_tgz/3829986 "scikit-learn LFW dataset lfw.tgz, Figshare"

[2]: https://creativecommons.org/licenses/by/4.0/ "Creative Commons Attribution 4.0 International License"

[3]: https://www.tensorflow.org/datasets/catalog/lfw "Labeled Faces in the Wild dataset overview"
