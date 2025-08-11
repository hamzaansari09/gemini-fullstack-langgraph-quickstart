import unittest
from unittest.mock import patch, MagicMock

from langchain_core.messages import AIMessage

from agent.graph import graph
from agent.tools_and_schemas import SearchQueryList, Reflection, ResearchTopic
from dotenv import load_dotenv
load_dotenv()

class TestGraph(unittest.TestCase):
    @patch('agent.graph.ChatAnthropic')
    @patch('agent.graph.tavily_client')
    def test_invoke_graph(self, mock_tavily_client, mock_chat_anthropic):
        # Mock for extract_context
        mock_structured_llm_extract_context = MagicMock()
        mock_structured_llm_extract_context.invoke.return_value = ResearchTopic(research_topic="Who won the euro 2024")

        # Mock for generate_query
        mock_structured_llm_generate_query = MagicMock()
        mock_structured_llm_generate_query.invoke.return_value = SearchQueryList(query=["query1", "query2"], rationale="test rationale")

        # Mock for reflection
        mock_structured_llm_reflection = MagicMock()
        mock_structured_llm_reflection.invoke.return_value = Reflection(
            is_sufficient=True,
            knowledge_gap="",
            follow_up_queries=[]
        )

        # Mock for finalize_answer
        mock_finalize_answer_llm = MagicMock()
        mock_finalize_answer_llm.invoke.return_value = AIMessage(content="Final Answer")

        # Mock the llm instance
        mock_llm_instance = MagicMock()
        mock_llm_instance.with_structured_output.side_effect = [
            mock_structured_llm_extract_context,
            mock_structured_llm_generate_query,
            mock_structured_llm_reflection,
        ]
        # The last call to the llm is not structured
        mock_llm_instance.invoke = mock_finalize_answer_llm.invoke

        mock_chat_anthropic.return_value = mock_llm_instance

        # Mock the tavily_client for web_research
        mock_tavily_client.search.return_value = {
            "results": [
                {
                    "url": "http://example.com/1",
                    "content": "some research text 1",
                    "title": "Example 1"
                },
                {
                    "url": "http://example.com/2",
                    "content": "some research text 2",
                    "title": "Example 2"
                }
            ]
        }


        # Invoke the graph
        state = graph.invoke({
            "messages": [{"role": "user", "content": "Who won the euro 2024"}],
            "max_research_loops": 1,
            "initial_search_query_count": 2,
        })

        # Add assertions to verify the state
        self.assertIn("messages", state)
        self.assertEqual(state["messages"][-1].content, "Final Answer")


if __name__ == '__main__':
    unittest.main()
