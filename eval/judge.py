"""
eval/judge.py
=============
Custom DeepEval LLM Judge using Google Gemini via LangChain / Google GenAI.
Connects DeepEval metrics to Gemini using GOOGLE_API_KEY.
Supports native structured outputs (schema enforcement) and JSON sanitization.
"""

from __future__ import annotations
import ast
import json
import os
import re
from typing import Optional, Any
from deepeval.models.base_model import DeepEvalBaseLLM
from langchain_google_genai import ChatGoogleGenerativeAI
from app.config import settings
from app.utils.logger import get_logger

logger = get_logger(name=__name__)


class GeminiJudge(DeepEvalBaseLLM):
    """
    DeepEval LLM Judge powered by Google Gemini with native schema support.
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

    @staticmethod
    def _sanitize_json(text: str) -> str:
        """
        Clean markdown code fences and convert Python-style single-quoted
        dictionary strings into RFC-compliant double-quoted JSON strings.
        """
        cleaned = text.strip()
        # 1. Strip markdown fences ```json ... ```
        if cleaned.startswith("```"):
            cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
            cleaned = re.sub(r"\s*```$", "", cleaned)
            cleaned = cleaned.strip()

        # 2. Check if a JSON block exists and validate/sanitize it
        start = cleaned.find("{")
        end = cleaned.rfind("}")
        if start != -1 and end != -1 and end > start:
            json_candidate = cleaned[start : end + 1]
            try:
                # If already valid JSON, return as-is
                json.loads(json_candidate)
                return json_candidate
            except json.JSONDecodeError:
                # If single-quoted like {'claims': [...]}, literal_eval parses safely
                try:
                    obj = ast.literal_eval(json_candidate)
                    return json.dumps(obj)
                except Exception:
                    pass
        return cleaned

    def generate(self, prompt: str, *args, **kwargs) -> str:
        """Synchronous text generation with JSON cleanup."""
        response = self.model.invoke(prompt)
        content = response.content
        raw = "".join(str(p) for p in content) if isinstance(content, list) else str(content)
        return self._sanitize_json(raw)

    async def a_generate(self, prompt: str, *args, **kwargs) -> str:
        """Asynchronous text generation running in thread executor to prevent event loop collisions."""
        import asyncio
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, lambda: self.generate(prompt, *args, **kwargs))

    def generate_with_schema(self, *args, schema: Any = None, **kwargs) -> Any:
        """Synchronous structured output generation conforming to a schema."""
        if schema is not None:
            try:
                prompt = args[0] if args else kwargs.get("prompt", "")
                structured_model = self.model.with_structured_output(schema)
                return structured_model.invoke(prompt)
            except Exception as e:
                logger.warning(f"Schema generation fallback: {e}")
        return self.generate(*args, **kwargs)

    async def a_generate_with_schema(self, *args, schema: Any = None, **kwargs) -> Any:
        """Asynchronous structured output generation running in thread executor."""
        import asyncio
        loop = asyncio.get_running_loop()
        prompt = args[0] if args else kwargs.get("prompt", "")
        return await loop.run_in_executor(
            None, lambda: self.generate_with_schema(prompt, schema=schema, **kwargs)
        )

    def get_model_name(self, *args, **kwargs) -> str:
        return self.model_name
