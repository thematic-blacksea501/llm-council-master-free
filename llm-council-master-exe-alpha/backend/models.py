from pydantic import BaseModel
from typing import List, Dict, Any, Optional

class CreateConversationRequest(BaseModel):
    """Request to create a new conversation."""
    pass


class SendMessageRequest(BaseModel):
    """Request to send a message in a conversation."""
    content: str
    council_models: Optional[List[str]] = None
    chairman_model: Optional[str] = None
    temperature: Optional[float] = None
    override_chains: Optional[Dict[str, List[str]]] = None
    api_keys: Optional[Dict[str, Optional[str]]] = None
    force_russian: Optional[bool] = False
    system_prompt: Optional[str] = None


class ConversationMetadata(BaseModel):
    """Conversation metadata for list view."""
    id: str
    created_at: str
    title: str
    message_count: int


class Conversation(BaseModel):
    """Full conversation with all messages."""
    id: str
    created_at: str
    title: str
    messages: List[Dict[str, Any]]


class TitleUpdateModel(BaseModel):
    title: str
