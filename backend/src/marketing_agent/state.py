from __future__ import annotations

from dataclasses import dataclass, field
from typing import TypedDict, Optional, Any

from langgraph.graph import add_messages
from typing_extensions import Annotated

import operator


class MarketingState(TypedDict):
    """Main state for marketing analysis workflow."""
    messages: Annotated[list, add_messages]
    image_data: Optional[str]  # Base64 encoded image data
    selected_date: Optional[str]  # User-selected date from query
    insights: Optional[list]  # List of ad insights
    improvements: Optional[list]  # List of improvement suggestions
    takeaways: Optional[list]  # List of key takeaways
    greeting_sent: bool  # Track if greeting has been sent
    analysis_complete: bool  # Track if analysis is complete


class DateExtractionState(TypedDict):
    """State for date extraction from user query."""
    selected_date: str
    date_found: bool


class GreetingState(TypedDict):
    """State for greeting message generation."""
    greeting_message: str
    user_name: Optional[str]


class InsightAnalysisState(TypedDict):
    """State for ad insight analysis."""
    insights: list[dict]
    image_processed: bool


class ImprovementSuggestionState(TypedDict):
    """State for ad improvement suggestions."""
    improvements: list[dict]
    suggestions_generated: bool


class TakeawayExtractionState(TypedDict):
    """State for key takeaway extraction."""
    takeaways: list[dict]
    summary_complete: bool


@dataclass(kw_only=True)
class MarketingAnalysisOutput:
    """Output structure for marketing analysis results."""
    insights: list[dict] = field(default_factory=list)
    improvements: list[dict] = field(default_factory=list)
    takeaways: list[dict] = field(default_factory=list)
    selected_date: Optional[str] = field(default=None)
    greeting_message: Optional[str] = field(default=None)

