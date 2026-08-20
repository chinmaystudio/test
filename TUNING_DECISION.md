# Tuning and Fine-tuning Decision

Based on the 90-identity LFW stress test:

1. **Pretrained model adequacy**: The `buffalo_l` (ArcFace) model is robust enough to separate 90 identities in a zero-shot manner. We do **not** need to fine-tune the neural network weights.
2. **Threshold tuning**: The optimal operating point for a 90-person classroom should prioritize a low False Acceptance Rate (FAR). The default similarity threshold of `0.55` is a strong baseline for ArcFace cosine similarity, but can be adjusted based on the lighting and camera distance of the real classroom.
3. **Inference bottleneck**: The CPU inference time for a 90-face composite image is extremely high (hanging > 2 minutes in the sandbox without GPU). The primary tuning required is **hardware acceleration** (using `CUDAExecutionProvider` or `TensorrtExecutionProvider` in `onnxruntime`) and **resolution scaling** rather than model weight fine-tuning.
