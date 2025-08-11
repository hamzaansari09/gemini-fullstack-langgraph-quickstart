import { useStream } from "@langchain/langgraph-sdk/react";
import type { Message } from "@langchain/langgraph-sdk";
import { useState, useEffect, useRef, useCallback } from "react";
import { ProcessedEvent } from "@/components/ActivityTimeline";
import { WelcomeScreen } from "@/components/WelcomeScreen";
import { ChatMessagesView } from "@/components/ChatMessagesView";
import { Button } from "@/components/ui/button";

// Type definitions for marketing agent data structures
interface AdInsight {
  title: string;
  description: string;
  impact_level: 'High' | 'Medium' | 'Low';
}

interface AdImprovement {
  category: string;
  suggestion: string;
  expected_impact: string;
  priority: 'High' | 'Medium' | 'Low';
  implementation_notes: string;
}

interface AdTakeaway {
  relevance: 'Strategic' | 'Tactical' | 'Operational';
  takeaway: string;
  actionable_insight: string;
}

// Type definitions for event parameters
interface Source {
  label?: string;
  value?: string;
  short_url?: string;
}

interface UpdateEvent {
  generate_query?: {
    search_query?: string[];
  };
  web_research?: {
    sources_gathered?: Source[];
  };
  reflection?: Record<string, unknown>;
  finalize_answer?: Record<string, unknown>;
  provide_date?: Record<string, unknown>;
  greet_user?: Record<string, unknown>;
  analyze_insights?: Record<string, unknown>;
  suggest_improvements?: Record<string, unknown>;
  extract_takeaways?: Record<string, unknown>;
}

