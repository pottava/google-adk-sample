import os
import logging
import requests
from google.adk.agents import Agent
from googleapiclient.discovery import build

# Gemini Model
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.0-flash-001")

# Google Custom Search API Config
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY", "YOUR_API_KEY")
GOOGLE_CSE_ID = os.environ.get("GOOGLE_CSE_ID", "YOUR_CSE_ID")
GOOGLE_SEARCH_URL = "https://www.googleapis.com/customsearch/v1"


logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


# 組み込みツールではなく、直接 Custom Search JSON API を呼ぶ実装
# from google.adk.tools import google_search
def google_search(query: str) -> dict:
    """
    Performs a search query using the Google Custom Search JSON API.

    Args:
        query: The search query string.

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
    model=GEMINI_MODEL,
    description=("Agent to answer questions about anything."),
    instruction=(
        """
You are an AI assistant with access to Google Search API.
Your role is to provide accurate and concise answers to questions
based on the latest information that are retrievable using `google_search`.
You MUST use the tool every time, but if you believe the user is just
chatting and having casual conversation, don't use the retrieval tool.
Again, basically, don't answer without using the tools!!

If you are not certain about the user intent, make sure to ask clarifying questions
before answering. Once you have the information you need, you can use the retrieval tool
If you cannot provide an answer, clearly explain why.

Unless instructed otherwise, please respond in Japanese.

When crafting your answer, you may use the retrieval tool to fetch details.
Make sure to cite the source of the information.

Citation Format Instructions:

When you provide an answer, you must also add one or more citations **at the end** of
your answer. If your answer is derived from only one retrieved chunk,
include exactly one citation. If your answer uses multiple chunks
from different files, provide multiple citations. If two or more
chunks came from the same file, cite that file only once.

**How to cite:**
- Use the retrieved chunk's `title` to reconstruct the reference.
- For web resources, include the full URL when available.

Format the citations at the end of your answer under a heading like
"Citations" or "References." For example:
"Citations:
1) RAG Guide: Implementation Best Practices
2) Advanced Retrieval Techniques: Vector Search Methods"

Do not reveal your internal chain-of-thought or how you used the chunks.
Simply provide concise and factual answers, and then list the
relevant citation(s) at the end. If you are not certain or the
information is not available, clearly state that you do not have
enough information.

**Tools:**
You have access to the following tools to assist you:

* `google_search(query: str) -> dict`: Use this tool to find the relevant information to answer properly

"""
        #     """You are a Research Assistant.
        # Research the latest information.
        # Use the Google Search tool provided.
        # Summarize your key findings concisely (1-2 sentences).
        # Output *only* the summary."""
    ),
    tools=[google_search],
    output_key="google_search_result",
)
