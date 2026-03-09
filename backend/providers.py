"""Provider handling with team failover logic."""

import time
import httpx
import asyncio
from typing import List, Dict, Any, Optional, Tuple
from .config import (
    PROVIDER_CHAINS, 
    OPENROUTER_API_KEY, 
    GOOGLE_API_KEY, 
    CEREBRAS_API_KEY, 
    OPENROUTER_API_URL, 
    GOOGLE_API_URL, 
    CEREBRAS_API_URL
)

class ProviderTeam:
    def __init__(self, name: str, models: List[str]):
        self.name = name
        self.models = models
        # model_id -> timestamp until which it is exhausted
        self.exhausted_until = {model: 0 for model in models}

    def get_best_available_model(self) -> Optional[str]:
        now = time.time()
        for model in self.models:
            if self.exhausted_until[model] < now:
                return model
        # If all exhausted, find the one that expires soonest
        if self.models:
            return min(self.models, key=lambda m: self.exhausted_until[m])
        return None

    def mark_exhausted(self, model: str, duration: int = 300):
        """Mark model as dead/exhausted for a duration in seconds (default 5 min)."""
        self.exhausted_until[model] = time.time() + duration

# Global teams registry
TEAMS = {name: ProviderTeam(name, models) for name, models in PROVIDER_CHAINS.items()}

async def query_google(model: str, messages: List[Dict[str, str]], timeout: float = 20.0, temperature: Optional[float] = None) -> Optional[Dict[str, Any]]:
    """Query Google Gemini API directly."""
    url = GOOGLE_API_URL.format(model=model)
    headers = {"Content-Type": "application/json"}
    params = {"key": GOOGLE_API_KEY}
    
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

async def query_openrouter(model: str, messages: List[Dict[str, str]], timeout: float = 30.0, temperature: Optional[float] = None) -> Optional[Dict[str, Any]]:
    """Query OpenRouter API."""
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
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

