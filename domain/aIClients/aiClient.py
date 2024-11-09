from __future__ import annotations
import asyncio
from enum import Enum
import os
import time
from typing import Literal, Optional, Type, TypeVar, Union

from openai import AsyncOpenAI
import httpx
from pydantic import BaseModel

from domain.aIClients.aiMessage import AIMessage
from domain.aws.s3client import S3Client
from domain.domainError.domainError import DomainError
from domain.logging.logger import Logger
from domain.option.option import Option
from domain.utility.errorHandling import serviceErrorHandling

OT = TypeVar("OT", bound=Union[str, BaseModel])


class TextGenerationModel(str, Enum):
    GPT4o = "gpt-4o-2024-08-06"
    GPT4oMini = "gpt-4o-mini"
    o1Mini = "o1-mini"
    o1 = "o1-preview"

INPUT_COST = {
    TextGenerationModel.GPT4o: 2.50,
    TextGenerationModel.GPT4oMini: 0.15,
    TextGenerationModel.o1Mini: 3.00,
    TextGenerationModel.o1: 15.00
}

CACHED_COST = {
    TextGenerationModel.GPT4o: 1.25,
    TextGenerationModel.GPT4oMini: 0.075,
    TextGenerationModel.o1Mini: 1.50,
    TextGenerationModel.o1: 7.50
}

OUTPUT_COST = {
    TextGenerationModel.GPT4o: 10.00,
    TextGenerationModel.GPT4oMini: 0.60,
    TextGenerationModel.o1Mini: 12.00,
    TextGenerationModel.o1: 60.00
}

class AIClient:
    _instance: AIClient = None  # type: ignore

    httpClient: httpx.AsyncClient

    openaiKey: str
    openaiClient: AsyncOpenAI

    bflKey: str

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(AIClient, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, "initialized"):
            self.httpClient = httpx.AsyncClient()

            self.openaiKey = os.environ.get("OPEN_AI_KEY", "")
            self.openaiClient = AsyncOpenAI(api_key=self.openaiKey)

            self.bflKey = os.environ.get("BFL_KEY", "")

            self.initialized = True

    @serviceErrorHandling
    async def generateImages(self, prompt: str, ratio: str, n=1) -> Option[list[str]]:
        width, height = 1024, 1024
        if ratio == "16:9":
            width, height = 1440, 800
        elif ratio == "9:16":
            width, height = 800, 1440

        startTime = time.time()

        startTasks = [
            self.httpClient.post(
                "https://api.bfl.ml/v1/flux-pro-1.1",
                headers={
                    "accept": "application/json",
                    "x-key": self.bflKey,
                    "Content-Type": "application/json",
                },
                json={
                    "prompt": prompt,
                    "width": width,
                    "height": height,
                    "safety_tolerance": 2,
                },
            )
            for _ in range(n)
        ]
        completedRequests = await asyncio.gather(*startTasks)
        requestIds = [request.json()["id"] for request in completedRequests]

        # Maximum 80 attempts, i.e. 40 seconds
        ogImageUrls = []
        for _ in range(80):
            await asyncio.sleep(0.5)
            getTasks = [
                self.httpClient.get(
                    "https://api.bfl.ml/v1/get_result",
                    headers={
                        "accept": "application/json",
                        "x-key": self.bflKey,
                    },
                    params={
                        "id": rid,
                    },
                )
                for rid in requestIds
            ]
            results = await asyncio.gather(*getTasks)

            ridsToRemove = []
            for result, rid in zip(results, requestIds):
                resultData = result.json()
                if resultData["status"] == "Ready":
                    output = resultData["result"]["sample"]

                    if isinstance(output, list):
                        ogImageUrls.append(output[0])
                    else:
                        ogImageUrls.append(output)

                    ridsToRemove.append(rid)

            requestIds = [rid for rid in requestIds if rid not in ridsToRemove]
            if not requestIds:
                break
        
        totalTime = time.time() - startTime
        Logger.info(
            f"Generated {len(ogImageUrls)} images using Flux Pro 1.1 in {round(totalTime, 3)} seconds.",
            {"time": totalTime},
        )

        reuploadStartTime = time.time()
        s3client = S3Client()
        reuploadTasks = [s3client.reuploadImage(im) for im in ogImageUrls]
        imageUrlOptionals = await asyncio.gather(*reuploadTasks)
        imageUrls: list[str] = [
            x.value for x in imageUrlOptionals if x.value is not None
        ]
        totalReuploadTime = time.time() - reuploadStartTime
        Logger.info(
            f"Reuploaded {len(ogImageUrls)} images in {round(totalReuploadTime, 3)} seconds.",
            {"time": totalReuploadTime},
        )

        return Option(imageUrls)

    @serviceErrorHandling
    async def isSafe(self, inputText: str) -> bool:
        response = await self.openaiClient.moderations.create(input=inputText)
        return not response.results[0].flagged

    @serviceErrorHandling
    async def generateText(
        self,
        system: str,
        messages: list[AIMessage],
        model: Union[TextGenerationModel, str] = TextGenerationModel.GPT4oMini,
        temperature: Optional[float] = None,
        maxTokens: Optional[int] = None,
        responseType: Type[OT] = str,
    ) -> Option[OT]:
        messageThread = [{"role": "system", "content": system}] + [
            m.oai() for m in messages
        ]

        safetyChecksTasks = [
            self.isSafe(m.get("content", "")) for m in messageThread if "content" in m
        ]
        safetyChecks: list[bool] = await asyncio.gather(*safetyChecksTasks)
        if any((not safe for safe in safetyChecks)):
            return Option.Error(
                DomainError(
                    "AIClient-ChatCompletion-E02",
                    "Completion request was flagged for inappropriate content.",
                    status=400,
                )
            )

        if responseType is str:
            response = await self.openaiClient.chat.completions.create(
                model=model,
                messages=messageThread,  # type: ignore
                temperature=temperature,
                max_tokens=maxTokens,
            )
            messageChoice = response.choices[0]
            result = messageChoice.message.content # type: ignore
        else:
            response = await self.openaiClient.beta.chat.completions.parse(
                model=model,
                messages=messageThread,  # type: ignore
                response_format=responseType,
                temperature=temperature,
                max_tokens=maxTokens,
            )
            messageChoice = response.choices[0]
            result = messageChoice.message.parsed

        if response.usage:
            cachedTokens = 0
            if ptd := response.usage.prompt_tokens_details:
                cachedTokens = ptd.cached_tokens or 0

            inputTokens = response.usage.prompt_tokens - cachedTokens
            outputTokens = response.usage.completion_tokens

        cachedCost = cachedTokens * CACHED_COST.get(TextGenerationModel(model), 0) / 1e6
        inputCost = inputTokens * INPUT_COST.get(TextGenerationModel(model), 0) / 1e6
        outputCost = outputTokens * OUTPUT_COST.get(TextGenerationModel(model), 0) / 1e6

        properties = {
            "cachedTokens": cachedTokens,
            "cachedCost": cachedCost,
            "inputTokens": inputTokens,
            "inputCost": inputCost,
            "outputTokens": outputTokens,
            "outputCost": outputCost,
            "totalCost": cachedCost + inputCost + outputCost,
        }

        Logger.info(
            f"Generated a chat completion using model {model}, costing ${(cachedCost + inputCost + outputCost)}. {cachedTokens} cached tokens, {inputTokens} input tokens, {outputTokens} output tokens.",
            properties=properties,
        )

        if result is None:
            return Option.Error(
                DomainError("AIClient-ChatCompletion-E03", "No response provided.")
            )

        return Option(result) # type: ignore
