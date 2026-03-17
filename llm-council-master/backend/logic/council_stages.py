from typing import List, Dict, Any, Tuple, Optional
from ..llm_providers import query_models_parallel, query_model
from ..config import COUNCIL_MODELS, CHAIRMAN_MODEL
from .council_utils import parse_ranking_from_text

async def stage1_collect_responses(
    user_query: str, 
    history: List[Dict[str, str]] = None,
    council_models: List[str] = COUNCIL_MODELS,
    temperature: Optional[float] = None,
    override_chains: Optional[Dict[str, List[str]]] = None,
    api_keys: Optional[Dict[str, Optional[str]]] = None,
) -> List[Dict[str, Any]]:
    """
    Stage 1: Collect individual responses from all council models.
    """
    messages = []
    if history:
        messages.extend(history)
    messages.append({"role": "user", "content": user_query})

    # Query all models in parallel
    responses = await query_models_parallel(
        council_models, 
        messages, 
        temperature=temperature,
        override_chains=override_chains,
        api_keys=api_keys,
    )

    # Format results
    stage1_results = []
    for model, response in responses.items():
        if response is not None:
            actual_model = response.get('model_id', model)
            stage1_results.append({
                "model": model,
                "actual_model": actual_model,
                "response": response.get('content', '')
            })

    return stage1_results


async def stage2_collect_rankings(
    user_query: str,
    stage1_results: List[Dict[str, Any]],
    history: List[Dict[str, str]] = None,
    council_models: List[str] = COUNCIL_MODELS,
    temperature: Optional[float] = None,
    override_chains: Optional[Dict[str, List[str]]] = None,
    api_keys: Optional[Dict[str, Optional[str]]] = None,
) -> Tuple[List[Dict[str, Any]], Dict[str, str]]:
    """
    Stage 2: Each model ranks the anonymized responses.
    """
    labels = [chr(65 + i) for i in range(len(stage1_results))]
    label_to_model = {
        f"Response {label}": result['model']
        for label, result in zip(labels, stage1_results)
    }
    responses_text = "\n\n".join([
        f"Response {label}:\n{result['response']}"
        for label, result in zip(labels, stage1_results)
    ])

    ranking_prompt = f"""You are evaluating different responses to the following question:

Question: {user_query}

Here are the responses from different models (anonymized):

{responses_text}

Your task:
1. First, evaluate each response individually. For each response, explain what it does well and what it does poorly.
2. Then, at the very end of your response, provide a final ranking.

IMPORTANT: Your final ranking MUST be formatted EXACTLY as follows:
- Start with the line "FINAL RANKING:" (all caps, with colon)
- Then list the responses from best to worst as a numbered list
- Each line should be: number, period, space, then ONLY the response label (e.g., "1. Response A")
- Do not add any other text or explanations in the ranking section

Example of the correct format for your ENTIRE response:

Response A provides good detail on X but misses Y...
Response B is accurate but lacks depth on Z...
Response C offers the most comprehensive answer...

FINAL RANKING:
1. Response C
2. Response A
3. Response B

Now provide your evaluation and ranking:"""

    messages = []
    if history:
        messages.extend(history)
    messages.append({"role": "user", "content": ranking_prompt})

    # Get rankings from all council models in parallel
    responses = await query_models_parallel(
        council_models, 
        messages, 
        temperature=temperature,
        override_chains=override_chains,
        api_keys=api_keys,
    )

    # Format results
    stage2_results = []
    for model, response in responses.items():
        if response is not None:
            full_text = response.get('content', '')
            parsed = parse_ranking_from_text(full_text)
            stage2_results.append({
                "model": model,
                "ranking": full_text,
                "parsed_ranking": parsed
            })

    return stage2_results, label_to_model


async def stage3_synthesize_final(
    user_query: str,
    stage1_results: List[Dict[str, Any]],
    stage2_results: List[Dict[str, Any]],
    history: List[Dict[str, str]] = None,
    chairman_model: str = CHAIRMAN_MODEL,
    temperature: Optional[float] = None,
    override_chains: Optional[Dict[str, List[str]]] = None,
    api_keys: Optional[Dict[str, Optional[str]]] = None,
    max_context_chars: int = 12000
) -> Dict[str, Any]:
    """
    Stage 3: Chairman synthesizes final response.
    """
    def truncate_text(text: str, max_chars: int) -> str:
        """Truncate text to max_chars, adding ellipsis if needed."""
        if len(text) <= max_chars:
            return text
        return text[:max_chars-3] + "..."
    
    # Calculate budget per response
    num_responses = len(stage1_results)
    num_rankings = len(stage2_results)
    
    # Allocate budget: 40% for stage1, 30% for stage2, 30% buffer for prompt
    stage1_budget = int(max_context_chars * 0.4)
    stage2_budget = int(max_context_chars * 0.3)
    
    per_response_chars = stage1_budget // max(num_responses, 1)
    per_ranking_chars = stage2_budget // max(num_rankings, 1)
    
    stage1_text = "\n\n".join([
        f"Model: {result['model']}\nResponse: {truncate_text(result['response'], per_response_chars)}"
        for result in stage1_results
    ])

    stage2_text = "\n\n".join([
        f"Model: {result['model']}\nRanking: {truncate_text(result['ranking'], per_ranking_chars)}"
        for result in stage2_results
    ])

    chairman_prompt = f"""You are the Chairman of an LLM Council. Multiple AI models have provided responses to a user's question, and then ranked each other's responses.

Original Question: {user_query}

STAGE 1 - Individual Responses:
{stage1_text}

STAGE 2 - Peer Rankings:
{stage2_text}

Your task as Chairman is to synthesize all of this information into a single, comprehensive, accurate answer to the user's original question. Consider:
- The individual responses and their insights
- The peer rankings and what they reveal about response quality
- Any patterns of agreement or disagreement

Provide a clear, well-reasoned final answer that represents the council's collective wisdom:"""

    messages = []
    if history:
        messages.extend(history)
    messages.append({"role": "user", "content": chairman_prompt})

    # Query the chairman model
    print(f"Stage 3: Querying chairman {chairman_model}...")
    response = await query_model(
        chairman_model, 
        messages, 
        timeout=120.0,
        temperature=temperature,
        override_chains=override_chains,
        api_keys=api_keys,
    )

    if response is None:
        # Fallback: use the longest Stage 1 response
        if stage1_results:
            best = max(stage1_results, key=lambda r: len(r.get('response', '')))
            return {
                "model": f"{chairman_model} (fallback to {best['model']})",
                "response": best.get('response', 'Error: Unable to generate final synthesis.')
            }
        return {
            "model": chairman_model,
            "response": "Error: Unable to generate final synthesis."
        }

    return {
        "model": chairman_model,
        "response": response.get('content', '')
    }
