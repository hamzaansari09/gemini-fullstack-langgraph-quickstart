import os
from typing import Any

from langchain_core.runnables import RunnableConfig
from pydantic import BaseModel, Field


class Configuration(BaseModel):
    """The configuration for the marketing analyst agent."""

    date_extraction_model: str = Field(
        default="gemini-2.0-flash",
        metadata={
            "description": "The name of the language model to use for date extraction from user queries."
        },
    )

    greeting_model: str = Field(
        default="gemini-2.0-flash",
        metadata={
            "description": "The name of the language model to use for generating personalized greetings."
        },
    )

    vision_model: str = Field(
        default="gemini-2.0-flash",
        metadata={
            "description": "The name of the vision model to use for ad image analysis and insights generation."
        },
    )

    improvements_model: str = Field(
        default="gemini-2.0-flash",
        metadata={
            "description": "The name of the vision model to use for generating ad improvement suggestions."
        },
    )

    reasoning_model: str = Field(
        default="gemini-2.5-flash",
        metadata={
            "description": "The name of the reasoning model to use for synthesizing takeaways and strategic insights."
        },
    )

    vision_temperature: float = Field(
        default=0.1,
        metadata={
            "description": "Temperature setting for vision model calls (lower for more consistent analysis)."
        },
    )

    reasoning_temperature: float = Field(
        default=0.2,
        metadata={
            "description": "Temperature setting for reasoning model calls (slightly higher for creative insights)."
        },
    )

    max_image_size_mb: int = Field(
        default=10,
        metadata={
            "description": "Maximum allowed image size in megabytes for ad analysis."
        },
    )

    supported_image_formats: list[str] = Field(
        default=["jpg", "jpeg", "png", "webp"],
        metadata={
            "description": "List of supported image formats for ad analysis."
        },
    )

    @classmethod
    def from_runnable_config(
        cls, config: RunnableConfig | None = None
    ) -> "Configuration":
        """Create a Configuration instance from a RunnableConfig."""
        configurable = (
            config["configurable"] if config and "configurable" in config else {}
        )

        # Get raw values from environment or config
        raw_values: dict[str, Any] = {
            name: os.environ.get(name.upper(), configurable.get(name))
            for name in cls.model_fields.keys()
        }

        # Filter out None values
        values = {k: v for k, v in raw_values.items() if v is not None}

        return cls(**values)

