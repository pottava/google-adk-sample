import os
import requests
from google.adk.agents import Agent
from googleapiclient.discovery import build

# Google Custom Search API Config
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY", "YOUR_API_KEY")
GOOGLE_CSE_ID = os.environ.get("GOOGLE_CSE_ID", "YOUR_CSE_ID")
GOOGLE_SEARCH_URL = "https://www.googleapis.com/customsearch/v1"


def google_search(query: str) -> dict:
    """
    Performs a search query using the Google Custom Search JSON API.

    Args:
        query: The search query string provided by the ADK agent.

    Returns:
        A dictionary containing a list of search results or an error message.
        Matches the output_schema defined in tools.yaml.
    """
    if GOOGLE_API_KEY == "YOUR_API_KEY" or GOOGLE_CSE_ID == "YOUR_CSE_ID":
        print("Warning: GOOGLE_API_KEY or GOOGLE_CSE_ID environment variables not set.")
        return {"error": "Google Custom Search is not configured (API Key or CSE ID missing)."}

    try:
        service = build("customsearch", "v1", developerKey=GOOGLE_API_KEY)
        result = (
            service.cse()
            .list(
                q=query,
                cx=GOOGLE_CSE_ID,
                num=5,
                hl="ja",
                gl="jp",
            )
            .execute()
        )

        results = []
        if "items" in result:
            for item in result["items"]:
                results.append(
                    {
                        "title": item.get("title", "No Title"),
                        "snippet": item.get("snippet", ""),
                        "url": item.get("link", ""),
                    }
                )
        return {"results": results}

    except requests.exceptions.RequestException as e:
        print(f"Error during Google Custom Search API call: {e}")
        return {"error": f"Failed to execute Google Custom Search: {str(e)}"}
    except Exception as e:
        print(f"Error processing Google Custom Search results: {e}")
        return {"error": f"Failed to process Google Custom Search results: {str(e)}"}


root_agent = Agent(
    name="google_search_agent",
    model="gemini-2.0-flash-001",
    description=("Agent to answer questions about anything."),
    instruction=("You are a helpful agent who can answer user questions about anything on the internet."),
    tools=[google_search],
)
