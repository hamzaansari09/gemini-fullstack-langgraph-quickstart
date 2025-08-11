import os
import base64
import re
from typing import Dict, Any, Optional

from marketing_agent.tools_and_schemas import (
    AdInsights, AdImprovements, AdTakeaways, 
    DateExtraction, GreetingMessage
)
from dotenv import load_dotenv
from langchain_core.messages import AIMessage, HumanMessage
from langgraph.graph import StateGraph
from langgraph.graph import START, END
from langchain_core.runnables import RunnableConfig
from google.genai import Client

from marketing_agent.state import MarketingState
from marketing_agent.configuration import Configuration
from marketing_agent.prompts import (
    get_current_date,
    date_extraction_instructions,
    greeting_instructions,
    ad_insights_instructions,
    ad_improvements_instructions,
    ad_takeaways_instructions,
)
from langchain_google_genai import ChatGoogleGenerativeAI

load_dotenv()

if os.getenv("GEMINI_API_KEY") is None:
    raise ValueError("GEMINI_API_KEY is not set")

# Used for Gemini Vision API
genai_client = Client(api_key=os.getenv("GEMINI_API_KEY"))


# Marketing Analysis Tool Functions

def provide_date_tool(state: MarketingState, config: RunnableConfig) -> Dict[str, Any]:
    """Extract and return the user-selected date from the query.
    
    Args:
        state: Current marketing state containing user messages
        config: Configuration for the runnable
        
    Returns:
        Dictionary with state update including selected_date
    """
    configurable = Configuration.from_runnable_config(config)
    
    # Get the latest user message
    user_message = ""
    for message in reversed(state["messages"]):
        if isinstance(message, HumanMessage):
            user_message = message.content
            break
    
    # Initialize Gemini model for date extraction
    llm = ChatGoogleGenerativeAI(
        model=configurable.query_generator_model,
        temperature=0,
        max_retries=2,
        api_key=os.getenv("GEMINI_API_KEY"),
    )
    structured_llm = llm.with_structured_output(DateExtraction)
    
    # Format the prompt for date extraction
    formatted_prompt = date_extraction_instructions.format(
        user_query=user_message,
        current_date=get_current_date()
    )
    
    result = structured_llm.invoke(formatted_prompt)
    
    return {
        "selected_date": result.selected_date if result.date_found else None,
    }


def greet_user_tool(state: MarketingState, config: RunnableConfig) -> Dict[str, Any]:
    """Provide a personalized greeting message.
    
    Args:
        state: Current marketing state
        config: Configuration for the runnable
        
    Returns:
        Dictionary with state update including greeting message
    """
    configurable = Configuration.from_runnable_config(config)
    
    # Get the latest user message
    user_message = ""
    for message in reversed(state["messages"]):
        if isinstance(message, HumanMessage):
            user_message = message.content
            break
    
    # Initialize Gemini model for greeting generation
    llm = ChatGoogleGenerativeAI(
        model=configurable.query_generator_model,
        temperature=0.7,
        max_retries=2,
        api_key=os.getenv("GEMINI_API_KEY"),
    )
    structured_llm = llm.with_structured_output(GreetingMessage)
    
    # Format the prompt for greeting generation
    formatted_prompt = greeting_instructions.format(
        user_query=user_message,
        selected_date=state.get("selected_date", "not specified"),
        current_date=get_current_date()
    )
    
    result = structured_llm.invoke(formatted_prompt)
    
    # Create greeting message
    greeting_content = f"{result.greeting}\n\n{result.acknowledgment}\n\n{result.next_steps}"
    
    return {
        "messages": [AIMessage(content=greeting_content)],
        "greeting_sent": True,
    }


