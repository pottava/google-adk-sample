import os
import logging
from google.adk.agents import Agent
from google.cloud import discoveryengine_v1 as discoveryengine

# Gemini Model
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.0-flash-001")

# Vertex AI Search Config
PROJECT_ID = os.environ.get("GOOGLE_CLOUD_PROJECT", "your-gcp-project-id")
DATA_STORE_ID = os.environ.get("VAIS_DATA_STORE_ID", "your-data-store-id")
DATA_STORE_LOCATION = "global"
SERVING_CONFIG = f"projects/{PROJECT_ID}/locations/{DATA_STORE_LOCATION}/collections/default_collection/dataStores/{DATA_STORE_ID}/servingConfigs/default_serving_config"


logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


# remove "gs://bucket_name/"
def extract_path_from_link(link: str):
    return "/".join(link[5:].split("/")[1:])


# === Vertex AI Search Tool Function ===
def vertex_ai_search(query: str) -> dict:
    """
    Performs a search query against a specified Vertex AI Search Data Store.

    Args:
        query: The search query string

    Returns:
        A dictionary containing a list of search results or an error message.
        Matches the output_schema defined in tools.yaml.
    """
    if PROJECT_ID == "your-gcp-project-id" or DATA_STORE_ID == "your-data-store-id":
        print("Warning: PROJECT_ID or DATA_STORE_ID might not be configured correctly.")
        return {"error": "Vertex AI Search is not configured (Project ID or Data Store ID missing)."}

    content_search_spec = discoveryengine.SearchRequest.ContentSearchSpec(
        snippet_spec=discoveryengine.SearchRequest.ContentSearchSpec.SnippetSpec(return_snippet=True),
        extractive_content_spec=discoveryengine.SearchRequest.ContentSearchSpec.ExtractiveContentSpec(
            max_extractive_answer_count=5,
            max_extractive_segment_count=1,
        ),
    )
    try:
        request = discoveryengine.SearchRequest(
            serving_config=SERVING_CONFIG,
            content_search_spec=content_search_spec,
            query=query,
            page_size=5,
            spell_correction_spec=discoveryengine.SearchRequest.SpellCorrectionSpec(
                mode=discoveryengine.SearchRequest.SpellCorrectionSpec.Mode.AUTO
            ),
        )
        response = discoveryengine.SearchServiceClient().search(request=request)

        results = []
        for result in response.results:
            doc = getattr(result.document, "derived_struct_data", None)
            if not doc:
                continue

            answer = ""
            for chunk in doc.get("extractive_answers", []):
                answer = chunk.get("content", "").replace("\n", "")

            segment = ""
            for chunk in doc.get("extractive_segments", []):
                segment = chunk.get("content", "").replace("\n", "")

            snippet = ""
            for chunk in doc.get("snippets", []):
                snippet = chunk.get("snippet", "").replace("\n", "")

            results.append(
                {
                    "id": result.document.id,
                    "title": doc.get("title", "No Title"),
                    "url": extract_path_from_link(doc.get("link", "")),
                    "answer": answer,
                    "segment": segment,
                    "snippet": snippet,
                }
            )
        return {"results": results}

    except Exception as e:
        print(f"Error during Vertex AI Search: {e}")
        return {"error": f"Failed to execute Vertex AI Search: {str(e)}"}


root_agent = Agent(
    name="vertex_ai_search_agent",
    model=GEMINI_MODEL,
    description=("Agent to answer questions about cars."),
    instruction=(
        """
You are an AI assistant with access to Vertex AI Search API.
Your role is to provide accurate and concise answers to questions
based on the internal information that are retrievable using `vertex_ai_search`.
You should use the tool if it is related to automotive, but if you believe the user
is just chatting and having casual conversation, don't use the retrieval tool.

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

* `vertex_ai_search(query: str) -> dict`: Use this tool to find the car related internal information

"""
        #     """You are a Research Assistant specializing in automotive specs.
        # Use the internal search tool names `vertex_ai_search`.
        # Summarize your key findings concisely (1-2 sentences).
        # Output *only* the summary."""
    ),
    tools=[vertex_ai_search],
    output_key="vertex_ai_search_result",
)
