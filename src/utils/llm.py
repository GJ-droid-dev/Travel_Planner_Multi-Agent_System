import json
from abc import ABC, abstractmethod
from typing import TypeVar, Type, Any
from pydantic import BaseModel
from tenacity import retry, wait_exponential, stop_after_attempt, retry_if_exception_type
from groq import AsyncGroq
from google import genai
from google.genai import types
import httpx

from src.config import settings

T = TypeVar('T', bound=BaseModel)

class LLMClient(ABC):
    @abstractmethod
    async def call(self, system_prompt: str, user_prompt: str, response_model: Type[T]) -> T:
        """Call the LLM and return a parsed Pydantic model."""
        pass

class GroqClient(LLMClient):
    def __init__(self):
        self.client = AsyncGroq(api_key=settings.groq_api_key.get_secret_value())
        self.model = settings.groq_model
        
    @retry(
        wait=wait_exponential(multiplier=1, min=2, max=10),
        stop=stop_after_attempt(3),
        retry=retry_if_exception_type(Exception),
        reraise=True
    )
    async def call(self, system_prompt: str, user_prompt: str, response_model: Type[T]) -> T:
        response = await self.client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            model=self.model,
            temperature=settings.llm_temperature,
            max_completion_tokens=settings.llm_max_tokens,
            response_format={"type": "json_object"}
        )
        # Groq returns a JSON string, we need to parse it into the Pydantic model
        content = response.choices[0].message.content
        if not content:
            raise ValueError("Empty response from Groq")
            
        return response_model.model_validate_json(content)

class GeminiClient(LLMClient):
    def __init__(self):
        # We need async support. google-genai provides AsyncClient
        self.client = genai.Client(
            api_key=settings.gemini_api_key.get_secret_value(),
            http_options={'api_version': 'v1alpha'} # Sometimes needed for structured outputs depending on the version
        )
        self.model = settings.gemini_model
        
    @retry(
        wait=wait_exponential(multiplier=1, min=2, max=10),
        stop=stop_after_attempt(3),
        retry=retry_if_exception_type(Exception),
        reraise=True
    )
    async def call(self, system_prompt: str, user_prompt: str, response_model: Type[T]) -> T:
        config = types.GenerateContentConfig(
            system_instruction=system_prompt,
            temperature=settings.llm_temperature,
            max_output_tokens=settings.llm_max_tokens,
            response_mime_type="application/json",
            response_schema=response_model,
        )
        
        response = await self.client.aio.models.generate_content(
            model=self.model,
            contents=user_prompt,
            config=config
        )
        
        if not response.text:
            raise ValueError("Empty response from Gemini")
            
        return response_model.model_validate_json(response.text)

def get_llm_client(provider: str) -> LLMClient:
    """Factory to get the right LLM client."""
    if provider.lower() == "groq":
        return GroqClient()
    elif provider.lower() == "gemini":
        return GeminiClient()
    else:
        raise ValueError(f"Unknown provider: {provider}")
