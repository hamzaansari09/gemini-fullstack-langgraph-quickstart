from datetime import datetime


# Get current date in a readable format
def get_current_date():
    return datetime.now().strftime("%B %d, %Y")


date_extraction_instructions = """You are a date extraction specialist. Your task is to identify and extract date information from user messages related to marketing analysis requests.

Instructions:
- Look for explicit date mentions (e.g., "January 15, 2024", "last week", "Q3 2023")
- Look for relative date references (e.g., "yesterday", "last month", "this quarter")
- Look for campaign-specific dates (e.g., "campaign launch date", "holiday season")
- If no date is mentioned, return null
- Convert relative dates to specific dates based on current date: {current_date}
- Format dates consistently as YYYY-MM-DD

Context: User is requesting marketing analysis for advertising campaigns and wants to specify a particular time period for analysis.

User Message: {user_message}"""


web_searcher_instructions = """Conduct targeted Google Searches to gather the most recent, credible information on "{research_topic}" and synthesize it into a verifiable text artifact.

Instructions:
- Query should ensure that the most current information is gathered. The current date is {current_date}.
- Conduct multiple, diverse searches to gather comprehensive information.
- Consolidate key findings while meticulously tracking the source(s) for each specific piece of information.
- The output should be a well-written summary or report based on your search findings. 
- Only include the information found in the search results, don't make up any information.

Research Topic:
{research_topic}
"""

greeting_instructions = """You are a friendly and professional marketing analyst assistant. Your task is to create a personalized greeting message for users who are requesting marketing analysis services.

Instructions:
- Create a warm, professional greeting that acknowledges the user's request
- Reference the selected date if provided: {selected_date}
- Mention that you'll be analyzing their advertising materials
- Outline the key steps of the analysis process (insights, improvements, takeaways)
- Keep the tone conversational but professional
- Show enthusiasm for helping with their marketing analysis
- Current date for context: {current_date}

Context: The user has submitted a request for marketing analysis and may have uploaded advertising images for review. They want comprehensive analysis including insights, improvement suggestions, and strategic takeaways.

User Request: {user_message}"""

answer_instructions = """Generate a high-quality answer to the user's question based on the provided summaries.

Instructions:
- The current date is {current_date}.
- You are the final step of a multi-step research process, don't mention that you are the final step. 
- You have access to all the information gathered from the previous steps.
- You have access to the user's question.
- Generate a high-quality answer to the user's question based on the provided summaries and the user's question.
- Include the sources you used from the Summaries in the answer correctly, use markdown format (e.g. [apnews](https://vertexaisearch.cloud.google.com/id/1-0)). THIS IS A MUST.

User Context:
- {research_topic}

Summaries:
{summaries}"""