def analyze_ad_insights_tool(state: MarketingState, config: RunnableConfig) -> Dict[str, Any]:
    """Use Gemini Vision models for extracting 3 key insights from uploaded ad images.
    
    Args:
        state: Current marketing state containing image data
        config: Configuration for the runnable
        
    Returns:
        Dictionary with state update including ad insights
    """
    configurable = Configuration.from_runnable_config(config)
    
    if not state.get("image_data"):
        return {
            "messages": [AIMessage(content="No image data provided for analysis. Please upload an ad image to continue.")],
        }
    
    # Initialize Gemini Vision model for image analysis
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.0-flash",  # Use vision-capable model
        temperature=0.3,
        max_retries=2,
        api_key=os.getenv("GEMINI_API_KEY"),
    )
    structured_llm = llm.with_structured_output(AdInsights)
    
    # Prepare image content for vision model
    image_content = {
        "type": "image_url",
        "image_url": {"url": f"data:image/jpeg;base64,{state['image_data']}"}
    }
    
    # Format the prompt for ad insights analysis
    formatted_prompt = ad_insights_instructions.format(
        current_date=get_current_date()
    )
    
    # Create message with both text and image
    messages = [
        HumanMessage(content=[
            {"type": "text", "text": formatted_prompt},
            image_content
        ])
    ]
    
    result = structured_llm.invoke(messages)
    
    # Convert insights to list format for state storage
    insights_list = [
        {
            "title": insight.title,
            "description": insight.description,
            "impact_level": insight.impact_level
        }
        for insight in result.insights
    ]
    
    # Create response message
    insights_content = f"## 🔍 Ad Analysis Insights\n\n{result.overall_assessment}\n\n"
    for i, insight in enumerate(result.insights, 1):
        insights_content += f"### {i}. {insight.title} ({insight.impact_level} Impact)\n{insight.description}\n\n"
    
    return {
        "insights": insights_list,
        "messages": [AIMessage(content=insights_content)],
    }


def suggest_ad_improvements_tool(state: MarketingState, config: RunnableConfig) -> Dict[str, Any]:
    """Generate 3 performance enhancement recommendations.
    
    Args:
        state: Current marketing state with insights data
        config: Configuration for the runnable
        
    Returns:
        Dictionary with state update including improvement suggestions
    """
    configurable = Configuration.from_runnable_config(config)
    
    if not state.get("image_data"):
        return {
            "messages": [AIMessage(content="No image data available for improvement suggestions. Please ensure ad analysis is completed first.")],
        }
    
    # Initialize Gemini Vision model for improvement suggestions
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.0-flash",  # Use vision-capable model
        temperature=0.4,
        max_retries=2,
        api_key=os.getenv("GEMINI_API_KEY"),
    )
    structured_llm = llm.with_structured_output(AdImprovements)
    
    # Prepare image content for vision model
    image_content = {
        "type": "image_url",
        "image_url": {"url": f"data:image/jpeg;base64,{state['image_data']}"}
    }
    
    # Include previous insights context if available
    insights_context = ""
    if state.get("insights"):
        insights_context = "Previous insights identified:\n"
        for insight in state["insights"]:
            insights_context += f"- {insight['title']}: {insight['description']}\n"
    
    # Format the prompt for improvement suggestions
    formatted_prompt = ad_improvements_instructions.format(
        current_date=get_current_date(),
        insights_context=insights_context
    )
    
    # Create message with both text and image
    messages = [
        HumanMessage(content=[
            {"type": "text", "text": formatted_prompt},
            image_content
        ])
    ]
    
    result = structured_llm.invoke(messages)
    
    # Convert improvements to list format for state storage
    improvements_list = [
        {
            "category": improvement.category,
            "suggestion": improvement.suggestion,
            "expected_impact": improvement.expected_impact,
            "priority": improvement.priority
        }
        for improvement in result.improvements
    ]
    
    # Create response message
    improvements_content = f"## 🚀 Performance Enhancement Recommendations\n\n{result.implementation_notes}\n\n"
    for i, improvement in enumerate(result.improvements, 1):
        improvements_content += f"### {i}. {improvement.category} ({improvement.priority} Priority)\n"
        improvements_content += f"**Suggestion:** {improvement.suggestion}\n"
        improvements_content += f"**Expected Impact:** {improvement.expected_impact}\n\n"
    
    return {
        "improvements": improvements_list,
        "messages": [AIMessage(content=improvements_content)],
    }


