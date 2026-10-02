"""
eval/judge.py
=============
Custom DeepEval LLM Judge using Google Gemini via LangChain / Google GenAI.
Connects DeepEval metrics to Gemini using GOOGLE_API_KEY.
"""

from __future__ import annotations
import os
from typing import Optional
from deepeval.models.base_model import DeepEvalBaseLLM
from langchain_google_genai import ChatGoogleGenerativeAI
from app.config import settings
from app.utils.logger import get_logger

logger = get_logger(name=__name__)


class GeminiJudge(DeepEvalBaseLLM):
    """
    DeepEval LLM Judge powered by Google Gemini.
    """

    def __init__(
        self,
        model_name: Optional[str] = None,
        temperature: float = 0.0,
        *args,
        **kwargs,
    ):
        self.model_name = (
            model_name
            or settings.GEMINI_CHAT_MODEL
            or "gemini-2.5-flash"
        )
        self.temperature = temperature
        self.api_key = settings.GOOGLE_API_KEY or os.getenv("GOOGLE_API_KEY")
        if not self.api_key:
            raise ValueError(
                "GOOGLE_API_KEY not found. Please ensure it is set in your .env file."
            )
        super().__init__(model=self.model_name, *args, **kwargs)

    def load_model(self) -> ChatGoogleGenerativeAI:
        """Initialize the Gemini chat model."""
        logger.info(f"Loading Gemini Judge model: {self.model_name}")
        return ChatGoogleGenerativeAI(
            model=self.model_name,
            google_api_key=self.api_key,
            temperature=self.temperature,
        )

    def generate(self, prompt: str, *args, **kwargs) -> str:
        """Synchronous generation."""
        response = self.model.invoke(prompt)
        content = response.content
        if isinstance(content, list):
            # If multimodal or multi-part content
            return "".join(str(part) for part in content)
        return str(content)

    async def a_generate(self, prompt: str, *args, **kwargs) -> str:
        """Asynchronous generation."""
        response = await self.model.ainvoke(prompt)
        content = response.content
        if isinstance(content, list):
            return "".join(str(part) for part in content)
        return str(content)

    def get_model_name(self, *args, **kwargs) -> str:
        return self.model_name
