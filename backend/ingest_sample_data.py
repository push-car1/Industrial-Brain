import os
import sys
import time
import httpx
import glob

API_BASE = "http://localhost:8000/api"

SAMPLE_DIR = "/app/data/sample_docs"


def wait_for_backend(max_retries=30):
    for i in range(max_retries):
        try:
            with httpx.Client(timeout=5) as client:
                r = client.get(f"{API_BASE}/health")
                if r.status_code == 200:
                    print("Backend is ready")
                    return True
        except Exception:
            pass
        print(f"Waiting for backend... ({i+1}/{max_retries})")
        time.sleep(5)
    return False


def ingest_files():
    if not os.path.exists(SAMPLE_DIR):
        print(f"Sample directory not found: {SAMPLE_DIR}")
        return

    files = glob.glob(os.path.join(SAMPLE_DIR, "*"))
    print(f"Found {len(files)} sample files to ingest")

    for file_path in sorted(files):
        filename = os.path.basename(file_path)
        print(f"Ingesting: {filename}...")

        try:
            with open(file_path, "rb") as f:
                files_data = {"file": (filename, f)}
                with httpx.Client(timeout=120) as client:
                    r = client.post(f"{API_BASE}/documents/upload", files=files_data)
                if r.status_code == 200:
                    result = r.json()
                    print(f"  OK: {result.get('message', '')}")
                else:
                    print(f"  FAIL: {r.status_code} - {r.text}")
        except Exception as e:
            print(f"  ERROR: {e}")

    print("\nSample data ingestion complete!")
    print("Access the app at http://localhost:8501")


if __name__ == "__main__":
    if wait_for_backend():
        ingest_files()
    else:
        print("Backend did not become ready. Skipping auto-ingest.")
        sys.exit(1)
