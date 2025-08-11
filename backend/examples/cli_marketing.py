import argparse
import base64
import os
from pathlib import Path
from langchain_core.messages import HumanMessage
from marketing_agent.graph import graph


def encode_image_to_base64(image_path: str) -> str:
    """Encode an image file to base64 string.
    
    Args:
        image_path: Path to the image file
        
    Returns:
        Base64 encoded string of the image
        
    Raises:
        FileNotFoundError: If the image file doesn't exist
        ValueError: If the file is not a supported image format
    """
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Image file not found: {image_path}")
    
    # Check if file has a supported extension
    supported_extensions = {'.jpg', '.jpeg', '.png', '.webp'}
    file_extension = Path(image_path).suffix.lower()
    if file_extension not in supported_extensions:
        raise ValueError(f"Unsupported image format: {file_extension}. Supported formats: {supported_extensions}")
    
    # Check file size (10MB limit)
    file_size = os.path.getsize(image_path)
    max_size = 10 * 1024 * 1024  # 10MB in bytes
    if file_size > max_size:
        raise ValueError(f"Image file too large: {file_size / (1024*1024):.1f}MB. Maximum size: 10MB")
    
    with open(image_path, "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
    
    return encoded_string


def main() -> None:
    """Run the marketing agent from the command line."""
    parser = argparse.ArgumentParser(
        description="Run the LangGraph marketing analyst agent for ad analysis",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python cli_marketing.py "Analyze this holiday campaign ad" --image ad_sample.jpg
  python cli_marketing.py "Review this social media ad for Q4 2024" --image campaign.png --date "2024-12-15"
  python cli_marketing.py "What insights can you provide for this ad?" --image ad.jpg --vision-model gemini-2.0-flash
        """
    )
    
    parser.add_argument(
        "query", 
        help="Marketing analysis query or request"
    )
    parser.add_argument(
        "--image", 
        required=True,
        help="Path to the advertisement image file (JPG, PNG, WebP)"
    )
    parser.add_argument(
        "--date",
        help="Analysis date (YYYY-MM-DD format) or relative date (e.g., 'today', 'last week')"
    )
    parser.add_argument(
        "--vision-model",
        default="gemini-2.0-flash",
        help="Vision model for image analysis (default: gemini-2.0-flash)"
    )
    parser.add_argument(
        "--reasoning-model",
        default="gemini-2.5-flash",
        help="Reasoning model for takeaways synthesis (default: gemini-2.5-flash)"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Show detailed output including intermediate steps"
    )
    
    args = parser.parse_args()

    try:
        # Encode the image to base64
        print(f"Loading and encoding image: {args.image}")
        image_data = encode_image_to_base64(args.image)
        print(f"✓ Image encoded successfully ({len(image_data)} characters)")
        
        # Create the marketing agent state
        state = {
            "messages": [HumanMessage(content=args.query)],
            "image_data": image_data,
            "selected_date": args.date,
            "insights": None,
            "improvements": None,
            "takeaways": None,
            "greeting_sent": False,
            "analysis_complete": False,
        }
        
        print(f"\n🚀 Starting marketing analysis...")
        print(f"Query: {args.query}")
        if args.date:
            print(f"Analysis Date: {args.date}")
        print(f"Vision Model: {args.vision_model}")
        print(f"Reasoning Model: {args.reasoning_model}")
        print("-" * 60)
        
        # Run the marketing agent graph
        result = graph.invoke(state)
        
        # Extract and display results
        messages = result.get("messages", [])
        
        if args.verbose:
            print(f"\n📊 Analysis Results:")
            print(f"Selected Date: {result.get('selected_date', 'Not specified')}")
            print(f"Greeting Sent: {result.get('greeting_sent', False)}")
            print(f"Analysis Complete: {result.get('analysis_complete', False)}")
            print(f"Total Messages: {len(messages)}")
            print("-" * 60)
        
        # Display all messages from the analysis
        if messages:
            print(f"\n📋 Marketing Analysis Results:\n")
            for i, message in enumerate(messages, 1):
                if hasattr(message, 'content') and message.content:
                    if args.verbose:
                        print(f"Step {i}:")
                    print(message.content)
                    if i < len(messages):
                        print("\n" + "="*60 + "\n")
        else:
            print("❌ No analysis results generated. Please check your inputs and try again.")
            
        # Display structured results if available
        if args.verbose:
            insights = result.get("insights")
            improvements = result.get("improvements") 
            takeaways = result.get("takeaways")
            
            if insights:
                print(f"\n🔍 Insights Count: {len(insights)}")
            if improvements:
                print(f"💡 Improvements Count: {len(improvements)}")
            if takeaways:
                print(f"📈 Takeaways Count: {len(takeaways)}")
                
    except FileNotFoundError as e:
        print(f"❌ Error: {e}")
        print("Please check that the image file path is correct.")
    except ValueError as e:
        print(f"❌ Error: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    main()
