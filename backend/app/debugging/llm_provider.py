import os
import json
import logging
import httpx
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

logger = logging.getLogger("llm_provider")

class LLMProvider(ABC):
    @abstractmethod
    def analyze_failure(self, evidence: Dict[str, Any]) -> Dict[str, Any]:
        """
        Send failure evidence to an LLM provider and return a structured dictionary.
        """
        pass

class GenericLLMProvider(LLMProvider):
    def __init__(self, provider: str, model: str, api_key: Optional[str]):
        self.provider = provider
        self.model = model
        self.api_key = api_key

    def analyze_failure(self, evidence: Dict[str, Any]) -> Dict[str, Any]:
        if not self.api_key:
            raise ValueError("LLM_API_KEY is not set.")

        # Determine API endpoint based on provider
        url = "https://api.openai.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        provider_lower = self.provider.lower()
        if "gemini" in provider_lower:
            url = "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions"
        elif "custom" in provider_lower or os.getenv("LLM_API_URL"):
            url = os.getenv("LLM_API_URL", url)

        # Build prompt
        system_instructions = (
            "You are an expert hardware verification and CPU design debugging assistant.\n"
            "You analyze HDL/RTL simulation failure evidence and output a strictly structured JSON object.\n"
            "Do not include any prose, markdown blocks, or extra text. Output ONLY valid JSON matching this schema:\n"
            "{\n"
            "  \"failure_category\": \"TIMEOUT\" | \"COMPILE_ERROR\" | \"ASSERTION_FAILURE\" | \"SIMULATION_ERROR\" | \"UNKNOWN\",\n"
            "  \"summary\": \"A short description of the simulation failure.\",\n"
            "  \"suspected_root_cause\": \"Detailed explanation of why the simulation failed based on the evidence.\",\n"
            "  \"evidence\": [\"specific log line 1\", \"specific log line 2\"],\n"
            "  \"recommended_fix\": \"Recommended fix for the RTL or testbench.\",\n"
            "  \"confidence\": 0.0 to 1.0,\n"
            "  \"affected_component\": \"Name of the module, file, or component affected (e.g. ALU, FIFO, etc.)\",\n"
            "  \"suggested_next_test\": \"Name or path of another test or debug step to run next\"\n"
            "}"
        )

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_instructions},
                {"role": "user", "content": f"Failure Evidence:\n{json.dumps(evidence)}"}
            ],
            "response_format": {"type": "json_object"}
        }

        # Log request safely (excluding API key)
        logger.info(f"Sending LLM request to {url} using provider={self.provider}, model={self.model}")
        
        try:
            with httpx.Client(timeout=30.0) as client:
                response = client.post(url, headers=headers, json=payload)
                response.raise_for_status()
                res_data = response.json()
                content = res_data["choices"][0]["message"]["content"]
                return json.loads(content)
        except Exception as e:
            logger.error(f"LLM API call failed: {str(e)}")
            raise e

def get_llm_provider() -> Optional[LLMProvider]:
    enabled = os.getenv("LLM_ENABLED", "false").lower() == "true"
    if not enabled:
        logger.info("LLM analyzer is disabled (LLM_ENABLED is not true)")
        return None
        
    provider = os.getenv("LLM_PROVIDER", "openai")
    model = os.getenv("LLM_MODEL", "gpt-4o")
    api_key = os.getenv("LLM_API_KEY")
    
    if not api_key:
        logger.warning("LLM_API_KEY environment variable is not set")
        return None
        
    return GenericLLMProvider(provider, model, api_key)
