import pytest
from pydantic import BaseModel
from src.utils.llm import get_llm_client, GroqClient, GeminiClient

class DummyResponse(BaseModel):
    message: str
    number: int

@pytest.mark.asyncio
async def test_get_llm_client():
    groq_client = get_llm_client("groq")
    assert isinstance(groq_client, GroqClient)
    
    gemini_client = get_llm_client("gemini")
    assert isinstance(gemini_client, GeminiClient)
    
    with pytest.raises(ValueError):
        get_llm_client("unknown")

# Note: We won't test the actual call() methods here to avoid hitting the APIs during basic testing, 
# but they should be tested in E2E tests or with mocked responses.
