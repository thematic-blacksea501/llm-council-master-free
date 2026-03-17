from typing import List, Dict, Any

def get_message_history(conversation: Dict[str, Any]) -> List[Dict[str, str]]:
    """Convert conversation messages to a simple role/content history for LLMs."""
    history = []
    for msg in conversation.get("messages", []):
        if msg["role"] == "user":
            history.append({"role": "user", "content": msg["content"]})
        elif msg["role"] == "assistant" and "stage3" in msg:
            content = msg["stage3"].get("response", "")
            if content:
                history.append({"role": "assistant", "content": content})
    return history
