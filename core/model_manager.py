import os
import gc
import glob
import onnxruntime as ort
from insightface.app import FaceAnalysis
from insightface.model_zoo import model_zoo
from insightface.utils import ensure_available

class ModelManager:
    """
    Singleton manager for InsightFace FaceAnalysis to ensure only one model
    is loaded into memory at a time, allowing deployment on 512MB instances.
    """
    _instance = None
    _app = None
    _current_model_name = None
    _selected_provider = None
    _config_logged = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ModelManager, cls).__new__(cls)
        return cls._instance

    def get_app(self, det_size=(640, 640)):
        """
        Lazily loads and returns the configured FaceAnalysis app.
        Reuses the existing app if the model name matches.
        """
        model_name = os.environ.get("MODEL_NAME", "buffalo_s")
        self.log_configuration()
        
        if self._app is not None and self._current_model_name == model_name:
            return self._app

        if self._app is not None:
            print(f"Releasing memory for {self._current_model_name}...")
            del self._app
            gc.collect()

        print(f"Loading InsightFace model: {model_name}...")
        
        # Determine execution provider
        env_provider = os.environ.get("ONNX_PROVIDER")
        available_providers = ort.get_available_providers()
        
        if env_provider and env_provider in available_providers:
            selected_providers = [env_provider]
        else:
            providers = ['CUDAExecutionProvider', 'TensorrtExecutionProvider', 'CPUExecutionProvider']
            selected_providers = [p for p in providers if p in available_providers]

        if not selected_providers:
            raise RuntimeError("No ONNX Runtime execution provider is available")
        self._selected_provider = selected_providers[0]
        print(f"Selected ONNX Providers: {selected_providers}")

        try:
            # Render Free has only 512MB RAM. Limiting ONNX Runtime's thread
            # pools, using sequential execution, and disabling its CPU arena
            # avoids large allocator/thread reservations during startup.
            session_options = ort.SessionOptions()
            if os.environ.get("MEMORY_OPTIMIZATION", "false").lower() in {"1", "true", "yes", "on"}:
                session_options.intra_op_num_threads = 1
                session_options.inter_op_num_threads = 1
                session_options.execution_mode = ort.ExecutionMode.ORT_SEQUENTIAL
                session_options.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_BASIC
                session_options.enable_mem_pattern = False
                session_options.enable_cpu_mem_arena = False
                print("ONNX_SESSION_OPTIONS=single-thread,sequential,basic-graph,no-arena")
            # We load both detection and recognition modules here for the singleton.
            # Even if a caller only needs detection, the memory overhead of having
            # recognition loaded in buffalo_s is minimal compared to loading two
            # separate FaceAnalysis instances.
            app = self._load_minimal_app(
                model_name=model_name,
                root=os.environ.get("INSIGHTFACE_ROOT", "~/.insightface"),
                providers=selected_providers,
                session_options=session_options,
                det_size=det_size,
            )
            
            self._app = app
            self._current_model_name = model_name
            print(f"Model {model_name} loaded successfully.")
            print("MODEL_LOADED=true")
            return self._app
        except Exception as e:
            print(f"CRITICAL: Failed to load model {model_name}. Memory limit exceeded or missing files.")
            print(f"Error: {e}")
            raise RuntimeError(f"Model load failed: {e}")

    def _load_minimal_app(self, model_name, root, providers, session_options, det_size):
        """Load only detector and recognition ONNX sessions.

        InsightFace's normal FaceAnalysis constructor opens every ONNX file in
        a model pack and then discards disallowed tasks. On a 512MB process,
        those temporary sessions can cause an OOM before they are discarded.
        This targeted loader selects the known detector and ArcFace filenames
        first, so unused landmark/gender sessions are never created.
        """
        ort.set_default_logger_severity(3)
        model_dir = ensure_available("models", model_name, root=root)
        onnx_files = sorted(glob.glob(os.path.join(model_dir, "*.onnx")))
        selected_files = [
            path for path in onnx_files
            if os.path.basename(path).startswith(("det_", "w600k"))
        ]
        if not selected_files:
            raise RuntimeError(f"No detector/recognition ONNX files found for model {model_name}")

        models = {}
        for onnx_file in selected_files:
            model = model_zoo.get_model(
                onnx_file,
                providers=providers,
                sess_options=session_options,
            )
            if model is None or model.taskname not in {"detection", "recognition"}:
                del model
                continue
            if model.taskname in models:
                del model
                continue
            models[model.taskname] = model

        if "detection" not in models or "recognition" not in models:
            for model in models.values():
                del model
            raise RuntimeError(f"Model {model_name} must provide detection and recognition ONNX files")

        # Construct the public FaceAnalysis shape without invoking its
        # directory-wide __init__, preserving app.get()/models semantics.
        app = FaceAnalysis.__new__(FaceAnalysis)
        app.models = models
        app.model_dir = model_dir
        app.det_model = models["detection"]
        app.prepare(ctx_id=0, det_size=det_size)
        return app

    def log_configuration(self):
        if not self._config_logged:
            print(f"MODEL_NAME={os.environ.get('MODEL_NAME', 'buffalo_s')}")
            print(f"ONNX_PROVIDER={os.environ.get('ONNX_PROVIDER', 'auto')}")
            print(f"MEMORY_OPTIMIZATION={os.environ.get('MEMORY_OPTIMIZATION', 'false')}")
            print("MODEL_LOADED=false")
            self._config_logged = True

    @property
    def provider(self):
        return self._selected_provider or "CPUExecutionProvider"

# Global singleton instance
model_manager = ModelManager()
model_manager.log_configuration()
