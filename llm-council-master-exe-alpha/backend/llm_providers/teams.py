import time
from typing import List, Optional

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
