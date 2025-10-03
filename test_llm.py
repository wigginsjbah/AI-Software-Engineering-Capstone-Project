#!/usr/bin/env python3
"""
Test script to verify LLM connection
"""

import asyncio
from openai import AsyncOpenAI
from config.settings import get_settings

async def test_llm_connection():
    """Test if LLM is working properly"""
    try:
        settings = get_settings()
        print(f"Using API key: {settings.OPENAI_API_KEY[:20]}...")
        
        client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        
        response = await client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "user", "content": "Hello, just testing the API connection. Please respond with 'API connection successful!'"}
            ],
            max_tokens=50
        )
        
        print("✅ LLM Response:", response.choices[0].message.content)
        return True
        
    except Exception as e:
        print("❌ LLM Connection Error:", str(e))
        return False

if __name__ == "__main__":
    asyncio.run(test_llm_connection())