import os
import resource
import time

os.environ.setdefault("MODEL_NAME", "buffalo_s")
os.environ.setdefault("ONNX_PROVIDER", "CPUExecutionProvider")
os.environ.setdefault("MEMORY_OPTIMIZATION", "true")
os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")
os.environ.setdefault("NUMEXPR_NUM_THREADS", "1")
os.environ.setdefault("ORT_NUM_THREADS", "1")

started = time.perf_counter()
from api.main import health_check
imported_seconds = time.perf_counter() - started
print(f"IMPORT_SECONDS={imported_seconds:.3f}")
print(f"RSS_AFTER_IMPORT_MB={resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024:.1f}")

started = time.perf_counter()
result = __import__("asyncio").run(health_check())
print(f"HEALTH_SECONDS={time.perf_counter() - started:.3f}")
print(f"HEALTH_RESULT={result}")
print(f"RSS_AFTER_HEALTH_MB={resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024:.1f}")
