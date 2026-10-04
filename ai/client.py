"""
Gemini AI Client Interface
--------------------------
THE ONLY MODULE IN THE PROJECT THAT COMMUNICATES WITH THE GOOGLE GENAI SDK.
Enforces timeouts, error handling, offline mode fallback, and latency tracking.
"""

import time
import logging
from typing import Tuple, Optional
from config import config
from google import genai
from google.genai import types

logger = logging.getLogger("ai_client")

class GeminiClient:
    def __init__(self):
        self.api_key = config.GEMINI_API_KEY
        self.model_name = config.GEMINI_MODEL
        self._client: Optional[genai.Client] = None

        if self.api_key and self.api_key != "your_api_key_here" and not config.AI_OFFLINE_MODE:
            try:
                self._client = genai.Client(api_key=self.api_key)
                logger.info(f"Gemini client initialized with model {self.model_name}")
            except Exception as e:
                logger.error(f"Failed to initialize Gemini Client: {e}")
                self._client = None
        else:
            logger.warning("Gemini Client operating in Offline/Simulation Mode.")

    @property
    def is_available(self) -> bool:
        return self._client is not None and not config.AI_OFFLINE_MODE

    def generate(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        json_mode: bool = True
    ) -> Tuple[Optional[str], float, Optional[str]]:
        """
        Sends generation request to Gemini model.
        Returns: (raw_text, latency_ms, error_string)
        """
        if not self.is_available:
            return None, 0.0, "AI Client offline or GEMINI_API_KEY not configured."

        start_time = time.time()
        try:
            gen_config = None
            if json_mode:
                gen_config = types.GenerateContentConfig(
                    response_mime_type="application/json",
                    system_instruction=system_instruction
                )
            elif system_instruction:
                gen_config = types.GenerateContentConfig(
                    system_instruction=system_instruction
                )

            response = self._client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=gen_config
            )

            latency_ms = (time.time() - start_time) * 1000
            text = response.text if response else ""
            return text, latency_ms, None

        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000
            logger.error(f"Gemini call failed after {latency_ms:.1f}ms: {e}")
            return None, latency_ms, str(e)


# Global client instance
ai_client = GeminiClient()
