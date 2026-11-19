"""Small Responses API wrapper around the official OpenRouter Python SDK."""

import math
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import httpx
from dotenv import load_dotenv
from openrouter import OpenRouter
from openrouter.errors import OpenRouterError as SDKError

REPO_ROOT = Path(__file__).resolve().parents[2]


class OpenRouterError(RuntimeError):
    """A request failed or did not produce a completed response."""


@dataclass(frozen=True)
class OpenRouterClient:
    api_key: str = field(repr=False)
    model: str

    @classmethod
    def from_env(cls) -> "OpenRouterClient":
        """Load the root .env only when requested; preserve shell overrides."""
        load_dotenv(REPO_ROOT / ".env", override=False)
        api_key = os.environ.get("OPENROUTER_API_KEY", "").strip()
        model = os.environ.get("OPENROUTER_MODEL", "").strip()
        if not api_key or not model:
            raise ValueError("Set OPENROUTER_API_KEY and OPENROUTER_MODEL in .env.")
        return cls(api_key=api_key, model=model)

    def create_response(
        self, payload: dict[str, Any], *, timeout_seconds: float = 30.0
    ) -> dict[str, Any]:
        """Send one request; return its JSON without running any tool."""
        if not math.isfinite(timeout_seconds) or timeout_seconds <= 0:
            raise ValueError("Timeout must be finite and positive.")
        if not self.api_key.strip() or not self.model.strip():
            raise ValueError("API key and model must not be empty.")
        if payload.get("stream") or payload.get("background"):
            raise ValueError("This lesson supports synchronous, non-streaming calls.")

        # Copy the caller's payload; take the model from our explicit configuration.
        body = {**payload, "model": self.model, "stream": False}
        # SDK 1.3.194 does not expose a store parameter. Accept the existing
        # store=False payload, but never silently accept a request to store data.
        if body.pop("store", False) is not False:
            raise ValueError("This SDK wrapper accepts only store=False.")
        try:
            # Disable SDK retries so one call means one attempted model request.
            with OpenRouter(
                api_key=self.api_key,
                timeout_ms=max(1, int(min(timeout_seconds, 30.0) * 1000)),
                retry_config=None,
            ) as sdk:
                response = sdk.responses.send(**body)
                result = response.model_dump(mode="json", by_alias=True)
        except httpx.RequestError:
            raise OpenRouterError("OpenRouter request failed or timed out.") from None
        except SDKError:
            # SDK exceptions can include provider bodies; do not expose them.
            raise OpenRouterError(
                "OpenRouter rejected the request or response."
            ) from None
        except ValueError:
            raise OpenRouterError(
                "Invalid OpenRouter request or response data."
            ) from None

        if result.get("error") or result.get("status") != "completed":
            raise OpenRouterError("OpenRouter did not return a completed response.")
        return result
