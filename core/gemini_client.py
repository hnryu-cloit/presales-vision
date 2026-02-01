# -*- coding: utf-8 -*-
"""
Google Gemini API Client for CEN AI DAM Editor

This module provides a unified client for interacting with Google's Gemini AI models.
Supports text generation, image generation, and multi-modal analysis.
"""

import os
import time
import mimetypes
import base64
from typing import List, Tuple, Optional

from google import genai
from google.genai import types
from dotenv import load_dotenv
import vertexai


class GeminiClient:
    """
    Unified Google Gemini API client with retry logic and error handling.

    Features:
        - Text generation (gemini-2.0-flash)
        - Image generation (gemini-2.5-flash-image-preview)
        - Multi-modal analysis (image + text)
        - Exponential backoff retry mechanism
    """

    def __init__(self):
        """Initialize Gemini client with API credentials from .env file."""
        load_dotenv()

        # Initialize Vertex AI
        vertexai.init(
            project=os.getenv('PROJECT_ID'),
            location=os.getenv('LOCATION')
        )

        # Initialize Gemini Client
        self.api_key = os.getenv('API_KEY')
        self.client = genai.Client(api_key=self.api_key)

        # Model configuration
        self.model_text = "gemini-2.0-flash"
        self.model_image = "gemini-2.5-flash-image-preview"

        # Retry configuration
        self.max_retries = 3
        self.initial_delay = 1

    def _retry_with_delay(self, func, *args, **kwargs):
        """
        Execute function with exponential backoff retry logic.

        Args:
            func: Function to execute
            *args: Positional arguments for the function
            **kwargs: Keyword arguments for the function

        Returns:
            Function result

        Raises:
            Exception: If all retry attempts fail
        """
        delay = self.initial_delay
        for attempt in range(self.max_retries):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                if attempt == self.max_retries - 1:
                    raise e
                print(f"Gemini API call failed (attempt {attempt + 1}/{self.max_retries}): {e}")
                time.sleep(delay)
                delay *= 2

    def generate_text(
        self,
        prompt: str,
        response_type: str = "application/json",
        model: Optional[str] = None
    ) -> str:
        """
        Generate text using Gemini text model.

        Args:
            prompt: Text prompt for generation
            response_type: MIME type for response format
            model: Model name (defaults to self.model_text)

        Returns:
            Generated text response
        """
        def _generate():
            response = self.client.models.generate_content(
                model=model or self.model_text,
                contents=[prompt],
                config={"response_mime_type": response_type}
            )
            return response.candidates[0].content.parts[0].text

        return self._retry_with_delay(_generate)

    def analyze_image(
        self,
        prompt: str,
        image_path: str,
        response_type: str = "application/json",
        model: Optional[str] = None
    ) -> str:
        """
        Analyze image with text prompt using multi-modal model.

        Args:
            prompt: Analysis prompt
            image_path: Path to image file
            response_type: MIME type for response format
            model: Model name (defaults to self.model_text)

        Returns:
            Analysis result as text
        """
        def _analyze():
            # Upload image to Gemini
            with open(image_path, "rb") as f:
                uploaded_file = self.client.files.upload(file=f)

            # Generate content
            response = self.client.models.generate_content(
                model=model or self.model_text,
                contents=[prompt, uploaded_file],
                config={
                    "response_mime_type": response_type,
                    "temperature": 0,
                    "top_p": 1,
                    "top_k": 1,
                }
            )
            return response.candidates[0].content.parts[0].text

        return self._retry_with_delay(_analyze)

    def generate_image(
        self,
        prompt: str,
        reference_images: List[str]
    ) -> Tuple[List, str]:
        """
        Generate images based on prompt and reference images.

        Args:
            prompt: Image generation prompt
            reference_images: List of reference image file paths

        Returns:
            Tuple of (generated_image_data_list, generated_text_response)
        """
        def _generate():
            # Prepare content parts
            parts = [types.Part.from_text(text=prompt)]

            # Add reference images
            for image_path in reference_images:
                if not os.path.exists(image_path):
                    print(f"Warning: Image not found: {image_path}")
                    continue

                with open(image_path, "rb") as f:
                    image_data = f.read()
                mime_type, _ = mimetypes.guess_type(image_path)
                if not mime_type:
                    mime_type = 'application/octet-stream'
                parts.append(types.Part.from_bytes(data=image_data, mime_type=mime_type))

            # Build content
            contents = [types.Content(role="user", parts=parts)]

            # Generation config
            generate_config = types.GenerateContentConfig(
                response_modalities=["IMAGE", "TEXT"],
                temperature=0,
                top_p=1,
                top_k=1,
                safety_settings=[
                    types.SafetySetting(category="HARM_CATEGORY_HATE_SPEECH", threshold="BLOCK_NONE"),
                    types.SafetySetting(category="HARM_CATEGORY_DANGEROUS_CONTENT", threshold="BLOCK_NONE"),
                    types.SafetySetting(category="HARM_CATEGORY_SEXUALLY_EXPLICIT", threshold="BLOCK_NONE"),
                    types.SafetySetting(category="HARM_CATEGORY_HARASSMENT", threshold="BLOCK_NONE"),
                ]
            )

            # Generate content stream
            image_parts = []
            full_text_response = ""

            response_stream = self.client.models.generate_content_stream(
                model=self.model_image,
                contents=contents,
                config=generate_config,
            )

            # Process stream
            for chunk in response_stream:
                if not (chunk.candidates and chunk.candidates[0].content and chunk.candidates[0].content.parts):
                    continue

                for part in chunk.candidates[0].content.parts:
                    if part.inline_data:
                        image_parts.append(part.inline_data)
                    elif part.text:
                        full_text_response += part.text

            return image_parts, full_text_response

        return self._retry_with_delay(_generate)


# Utility functions
def encode_image_to_base64(file_path: str) -> Optional[str]:
    """Encode local image file to Base64 string."""
    try:
        with open(file_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode("utf-8")
    except FileNotFoundError:
        print(f"Error: File not found: {file_path}")
        return None


def load_image_bytes(file_path: str) -> Optional[bytes]:
    """Load local image file as bytes."""
    try:
        with open(file_path, "rb") as image_file:
            return image_file.read()
    except FileNotFoundError:
        print(f"Error: File not found: {file_path}")
        return None