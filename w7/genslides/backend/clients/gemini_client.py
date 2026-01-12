"""Google Gemini AI client for image generation."""

import asyncio

from google import genai
from google.genai import types


class GeminiClient:
    """Google AI SDK (Gemini) image generation client."""

    MODEL_NAME = "gemini-3-pro-image-preview"
    COST_PER_IMAGE = 0.134

    def __init__(self, api_key: str | None = None):
        """
        Initialize Gemini client.

        Args:
            api_key: Google AI API key (optional, uses env var if not provided)
        """
        if api_key:
            self.client = genai.Client(api_key=api_key)
        else:
            # Uses GOOGLE_API_KEY from environment
            self.client = genai.Client()

    async def generate_image(
        self, prompt: str, style_image: bytes | None = None
    ) -> bytes:
        """
        Generate an image using Gemini API.

        Args:
            prompt: Image description prompt
            style_image: Optional style reference image (binary data)

        Returns:
            Generated image as PNG bytes

        Raises:
            ValueError: If no image is generated in response
        """
        contents = []

        if style_image:
            # Pass image bytes directly using Part.from_bytes
            image_part = types.Part.from_bytes(data=style_image, mime_type="image/png")
            contents.append(image_part)
            contents.append(f"Please reference the style of the image above and generate the following content: {prompt}. Make best guess what text should be included in the image. Most of the time, the control message shouldn't be included. For example, 标题: <text>, only <text> should be included in the image. All text should be using hand writing style font.")
        else:
            contents.append(prompt)

        # Run synchronous API call in thread pool to avoid blocking event loop
        response = await asyncio.to_thread(
            self.client.models.generate_content,
            model=self.MODEL_NAME,
            contents=contents,
            config=types.GenerateContentConfig(
                image_config=types.ImageConfig(
                    aspect_ratio="16:9",
                    image_size="2K",
                )
            ),
        )

        # Extract image from response
        for part in response.parts:
            if part.inline_data is not None:
                # Get the raw image bytes directly from inline_data
                return part.inline_data.data

        raise ValueError("No image generated in response")

    async def generate_style_candidates(self, prompt: str, count: int = 2) -> list[bytes]:
        """
        Generate style candidate images.

        Args:
            prompt: Style description prompt
            count: Number of images to generate (default 2)

        Returns:
            List of generated image binary data
        """
        candidates = []
        style_prompt = f"Generate an artistic image showcasing the '{prompt}' style. This image will be used as a style reference for subsequent image generation. Make it visually distinctive and representative of this style."

        for i in range(count):
            varied_prompt = f"{style_prompt} (variation {i + 1}, make it unique)"

            # Run synchronous API call in thread pool to avoid blocking event loop
            response = await asyncio.to_thread(
                self.client.models.generate_content,
                model=self.MODEL_NAME,
                contents=[varied_prompt],
                config=types.GenerateContentConfig(
                    image_config=types.ImageConfig(
                        aspect_ratio="16:9",
                        image_size="2K",
                    )
                ),
            )

            # Extract image from response
            for part in response.parts:
                if part.inline_data is not None:
                    # Get the raw image bytes directly from inline_data
                    candidates.append(part.inline_data.data)
                    break

        return candidates
