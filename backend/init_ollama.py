import os
import time
import httpx

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://ollama:11434")
MODEL = os.getenv("LLM_MODEL", "mistral:7b")

def pull_model():
    url = f"{OLLAMA_BASE_URL}/api/pull"
    payload = {"name": MODEL}
    for attempt in range(30):
        try:
            with httpx.Client(timeout=300) as client:
                response = client.post(url, json=payload)
                if response.status_code == 200:
                    print(f"Successfully pulled model: {MODEL}")
                    return True
                else:
                    print(f"Pull returned {response.status_code}: {response.text}")
        except Exception as e:
            print(f"Attempt {attempt + 1}/30: Waiting for Ollama... ({e})")
        time.sleep(5)
    print(f"Failed to pull model {MODEL} after 30 attempts")
    return False

if __name__ == "__main__":
    time.sleep(10)
    pull_model()
