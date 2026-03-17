"""Provider handling with team failover logic."""

import asyncio
from typing import Any, Dict, List, Optional

from ..config import PROVIDER_CHAINS
from .teams import ProviderTeam
from .clients import query_google, query_openrouter, query_cerebras

# Global teams registry
TEAMS = {name: ProviderTeam(name, models) for name, models in PROVIDER_CHAINS.items()}


async def _raw_query_provider(
    provider: str,
    model: str,
    messages: List[Dict[str, str]],
    temperature: Optional[float] = None,
    timeout: float = 20.0,
    api_keys: Optional[Dict[str, Optional[str]]] = None,
) -> Optional[Dict[str, Any]]:
    """Internal helper to route to the correct provider function."""
    if provider == "google":
        return await query_google(
            model,
            messages,
            timeout=timeout,
            temperature=temperature,
            api_keys=api_keys,
        )
    elif provider == "openrouter":
        return await query_openrouter(
            model,
            messages,
            timeout=timeout,
            temperature=temperature,
            api_keys=api_keys,
        )
    elif provider == "cerebras":
        return await query_cerebras(
            model,
            messages,
            timeout=timeout,
            temperature=temperature,
            api_keys=api_keys,
        )
    elif provider == "or":
        return await query_openrouter(
            model,
            messages,
            timeout=timeout,
            temperature=temperature,
            api_keys=api_keys,
        )
    return None


async def query_model_any(
    model_id: str,
    messages: List[Dict[str, str]],
    temperature: Optional[float] = None,
    timeout: float = 20.0,
    api_keys: Optional[Dict[str, Optional[str]]] = None,
) -> Optional[Dict[str, Any]]:
    """Routes a model ID and tries original name first, then an fixed alias if it fails."""
    if '/' not in model_id:
        return None
    
    provider, model = model_id.split('/', 1)
    
    # 1. Сначала пробуем РОДНОЕ название от пользователя
    result = await _raw_query_provider(
        provider,
        model,
        messages,
        temperature=temperature,
        timeout=timeout,
        api_keys=api_keys,
    )
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
        return await _raw_query_provider(
            provider,
            fixed_model,
            messages,
            temperature=temperature,
            timeout=timeout,
            api_keys=api_keys,
        )
    
    return None


async def api_call_with_failover(
    team_name: str, 
    messages: List[Dict[str, str]], 
    temperature: Optional[float] = None,
    override_chains: Optional[Dict[str, List[str]]] = None,
    api_keys: Optional[Dict[str, Optional[str]]] = None,
    per_model_timeout: float = 45.0
) -> Optional[Dict[str, Any]]:
    """Implements the failover cycle for a provider team."""
    models = None
    if override_chains and team_name in override_chains:
        models = override_chains[team_name]
    
    team = None
    if models is None:
        team = TEAMS.get(team_name)
    else:
        team = ProviderTeam(team_name, models)

    if not team:
        return await query_model_any(
            team_name,
            messages,
            temperature=temperature,
            api_keys=api_keys,
        )
    
    for _ in range(len(team.models)):
        model_id = team.get_best_available_model()
        if not model_id:
            break
            
        print(f"Team {team_name}: Trying {model_id}...")
        result = await query_model_any(
            model_id,
            messages,
            temperature=temperature,
            timeout=25.0, # Уменьшил таймаут для ускорения переключения
            api_keys=api_keys,
        )
        if result:
            print(f"Team {team_name}: {model_id} success!")
            return result
        else:
            team.mark_exhausted(model_id, duration=60)
            print(f"Team {team_name}: ERROR - Model {model_id} failed or timed out, switching...")
    
    return None


async def query_model(
    model: str,
    messages: List[Dict[str, str]],
    timeout: float = 30.0,
    temperature: Optional[float] = None,
    override_chains: Optional[Dict[str, List[str]]] = None,
    api_keys: Optional[Dict[str, Optional[str]]] = None,
) -> Optional[Dict[str, Any]]:
    """Main entry point for querying a 'model' (team or direct ID)."""
    try:
        return await asyncio.wait_for(
            api_call_with_failover(
                model,
                messages,
                temperature=temperature,
                override_chains=override_chains,
                api_keys=api_keys,
            ),
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
    override_chains: Optional[Dict[str, List[str]]] = None,
    api_keys: Optional[Dict[str, Optional[str]]] = None,
) -> Dict[str, Optional[Dict[str, Any]]]:
    """Query multiple models (teams) in parallel."""
    stage_timeout = 120.0
    
    tasks = [
        asyncio.create_task(
            query_model(
                m,
                messages,
                timeout=90.0,
                temperature=temperature,
                override_chains=override_chains,
                api_keys=api_keys,
            )
        )
        for m in models
    ]
    
    if not tasks:
        return {}

    try:
        done, pending = await asyncio.wait(tasks, timeout=stage_timeout)
        
        for task in pending:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
            
        results = []
        for task in tasks:
            if task in done:
                try:
                    result = task.result()
                    results.append(result)
                except Exception as e:
                    print(f"Task result error: {e}")
                    results.append(None)
            else:
                results.append(None)
    except Exception as e:
        print(f"Parallel query collection error: {e}")
        results = [None] * len(models)
        
    return {model: result for model, result in zip(models, results)}
