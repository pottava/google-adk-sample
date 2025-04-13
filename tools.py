# tools.py
# Contains custom tool functions for ADK:
# - search_google_custom: Searches Google Custom Search API
# - search_vertex_ai: Searches Vertex AI Search

# --- Prerequisites ---
# 1. Install necessary Google Cloud & HTTP client libraries:
#    pip install google-cloud-discoveryengine requests
# 2. Authentication:
#    - For Vertex AI: Ensure ADC is set up (gcloud auth application-default login)
#      or service account has permissions ('roles/discoveryengine.viewer').
#    - For Google Custom Search: Obtain an API Key and Search Engine ID (CX).
# 3. Environment Variables: Set the following environment variables:
#    - GOOGLE_CLOUD_PROJECT: Your GCP project ID.
#    - GOOGLE_API_KEY: Your Google Custom Search API Key.
#    - GOOGLE_CSE_ID: Your Google Custom Search Engine ID (CX).
# ---------------------
import sys
import os
import requests
from google.cloud import discoveryengine_v1 as discoveryengine
from googleapiclient.discovery import build

# Vertex AI Search Config
PROJECT_ID = os.environ.get("GOOGLE_CLOUD_PROJECT", "your-gcp-project-id")
LOCATION = "global"
DATA_STORE_ID = os.environ.get("VAIS_DATA_STORE_ID", "your-data-store-id")
SERVING_CONFIG = f"projects/{PROJECT_ID}/locations/{LOCATION}/collections/default_collection/dataStores/{DATA_STORE_ID}/servingConfigs/default_serving_config"

# Google Custom Search API Config
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY", "YOUR_API_KEY")
GOOGLE_CSE_ID = os.environ.get("GOOGLE_CSE_ID", "YOUR_CSE_ID")
GOOGLE_SEARCH_URL = "https://www.googleapis.com/customsearch/v1"


# remove "gs://bucket_name/"
def extract_path_from_link(link: str):
    return "/".join(link[5:].split("/")[1:])


# === Vertex AI Search Tool Function ===
def search_vertex_ai(query: str) -> dict:
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


# === Google Custom Search Tool Function ===
def search_google_custom(query: str) -> dict:
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


# --- Example Usage for testing this script directly ---
if __name__ == "__main__":
    args = sys.argv
    test_query_vertex = args[1]
    test_query_google = args[2]

    # --- Test Vertex AI Search ---
    if PROJECT_ID == "your-gcp-project-id" or DATA_STORE_ID == "your-data-store-id":
        print("\n--- Vertex AI Search Test Skipped (Configuration Missing) ---")
    else:
        print(f"\n--- Testing Vertex AI Search with query: '{test_query_vertex}' ---")
        vertex_result = search_vertex_ai(test_query_vertex)

        if "error" in vertex_result:
            print(f"Search failed: {vertex_result['error']}")

        elif vertex_result.get("results"):
            print("--- Vertex AI Search Results ---")
            for i, res in enumerate(vertex_result["results"]):
                print(f"{i+1}. URL: {res.get('url')}")
                # print(f"   Answer: {res.get('answer')}")
                # print(f"   Segment: {res.get('segment')}")
                print(f"   Snippet: {res.get('snippet')}")
                print("-" * 10)
        else:
            print("No Vertex AI results found.")

    # --- Test Google Custom Search ---
    if GOOGLE_API_KEY == "YOUR_API_KEY" or GOOGLE_CSE_ID == "YOUR_CSE_ID":
        print("\n--- Google Custom Search Test Skipped (Configuration Missing) ---")
    else:
        print(f"\n--- Testing Google Custom Search with query: '{test_query_google}' ---")
        google_result = search_google_custom(test_query_google)

        if "error" in google_result:
            print(f"Search failed: {google_result['error']}")

        elif google_result.get("results"):
            print("--- Google Custom Search Results ---")
            for i, res in enumerate(google_result["results"]):
                print(f"{i+1}. Title: {res.get('title')}")
                print(f"   URL: {res.get('url')}")
                print(f"   Snippet: {res.get('snippet')}")
                print("-" * 10)
        else:
            print("No Google Custom Search results found.")
