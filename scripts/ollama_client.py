#!/usr/bin/env python3
"""
Ollama client for local LLM integration.
Communicates with local Ollama instance via HTTP.
"""

import json
import urllib.request
import urllib.error
from typing import Optional

OLLAMA_BASE_URL = "http://localhost:11434"
DEFAULT_MODEL = "llama3.1"  # Local model
REQUEST_TIMEOUT = 300  # 5 minutes for long documents


def generate(
    prompt: str,
    system: Optional[str] = None,
    model: str = DEFAULT_MODEL,
    temperature: float = 0.1
) -> str:
    """
    Generate text using local Ollama instance.
    
    Args:
        prompt: User message/prompt
        system: System prompt for context
        model: Model name (must be available locally)
        temperature: Creativity level (0.1 = deterministic for docs)
    
    Returns:
        Generated text response
        
    Raises:
        ConnectionError: If Ollama server is unreachable
        json.JSONDecodeError: If response is malformed
    """
    
    # Build messages list
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})
    
    # Prepare request
    payload = {
        "model": model,
        "stream": False,
        "messages": messages,
        "options": {
            "temperature": temperature,
            "num_ctx": 8192,  # Context window
            "top_p": 0.95,
            "top_k": 40,
        }
    }
    
    try:
        # Send request to Ollama
        req = urllib.request.Request(
            f"{OLLAMA_BASE_URL}/api/chat",
            data=json.dumps(payload).encode('utf-8'),
            headers={"Content-Type": "application/json"}
        )
        
        with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT) as response:
            result = json.loads(response.read().decode('utf-8'))
            return result["message"]["content"]
        
    except urllib.error.URLError as e:
        if "Connection refused" in str(e) or "nodename nor servname provided" in str(e):
            raise ConnectionError(
                f"Cannot connect to Ollama at {OLLAMA_BASE_URL}. "
                "Make sure Ollama is running: ollama serve"
            )
        raise ConnectionError(f"Ollama connection error: {e}")
    except urllib.error.HTTPError as e:
        raise ConnectionError(f"Ollama HTTP error: {e.code} {e.reason}")
    except (TimeoutError, socket.timeout):
        raise TimeoutError(
            f"Ollama request timed out after {REQUEST_TIMEOUT}s. "
            "Try shortening the prompt or increasing timeout."
        )


def check_connection(model: str = DEFAULT_MODEL) -> bool:
    """
    Check if Ollama is running and model is available.
    
    Returns:
        True if connection successful and model exists
    """
    try:
        with urllib.request.urlopen(
            f"{OLLAMA_BASE_URL}/api/tags",
            timeout=5.0
        ) as response:
            data = json.loads(response.read().decode('utf-8'))
            models = data.get("models", [])
            model_names = [m["name"] for m in models]
            
            # Check if requested model is available
            available = any(model in m for m in model_names)
            
            if not available:
                print(f"⚠️  Model '{model}' not found in Ollama")
                print(f"   Available models: {', '.join(model_names)}")
                return False
            
            return True
        
    except urllib.error.URLError:
        print(f"❌ Cannot reach Ollama at {OLLAMA_BASE_URL}")
        print("   Start Ollama with: ollama serve")
        return False
    except Exception as e:
        print(f"❌ Error checking Ollama: {e}")
        return False


if __name__ == "__main__":
    # Test connection
    if check_connection():
        print("✅ Ollama connection OK")
        
        # Test generation
        response = generate(
            prompt="Explain Power BI in one sentence.",
            system="You are a BI assistant.",
            temperature=0.5
        )
        print(f"\n📝 Response:\n{response}")
    else:
        print("❌ Ollama not available")
