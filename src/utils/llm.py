import json
from abc import ABC, abstractmethod
from typing import TypeVar, Type, Any
from pydantic import BaseModel
from tenacity import retry, wait_exponential_jitter, stop_after_attempt, retry_if_exception_type, RetryCallState
import groq
from groq import AsyncGroq
from google import genai
from google.genai import types
import httpx

from src.config import settings
from src.utils.logger import get_logger

logger = get_logger("llm")

T = TypeVar('T', bound=BaseModel)

class TransientLLMError(Exception):
    """Exception for HTTP 429, 500, 502, 503, 504 and network errors."""
    pass

def log_retry_attempt(retry_state: RetryCallState):
    if retry_state.attempt_number > 1:
        logger.warning(
            "llm_retry",
            attempt=retry_state.attempt_number,
            exception=str(retry_state.outcome.exception()) if retry_state.outcome else None
        )

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
        wait=wait_exponential_jitter(initial=2, max=12),
        stop=stop_after_attempt(3),
        retry=retry_if_exception_type(TransientLLMError),
        reraise=True,
        before_sleep=log_retry_attempt
    )
    async def call(self, system_prompt: str, user_prompt: str, response_model: Type[T]) -> T:
        try:
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
        except (groq.APIConnectionError, groq.RateLimitError, groq.InternalServerError, httpx.RequestError) as e:
            raise TransientLLMError(f"Transient Groq error: {str(e)}") from e
        except groq.APIStatusError as e:
            if e.status_code in (429, 500, 502, 503, 504):
                raise TransientLLMError(f"Transient Groq HTTP {e.status_code}: {str(e)}") from e
            raise # Other errors like 400, 401, 404 should not be retried

class GeminiClient(LLMClient):
    def __init__(self):
        # We need async support. google-genai provides AsyncClient
        self.client = genai.Client(
            api_key=settings.gemini_api_key.get_secret_value(),
            http_options={'api_version': 'v1alpha'} # Sometimes needed for structured outputs depending on the version
        )
        self.model = settings.gemini_model
        
    @retry(
        wait=wait_exponential_jitter(initial=2, max=12),
        stop=stop_after_attempt(3),
        retry=retry_if_exception_type(TransientLLMError),
        reraise=True,
        before_sleep=log_retry_attempt
    )
    async def call(self, system_prompt: str, user_prompt: str, response_model: Type[T]) -> T:
        config = types.GenerateContentConfig(
            system_instruction=system_prompt,
            temperature=settings.llm_temperature,
            max_output_tokens=settings.llm_max_tokens,
            response_mime_type="application/json",
            response_schema=response_model,
        )
        
        try:
            response = await self.client.aio.models.generate_content(
                model=self.model,
                contents=user_prompt,
                config=config
            )
            
            if not response.text:
                raise ValueError("Empty response from Gemini")
                
            return response_model.model_validate_json(response.text)
        except google.genai.errors.APIError as e:
            if e.code in (429, 500, 502, 503, 504):
                raise TransientLLMError(f"Transient Gemini HTTP {e.code}: {str(e)}") from e
            raise
        except (httpx.RequestError) as e:
            raise TransientLLMError(f"Transient Gemini network error: {str(e)}") from e

def get_llm_client(provider: str) -> LLMClient:
    """Factory to get the right LLM client."""
    if provider.lower() == "groq":
        return GroqClient()
    elif provider.lower() == "gemini":
        return GeminiClient()
    else:
        raise ValueError(f"Unknown provider: {provider}")
