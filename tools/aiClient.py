from __future__ import annotations
import asyncio
from io import BytesIO
from typing import AsyncIterator, Literal, Optional, Type, TypeVar

from openai import AsyncOpenAI
import os
import httpx
from pydantic import BaseModel

OT = TypeVar("OT", bound=BaseModel)

class AIClient:
    _instance: AIClient = None  # type: ignore

    httpClient: httpx.AsyncClient

    openaiKey: str
    openaiClient: AsyncOpenAI

    stabilityKey: str

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(AIClient, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, "initialized"):
            self.httpClient = httpx.AsyncClient()

            self.openaiKey = os.environ.get("OPEN_AI_KEY", "")
            self.openaiClient = AsyncOpenAI(api_key=self.openaiKey)

            self.initialized = True

    async def chatCompletion(
        self,
        system: str,
        user: str,
        model: str = "gpt-4o-mini"
    ) -> str:
        messageThread = [{"role": "system", "content": system}, {"role": "user", "content": user}]
        
        response = await self.openaiClient.chat.completions.create(
            model=model,
            messages=messageThread, # type: ignore
        )

        result = response.choices[0].message.content
        return result or "FAILED"