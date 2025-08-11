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

    # Format the prompt
    current_date = get_current_date()
    formatted_prompt = reflection_instructions.format(
        current_date=current_date,
        research_topic=get_research_topic(state["messages"]),
        summaries="\n\n---\n\n".join(state["web_research_result"]),
    )
    # init Reasoning Model
    llm = ChatGoogleGenerativeAI(
        model=reasoning_model,
        temperature=1.0,
        max_retries=2,
        api_key=os.getenv("GEMINI_API_KEY"),
    )
    result = llm.with_structured_output(Reflection).invoke(formatted_prompt)

    return {
        "is_sufficient": result.is_sufficient,
        "knowledge_gap": result.knowledge_gap,
        "follow_up_queries": result.follow_up_queries,
        "research_loop_count": state["research_loop_count"],
        "number_of_ran_queries": len(state["search_query"]),
    }


def evaluate_research(
    state: ReflectionState,
    config: RunnableConfig,
) -> OverallState:
    """LangGraph routing function that determines the next step in the research flow.

    Controls the research loop by deciding whether to continue gathering information
    or to finalize the summary based on the configured maximum number of research loops.

    Args:
        state: Current graph state containing the research loop count
        config: Configuration for the runnable, including max_research_loops setting

    Returns:
        String literal indicating the next node to visit ("web_research" or "finalize_summary")
    """
    configurable = Configuration.from_runnable_config(config)
    max_research_loops = (
        state.get("max_research_loops")
        if state.get("max_research_loops") is not None
        else configurable.max_research_loops
    )
    if state["is_sufficient"] or state["research_loop_count"] >= max_research_loops:
        return "finalize_answer"
    else:
        return [
            Send(
                "web_research",
                {
                    "search_query": follow_up_query,
                    "id": state["number_of_ran_queries"] + int(idx),
                },
            )
            for idx, follow_up_query in enumerate(state["follow_up_queries"])
        ]


def finalize_answer(state: OverallState, config: RunnableConfig):
    """LangGraph node that finalizes the research summary.

    Prepares the final output by deduplicating and formatting sources, then
    combining them with the running summary to create a well-structured
    research report with proper citations.

    Args:
        state: Current graph state containing the running summary and sources gathered

    Returns:
        Dictionary with state update, including running_summary key containing the formatted final summary with sources
    """
    configurable = Configuration.from_runnable_config(config)
    reasoning_model = state.get("reasoning_model") or configurable.answer_model

    # Format the prompt
    current_date = get_current_date()
    formatted_prompt = answer_instructions.format(
        current_date=current_date,
        research_topic=get_research_topic(state["messages"]),
        summaries="\n---\n\n".join(state["web_research_result"]),
    )

    # init Reasoning Model, default to Gemini 2.5 Flash
    llm = ChatGoogleGenerativeAI(
        model=reasoning_model,
        temperature=0,
        max_retries=2,
        api_key=os.getenv("GEMINI_API_KEY"),
    )
    result = llm.invoke(formatted_prompt)

    # Replace the short urls with the original urls and add all used urls to the sources_gathered
    unique_sources = []
    for source in state["sources_gathered"]:
        if source["short_url"] in result.content:
            result.content = result.content.replace(
                source["short_url"], source["value"]
            )
            unique_sources.append(source)

    return {
        "messages": [AIMessage(content=result.content)],
        "sources_gathered": unique_sources,
    }


# Create our Agent Graph
builder = StateGraph(OverallState, config_schema=Configuration)

# Define the nodes we will cycle between
builder.add_node("generate_query", generate_query)
builder.add_node("web_research", web_research)
builder.add_node("reflection", reflection)
builder.add_node("finalize_answer", finalize_answer)

# Set the entrypoint as `generate_query`
# This means that this node is the first one called
builder.add_edge(START, "generate_query")
# Add conditional edge to continue with search queries in a parallel branch
builder.add_conditional_edges(
    "generate_query", continue_to_web_research, ["web_research"]
)
# Reflect on the web research
builder.add_edge("web_research", "reflection")
# Evaluate the research
builder.add_conditional_edges(
    "reflection", evaluate_research, ["web_research", "finalize_answer"]
)
# Finalize the answer
builder.add_edge("finalize_answer", END)

graph = builder.compile(name="pro-search-agent")








