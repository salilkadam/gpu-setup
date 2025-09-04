"""
Backend implementations for different inference engines.

This module provides backend abstractions for vLLM, Transformers,
and custom inference engines.
"""

from .base_backend import BaseBackend, BackendResult
from .vllm_backend import VLLMBackend
from .transformers_backend import TransformersBackend

__all__ = [
    "BaseBackend",
    "BackendResult", 
    "VLLMBackend",
    "TransformersBackend"
]
