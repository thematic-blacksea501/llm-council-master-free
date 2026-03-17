import httpx
from typing import Any, Dict, List, Optional
from ..config import (
    OPENROUTER_API_KEY, 
    GOOGLE_API_KEY, 
    CEREBRAS_API_KEY, 
    OPENROUTER_API_URL, 
    GOOGLE_API_URL, 
    CEREBRAS_API_URL
)

def resolve_api_key(
    provider: str,
    api_keys: Optional[Dict[str, Optional[str]]] = None,
) -> Optional[str]:
    """Return a per-request API key, falling back to environment config."""
    request_keys = api_keys or {}
    provider_key_map = {
        "google": request_keys.get("google") or GOOGLE_API_KEY,
        "openrouter": request_keys.get("openrouter") or OPENROUTER_API_KEY,
        "cerebras": request_keys.get("cerebras") or CEREBRAS_API_KEY,
        "or": request_keys.get("openrouter") or OPENROUTER_API_KEY,
    }
    return provider_key_map.get(provider)


async def query_google(
    model: str,
    messages: List[Dict[str, str]],
    timeout: float = 20.0,
    temperature: Optional[float] = None,
    api_keys: Optional[Dict[str, Optional[str]]] = None,
) -> Optional[Dict[str, Any]]:
    """Query Google Gemini API directly."""
    api_key = resolve_api_key("google", api_keys)
    if not api_key:
        return None

    url = GOOGLE_API_URL.format(model=model)
    headers = {"Content-Type": "application/json"}
    params = {"key": api_key}
    
    contents = []
    for m in messages:
        role = "user" if m["role"] == "user" else "model"
        contents.append({"role": role, "parts": [{"text": m["content"]}]})
    
    payload = {"contents": contents}
    if temperature is not None:
        payload["generationConfig"] = {"temperature": temperature}
    
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(url, headers=headers, params=params, json=payload)
            if response.status_code == 429:
                print(f"Google API Rate Limit (429) for {model}")
                return None
            response.raise_for_status()
            data = response.json()
            
            if 'candidates' in data and len(data['candidates']) > 0:
                text = data['candidates'][0]['content']['parts'][0]['text']
                return {
                    'content': text,
                    'model_id': f"google/{model}"
                }
    except httpx.HTTPStatusError as e:
        print(f"Google API HTTP Error ({model}): {e.response.status_code} - {e.response.text[:100]}")
    except Exception as e:
        print(f"Google API Error ({model}): {e}")
    return None


async def query_openrouter(
    model: str,
    messages: List[Dict[str, str]],
    timeout: float = 30.0,
    temperature: Optional[float] = None,
    api_keys: Optional[Dict[str, Optional[str]]] = None,
) -> Optional[Dict[str, Any]]:
    """Query OpenRouter API."""
    api_key = resolve_api_key("openrouter", api_keys)
    if not api_key:
        return None

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/karpathy/llm-council",
        "X-Title": "LLM Council",
    }
    payload = {"model": model, "messages": messages}
    if temperature is not None:
        payload["temperature"] = temperature
        
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(OPENROUTER_API_URL, headers=headers, json=payload)
            if response.status_code == 429:
                print(f"OpenRouter Rate Limit (429) for {model}")
                return None
            response.raise_for_status()
            data = response.json()
            message = data['choices'][0]['message']
            return {
                'content': message.get('content'),
                'reasoning_details': message.get('reasoning_details'),
                'model_id': model
            }
    except httpx.HTTPStatusError as e:
        print(f"OpenRouter HTTP Error ({model}): {e.response.status_code} - {e.response.text[:100]}")
    except Exception as e:
        print(f"OpenRouter API Error ({model}): {e}")
    return None


async def query_cerebras(
    model: str,
    messages: List[Dict[str, str]],
    timeout: float = 30.0,
    temperature: Optional[float] = None,
    api_keys: Optional[Dict[str, Optional[str]]] = None,
) -> Optional[Dict[str, Any]]:
    """Query Cerebras API (OpenAI compatible)."""
    api_key = resolve_api_key("cerebras", api_keys)
    if not api_key:
        return None

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {"model": model, "messages": messages}
    if temperature is not None:
        payload["temperature"] = temperature
        
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(CEREBRAS_API_URL, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()
            message = data['choices'][0]['message']
            return {
                'content': message.get('content'),
                'model_id': f"cerebras/{model}"
            }
    except Exception as e:
        print(f"Cerebras API Error ({model}): {e}")
    return None
