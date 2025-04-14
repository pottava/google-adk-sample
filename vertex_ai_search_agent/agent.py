import os
from google.adk.agents import Agent
from google.cloud import discoveryengine_v1 as discoveryengine

# Vertex AI Search Config
PROJECT_ID = os.environ.get("GOOGLE_CLOUD_PROJECT", "your-gcp-project-id")
DATA_STORE_ID = os.environ.get("VAIS_DATA_STORE_ID", "your-data-store-id")
DATA_STORE_LOCATION = "global"
SERVING_CONFIG = f"projects/{PROJECT_ID}/locations/{DATA_STORE_LOCATION}/collections/default_collection/dataStores/{DATA_STORE_ID}/servingConfigs/default_serving_config"


# remove "gs://bucket_name/"
def extract_path_from_link(link: str):
    return "/".join(link[5:].split("/")[1:])


# === Vertex AI Search Tool Function ===
def vertex_ai_search(query: str) -> dict:
    """
    Performs a search query against a specified Vertex AI Search Data Store.

    Args:
        query: The search query string provided by the ADK agent.

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
    model="gemini-2.0-flash-001",
    description=("Agent to answer questions about cars."),
    instruction=("You are a helpful agent who can answer user questions about cars."),
    tools=[vertex_ai_search],
)
