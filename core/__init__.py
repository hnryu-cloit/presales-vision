"""
CEN AI DAM Editor - Core Backend Module

This package contains the core backend logic for the CEN AI DAM Editor application.
It provides reusable components for AI-powered image generation and analysis.

Modules:
    - gemini_client: Google Gemini API client
    - config: Product categories and attributes configuration
    - prompt_templates: AI prompt templates
    - image_generator: AI image generation engine
    - image_analyzer: AI image analysis engine
    - logger: Logging utilities
"""

__version__ = "1.0.0"
__author__ = "ITCEN CLOIT"

from .gemini_client import GeminiClient
from .config import COLOR, PRODUCT_CATEGORY, PRODUCT_ATTRIBUTE, COMMON_ATTRIBUTE
from .prompt_templates import PromptTemplates
from .image_generator import ImageGenerator
from .image_analyzer import ImageAnalyzer
from .logger import init_logger, get_logger, timefn, APP_LOGGER_NAME

__all__ = [
    "GeminiClient",
    "COLOR",
    "PRODUCT_CATEGORY",
    "PRODUCT_ATTRIBUTE",
    "COMMON_ATTRIBUTE",
    "PromptTemplates",
    "ImageGenerator",
    "ImageAnalyzer",
    "init_logger",
    "get_logger",
    "timefn",
    "APP_LOGGER_NAME",
]