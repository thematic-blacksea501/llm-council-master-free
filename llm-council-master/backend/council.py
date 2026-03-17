from typing import List, Dict, Any, Tuple, Optional
from .llm_providers import query_model
from .config import COUNCIL_MODELS, CHAIRMAN_MODEL
from .logic.council_utils import calculate_aggregate_rankings, parse_ranking_from_text
from .logic.council_stages import (
    stage1_collect_responses,
    stage2_collect_rankings,
    stage3_synthesize_final
)

# Re-exporting for backward compatibility if needed, 
# although we updated imports in routes
__all__ = [
    "stage1_collect_responses",
    "stage2_collect_rankings",
    "stage3_synthesize_final",
    "calculate_aggregate_rankings",
    "parse_ranking_from_text",
    "generate_conversation_title",
    "run_full_council"
]


async def generate_conversation_title(
    user_query: str,
    api_keys: Optional[Dict[str, Optional[str]]] = None,
) -> str:
    """
    Generate a short title for a conversation based on the first user message.
    """
    # Quick cleanup of query for prompt
    clean_query = user_query[:200].replace('\n', ' ')
    
    title_prompt = f"""Придумай очень короткое название (3-5 слов максимум) для чата, который начинается с этого вопроса. 
Название должно быть кратким и описывать суть. Не используй кавычки.
Отвечай ТОЛЬКО названием, больше ничего не пиши.

Вопрос: {clean_query}

Название:"""

    messages = [{"role": "user", "content": title_prompt}]

    try:
        # Use a reliable fast model
        response = await query_model(
            "google/gemini-2.5-flash",
            messages,
            timeout=10.0,
            api_keys=api_keys,
        )
        
        if response and response.get('content'):
            title = response['content'].strip().strip('"\'*')
            if title and len(title) > 2:
                # Truncate if too long
                if len(title) > 50:
                    title = title[:47] + "..."
                return title
    except Exception as e:
        print(f"Title generation failed: {e}")

    # Fallback to the first words of the query
    words = user_query.split()
    fallback = " ".join(words[:5])
    if len(fallback) > 40:
        fallback = fallback[:37] + "..."
    return fallback or "Новый чат"


async def run_full_council(
    user_query: str,
    history: List[Dict[str, str]] = None,
    council_models: List[str] = COUNCIL_MODELS,
    chairman_model: str = CHAIRMAN_MODEL,
    temperature: Optional[float] = None,
    override_chains: Optional[Dict[str, List[str]]] = None,
    api_keys: Optional[Dict[str, Optional[str]]] = None,
) -> Tuple[List, List, Dict, Dict]:
    """
    Run the complete 3-stage council process.
    """
    # Stage 1: Collect individual responses
    stage1_results = await stage1_collect_responses(
        user_query, 
        history=history,
        council_models=council_models, 
        temperature=temperature,
        override_chains=override_chains,
        api_keys=api_keys,
    )

    # If no models responded successfully, return error
    if not stage1_results:
        return [], [], {
            "model": "error",
            "response": "All models failed to respond. Please try again."
        }, {}

    # Stage 2: Collect rankings
    stage2_results, label_to_model = await stage2_collect_rankings(
        user_query, 
        stage1_results, 
        history=history,
        council_models=council_models,
        temperature=temperature,
        override_chains=override_chains,
        api_keys=api_keys,
    )

    # Calculate aggregate rankings
    aggregate_rankings = calculate_aggregate_rankings(stage2_results, label_to_model)

    # Stage 3: Synthesize final answer
    stage3_result = await stage3_synthesize_final(
        user_query,
        stage1_results,
        stage2_results,
        history=history,
        chairman_model=chairman_model,
        temperature=temperature,
        override_chains=override_chains,
        api_keys=api_keys,
    )

    # Prepare metadata
    metadata = {
        "label_to_model": label_to_model,
        "aggregate_rankings": aggregate_rankings
    }

    return stage1_results, stage2_results, stage3_result, metadata
