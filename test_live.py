import asyncio
from pydantic import BaseModel
from src.utils.llm import get_llm_client

class TestResponse(BaseModel):
    greeting: str
    number: int

async def test_llms():
    print("Testing Gemini Client...")
    gemini = get_llm_client("gemini")
    gemini_resp = await gemini.call(
        system_prompt="You are a helpful assistant that returns JSON.",
        user_prompt="Say hello and pick a number between 1 and 10.",
        response_model=TestResponse
    )
    print("Gemini Response:", gemini_resp.model_dump())

    print("\nTesting Groq Client...")
    groq = get_llm_client("groq")
    groq_resp = await groq.call(
        system_prompt="You are a helpful assistant that returns JSON.",
        user_prompt="Say hi and pick a number between 1 and 10.",
        response_model=TestResponse
    )
    print("Groq Response:", groq_resp.model_dump())

if __name__ == "__main__":
    asyncio.run(test_llms())
