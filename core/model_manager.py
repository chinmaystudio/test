import os
import gc
import onnxruntime as ort
from insightface.app import FaceAnalysis

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
            # We load both detection and recognition modules here for the singleton.
            # Even if a caller only needs detection, the memory overhead of having
            # recognition loaded in buffalo_s is minimal compared to loading two
            # separate FaceAnalysis instances.
            app = FaceAnalysis(
                name=model_name,
                allowed_modules=['detection', 'recognition'],
                providers=selected_providers
            )
            app.prepare(ctx_id=0, det_size=det_size)
            
            self._app = app
            self._current_model_name = model_name
            print(f"Model {model_name} loaded successfully.")
            print("MODEL_LOADED=true")
            return self._app
        except Exception as e:
            print(f"CRITICAL: Failed to load model {model_name}. Memory limit exceeded or missing files.")
            print(f"Error: {e}")
            raise RuntimeError(f"Model load failed: {e}")

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
