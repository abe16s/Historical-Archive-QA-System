from typing import List, Dict, Optional, Any
import google.generativeai as genai
from abc import ABC, abstractmethod
import re

from app.core.config import settings


class QuotaExceededError(Exception):
    """Custom exception for API quota/rate limit errors."""
    def __init__(self, message: str, retry_after: Optional[float] = None, quota_limit: Optional[int] = None):
        self.message = message
        self.retry_after = retry_after
        self.quota_limit = quota_limit
        super().__init__(self.message)


class LLMClient(ABC):
    """Abstract base class for LLM clients."""
    
    def __init__(self, temperature: float = 0.7):
        self.temperature = temperature
    
    @abstractmethod
    def invoke(self, messages: List[Dict[str, str]]) -> Any:
        """Invoke the LLM with messages and return a response object with .content attribute."""
        pass


class GeminiClient(LLMClient):
    """Google Gemini LLM client using direct API."""
    
    def __init__(self, model_name: str, api_key: str, temperature: float = 0.7):
        super().__init__(temperature)
        genai.configure(api_key=api_key)
        self.model_name = model_name
        self.model = genai.GenerativeModel(model_name)
    
    def invoke(self, messages: List[Dict[str, str]]) -> Any:
        """Invoke Gemini with messages."""
        system_instruction = None
        conversation_messages = []
        
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            
            if role == "system":
                system_instruction = content
            elif role == "human" or role == "user":
                conversation_messages.append({"role": "user", "parts": [content]})
            elif role == "ai" or role == "assistant":
                conversation_messages.append({"role": "model", "parts": [content]})
        
        if system_instruction and conversation_messages:
            first_user_msg = conversation_messages[0]
            if first_user_msg["role"] == "user":
                first_user_msg["parts"][0] = f"{system_instruction}\n\n{first_user_msg['parts'][0]}"
        
        history = conversation_messages[:-1] if len(conversation_messages) > 1 else []
        current_query = conversation_messages[-1]["parts"][0] if conversation_messages else ""
        
        try:
            if history:
                chat = self.model.start_chat(history=history)
                response = chat.send_message(
                    current_query,
                    generation_config=genai.types.GenerationConfig(temperature=self.temperature)
                )
            else:
                response = self.model.generate_content(
                    current_query,
                    generation_config=genai.types.GenerationConfig(temperature=self.temperature)
                )
            
            class Response:
                def __init__(self, text: str):
                    self.content = text
            
            return Response(response.text)
        except Exception as e:
            error_str = str(e)
            error_repr = repr(e)
            
            is_quota_error = (
                "429" in error_str or 
                "quota" in error_str.lower() or 
                "rate limit" in error_str.lower() or
                "ResourceExhausted" in error_repr or
                "exceeded" in error_str.lower()
            )
            
            if is_quota_error:
                retry_after = None
                retry_patterns = [
                    r'retry.*?(\d+\.?\d*)\s*s[ec]',
                    r'retry_delay.*?seconds[:\s]+(\d+)',
                    r'Please retry in (\d+\.?\d*)\s*s',
                ]
                for pattern in retry_patterns:
                    retry_match = re.search(pattern, error_str, re.IGNORECASE)
                    if retry_match:
                        try:
                            retry_after = float(retry_match.group(1))
                            break
                        except (ValueError, IndexError):
                            continue
                
                quota_limit = None
                limit_patterns = [
                    r'limit[:\s]+(\d+)',
                    r'quota.*?limit[:\s]+(\d+)',
                    r'limit of (\d+)',
                ]
                for pattern in limit_patterns:
                    limit_match = re.search(pattern, error_str, re.IGNORECASE)
                    if limit_match:
                        try:
                            quota_limit = int(limit_match.group(1))
                            break
                        except (ValueError, IndexError):
                            continue
                
                if quota_limit:
                    message = f"API quota exceeded. You've reached the daily limit of {quota_limit} requests."
                else:
                    message = "API quota exceeded. You've reached the daily request limit."
                
                if retry_after:
                    minutes = int(retry_after // 60)
                    seconds = int(retry_after % 60)
                    if minutes > 0:
                        message += f" Please try again in {minutes} minute{'s' if minutes > 1 else ''}."
                    elif seconds > 0:
                        message += f" Please try again in {seconds} second{'s' if seconds > 1 else ''}."
                    else:
                        message += " Please try again in a few moments."
                else:
                    message += " Please try again later or check your API plan and billing details."
                
                raise QuotaExceededError(message, retry_after=retry_after, quota_limit=quota_limit)
            raise


def initialize_llm(provider: Optional[str] = None, api_key: Optional[str] = None) -> LLMClient:
    """Initialize the Gemini LLM client using direct API calls."""
    provider = provider or settings.LLM_PROVIDER.lower()

    if provider != "gemini":
        raise ValueError(f"Only Gemini is supported. Current provider: {provider}. Please set LLM_PROVIDER=gemini")

    api_key = api_key or settings.GEMINI_API_KEY
    if not api_key:
        raise ValueError(
            "GEMINI_API_KEY environment variable is required. "
            "Get your API key from https://makersuite.google.com/app/apikey"
        )

    model_name = settings.GEMINI_MODEL
    if model_name.startswith("models/"):
        model_name = model_name.replace("models/", "")

    try:
        return GeminiClient(
            model_name=model_name,
            api_key=api_key,
            temperature=settings.LLM_TEMPERATURE,
        )
    except Exception as exc:
        fallback_models = ["gemini-1.5-flash-latest", "gemini-pro", "gemini-1.5-pro"]
        error_msg = str(exc)
        if "not found" in error_msg.lower() or "not supported" in error_msg.lower():
            for fallback in fallback_models:
                if fallback != model_name:
                    try:
                        print(f"Trying fallback model: {fallback}")
                        return GeminiClient(
                            model_name=fallback,
                            api_key=api_key,
                            temperature=settings.LLM_TEMPERATURE,
                        )
                    except Exception:
                        continue
            raise ValueError(
                f"Model '{model_name}' not available. "
                f"Tried fallbacks: {', '.join(fallback_models)}. "
                f"Please set GEMINI_MODEL to a valid model name. "
                f"Original error: {error_msg}"
            )
        raise