async def query_cerebras(model: str, messages: List[Dict[str, str]], timeout: float = 30.0, temperature: Optional[float] = None) -> Optional[Dict[str, Any]]:
    """Query Cerebras API (OpenAI compatible)."""
    headers = {
        "Authorization": f"Bearer {CEREBRAS_API_KEY}",
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

async def _raw_query_provider(provider: str, model: str, messages: List[Dict[str, str]], temperature: Optional[float] = None, timeout: float = 20.0) -> Optional[Dict[str, Any]]:
    """Internal helper to route to the correct provider function."""
    if provider == "google":
        return await query_google(model, messages, timeout=timeout, temperature=temperature)
    elif provider == "openrouter":
        return await query_openrouter(model, messages, timeout=timeout, temperature=temperature)
    elif provider == "cerebras":
        return await query_cerebras(model, messages, timeout=timeout, temperature=temperature)
    elif provider == "or":
        return await query_openrouter(model, messages, timeout=timeout, temperature=temperature)
    return None

async def query_model_any(model_id: str, messages: List[Dict[str, str]], temperature: Optional[float] = None, timeout: float = 20.0) -> Optional[Dict[str, Any]]:
    """Routes a model ID and tries original name first, then an fixed alias if it fails."""
    if '/' not in model_id:
        return None
    
    provider, model = model_id.split('/', 1)
    
    # 1. Сначала пробуем РОДНОЕ название от пользователя
    result = await _raw_query_provider(provider, model, messages, temperature=temperature, timeout=timeout)
    if result:
        return result
        
    # 2. Если не ответило, пробуем применить техническую "заплатку"
    fixed_model = model
    if provider == "google":
        if "gemma" in model and not model.endswith("-it"):
            fixed_model = f"{model}-it"
            
    elif provider == "openrouter":
        if "gemma-3" in model and ":free" not in model:
            if not model.startswith("google/"): 
                fixed_model = f"google/{model}"
            if not fixed_model.endswith(":free"):
                fixed_model = f"{fixed_model}:free"
        elif "step-3.5" in model and not model.startswith("stepfun/"):
            fixed_model = f"stepfun/{model}"
        elif model.startswith("openrouter/"):
            fixed_model = model.replace("openrouter/", "")

    # Если название изменилось - пробуем второй раз
    if fixed_model != model:
        print(f"Original {provider}/{model} failed, trying fixed version: {provider}/{fixed_model}...")
        return await _raw_query_provider(provider, fixed_model, messages, temperature=temperature, timeout=timeout)
    
    return None

async def api_call_with_failover(
    team_name: str, 
    messages: List[Dict[str, str]], 
    temperature: Optional[float] = None,
    override_chains: Optional[Dict[str, List[str]]] = None,
    per_model_timeout: float = 45.0  # Balanced timeout for code generation
) -> Optional[Dict[str, Any]]:
    """Implements the failover cycle for a provider team with fast switching."""
    # Check if we have an override for this specific team/chain
    models = None
    if override_chains and team_name in override_chains:
        models = override_chains[team_name]
    
    team = None
    if models is None:
        team = TEAMS.get(team_name)
    else:
        # Create a temporary team for this request
        team = ProviderTeam(team_name, models)

    if not team:
        return await query_model_any(team_name, messages, temperature=temperature)
    
    for _ in range(len(team.models)):
        model_id = team.get_best_available_model()
        if not model_id:
            break
            
        # Fast timeout per model - if it fails, switch quickly
        result = await query_model_any(model_id, messages, temperature=temperature, timeout=per_model_timeout)
        if result:
            return result
        else:
            # Mark as exhausted for 60 seconds (shorter than before)
            team.mark_exhausted(model_id, duration=60)
            print(f"Team {team_name}: Model {model_id} failed, switching to next...")
    
    return None

async def query_model(
    model: str,
    messages: List[Dict[str, str]],
    timeout: float = 30.0,
    temperature: Optional[float] = None,
    override_chains: Optional[Dict[str, List[str]]] = None
) -> Optional[Dict[str, Any]]:
    """Main entry point for querying a 'model' (which can be a team or a direct ID)."""
    try:
        # Wrap everything in a timeout to ensure we don't hang forever
        return await asyncio.wait_for(
            api_call_with_failover(model, messages, temperature=temperature, override_chains=override_chains),
            timeout=timeout
        )
    except asyncio.TimeoutError:
        print(f"Timeout querying {model} after {timeout}s")
        return None
    except Exception as e:
        print(f"Error querying {model}: {e}")
        return None

async def query_models_parallel(
    models: List[str],
    messages: List[Dict[str, str]],
    temperature: Optional[float] = None,
    override_chains: Optional[Dict[str, List[str]]] = None
) -> Dict[str, Optional[Dict[str, Any]]]:
    """Query multiple models (teams) in parallel with extended timeout."""
    # Extended stage limit for slow models
    stage_timeout = 120.0  # Increased from 60s
    
    # Wrap coroutines in Tasks properly with longer timeout per model
    tasks = [
        asyncio.create_task(query_model(m, messages, timeout=90.0, temperature=temperature, override_chains=override_chains)) 
        for m in models
    ]
    
    if not tasks:
        return {}

    try:
        # Wait for all tasks but with a total timeout for the entire stage
        done, pending = await asyncio.wait(tasks, timeout=stage_timeout)
        
        # Cancel any that didn't finish
        for task in pending:
            task.cancel()
            try:
                await task  # Wait for cancellation to complete
            except asyncio.CancelledError:
                pass
            
        # Collect results
        results = []
        for task in tasks:
            if task in done:
                try:
                    result = task.result()
                    results.append(result)
                except asyncio.CancelledError:
                    results.append(None)
                except Exception as e:
                    print(f"Task result error: {e}")
                    results.append(None)
            else:
                results.append(None)
    except Exception as e:
        print(f"Parallel query collection error: {e}")
        results = [None] * len(models)
        
    return {model: result for model, result in zip(models, results)}
