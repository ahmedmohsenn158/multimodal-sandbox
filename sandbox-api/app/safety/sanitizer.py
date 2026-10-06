import re
from .rules import BLOCKED_TERMS

class PromptSanitizer:
    @staticmethod
    def normalize(prompt: str) -> str:
        # Lowercase
        normalized = prompt.lower()
        # Remove repeated characters
        normalized = re.sub(r'(.)\1{4,}', r'\1', normalized)
        # Simplify whitespace
        normalized = re.sub(r'\s+', ' ', normalized).strip()
        return normalized

    @staticmethod
    def is_allowed(prompt: str) -> dict:
        normalized = PromptSanitizer.normalize(prompt)
        
        for term in BLOCKED_TERMS:
            if term in normalized:
                return {
                    "allowed": False,
                    "category": "policy_violation",
                    "reason": f"Prompt contains blocked term."
                }
                
        return {
            "allowed": True,
            "category": "safe",
            "reason": None
        }
