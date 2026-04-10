"""Synapse embedding provider.

VECTOR_DB_PROVIDER 환경변수로 embedding 모델을 선택한다:
  - "gemini" (기본): gemini-embedding-2-preview (768차원, API key 필요)
  - "local": intfloat/multilingual-e5-small (384차원, 무료, 로컬 실행)
"""

import os
from functools import cached_property
from typing import Union

from lancedb.embeddings import TextEmbeddingFunction, register, get_registry


# --- Gemini Provider ---

@register("gemini-embedding-2")
class GeminiEmbedding2(TextEmbeddingFunction):
    """gemini-embedding-2-preview 커스텀 EmbeddingFunction."""

    name: str = "gemini-embedding-2-preview"
    output_dimensionality: int = 768
    api_key: Union[str, None] = None

    @cached_property
    def _client(self):
        from google import genai
        if self.api_key:
            return genai.Client(api_key=self.api_key)
        return genai.Client()

    def generate_embeddings(self, texts: list[str]) -> list[list[float]]:
        from google.genai import types
        all_embeddings = []
        for text in texts:
            response = self._client.models.embed_content(
                model=f"models/{self.name}",
                contents=text,
                config=types.EmbedContentConfig(
                    output_dimensionality=self.output_dimensionality,
                ),
            )
            all_embeddings.append(response.embeddings[0].values)
        return all_embeddings

    def ndims(self) -> int:
        return self.output_dimensionality


# --- Provider Factory ---

def get_embedder():
    """VECTOR_DB_PROVIDER 환경변수에 따라 적절한 embedder를 반환한다."""
    provider = os.environ.get("VECTOR_DB_PROVIDER", "local").lower()

    if provider == "gemini":
        return get_registry().get("gemini-embedding-2").create()
    elif provider == "local":
        import torch
        device = "cuda" if torch.cuda.is_available() else "cpu"
        return get_registry().get("sentence-transformers").create(
            name="intfloat/multilingual-e5-small",
            device=device,
        )
    else:
        raise ValueError(
            f"Unknown VECTOR_DB_PROVIDER: '{provider}'. "
            "Use 'gemini' or 'local'."
        )