def extract_key_takeaways_tool(state: MarketingState, config: RunnableConfig) -> Dict[str, Any]:
    """Summarize the main takeaways from the ad analysis.
    
    Args:
        state: Current marketing state with all analysis data
        config: Configuration for the runnable
        
    Returns:
        Dictionary with state update including key takeaways
    """
    configurable = Configuration.from_runnable_config(config)
    
    # Check if we have sufficient analysis data
    if not state.get("insights") or not state.get("improvements"):
        return {
            "messages": [AIMessage(content="Insufficient analysis data for generating takeaways. Please complete insights and improvements analysis first.")],
        }
    
    # Initialize Gemini model for takeaway extraction
    llm = ChatGoogleGenerativeAI(
        model=configurable.answer_model,  # Use reasoning model for synthesis
        temperature=0.2,
        max_retries=2,
        api_key=os.getenv("GEMINI_API_KEY"),
    )
    structured_llm = llm.with_structured_output(AdTakeaways)
    
    # Prepare context from previous analysis
    insights_context = "Key Insights:\n"
    for insight in state["insights"]:
        insights_context += f"- {insight['title']}: {insight['description']}\n"
    
    improvements_context = "Improvement Suggestions:\n"
    for improvement in state["improvements"]:
        improvements_context += f"- {improvement['category']}: {improvement['suggestion']}\n"
    
    # Format the prompt for takeaway extraction
    formatted_prompt = ad_takeaways_instructions.format(
        current_date=get_current_date(),
        insights_context=insights_context,
        improvements_context=improvements_context,
        selected_date=state.get("selected_date", "not specified")
    )
    
    result = structured_llm.invoke(formatted_prompt)
    
    # Convert takeaways to list format for state storage
    takeaways_list = [
        {
            "takeaway": takeaway.takeaway,
            "actionable_insight": takeaway.actionable_insight,
            "relevance": takeaway.relevance
        }
        for takeaway in result.takeaways
    ]
    
    # Create response message
    takeaways_content = f"## 📋 Key Takeaways & Strategic Insights\n\n{result.summary}\n\n"
    for i, takeaway in enumerate(result.takeaways, 1):
        takeaways_content += f"### {i}. {takeaway.relevance} Level\n"
        takeaways_content += f"**Takeaway:** {takeaway.takeaway}\n"
        takeaways_content += f"**Actionable Insight:** {takeaway.actionable_insight}\n\n"
    
    return {
        "takeaways": takeaways_list,
        "messages": [AIMessage(content=takeaways_content)],
        "analysis_complete": True,
    }


# Conditional routing functions for supervisor agent workflow

def route_after_date_extraction(state: MarketingState) -> str:
    """Route after date extraction - always proceed to greeting."""
    return "greet_user"


def route_after_greeting(state: MarketingState) -> str:
    """Route after greeting - check if we have image data to analyze."""
    if not state.get("image_data"):
        # If no image data, we can't proceed with analysis
        return END
    return "analyze_insights"


def route_after_insights(state: MarketingState) -> str:
    """Route after insights analysis - proceed to improvements if insights exist."""
    if state.get("insights"):
        return "suggest_improvements"
    # If insights failed, end the workflow
    return END


def route_after_improvements(state: MarketingState) -> str:
    """Route after improvements - proceed to takeaways if improvements exist."""
    if state.get("improvements"):
        return "extract_takeaways"
    # If improvements failed, end the workflow
    return END


def route_after_takeaways(state: MarketingState) -> str:
    """Route after takeaways - workflow is complete."""
    return END




# Create the Marketing Agent Supervisor Graph
builder = StateGraph(MarketingState, config_schema=Configuration)

# Add nodes for each marketing analysis tool
builder.add_node("provide_date", provide_date_tool)
builder.add_node("greet_user", greet_user_tool)
builder.add_node("analyze_insights", analyze_ad_insights_tool)
builder.add_node("suggest_improvements", suggest_ad_improvements_tool)
builder.add_node("extract_takeaways", extract_key_takeaways_tool)

# Set the entrypoint as `provide_date` - always start with date extraction
builder.add_edge(START, "provide_date")

# Define the supervisor agent workflow with conditional routing
# Date extraction -> Greeting (always)
builder.add_conditional_edges("provide_date", route_after_date_extraction, ["greet_user"])

# Greeting -> Insights analysis (if image data exists) or END (if no image)
builder.add_conditional_edges("greet_user", route_after_greeting, ["analyze_insights", END])

# Insights -> Improvements (if insights successful) or END (if failed)
builder.add_conditional_edges("analyze_insights", route_after_insights, ["suggest_improvements", END])

# Improvements -> Takeaways (if improvements successful) or END (if failed)
builder.add_conditional_edges("suggest_improvements", route_after_improvements, ["extract_takeaways", END])

# Takeaways -> END (workflow complete)
builder.add_conditional_edges("extract_takeaways", route_after_takeaways, [END])

# Compile the graph with optimized configuration for Gemini Vision models
graph = builder.compile(
    name="marketing-analyst-supervisor-agent",
    checkpointer=None,  # Can be configured later for persistence
)