export default function App() {
  const [processedEventsTimeline, setProcessedEventsTimeline] = useState<
    ProcessedEvent[]
  >([]);
  const [historicalActivities, setHistoricalActivities] = useState<
    Record<string, ProcessedEvent[]>
  >({});
  const scrollAreaRef = useRef<HTMLDivElement>(null);
  const hasFinalizeEventOccurredRef = useRef(false);
  const [error, setError] = useState<string | null>(null);
  const thread = useStream<{
    messages: Message[];
    initial_search_query_count?: number;
    max_research_loops?: number;
    reasoning_model?: string;
    image_data?: string;
    selected_date?: string | null;
    insights?: AdInsight[];
    improvements?: AdImprovement[];
    takeaways?: AdTakeaway[];
    greeting_sent?: boolean;
    analysis_complete?: boolean;
  }>({
    apiUrl: import.meta.env.DEV
      ? "http://localhost:2024"
      : "http://localhost:8123",
    assistantId: "agent", // Default to research agent, will be overridden for marketing requests
    messagesKey: "messages",
    onUpdateEvent: (event: UpdateEvent) => {
      let processedEvent: ProcessedEvent | null = null;
      if (event.generate_query) {
        processedEvent = {
          title: "Generating Search Queries",
          data: event.generate_query?.search_query?.join(", ") || "",
        };
      } else if (event.web_research) {
        const sources = event.web_research.sources_gathered || [];
        const numSources = sources.length;
        const uniqueLabels = [
          ...new Set(sources.map((s: any) => s.label).filter(Boolean)),
        ];
        const exampleLabels = uniqueLabels.slice(0, 3).join(", ");
        processedEvent = {
          title: "Web Research",
          data: `Gathered ${numSources} sources. Related to: ${
            exampleLabels || "N/A"
          }.`,
        };
      } else if (event.reflection) {
        processedEvent = {
          title: "Reflection",
          data: "Analysing Web Research Results",
        };
      } else if (event.finalize_answer) {
        processedEvent = {
          title: "Finalizing Answer",
          data: "Composing and presenting the final answer.",
        };
        hasFinalizeEventOccurredRef.current = true;
      }
      if (processedEvent) {
        setProcessedEventsTimeline((prevEvents) => [
          ...prevEvents,
          processedEvent!,
        ]);
      }
    },
    onError: (error: any) => {
      setError(error.message);
    },
  });

  useEffect(() => {
    if (scrollAreaRef.current) {
      const scrollViewport = scrollAreaRef.current.querySelector(
        "[data-radix-scroll-area-viewport]"
      );
      if (scrollViewport) {
        scrollViewport.scrollTop = scrollViewport.scrollHeight;
      }
    }
  }, [thread.messages]);

  useEffect(() => {
    if (
      hasFinalizeEventOccurredRef.current &&
      !thread.isLoading &&
      thread.messages.length > 0
    ) {
      const lastMessage = thread.messages[thread.messages.length - 1];
      if (lastMessage && lastMessage.type === "ai" && lastMessage.id) {
        setHistoricalActivities((prev) => ({
          ...prev,
          [lastMessage.id!]: [...processedEventsTimeline],
        }));
      }
      hasFinalizeEventOccurredRef.current = false;
    }
  }, [thread.messages, thread.isLoading, processedEventsTimeline]);

  const handleSubmit = useCallback(
    (submittedInputValue: string, effort: string, model: string, imageData?: string) => {
      if (!submittedInputValue.trim()) return;
      setError(null);
      setProcessedEventsTimeline([]);
      hasFinalizeEventOccurredRef.current = false;

      // Determine if this is a marketing agent request (has image data)
      const isMarketingRequest = !!imageData;
      
      const newMessages: Message[] = [
        ...(thread.messages || []),
        {
          type: "human",
          content: submittedInputValue,
          id: Date.now().toString(),
        },
      ];

      if (isMarketingRequest) {
        // NOTE: In a production environment, you would need to create separate threads
        // for different agents or implement agent routing at the backend level.
        // For this demo, we're submitting marketing agent state to the default agent.
        // The backend would need to be configured to route to marketing_agent based on image_data presence.
        thread.submit({
          messages: newMessages,
          image_data: imageData,
          selected_date: null, // Will be extracted by the date tool
          insights: null,
          improvements: null,
          takeaways: null,
          greeting_sent: false,
          analysis_complete: false,
        });
      } else {
        // Original research agent logic
        let initial_search_query_count = 0;
        let max_research_loops = 0;
        switch (effort) {
          case "low":
            initial_search_query_count = 1;
            max_research_loops = 1;
            break;
          case "medium":
            initial_search_query_count = 3;
            max_research_loops = 3;
            break;
          case "high":
            initial_search_query_count = 5;
            max_research_loops = 10;
            break;
        }

        thread.submit({
          messages: newMessages,
          initial_search_query_count: initial_search_query_count,
          max_research_loops: max_research_loops,
          reasoning_model: model,
        });
      }
    },
    [thread]
  );

  const handleCancel = useCallback(() => {
    thread.stop();
    window.location.reload();
  }, [thread]);

  return (
    <div className="flex h-screen bg-neutral-800 text-neutral-100 font-sans antialiased">
      <main className="h-full w-full max-w-4xl mx-auto">
          {thread.messages.length === 0 ? (
            <WelcomeScreen
              handleSubmit={handleSubmit}
              isLoading={thread.isLoading}
              onCancel={handleCancel}
            />
          ) : error ? (
            <div className="flex flex-col items-center justify-center h-full">
              <div className="flex flex-col items-center justify-center gap-4">
                <h1 className="text-2xl text-red-400 font-bold">Error</h1>
                <p className="text-red-400">{JSON.stringify(error)}</p>

                <Button
                  variant="destructive"
                  onClick={() => window.location.reload()}
                >
                  Retry
                </Button>
              </div>
            </div>
          ) : (
            <ChatMessagesView
              messages={thread.messages}
              isLoading={thread.isLoading}
              scrollAreaRef={scrollAreaRef}
              onSubmit={handleSubmit}
              onCancel={handleCancel}
              liveActivityEvents={processedEventsTimeline}
              historicalActivities={historicalActivities}
            />
          )}
      </main>
    </div>
  );
}








