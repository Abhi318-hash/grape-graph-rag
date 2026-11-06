import os
import time
import logging
from typing import List, Tuple, Optional, Any
import google.generativeai as genai
from google.api_core import exceptions

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("GeminiManager")

# Safety settings: We allow "Dangerous Content" because agricultural contexts
# legitimately discuss chemical pesticides, fungicides, and disease treatments.
DEFAULT_SAFETY_SETTINGS = [
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
]

# Preferred priority order of models for agriculture RAG (fastest and most reliable first)
DEFAULT_CASCADE_ORDER = [
    "gemini-2.5-flash",
    "gemini-3.5-flash-lite",
    "gemini-3.5-flash",
    "gemini-3.1-flash-lite",
    "gemini-3.6-flash",
    "gemini-2.5-pro",
]

class GeminiModelManager:
    """
    Manages Gemini model selection, dynamic discovery, and automatic fallback loop.
    When a model hits a 429 (ResourceExhausted), 504 (DeadlineExceeded), or 404 (NotFound),
    it automatically fails over to the next available working model in the cascade.
    """
    _cached_available_models: Optional[List[str]] = None

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY")
        if self.api_key:
            genai.configure(api_key=self.api_key)

    def get_available_models(self, force_refresh: bool = False) -> List[str]:
        """
        Dynamically queries Google AI Studio for all models that support generateContent.
        Returns a clean list of model IDs (e.g. 'gemini-2.5-flash').
        """
        if self._cached_available_models and not force_refresh:
            return self._cached_available_models

        discovered = []
        try:
            for m in genai.list_models():
                if "generateContent" in getattr(m, "supported_generation_methods", []):
                    clean_name = m.name.replace("models/", "")
                    # Filter out embedding-only, tts, imagen, and specialized tools
                    ignored_keywords = ["embedding", "aqa", "tts", "imagen", "deep-research", "computer-use"]
                    if not any(k in clean_name.lower() for k in ignored_keywords):
                        discovered.append(clean_name)
        except Exception as e:
            logger.warning(f"Could not list models via genai.list_models(): {e}")

        # Prioritize known working cascade models first, then append other discovered models
        ordered = []
        for model in DEFAULT_CASCADE_ORDER:
            if model in discovered and model not in ordered:
                ordered.append(model)
        for model in discovered:
            if model not in ordered:
                ordered.append(model)

        # Fallback to default cascade if discovery returned nothing (e.g. offline/restricted)
        if not ordered:
            ordered = list(DEFAULT_CASCADE_ORDER)

        GeminiModelManager._cached_available_models = ordered
        return ordered

    def generate_content_with_fallback(
        self,
        contents: Any,
        preferred_model: Optional[str] = None,
        auto_fallback: bool = True,
        safety_settings: Optional[List[dict]] = None,
        generation_config: Optional[dict] = None
    ) -> Tuple[Any, str, List[dict]]:
        """
        Executes generate_content with continuous error handling and failover loop.
        
        Args:
            contents: String, PIL Image, or list of parts (prompt + image)
            preferred_model: The model to try first (e.g. 'gemini-2.5-flash')
            auto_fallback: If True, automatically falls back to other models on error
            safety_settings: Safety settings list (defaults to DEFAULT_SAFETY_SETTINGS)
            generation_config: Optional GenerationConfig dict
            
        Returns:
            Tuple of:
              - response (genai response object)
              - successful_model_name (str)
              - fallback_history (list of dicts recording attempts and errors)
        """
        settings = safety_settings or DEFAULT_SAFETY_SETTINGS
        available = self.get_available_models()

        # Build candidate order
        candidates = []
        if preferred_model:
            clean_pref = preferred_model.replace("models/", "")
            candidates.append(clean_pref)

        for m in available:
            if m not in candidates:
                candidates.append(m)

        for m in DEFAULT_CASCADE_ORDER:
            if m not in candidates:
                candidates.append(m)

        if not auto_fallback:
            candidates = candidates[:1]

        fallback_history = []

        for candidate in candidates:
            logger.info(f"Attempting generation with model: '{candidate}'...")
            try:
                model_instance = genai.GenerativeModel(
                    candidate,
                    safety_settings=settings,
                    generation_config=generation_config
                )
                response = model_instance.generate_content(contents)
                
                # Check that response has text
                _ = response.text
                
                logger.info(f"Successfully generated response with model: '{candidate}'")
                return response, candidate, fallback_history

            except exceptions.ResourceExhausted as e:
                # 429 Quota Exceeded
                err_msg = f"Quota exceeded (429) on '{candidate}': {e.message if hasattr(e, 'message') else e}"
                logger.warning(err_msg)
                fallback_history.append({"model": candidate, "error": "429 Quota Exceeded", "details": str(e)})
            except exceptions.DeadlineExceeded as e:
                # 504 Gateway / API Timeout
                err_msg = f"Timeout (504) on '{candidate}': {e.message if hasattr(e, 'message') else e}"
                logger.warning(err_msg)
                fallback_history.append({"model": candidate, "error": "504 Timeout", "details": str(e)})
            except exceptions.NotFound as e:
                # 404 Model Not Found / Retired
                err_msg = f"Model '{candidate}' not found / retired (404)"
                logger.warning(err_msg)
                fallback_history.append({"model": candidate, "error": "404 Not Found", "details": str(e)})
            except exceptions.ServiceUnavailable as e:
                # 503 Backend overloaded
                err_msg = f"Model '{candidate}' temporarily unavailable (503)"
                logger.warning(err_msg)
                fallback_history.append({"model": candidate, "error": "503 Service Unavailable", "details": str(e)})
            except Exception as e:
                err_str = str(e)
                # Catch string-based quota / timeout errors if not typed
                if "429" in err_str or "ResourceExhausted" in err_str or "quota" in err_str.lower():
                    tag = "429 Quota Exceeded"
                elif "504" in err_str or "Deadline" in err_str or "timed out" in err_str.lower():
                    tag = "504 Timeout"
                elif "404" in err_str or "not found" in err_str.lower():
                    tag = "404 Not Found"
                else:
                    tag = "Execution Error"

                logger.warning(f"Error on '{candidate}' ({tag}): {err_str}")
                fallback_history.append({"model": candidate, "error": tag, "details": err_str})

            if not auto_fallback:
                break

        # If all candidates exhausted
        attempted_summary = "\n".join([f"- {h['model']}: {h['error']}" for h in fallback_history])
        raise RuntimeError(
            f"All Gemini models in the fallback cascade failed!\n"
            f"Attempted models:\n{attempted_summary}\n\n"
            f"Please check your GOOGLE_API_KEY quota or link a billing account in Google Cloud Console."
        )

# Global singleton helper
_default_manager: Optional[GeminiModelManager] = None

def get_gemini_manager() -> GeminiModelManager:
    global _default_manager
    if _default_manager is None:
        _default_manager = GeminiModelManager()
    return _default_manager
