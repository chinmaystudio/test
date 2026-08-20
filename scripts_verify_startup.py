import os
import sys
import time
import json
import subprocess
from urllib.request import urlopen
from urllib.error import URLError

def run_server():
    # Run uvicorn on a specific port
    env = os.environ.copy()
    env["MODEL_NAME"] = "buffalo_s"
    env["ONNX_PROVIDER"] = "CPUExecutionProvider"
    env["MEMORY_OPTIMIZATION"] = "true"
    
    process = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "api.main:app", "--host", "127.0.0.1", "--port", "8001"],
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    return process

def verify_startup():
    print("Starting API server with Render Free constraints...")
    server_process = run_server()
    
    # Wait for startup
    max_retries = 30
    health_url = "http://127.0.0.1:8001/health"
    
    for i in range(max_retries):
        try:
            time.sleep(1)
            with urlopen(health_url, timeout=2) as response:
                if response.status != 200:
                    continue
                data = json.loads(response.read().decode('utf-8'))
                print(f"\nHealth check passed! Status: {data['status']}")
                print(f"Loaded Model: {data['model']}")
                print(f"ONNX Provider: {data['provider']}")
                print(f"Memory Optimization: {data['memory_optimization']}")
                
                assert data['status'] == "healthy", "API reported unhealthy status"
                assert data['model'] == "buffalo_s", f"Expected buffalo_s, got {data['model']}"
                assert "CPUExecutionProvider" in data['provider'], "Expected CPUExecutionProvider"
                
                print("\nAll startup verification checks passed successfully.")
                server_process.terminate()
                return True
        except (URLError, ConnectionError):
            print(".", end="", flush=True)
        except Exception as e:
            print(f"\nError during health check: {e}")
            break
            
    print("\nFailed to verify startup within timeout.")
    server_process.terminate()
    stdout, stderr = server_process.communicate()
    print("--- STDOUT ---")
    print(stdout)
    print("--- STDERR ---")
    print(stderr)
    return False

if __name__ == "__main__":
    success = verify_startup()
    sys.exit(0 if success else 1)
