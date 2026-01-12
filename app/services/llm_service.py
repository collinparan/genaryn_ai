"""
LLM Service for Digital Ocean endpoint integration
"""

import json
from typing import AsyncGenerator, Dict, List, Optional, Any
from dataclasses import dataclass
import httpx
import structlog

from app.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)

# Military system prompt
MILITARY_SYSTEM_PROMPT = """You are the Genaryn AI Deputy Commander, a strategic advisor for military operations.

Your role:
- Provide clear, actionable intelligence and recommendations
- Analyze multiple courses of action (COAs) with risk assessments
- Support the Military Decision Making Process (MDMP)
- Maintain operational security (OPSEC)
- Consider tactical, operational, and strategic implications

Always consider:
- Mission objectives and commander's intent
- Available resources and time constraints
- Enemy capabilities and terrain factors
- Force protection and risk mitigation
- Legal and ethical considerations

Communicate in clear, concise military language. Use proper military terminology and brevity codes when appropriate.
Classification: UNCLASSIFIED unless otherwise specified."""


@dataclass
class LLMResponse:
    """LLM response structure."""

    content: str
    tokens_used: int
    model: str
    finish_reason: str
    metadata: Dict[str, Any]


class LLMService:
    """Service for interacting with Digital Ocean LLM endpoint."""

    def __init__(self):
        """Initialize LLM service."""
        self.endpoint = settings.DO_LLM_ENDPOINT
        self.model = settings.LLM_MODEL
        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(60.0, connect=10.0),
            limits=httpx.Limits(max_keepalive_connections=5, max_connections=10),
        )
        self.system_prompt = MILITARY_SYSTEM_PROMPT

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.client.aclose()

    async def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 2000,
        stream: bool = False,
        system_override: Optional[str] = None,
    ) -> LLMResponse:
        """
        Send chat completion request to LLM.

        Args:
            messages: List of message dictionaries with 'role' and 'content'
            temperature: Sampling temperature (0-1)
            max_tokens: Maximum tokens in response
            stream: Whether to stream the response
            system_override: Override system prompt if provided

        Returns:
            LLMResponse object
        """
        # Prepare messages with system prompt
        system_prompt = system_override or self.system_prompt
        full_messages = [{"role": "system", "content": system_prompt}] + messages

        # Prepare request payload
        payload = {
            "model": self.model,
            "messages": full_messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": stream,
        }

        try:
            response = await self.client.post(
                self.endpoint,
                json=payload,
                headers={"Content-Type": "application/json"},
            )
            response.raise_for_status()

            if stream:
                return await self._handle_stream_response(response)
            else:
                return await self._handle_response(response)

        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error calling LLM", status_code=e.response.status_code, detail=str(e))
            raise
        except Exception as e:
            logger.error(f"Error calling LLM", error=str(e))
            raise

    async def stream_chat(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 2000,
        system_override: Optional[str] = None,
    ) -> AsyncGenerator[str, None]:
        """
        Stream chat completion response from LLM.

        Args:
            messages: List of message dictionaries
            temperature: Sampling temperature
            max_tokens: Maximum tokens
            system_override: Override system prompt

        Yields:
            Response chunks as strings
        """
        # Prepare messages with system prompt
        system_prompt = system_override or self.system_prompt
        full_messages = [{"role": "system", "content": system_prompt}] + messages

        # Prepare request payload
        payload = {
            "model": self.model,
            "messages": full_messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": True,
        }

        try:
            async with self.client.stream(
                "POST",
                self.endpoint,
                json=payload,
                headers={"Content-Type": "application/json"},
            ) as response:
                response.raise_for_status()

                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data = line[6:]  # Remove "data: " prefix
                        if data == "[DONE]":
                            break

                        try:
                            chunk = json.loads(data)
                            if "choices" in chunk and len(chunk["choices"]) > 0:
                                delta = chunk["choices"][0].get("delta", {})
                                if "content" in delta:
                                    yield delta["content"]
                        except json.JSONDecodeError:
                            logger.warning(f"Failed to parse streaming chunk", chunk=data)
                            continue

        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error streaming from LLM", status_code=e.response.status_code)
            raise
        except Exception as e:
            logger.error(f"Error streaming from LLM", error=str(e))
            raise

    async def _handle_response(self, response: httpx.Response) -> LLMResponse:
        """Handle non-streaming response."""
        data = response.json()

        if "choices" not in data or len(data["choices"]) == 0:
            raise ValueError("Invalid response format from LLM")

        choice = data["choices"][0]
        message = choice.get("message", {})

        return LLMResponse(
            content=message.get("content", ""),
            tokens_used=data.get("usage", {}).get("total_tokens", 0),
            model=data.get("model", self.model),
            finish_reason=choice.get("finish_reason", "unknown"),
            metadata={
                "prompt_tokens": data.get("usage", {}).get("prompt_tokens", 0),
                "completion_tokens": data.get("usage", {}).get("completion_tokens", 0),
            },
        )

    async def _handle_stream_response(self, response: httpx.Response) -> LLMResponse:
        """Handle streaming response (collects full response)."""
        content = ""
        finish_reason = "unknown"

        async for line in response.aiter_lines():
            if line.startswith("data: "):
                data = line[6:]
                if data == "[DONE]":
                    break

                try:
                    chunk = json.loads(data)
                    if "choices" in chunk and len(chunk["choices"]) > 0:
                        delta = chunk["choices"][0].get("delta", {})
                        if "content" in delta:
                            content += delta["content"]
                        if "finish_reason" in chunk["choices"][0]:
                            finish_reason = chunk["choices"][0]["finish_reason"]
                except json.JSONDecodeError:
                    continue

        # Estimate tokens (rough approximation)
        estimated_tokens = len(content.split()) * 1.3

        return LLMResponse(
            content=content,
            tokens_used=int(estimated_tokens),
            model=self.model,
            finish_reason=finish_reason,
            metadata={},
        )

    async def analyze_decision(
        self,
        context: str,
        options: List[str],
        constraints: Optional[str] = None,
    ) -> str:
        """
        Analyze a military decision with COA analysis.

        Args:
            context: Situational context
            options: List of possible courses of action
            constraints: Any constraints or limitations

        Returns:
            Analysis and recommendation
        """
        prompt = f"""Analyze the following military decision:

SITUATION: {context}

COURSES OF ACTION:
{chr(10).join(f'{i+1}. {option}' for i, option in enumerate(options))}

{'CONSTRAINTS: ' + constraints if constraints else ''}

Provide:
1. Analysis of each COA (advantages, disadvantages, risks)
2. Recommended COA with rationale
3. Risk mitigation measures
4. Critical success factors
5. Decision points and triggers"""

        messages = [{"role": "user", "content": prompt}]
        response = await self.chat(messages, temperature=0.5)
        return response.content

    async def assess_risk(
        self,
        operation: str,
        factors: List[str],
    ) -> str:
        """
        Assess operational risk.

        Args:
            operation: Operation description
            factors: Risk factors to consider

        Returns:
            Risk assessment
        """
        prompt = f"""Conduct a risk assessment for the following operation:

OPERATION: {operation}

RISK FACTORS:
{chr(10).join(f'- {factor}' for factor in factors)}

Provide:
1. Overall risk level (LOW/MODERATE/HIGH/EXTREME)
2. Probability of occurrence for each risk
3. Potential impact assessment
4. Risk mitigation strategies
5. Residual risk after mitigation"""

        messages = [{"role": "user", "content": prompt}]
        response = await self.chat(messages, temperature=0.3)
        return response.content

    async def generate_sitrep(
        self,
        situation: str,
        friendly_forces: str,
        enemy_forces: str,
        mission: str,
    ) -> str:
        """
        Generate a situation report (SITREP).

        Args:
            situation: Current situation
            friendly_forces: Friendly force status
            enemy_forces: Enemy force status
            mission: Current mission

        Returns:
            Formatted SITREP
        """
        prompt = f"""Generate a military SITREP based on:

SITUATION: {situation}
FRIENDLY FORCES: {friendly_forces}
ENEMY FORCES: {enemy_forces}
MISSION: {mission}

Format as a standard military SITREP with:
- Line 1: DATE-TIME GROUP
- Line 2: UNIT
- Line 3: ACTIVITY
- Line 4: LOCATION
- Line 5: ENEMY ACTIVITY
- Line 6: FRIENDLY ACTIVITY
- Line 7: ADMIN/LOG
- Line 8: COMMANDER'S ASSESSMENT"""

        messages = [{"role": "user", "content": prompt}]
        response = await self.chat(messages, temperature=0.3)
        return response.content

    async def close(self):
        """Close HTTP client."""
        await self.client.aclose()


# Singleton instance
_llm_service: Optional[LLMService] = None


async def get_llm_service() -> LLMService:
    """Get or create LLM service instance."""
    global _llm_service
    if _llm_service is None:
        _llm_service = LLMService()
    return _llm_service