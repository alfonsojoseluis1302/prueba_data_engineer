"""Agente ReAct con Ollama/MLX para RetailTech S.A.S."""

import json
import os
import re
from pathlib import Path
from typing import Optional

from agent.llm_backend import LLMBackend
from agent.tools import TOOLS_REGISTRY
from agent.guardrails import sanitize_output

PROMPTS_DIR = Path(__file__).parent / "prompts"
MAX_ITERATIONS = 5


def _load_prompt(filename: str) -> str:
    path = PROMPTS_DIR / filename
    if path.exists():
        return path.read_text(encoding="utf-8")
    return ""


class RetailTechAgent:
    """Agente conversacional ReAct para consultas analíticas."""

    def __init__(self, model: str = "llama3.2"):
        self.model = model
        self.system_prompt = _load_prompt("system.txt")
        self.few_shots = _load_prompt("few_shots.txt")
        self._llm = LLMBackend(
            model=model,
            backend=os.getenv("LLM_BACKEND", "auto"),
            timeout=int(os.getenv("LLM_TIMEOUT", "60")),
        )

    def _build_messages(self, history: list[dict], question: str) -> list[dict]:
        """Construye la lista de mensajes para Ollama."""
        messages = [{"role": "system", "content": self.system_prompt + "\n\n" + self.few_shots}]

        # Historial reciente (últimos 10 mensajes)
        for msg in history[-10:]:
            messages.append({"role": msg["role"], "content": msg["content"]})

        messages.append({"role": "user", "content": question})
        return messages

    def _parse_tool_call(self, text: str) -> Optional[tuple[str, dict]]:
        """Parsea una tool call del formato TOOL/ARGS del texto del agente."""
        tool_match = re.search(r"TOOL:\s*(\w+)", text)
        if not tool_match:
            return None

        tool_name = tool_match.group(1)
        if tool_name not in TOOLS_REGISTRY:
            return None

        # Parsear argumentos
        args_match = re.search(r"ARGS:\s*(\{.*?\})", text, re.DOTALL)
        args = {}
        if args_match:
            try:
                args = json.loads(args_match.group(1))
            except json.JSONDecodeError:
                # Intentar extraer el valor directamente
                raw = args_match.group(1)
                # Caso simple: {"query": "SELECT ..."}
                simple_match = re.search(r'"(\w+)":\s*"(.*?)"', raw, re.DOTALL)
                if simple_match:
                    args = {simple_match.group(1): simple_match.group(2)}

        return tool_name, args

    def _execute_tool(self, tool_name: str, args: dict) -> str:
        """Ejecuta una herramienta y retorna el resultado."""
        tool = TOOLS_REGISTRY.get(tool_name)
        if not tool:
            return f"ERROR: Herramienta '{tool_name}' no encontrada."

        func = tool["function"]
        try:
            return func(**args)
        except Exception as e:
            return f"ERROR ejecutando {tool_name}: {e}"

    def chat(self, question: str, history: list[dict] = None) -> dict:
        """Procesa una pregunta del usuario con loop ReAct.

        Retorna: {answer, reasoning_steps, tools_used, pii_filtered}
        """
        if history is None:
            history = []

        reasoning_steps = []
        tools_used = []
        messages = self._build_messages(history, question)

        for iteration in range(MAX_ITERATIONS):
            try:
                assistant_text = self._llm.call(messages)
            except TimeoutError:
                return {
                    "answer": "El modelo tardó demasiado en responder. Intente con una pregunta más corta o verifique que Ollama esté funcionando correctamente.",
                    "reasoning_steps": reasoning_steps,
                    "tools_used": tools_used,
                    "pii_filtered": False,
                }
            except Exception as e:
                return {
                    "answer": f"Error del LLM: {e}",
                    "reasoning_steps": reasoning_steps,
                    "tools_used": tools_used,
                    "pii_filtered": False,
                }

            reasoning_steps.append({
                "iteration": iteration + 1,
                "type": "llm_response",
                "content": assistant_text[:500],
            })

            # Intentar parsear tool call
            tool_call = self._parse_tool_call(assistant_text)
            if tool_call:
                tool_name, args = tool_call
                tools_used.append(tool_name)

                reasoning_steps.append({
                    "iteration": iteration + 1,
                    "type": "tool_call",
                    "tool": tool_name,
                    "args": args,
                })

                # Ejecutar herramienta
                result = self._execute_tool(tool_name, args)

                reasoning_steps.append({
                    "iteration": iteration + 1,
                    "type": "tool_result",
                    "result": result[:500],
                })

                # Agregar al contexto y continuar
                messages.append({"role": "assistant", "content": assistant_text})
                messages.append({
                    "role": "user",
                    "content": f"OBSERVE: {result}\n\nAhora proporciona tu ANSWER final al usuario basándote en estos resultados.",
                })
            else:
                # Sin tool call → respuesta final
                # Extraer ANSWER si existe
                answer_match = re.search(r"ANSWER:\s*(.*)", assistant_text, re.DOTALL)
                if answer_match:
                    answer = answer_match.group(1).strip()
                else:
                    answer = assistant_text.strip()

                # Sanitizar PII
                answer, pii_filtered = sanitize_output(answer)

                return {
                    "answer": answer,
                    "reasoning_steps": reasoning_steps,
                    "tools_used": tools_used,
                    "pii_filtered": pii_filtered,
                }

        # Si agotamos iteraciones
        return {
            "answer": "No pude completar el análisis en el número máximo de pasos. Por favor, reformule su pregunta de forma más específica.",
            "reasoning_steps": reasoning_steps,
            "tools_used": tools_used,
            "pii_filtered": False,
        }
