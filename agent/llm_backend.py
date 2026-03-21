"""Cross-platform LLM backend abstraction with timeout support."""

import os
import sys
import logging
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeout

logger = logging.getLogger(__name__)

DEFAULT_TIMEOUT = int(os.getenv("LLM_TIMEOUT", "60"))
DEFAULT_MAX_TOKENS = 2048

try:
    import ollama
except ImportError:
    ollama = None

_mlx_available = False
if sys.platform == "darwin":
    try:
        from mlx_lm import load as mlx_load, generate as mlx_generate
        _mlx_available = True
    except ImportError:
        pass


class LLMBackend:
    """Unified LLM interface with timeout and platform detection."""

    def __init__(
        self,
        model: str = "llama3.2",
        backend: str = "auto",
        timeout: int = DEFAULT_TIMEOUT,
        mlx_model_id: str | None = None,
    ):
        self.model = model
        self.timeout = timeout
        self._backend = backend
        self._mlx_model_id = mlx_model_id or os.getenv(
            "MLX_MODEL", "mlx-community/Llama-3.2-3B-Instruct-4bit"
        )
        self._mlx_model = None
        self._mlx_tokenizer = None
        self._executor = ThreadPoolExecutor(max_workers=1)
        self._resolved_backend = self._resolve_backend()
        logger.info("LLM backend resolved to: %s", self._resolved_backend)

    def _resolve_backend(self) -> str:
        if self._backend == "ollama":
            return "ollama"
        if self._backend == "mlx":
            return "mlx"
        # auto mode
        if ollama is not None:
            try:
                ollama.list()
                return "ollama"
            except Exception:
                pass
        if _mlx_available and sys.platform == "darwin":
            return "mlx"
        if ollama is not None:
            return "ollama"  # installed but server may not be running yet
        raise RuntimeError(
            "No LLM backend available. Install Ollama (https://ollama.com) "
            "and run: ollama pull llama3.2"
        )

    def call(self, messages: list[dict]) -> str:
        """Call LLM with timeout. Raises TimeoutError or RuntimeError."""
        future = self._executor.submit(self._call_inner, messages)
        try:
            return future.result(timeout=self.timeout)
        except FuturesTimeout:
            raise TimeoutError(
                f"LLM call exceeded {self.timeout}s timeout. "
                "Consider using a smaller model or increasing LLM_TIMEOUT."
            )

    def _call_inner(self, messages: list[dict]) -> str:
        if self._resolved_backend == "ollama":
            return self._call_ollama(messages)
        if self._resolved_backend == "mlx":
            return self._call_mlx(messages)
        raise RuntimeError(f"Unknown backend: {self._resolved_backend}")

    def _call_ollama(self, messages: list[dict]) -> str:
        response = ollama.chat(
            model=self.model,
            messages=messages,
            options={"num_predict": DEFAULT_MAX_TOKENS},
        )
        return response["message"]["content"]

    def _call_mlx(self, messages: list[dict]) -> str:
        if self._mlx_model is None:
            self._mlx_model, self._mlx_tokenizer = mlx_load(self._mlx_model_id)
        prompt = self._messages_to_prompt(messages)
        return mlx_generate(
            self._mlx_model,
            self._mlx_tokenizer,
            prompt=prompt,
            max_tokens=DEFAULT_MAX_TOKENS,
        )

    def _messages_to_prompt(self, messages: list[dict]) -> str:
        if self._mlx_tokenizer and hasattr(self._mlx_tokenizer, "apply_chat_template"):
            return self._mlx_tokenizer.apply_chat_template(
                messages, tokenize=False, add_generation_prompt=True,
            )
        parts = []
        for msg in messages:
            role = msg["role"]
            content = msg["content"]
            if role == "system":
                parts.append(
                    f"<|begin_of_text|><|start_header_id|>system<|end_header_id|>\n\n{content}<|eot_id|>"
                )
            elif role == "user":
                parts.append(
                    f"<|start_header_id|>user<|end_header_id|>\n\n{content}<|eot_id|>"
                )
            elif role == "assistant":
                parts.append(
                    f"<|start_header_id|>assistant<|end_header_id|>\n\n{content}<|eot_id|>"
                )
        parts.append("<|start_header_id|>assistant<|end_header_id|>\n\n")
        return "".join(parts)

    @property
    def backend_name(self) -> str:
        return self._resolved_backend

    def is_healthy(self) -> bool:
        try:
            if self._resolved_backend == "ollama":
                ollama.list()
                return True
            if self._resolved_backend == "mlx":
                return _mlx_available
        except Exception:
            return False
        return False
