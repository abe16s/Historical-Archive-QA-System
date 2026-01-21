from typing import List, Dict, Optional, Any
import google.generativeai as genai
from abc import ABC, abstractmethod

from app.core.config import settings


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
