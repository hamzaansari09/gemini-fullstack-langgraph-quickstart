from typing import List

from pydantic import BaseModel, Field


class AdInsight(BaseModel):
    """Individual ad insight model."""
    title: str = Field(
        description="A concise title for the insight (e.g., 'Visual Appeal', 'Target Audience', 'Brand Message')"
    )
    description: str = Field(
        description="Detailed description of the insight based on the ad image analysis"
    )
    impact_level: str = Field(
        description="Impact level of this insight: 'High', 'Medium', or 'Low'"
    )


class AdInsights(BaseModel):
    """Collection of 3 key insights from ad image analysis."""
    insights: List[AdInsight] = Field(
        description="List of exactly 3 key insights extracted from the ad image",
        min_items=3,
        max_items=3
    )
    overall_assessment: str = Field(
        description="Overall assessment of the ad's effectiveness based on the insights"
    )


class AdImprovement(BaseModel):
    """Individual ad improvement suggestion model."""
    category: str = Field(
        description="Category of improvement (e.g., 'Visual Design', 'Messaging', 'Call-to-Action', 'Target Audience')"
    )
    suggestion: str = Field(
        description="Specific improvement suggestion to enhance ad performance"
    )
    expected_impact: str = Field(
        description="Expected impact of implementing this improvement"
    )
    priority: str = Field(
        description="Priority level: 'High', 'Medium', or 'Low'"
    )


class AdImprovements(BaseModel):
    """Collection of 3 key improvement suggestions for ad performance."""
    improvements: List[AdImprovement] = Field(
        description="List of exactly 3 improvement suggestions to enhance ad performance",
        min_items=3,
        max_items=3
    )
    implementation_notes: str = Field(
        description="General notes on implementing these improvements"
    )


class AdTakeaway(BaseModel):
    """Individual key takeaway model."""
    takeaway: str = Field(
        description="A key takeaway or lesson learned from the ad analysis"
    )
    actionable_insight: str = Field(
        description="Actionable insight that can be applied to future marketing efforts"
    )
    relevance: str = Field(
        description="Relevance to broader marketing strategy: 'Strategic', 'Tactical', or 'Operational'"
    )


class AdTakeaways(BaseModel):
    """Collection of key takeaways from the ad analysis."""
    takeaways: List[AdTakeaway] = Field(
        description="List of key takeaways from the comprehensive ad analysis",
        min_items=3,
        max_items=5
    )
    summary: str = Field(
        description="Executive summary of the main takeaways for stakeholders"
    )


class DateExtraction(BaseModel):
    """Model for extracting date from user query."""
    selected_date: str | None = Field(
        description="The date mentioned by the user in their query, formatted as YYYY-MM-DD if found"
    )
    date_found: bool = Field(
        description="Whether a specific date was found in the user's query"
    )
    date_context: str | None = Field(
        description="Context around the date mention in the user's query"
    )


class GreetingMessage(BaseModel):
    """Model for personalized greeting message."""
    greeting: str = Field(
        description="Personalized greeting message for the user"
    )
    acknowledgment: str = Field(
        description="Acknowledgment of the user's request and selected date (if any)"
    )
    next_steps: str = Field(
        description="Brief description of what the marketing analysis will include"
    )

